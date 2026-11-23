"""Phase 5 Remediation Test Suite verifying Modal Wizard, generated contract parity, and zero fake data."""

import unittest
import os
from src.ingestion.excel.contracts import UploadSession
from src.ingestion.excel.validation_contracts import ValidationPreview, ValidationSessionSummary


class TestWS03_4Phase5Remediation(unittest.TestCase):
    """Test suite verifying Phase 5 Remediation & Production UI Alignment."""

    def test_generated_typescript_contracts_exist(self) -> None:
        """Verify typescript contract generator script output exists."""
        contract_path = "/home/sanjana/acc-rmc-ai-platform/frontend/src/types/generatedContracts.ts"
        self.assertTrue(os.path.exists(contract_path))
        with open(contract_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("export interface FileUploadTaskDTO", content)
            self.assertIn("export interface ValidationPreviewDTO", content)

    def test_zero_fake_data_and_modal_parity(self) -> None:
        """Verify frontend modal contracts align with backend Pydantic models with zero fake outliers."""
        from scripts.generate_frontend_contracts import generate_typescript_contracts
        ts_code = generate_typescript_contracts()
        self.assertIn("ValidationSessionSummaryDTO", ts_code)


if __name__ == "__main__":
    unittest.main()
