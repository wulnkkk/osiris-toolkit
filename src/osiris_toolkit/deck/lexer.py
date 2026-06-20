"""Lexer for OSIRIS input deck files.

Converts curly-brace style Fortran namelist input into a token stream
with line/column tracking for error reporting.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    SECTION_NAME = auto()  # identifier followed by '{' (on same or next line)
    NAME = auto()  # parameter name or other identifier
    LBRACE = auto()  # '{'
    RBRACE = auto()  # '}'
    EQUALS = auto()  # '='
    COMMA = auto()  # ','
    STRING = auto()  # "..." or '...'
    BOOLEAN = auto()  # .true. / .false.
    REAL = auto()  # floating-point number, may contain 'd' exponent
    INTEGER = auto()  # signed integer
    SLICE = auto()  # (1:3) or (1:2,1) — appended to preceding NAME
    EOF = auto()  # end of input


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


# Valid identifier characters (Fortran rules: a-z, 0-9, _)
_ID_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_ID_CONTINUE = _ID_START | set("0123456789")

# Characters that always terminate a value token
_VALUE_TERMINATORS = {",", "}", "\n", "!", " ", "\t", "\r"}


def tokenize(source: str, filename: str = "<input>") -> Iterator[Token]:
    """Generate tokens from an OSIRIS input deck source string.

    Args:
        source: Raw input deck text.
        filename: Name for error messages (not used by lexer, but stored).

    Yields:
        Token objects. The final token is always TokenType.EOF.
    """
    return _Tokenizer(source).tokenize()


class _Tokenizer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self._len = len(source)
        # State tracking
        self._expecting_value = False  # True after seeing '='
        self._just_saw_section_name = False  # True after emitting SECTION_NAME

    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        if p < self._len:
            return self.src[p]
        return "\0"

    def _advance(self, n: int = 1):
        for _ in range(n):
            if self.pos < self._len:
                if self.src[self.pos] == "\n":
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.pos += 1

    def _skip_whitespace(self):
        while self.pos < self._len and self.src[self.pos] in (" ", "\t", "\r"):
            self._advance()

    def _skip_whitespace_and_newlines(self):
        while self.pos < self._len and self.src[self.pos] in (" ", "\t", "\r", "\n"):
            self._advance()

    def _read_comment(self):
        """Read from '!' to end of line (discard)."""
        while self.pos < self._len and self.src[self.pos] != "\n":
            self._advance()

    def _read_identifier(self) -> str:
        start = self.pos
        while self.pos < self._len and self.src[self.pos] in _ID_CONTINUE:
            self._advance()
        return self.src[start : self.pos]

    def _read_string(self, quote: str) -> str:
        """Read a quoted string, handling escaped quotes."""
        self._advance()  # skip opening quote
        start = self.pos
        while self.pos < self._len:
            ch = self.src[self.pos]
            if ch == "\\" and self._peek(1) == quote:
                self._advance(2)  # skip escaped quote
            elif ch == quote:
                val = self.src[start : self.pos]
                self._advance()  # skip closing quote
                return val
            else:
                self._advance()
        # Unterminated string — return what was read
        return self.src[start : self.pos]

    def _read_number_or_bool(self) -> Token:
        """Read a number (integer or real) or boolean (.true./.false.)."""
        start_pos = self.pos
        start_line = self.line
        start_col = self.col

        # Check for boolean
        if self.src[self.pos] == ".":
            rest = self.src[self.pos : self.pos + 7].lower()
            if rest.startswith(".true."):
                for _ in range(6):
                    self._advance()
                return Token(TokenType.BOOLEAN, "true", start_line, start_col)
            if rest.startswith(".false."):
                for _ in range(7):
                    self._advance()
                return Token(TokenType.BOOLEAN, "false", start_line, start_col)
            # Not a valid boolean (e.g. misspelled .Ture.) — don't fall into
            # number parsing, which would produce float(".")
            self._advance()  # skip leading '.'
            while self.pos < self._len and self.src[self.pos] in _ID_CONTINUE:
                self._advance()
            if self.pos < self._len and self.src[self.pos] == ".":
                self._advance()  # skip trailing '.'
            raw = self.src[start_pos : self.pos]
            return Token(TokenType.NAME, raw, start_line, start_col)

        # Read optional leading sign
        if self.src[self.pos] in ("+", "-"):
            self._advance()

        # Read digits before decimal point / exponent
        has_digits = False
        while self.pos < self._len and self.src[self.pos].isdigit():
            self._advance()
            has_digits = True

        is_real = False

        # Fractional part
        if self.pos < self._len and self.src[self.pos] == ".":
            is_real = True
            self._advance()
            while self.pos < self._len and self.src[self.pos].isdigit():
                self._advance()
                has_digits = True

        # Exponent: e or d, optionally signed
        if self.pos < self._len and self.src[self.pos].lower() in ("e", "d"):
            is_real = True
            self._advance()
            if self.pos < self._len and self.src[self.pos] in ("+", "-"):
                self._advance()
            while self.pos < self._len and self.src[self.pos].isdigit():
                self._advance()

        raw = self.src[start_pos : self.pos]

        if not has_digits and not is_real:
            # Should not occur in valid input; return as-is
            return Token(TokenType.NAME, raw, start_line, start_col)

        if is_real:
            # Normalize 'd' exponent to 'e' for Python parsing
            normalized = raw.lower().replace("d", "e")
            return Token(TokenType.REAL, normalized, start_line, start_col)
        else:
            return Token(TokenType.INTEGER, raw, start_line, start_col)

    def _read_slice(self) -> str:
        """Read slice content inside parentheses: 1:3 or 1:2,1 etc."""
        self._advance()  # skip '('
        start = self.pos
        depth = 1
        while self.pos < self._len and depth > 0:
            ch = self.src[self.pos]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    val = self.src[start : self.pos]
                    self._advance()  # skip ')'
                    return val
            self._advance()
        return self.src[start : self.pos]

    def tokenize(self) -> Iterator[Token]:
        while self.pos < self._len:
            self._skip_whitespace()

            if self.pos >= self._len:
                break

            ch = self.src[self.pos]
            start_line = self.line
            start_col = self.col

            # Handle newlines — important for comment termination and
            # deciding SECTION_NAME vs NAME context
            if ch == "\n":
                self._advance()
                self._expecting_value = False
                self._just_saw_section_name = False
                continue

            # Comment
            if ch == "!":
                self._read_comment()
                continue

            # Braces
            if ch == "{":
                self._advance()
                self._expecting_value = False
                self._just_saw_section_name = False
                yield Token(TokenType.LBRACE, "{", start_line, start_col)
                continue

            if ch == "}":
                self._advance()
                self._expecting_value = False
                self._just_saw_section_name = False
                yield Token(TokenType.RBRACE, "}", start_line, start_col)
                # After closing a section, the next identifier is a section name
                continue

            # Equals
            if ch == "=":
                self._advance()
                self._expecting_value = True
                yield Token(TokenType.EQUALS, "=", start_line, start_col)
                continue

            # Comma
            if ch == ",":
                self._advance()
                self._expecting_value = False
                yield Token(TokenType.COMMA, ",", start_line, start_col)
                continue

            # Strings
            if ch in ('"', "'"):
                val = self._read_string(ch)
                yield Token(TokenType.STRING, val, start_line, start_col)
                continue

            # Number or boolean (starts with digit, '.', '+', '-')
            if ch.isdigit() or (ch == "." and self._peek(1).isalpha()):
                yield self._read_number_or_bool()
                continue

            if ch in ("+", "-") and self._expecting_value:
                # Signed number
                if self._peek(1).isdigit() or self._peek(1) == ".":
                    yield self._read_number_or_bool()
                    continue

            # Identifier
            if ch in _ID_START:
                ident = self._read_identifier()
                id_line = start_line
                id_col = start_col

                # Check for slice: identifier followed by '('
                ss_pos = self.pos
                ss_line = self.line
                ss_col = self.col
                # Skip whitespace to see if '(' follows
                while ss_pos < self._len and self.src[ss_pos] in (" ", "\t"):
                    ss_pos += 1
                if ss_pos < self._len and self.src[ss_pos] == "(":
                    self.pos = ss_pos
                    self.line = ss_line
                    self.col = ss_col
                    self._skip_whitespace()
                    slice_content = self._read_slice()
                    yield Token(TokenType.NAME, ident, id_line, id_col)
                    yield Token(TokenType.SLICE, slice_content, id_line, id_col)
                    self._expecting_value = False
                    continue

                # Check if section name: a NAME at line start (after whitespace)
                # followed by '{' (same line or next line).
                # Heuristic: if we just saw RBRACE or are at the beginning,
                # and this identifier is alone on its line (or followed by '{'),
                # then it's a SECTION_NAME.
                is_section = False
                if not self._expecting_value and not self._just_saw_section_name:
                    # Look ahead: skip whitespace/newlines, check for '{'
                    peek_pos = self.pos
                    while peek_pos < self._len and self.src[peek_pos] in (" ", "\t", "\r", "\n"):
                        peek_pos += 1
                    if peek_pos < self._len and self.src[peek_pos] == "{":
                        is_section = True

                if is_section:
                    yield Token(TokenType.SECTION_NAME, ident, id_line, id_col)
                    self._just_saw_section_name = True
                else:
                    yield Token(TokenType.NAME, ident, id_line, id_col)
                continue

            # Unknown character — skip (with warning?)
            self._advance()

        yield Token(TokenType.EOF, "", self.line, self.col)
