import pytest
from unittest.mock import patch
from claw2manus.cli import on_unresolved_tool_cli


@pytest.mark.parametrize(
    "user_input, expected_result",
    [
        ("Use my custom tool", "Use my custom tool"),
        ("", "Use default tool"),
        ("   Use my custom tool   ", "Use my custom tool"),
        ("   ", "Use default tool"),
    ],
)
def test_on_unresolved_tool_cli(user_input, expected_result, capsys):
    with patch(
        "builtins.input", return_value=user_input
    ) as mocked_input:
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == expected_result

        mocked_input.assert_called_once_with(
            "Enter custom instruction (or press Enter to use default): "
        )
        captured = capsys.readouterr()
        assert "Unresolved tool mapping found: 'unknown_tool'" in captured.out
        assert "Default instruction: Use default tool" in captured.out
