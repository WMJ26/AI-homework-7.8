import os
import yaml


DEFAULT_CONFIG = {
    "max_rounds": 5,
    "timeout": 300,
    "test_command": "pytest",
    "provider": "openai",
    "model": None,
    "allowed_tools": ["read_file", "write_file", "run_command", "run_tests"],
}


def load_config(work_dir: str) -> dict:
    config = dict(DEFAULT_CONFIG)
    config_dir = os.path.join(work_dir, ".fixlot")
    config_path = os.path.join(config_dir, "config.yaml")

    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        config.update(user_config)

    return config