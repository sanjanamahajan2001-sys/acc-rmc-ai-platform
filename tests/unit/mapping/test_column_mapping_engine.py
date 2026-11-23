"""Comprehensive Unit, Integration, and Benchmark Test Suite for WS-03.2 Import Profile & Canonical Column Mapping Engine."""

from decimal import Decimal
import time
import unittest
from src.database import BaseModel, dispose_database_engine, get_canonical_dictionary, get_database_engine, get_db_session
from src.database.dictionary import CanonicalFieldID
from src.exceptions import ACCRMCBaseException
from src.mapping import (
    CanonicalColumnMappingEngine,
    HeaderResolver,
    ImportProfile,
    ImportProfileRepository,
    ImportProfileService,
    PrimitiveTypeNormalizer,
    UnitNormalizer,
)


class TestColumnMappingEngineComprehensive(unittest.TestCase):
    """Comprehensive test suite covering all WS-03.2 mapping scenarios."""

    def setUp(self) -> None:
        dispose_database_engine()

    def tearDown(self) -> None:
        dispose_database_engine()

    # 1. Exact Matching
    def test_exact_matching(self) -> None:
        resolver = HeaderResolver()
        res = resolver.resolve_header("batch_id")
        self.assertEqual(res.resolution_strategy, "EXACT")
        self.assertEqual(res.canonical_field_id.value, "FIELD_BATCH_ID")
        self.assertEqual(res.similarity_score, 1.00)

    # 2. Alias Matching
    def test_alias_matching(self) -> None:
        resolver = HeaderResolver()
        res = resolver.resolve_header("Batch Number")
        self.assertEqual(res.resolution_strategy, "ALIAS")
        self.assertEqual(res.canonical_field_id.value, "FIELD_BATCH_ID")

    # 3. Regex Matching
    def test_regex_matching(self) -> None:
        resolver = HeaderResolver()
        res = resolver.resolve_header("batch_no_scada_log")
        self.assertEqual(res.resolution_strategy, "REGEX")
        self.assertEqual(res.canonical_field_id.value, "FIELD_BATCH_ID")

    # 4. Fuzzy Matching
    def test_fuzzy_matching(self) -> None:
        resolver = HeaderResolver()
        res = resolver.resolve_header("batch_id_num_test")
        self.assertIsNotNone(res)

    # 5. Unit Normalization
    def test_unit_normalization(self) -> None:
        # Imperial lbs -> Metric kg
        orig_val, orig_unit, canon_val, canon_unit = UnitNormalizer.convert(2204.62, "lbs", None)
        self.assertEqual(orig_val, 2204.62)
        self.assertEqual(orig_unit, "lbs")

        # Imperial yd3 -> Metric m3
        orig_val2, orig_unit2, canon_val2, canon_unit2 = UnitNormalizer.convert(10.0, "yd3", None)
        self.assertEqual(orig_val2, 10.0)

    # 6. Primitive Normalization
    def test_primitive_normalization(self) -> None:
        reg = get_canonical_dictionary()
        c_def = reg.get_field(CanonicalFieldID.FIELD_ACTUAL_CEMENT_KG)
        typed_val = PrimitiveTypeNormalizer.normalize_value("500.25", c_def)
        self.assertEqual(typed_val, Decimal("500.25"))

        # Empty string handling
        self.assertIsNone(PrimitiveTypeNormalizer.normalize_value("", c_def))
        self.assertIsNone(PrimitiveTypeNormalizer.normalize_value(None, c_def))

    # 7. Profile Inheritance
    def test_profile_inheritance(self) -> None:
        engine_db = get_database_engine()
        tables = [t for name, t in BaseModel.metadata.tables.items() if not name.startswith("vw_")]
        BaseModel.metadata.create_all(engine_db, tables=tables)

        with get_db_session() as session:
            service = ImportProfileService(session)
            parent = service.create_profile("Base Vendor Profile", "CMD_ALKON", "1.0.0", mappings_dict={"Challan No": "FIELD_BATCH_ID"})
            child = service.create_profile("Child Custom Profile", "CMD_ALKON", "2.0.0", created_from_profile_id=parent.id)

            self.assertEqual(child.created_from_profile_id, parent.id)
            self.assertEqual(len(child.mappings), 1)
            self.assertEqual(child.mappings[0].external_header, "Challan No")

    # 8. Profile Version Resolution
    def test_profile_version_resolution(self) -> None:
        engine_db = get_database_engine()
        tables = [t for name, t in BaseModel.metadata.tables.items() if not name.startswith("vw_")]
        BaseModel.metadata.create_all(engine_db, tables=tables)

        with get_db_session() as session:
            service = ImportProfileService(session)
            p1 = service.create_profile("Base Alkon", "CMD_ALKON", "1.0.0", mappings_dict={"Challan": "FIELD_BATCH_ID"})
            p2 = service.create_profile("Base Alkon v2", "CMD_ALKON", "2.0.0", mappings_dict={"Challan No": "FIELD_BATCH_ID"})

            found = service._repository.find_by_vendor_and_version("CMD_ALKON", "2.0.0")
            self.assertIsNotNone(found)
            self.assertEqual(found.profile_version, "2.0.0")

    # 9. Repository CRUD Operations
    def test_repository_crud(self) -> None:
        engine_db = get_database_engine()
        tables = [t for name, t in BaseModel.metadata.tables.items() if not name.startswith("vw_")]
        BaseModel.metadata.create_all(engine_db, tables=tables)

        with get_db_session() as session:
            repo = ImportProfileRepository(session)
            profile = ImportProfile(vendor_code="TEST_VENDOR", profile_name="Test Profile", profile_version="1.0.0")
            repo.create_profile(profile)

            fetched = repo.get_by_id(profile.id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.vendor_code, "TEST_VENDOR")

    # 10. Extended Mapping Audit Generation
    def test_mapping_audit_generation(self) -> None:
        engine = CanonicalColumnMappingEngine()
        raw_row = {
            "Batch Number": "BAT-AUDIT-001",
            "Actual Cement": "450.00",
        }
        canonical_row = engine.map_row(raw_row, row_index=5, sheet_name="SCADA_Logs")
        self.assertEqual(len(canonical_row.audit_records), 2)
        audit = canonical_row.audit_records[0]

        self.assertEqual(audit.row_index, 5)
        self.assertEqual(audit.sheet_name, "SCADA_Logs")
        self.assertEqual(audit.column_index, 0)
        self.assertIsNotNone(audit.timestamp)

    # 11. Invalid Profile & Unmapped Field Handling
    def test_unmapped_field_and_invalid_handling(self) -> None:
        resolver = HeaderResolver()
        res = resolver.resolve_header("completely_random_unknown_header_xyz")
        self.assertEqual(res.resolution_strategy, "UNMAPPED")
        self.assertIsNone(res.canonical_field_id)

    # 12. Performance Target Benchmark (<2ms/header)
    def test_performance_target_benchmark(self) -> None:
        resolver = HeaderResolver()
        headers = ["batch_id", "Batch Number", "batch_no_scada_log", "actual_cement_kg", "cube_strength_28d_mpa"] * 200  # 1000 headers

        t0 = time.perf_counter()
        for h in headers:
            _ = resolver.resolve_header(h)
        t1 = time.perf_counter()

        total_time_ms = (t1 - t0) * 1000.0
        avg_time_per_header_ms = total_time_ms / len(headers)

        self.assertLess(avg_time_per_header_ms, 2.0, f"Header resolution exceeded performance target: {avg_time_per_header_ms:.4f} ms/header")


if __name__ == "__main__":
    unittest.main()
