"""Unit tests for WS-01.2C Quality Tooling & pyproject.toml Configuration Validation."""

import os
import tomllib


def test_pyproject_toml_parsing() -> None:
    pyproject_path = "/home/sanjana/acc-rmc-ai-platform/pyproject.toml"
    assert os.path.exists(pyproject_path) is True

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    # 1. Project metadata
    assert config["project"]["name"] == "acc-rmc-ai-platform"
    assert config["project"]["requires-python"] == ">=3.12"

    # 2. Ruff configuration
    assert "ruff" in config["tool"]
    assert config["tool"]["ruff"]["target-version"] == "py312"
    assert config["tool"]["ruff"]["line-length"] == 100

    # 3. Black configuration
    assert "black" in config["tool"]
    assert config["tool"]["black"]["line-length"] == 100

    # 4. isort configuration
    assert "isort" in config["tool"]
    assert config["tool"]["isort"]["profile"] == "black"

    # 5. mypy configuration
    assert "mypy" in config["tool"]
    assert config["tool"]["mypy"]["strict"] is True
    assert config["tool"]["mypy"]["python_version"] == "3.12"
