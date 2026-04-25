import pytest
from unittest.mock import patch
from claw2manus.cli import on_unresolved_tool_cli

def test_on_unresolved_tool_cli_custom_input():
    with patch('builtins.input', return_value="Use my custom tool"):
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == "Use my custom tool"

def test_on_unresolved_tool_cli_empty_input():
    with patch('builtins.input', return_value=""):
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == "Use default tool"

def test_on_unresolved_tool_cli_whitespace_input():
    with patch('builtins.input', return_value="   Use my custom tool   "):
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == "Use my custom tool"

def test_on_unresolved_tool_cli_only_whitespace_input():
    with patch('builtins.input', return_value="   "):
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == "Use default tool"
