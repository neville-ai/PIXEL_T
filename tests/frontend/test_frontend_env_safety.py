import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_SRC = ROOT_DIR / "frontend" / "src"
BACKEND_APP = ROOT_DIR / "backend" / "app"
ENV_EXAMPLE = ROOT_DIR / ".env.example"

SOURCE_EXTENSIONS = ('.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.py', '.json')


def test_no_service_role_in_frontend():
    """Ensure that the backend SERVICE_ROLE key is never referenced in frontend source code."""
    pattern = re.compile(r'SERVICE_ROLE', re.IGNORECASE)

    for root, _, files in os.walk(FRONTEND_SRC):
        for file in files:
            if file.endswith(SOURCE_EXTENSIONS):
                file_path = Path(root) / file
                content = file_path.read_text(encoding='utf-8')
                assert not pattern.search(content), (
                    f"Found forbidden SERVICE_ROLE reference in frontend file: {file_path}"
                )


def test_no_vite_service_role_env():
    """Ensure no VITE_ prefix is ever combined with SERVICE_ROLE in frontend or env.example."""
    pattern = re.compile(r'VITE_[a-zA-Z0-9_]*SERVICE_ROLE', re.IGNORECASE)

    # Check .env.example
    if ENV_EXAMPLE.exists():
        content = ENV_EXAMPLE.read_text(encoding='utf-8')
        assert not pattern.search(content), (
            "Found forbidden VITE_*SERVICE_ROLE pattern in .env.example"
        )

    # Check frontend source
    for root, _, files in os.walk(FRONTEND_SRC):
        for file in files:
            if file.endswith(SOURCE_EXTENSIONS):
                file_path = Path(root) / file
                content = file_path.read_text(encoding='utf-8')
                assert not pattern.search(content), (
                    f"Found forbidden VITE_*SERVICE_ROLE pattern in {file_path}"
                )


def test_no_hardcoded_jwt_secrets():
    """Ensure no hardcoded JWT tokens (starting with eyJ...) exist in codebase source."""
    jwt_pattern = re.compile(r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}')

    for target_dir in [FRONTEND_SRC, BACKEND_APP]:
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith(SOURCE_EXTENSIONS):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        assert not jwt_pattern.search(content), (
                            f"Possible hardcoded JWT token found in {file_path}"
                        )
                    except UnicodeDecodeError:
                        continue


def test_gitignore_protects_env():
    """Ensure .gitignore explicitly ignores .env and .env.* files."""
    gitignore_path = ROOT_DIR / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist"
    content = gitignore_path.read_text(encoding='utf-8')
    lines = [line.strip() for line in content.splitlines()]

    assert ".env" in lines, ".env must be ignored in .gitignore"
    assert ".env.*" in lines, ".env.* must be ignored in .gitignore"
    assert "!.env.example" in lines, "!.env.example must be kept in .gitignore"
