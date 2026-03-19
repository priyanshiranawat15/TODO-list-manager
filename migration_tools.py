import subprocess
from pathlib import Path

PROJECT_DIR = Path("/Users/priyanshiranawat/TODO_LIST")

def _run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, check=True)
    return (out.stdout or "") + (out.stderr or "")

def create_autogen_migration(message: str) -> str:
    return _run(["alembic", "revision", "--autogenerate", "-m", message])

def upgrade_head() -> str:
    return _run(["alembic", "upgrade", "head"])