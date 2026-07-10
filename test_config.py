import os
import tempfile
import pytest
import yaml
from fixlot.config.loader import load_config, DEFAULT_CONFIG
from fixlot.config.credentials import load_credentials


class TestLoadConfig:
    def test_default_config_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(tmpdir)
            assert config["max_rounds"] == DEFAULT_CONFIG["max_rounds"]
            assert config["timeout"] == DEFAULT_CONFIG["timeout"]
            assert config["test_command"] == DEFAULT_CONFIG["test_command"]
            assert config["provider"] == DEFAULT_CONFIG["provider"]

    def test_loads_config_from_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixlot_dir = os.path.join(tmpdir, ".fixlot")
            os.makedirs(fixlot_dir)
            config_path = os.path.join(fixlot_dir, "config.yaml")
            with open(config_path, "w") as f:
                yaml.dump({"max_rounds": 10, "provider": "anthropic"}, f)

            config = load_config(tmpdir)
            assert config["max_rounds"] == 10
            assert config["provider"] == "anthropic"
            assert config["test_command"] == DEFAULT_CONFIG["test_command"]

    def test_merges_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixlot_dir = os.path.join(tmpdir, ".fixlot")
            os.makedirs(fixlot_dir)
            config_path = os.path.join(fixlot_dir, "config.yaml")
            with open(config_path, "w") as f:
                yaml.dump({"max_rounds": 3}, f)

            config = load_config(tmpdir)
            assert config["max_rounds"] == 3
            assert config["timeout"] == DEFAULT_CONFIG["timeout"]
            assert config["test_command"] == DEFAULT_CONFIG["test_command"]
            assert config["provider"] == DEFAULT_CONFIG["provider"]


class TestLoadCredentials:
    def test_loads_from_env_file(self):
        old_openai = os.environ.pop("OPENAI_API_KEY", None)
        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env_path = os.path.join(tmpdir, ".env")
                with open(env_path, "w") as f:
                    f.write("OPENAI_API_KEY=sk-test-key\n")
                    f.write("ANTHROPIC_API_KEY=sk-ant-test\n")

                creds = load_credentials(tmpdir)
                assert creds["OPENAI_API_KEY"] == "sk-test-key"
                assert creds["ANTHROPIC_API_KEY"] == "sk-ant-test"
        finally:
            if old_openai:
                os.environ["OPENAI_API_KEY"] = old_openai
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic

    def test_returns_empty_dict_when_no_env_file(self):
        old_openai = os.environ.pop("OPENAI_API_KEY", None)
        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                creds = load_credentials(tmpdir)
                assert creds == {}
        finally:
            if old_openai:
                os.environ["OPENAI_API_KEY"] = old_openai
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic

    def test_merges_with_environment_variables(self):
        old_openai = os.environ.pop("OPENAI_API_KEY", None)
        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                env_path = os.path.join(tmpdir, ".env")
                with open(env_path, "w") as f:
                    f.write("OPENAI_API_KEY=sk-from-file\n")

                os.environ["ANTHROPIC_API_KEY"] = "sk-from-env"
                try:
                    creds = load_credentials(tmpdir)
                    assert creds["OPENAI_API_KEY"] == "sk-from-file"
                    assert creds["ANTHROPIC_API_KEY"] == "sk-from-env"
                finally:
                    del os.environ["ANTHROPIC_API_KEY"]
        finally:
            if old_openai:
                os.environ["OPENAI_API_KEY"] = old_openai
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic