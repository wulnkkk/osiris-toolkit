"""Recursive-descent parser: token stream -> AST (Deck containing Sections)."""

from collections.abc import Iterator

from .ast import Deck, KeySpec, ParamAssignment, Section, SliceSpec
from .lexer import Token, TokenType
from .value_parser import assemble_params, parse_slice_dims, parse_value


class ParseError(Exception):
    """Error encountered during parsing."""

    def __init__(self, message: str, line: int = 0, col: int = 0):
        self.line = line
        self.col = col
        super().__init__(f"L{line}:{col} - {message}")


def parse_tokens(tokens: Iterator[Token], filename: str = "") -> Deck:
    """Parse a token stream into a Deck AST.

    Args:
        tokens: Iterator of Token objects.
        filename: Source filename for the deck.

    Returns:
        A Deck containing the parsed sections.

    Raises:
        ParseError: On syntax errors.
    """
    parser = _Parser(tokens, filename)
    return parser.parse()


class _Parser:
    def __init__(self, tokens: Iterator[Token], filename: str):
        self.tokens = tokens
        self.filename = filename
        self._current: Token | None = None
        self._advance()

    def _advance(self):
        try:
            self._current = next(self.tokens)
        except StopIteration:
            self._current = Token(TokenType.EOF, "", 0, 0)

    def _peek(self) -> Token:
        return self._current

    def _expect(self, expected_type: TokenType, message: str = "") -> Token:
        token = self._current
        if token.type != expected_type:
            msg = message or f"Expected {expected_type.name}, got {token.type.name} ({token.value!r})"
            raise ParseError(msg, token.line, token.col)
        self._advance()
        return token

    def parse(self) -> Deck:
        sections = []
        while self._peek().type != TokenType.EOF:
            sections.append(self._parse_section())
        return Deck(sections=sections, filename=self.filename)

    def _parse_section(self) -> Section:
        # Expect section name
        name_token = self._peek()
        if name_token.type != TokenType.SECTION_NAME:
            # Attempt recovery: skip to next SECTION_NAME or LBRACE
            raise ParseError(
                f"Expected section name, got {name_token.type.name} ({name_token.value!r})",
                name_token.line,
                name_token.col,
            )
        name = name_token.value
        line = name_token.line
        self._advance()

        # Optional whitespace/comments/newlines, then '{'
        brace_token = self._peek()
        if brace_token.type != TokenType.LBRACE:
            # Allow section name and '{' on different lines
            raise ParseError(
                f"Expected '{{' after section '{name}', got {brace_token.type.name}",
                brace_token.line,
                brace_token.col,
            )
        self._advance()

        # Parse parameters inside the braces
        raw_params = self._parse_param_list()

        # Expect '}'
        end_token = self._peek()
        if end_token.type != TokenType.RBRACE:
            raise ParseError(
                f"Expected '}}' to close section '{name}', got {end_token.type.name} ({end_token.value!r})",
                end_token.line,
                end_token.col,
            )
        self._advance()

        # Assemble typed parameters with schema awareness
        params = assemble_params(raw_params, section_name=name)

        return Section(name=name, params=params, raw_params=raw_params, line=line)

    def _parse_param_list(self) -> list[ParamAssignment]:
        """Parse zero or more ParamAssignments until RBRACE."""
        params = []
        while self._peek().type != TokenType.RBRACE:
            if self._peek().type == TokenType.EOF:
                raise ParseError(
                    "Unexpected end of file inside section (missing '}')",
                    self._peek().line,
                    self._peek().col,
                )
            params.append(self._parse_assignment())
            # Consume optional trailing comma
            if self._peek().type == TokenType.COMMA:
                self._advance()
            # Allow missing trailing comma before RBRACE
        return params

    def _parse_assignment(self) -> ParamAssignment:
        """Parse: keys... = value, value, ...

        keys may be: NAME or NAME SLICE (comma-separated for repetition).
        """
        line = self._peek().line

        # Parse key list
        keys = []
        while True:
            key_token = self._expect(TokenType.NAME, "Expected parameter name")
            key_name = key_token.value
            key_slice = None

            # Check for slice notation
            if self._peek().type == TokenType.SLICE:
                slice_token = self._current
                self._advance()
                key_slice = SliceSpec(dims=parse_slice_dims(slice_token.value))

            keys.append(KeySpec(name=key_name, slice=key_slice))

            # More keys (multi-key assignment)?
            if self._peek().type == TokenType.COMMA:
                # Check whether the next token is NAME (another key) or a value.
                # Since we use an iterator we cannot easily look ahead.
                # Strategy: consume comma, then check if next token is NAME.
                # If not a value, treat as another key.
                # Heuristic: if after comma we see NAME + EQUALS pattern,
                # it's another assignment (trailing comma). If NAME + COMMA
                # or NAME + SLICE, treat as multi-key.
                self._advance()  # consume comma
                if self._peek().type == TokenType.EQUALS:
                    # Trailing comma before equals
                    break
                if self._peek().type == TokenType.NAME:
                    # Check further: does this NAME have another comma, slice,
                    # or equals following it?
                    # For now, continue collecting keys
                    continue
                else:
                    # Could be a value after a broken comma — can't rewind,
                    # but should not occur in valid input.
                    break
            elif self._peek().type == TokenType.EQUALS:
                break
            else:
                raise ParseError(
                    f"Expected ',' or '=' after parameter '{keys[-1].name}', got {self._peek().type.name}",
                    self._peek().line,
                    self._peek().col,
                )

        # Expect '='
        self._expect(TokenType.EQUALS, "Expected '=' after parameter name")

        # Parse value list
        values: list[str] = []
        value_types: list[TokenType] = []
        while True:
            token = self._peek()
            if token.type in (TokenType.STRING, TokenType.BOOLEAN, TokenType.REAL, TokenType.INTEGER):
                values.append(parse_value(token.value, token.type))
                value_types.append(token.type)
                self._advance()

                # Next: comma means another value, or end of assignment
                if self._peek().type == TokenType.COMMA:
                    self._advance()
                    # Check if next is a value or start of a new assignment
                    if self._peek().type in (TokenType.NAME, TokenType.RBRACE):
                        # Comma is trailing (or end of parameter list)
                        # For multi-key assignment this comma separates keys.
                        # For values, it's a trailing comma before RBRACE.
                        # The NAME case is handled by _parse_param_list.
                        break
                    continue
                else:
                    break
            else:
                # Not a value — end of assignment
                break

        return ParamAssignment(keys=keys, raw_values=values, line=line)
