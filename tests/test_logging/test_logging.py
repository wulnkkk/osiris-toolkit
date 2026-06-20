"""Tests for _logging module."""
import json
import logging

from osiris_toolkit._logging import configure, get_logger


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "osiris_toolkit"

    def test_child_logger(self):
        child = get_logger("osiris_toolkit.vis.batch")
        assert child.name == "osiris_toolkit.vis.batch"

    def test_same_instance(self):
        a = get_logger()
        b = get_logger()
        assert a is b


class TestConfigure:
    def test_set_level(self):
        configure(logging.DEBUG)
        logger = get_logger()
        assert logger.level == logging.DEBUG
        configure(logging.WARNING)

    def test_json_output(self, capsys):
        configure(logging.INFO, json_output=True)
        logger = get_logger("osiris_toolkit.test")
        logger.info("test message")
        captured = capsys.readouterr()
        record = json.loads(captured.err.strip().split("\n")[-1])
        assert record["level"] == "INFO"
        assert record["message"] == "test message"
        assert record["name"] == "osiris_toolkit.test"
        configure(logging.WARNING)
