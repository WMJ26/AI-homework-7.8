import os
from dotenv import load_dotenv


def load_credentials(work_dir: str) -> dict:
    env_path = os.path.join(work_dir, ".env")
    if os.path.isfile(env_path):
        load_dotenv(env_path)

    credentials = {}
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        value = os.environ.get(key)
        if value:
            credentials[key] = value

    return credentials