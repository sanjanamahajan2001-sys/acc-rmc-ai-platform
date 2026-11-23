"""Unit tests for WS-01.2B Import Ordering and Layer Isolation Framework."""

import os
import tempfile
from src.shared.import_validator import (
    extract_file_imports,
    validate_layer_isolation,
    detect_circular_dependencies,
)


def test_layer_isolation_rules() -> None:
    # Leaf packages (level 1) can import level 1
    assert validate_layer_isolation("src.core.config", "src.shared.enums") is True

    # Domain (level 4) can import leaf (level 1) and exceptions (level 2)
    assert validate_layer_isolation("src.domain.batch", "src.exceptions") is True

    # Violations: Leaf package importing higher domain layer
    assert validate_layer_isolation("src.shared.enums", "src.domain.batch") is False

    # Violations: Domain layer importing presentation layer (src.api)
    assert validate_layer_isolation("src.domain.batch", "src.api.v1") is False


def test_ast_import_extraction() -> None:
    code_content = """import os\nfrom src.shared.enums import BatchStatus\nfrom src.domain.batch import state_machine\n"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(code_content)
        tmp_path = tmp.name

    try:
        imports = extract_file_imports(tmp_path)
        assert "os" in imports
        assert "src.shared.enums" in imports
        assert "src.domain.batch" in imports
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_circular_dependency_detection() -> None:
    # Verify no circular dependencies exist in current repo structure
    repo_src = "/home/sanjana/acc-rmc-ai-platform/src"
    cycles = detect_circular_dependencies(repo_src)
    assert len(cycles) == 0
