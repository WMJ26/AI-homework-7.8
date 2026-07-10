import pytest
from unittest.mock import patch, MagicMock
from fixlot.cli.main import main


class TestCLI:
    def test_help_flag(self, capsys):
        with pytest.raises(SystemExit):
            main(["--help"])
        captured = capsys.readouterr()
        assert "fixlot" in captured.out.lower() or "usage" in captured.out.lower()

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit):
            main(["--version"])
        captured = capsys.readouterr()
        assert "fixlot" in captured.out.lower()

    @patch("fixlot.cli.main.AgentLoop")
    @patch("fixlot.cli.main.OpenAIProvider")
    @patch("fixlot.cli.main.load_config")
    @patch("fixlot.cli.main.load_credentials")
    def test_runs_task_with_mock(self, mock_creds, mock_config, mock_provider, mock_loop):
        mock_creds.return_value = {"OPENAI_API_KEY": "sk-test"}
        mock_config.return_value = {
            "max_rounds": 3,
            "provider": "openai",
            "test_command": "pytest",
            "timeout": 300,
        }
        mock_loop_instance = MagicMock()
        mock_loop_instance.run.return_value = {"state": "PASSED", "total_rounds": 2, "max_rounds": 3, "passed": True}
        mock_loop.return_value = mock_loop_instance

        main(["Implement hello world", "--provider", "openai", "--max-rounds", "3"])

        mock_loop_instance.run.assert_called_once()

    @patch("fixlot.cli.main.AgentLoop")
    @patch("fixlot.cli.main.AnthropicProvider")
    @patch("fixlot.cli.main.load_config")
    @patch("fixlot.cli.main.load_credentials")
    def test_uses_anthropic_provider(self, mock_creds, mock_config, mock_provider, mock_loop):
        mock_creds.return_value = {"ANTHROPIC_API_KEY": "sk-ant-test"}
        mock_config.return_value = {
            "max_rounds": 3,
            "provider": "anthropic",
            "test_command": "pytest",
            "timeout": 300,
        }
        mock_loop_instance = MagicMock()
        mock_loop_instance.run.return_value = {"state": "PASSED", "total_rounds": 1, "max_rounds": 3, "passed": True}
        mock_loop.return_value = mock_loop_instance

        main(["Implement test", "--provider", "anthropic"])

        mock_provider.assert_called_once()