"""Automated test suite for WS-03.3 Phase 2 Validation Rule Registry & Metadata Infrastructure."""

from concurrent.futures import ThreadPoolExecutor
import time
from typing import Any, Optional
import unittest
from src.validation import (
    BaseValidationRule,
    DuplicateRuleException,
    FieldErrorDetail,
    RuleExecutionContext,
    RuleMetadata,
    UnknownRuleException,
    ValidationCategory,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationTier,
)


class DummyTestRule(BaseValidationRule):
    """Concrete dummy rule for testing registry infrastructure."""

    def validate(self, value: Any, context: RuleExecutionContext) -> Optional[FieldErrorDetail]:
        return None

    def supports(self, field_id: str) -> bool:
        return True


class TestValidationRuleRegistry(unittest.TestCase):
    """Unit and benchmark test suite for Phase 2 ValidationRuleRegistry."""

    def setUp(self) -> None:
        self.registry = ValidationRuleRegistry()

    def test_rule_registration_and_lookup(self) -> None:
        meta = RuleMetadata(
            rule_id="ACC_VAL_001",
            rule_name="Test Rule 1",
            description="Test description",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.CONCRETE,
            severity=ValidationSeverity.CRITICAL,
            version="1.0.0",
        )
        rule = DummyTestRule(meta)
        self.registry.register_rule(rule)

        fetched = self.registry.get_rule("ACC_VAL_001", "1.0.0")
        self.assertEqual(fetched.rule_id, "ACC_VAL_001")
        self.assertEqual(fetched.severity, ValidationSeverity.CRITICAL)

    def test_duplicate_rule_prevention(self) -> None:
        meta = RuleMetadata(
            rule_id="ACC_VAL_001",
            rule_name="Test Rule 1",
            description="Test description",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.CONCRETE,
            severity=ValidationSeverity.CRITICAL,
            version="1.0.0",
        )
        rule1 = DummyTestRule(meta)
        rule2 = DummyTestRule(meta)

        self.registry.register_rule(rule1)
        with self.assertRaises(DuplicateRuleException):
            self.registry.register_rule(rule2)

    def test_unknown_rule_exception(self) -> None:
        with self.assertRaises(UnknownRuleException):
            self.registry.get_rule("NON_EXISTENT_RULE")

    def test_rule_removal(self) -> None:
        meta = RuleMetadata(
            rule_id="ACC_VAL_DEL",
            rule_name="Delete Rule",
            description="Test delete",
            tier=ValidationTier.TIER_2_PRIMITIVES,
            category=ValidationCategory.SCADA,
            severity=ValidationSeverity.WARNING,
            version="1.0.0",
        )
        rule = DummyTestRule(meta)
        self.registry.register_rule(rule)
        self.registry.unregister_rule("ACC_VAL_DEL", "1.0.0")

        with self.assertRaises(UnknownRuleException):
            self.registry.get_rule("ACC_VAL_DEL", "1.0.0")

    def test_filtering_by_tier_and_category(self) -> None:
        meta1 = RuleMetadata(
            rule_id="R1",
            rule_name="R1",
            description="D",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.CONCRETE,
            severity=ValidationSeverity.CRITICAL,
        )
        meta2 = RuleMetadata(
            rule_id="R2",
            rule_name="R2",
            description="D",
            tier=ValidationTier.TIER_2_PRIMITIVES,
            category=ValidationCategory.CONCRETE,
            severity=ValidationSeverity.ERROR,
        )
        meta3 = RuleMetadata(
            rule_id="R3",
            rule_name="R3",
            description="D",
            tier=ValidationTier.TIER_1_STRUCTURAL,
            category=ValidationCategory.LABORATORY,
            severity=ValidationSeverity.WARNING,
        )

        self.registry.register_rule(DummyTestRule(meta1))
        self.registry.register_rule(DummyTestRule(meta2))
        self.registry.register_rule(DummyTestRule(meta3))

        tier1_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_1_STRUCTURAL)
        self.assertEqual(len(tier1_rules), 2)

        concrete_rules = self.registry.get_rules_for_category(ValidationCategory.CONCRETE)
        self.assertEqual(len(concrete_rules), 2)

    def test_deterministic_ordering(self) -> None:
        # Register out of order
        meta_t3 = RuleMetadata(rule_id="T3_R1", rule_name="T3", description="D", tier=ValidationTier.TIER_3_RANGES_ENUMS, category=ValidationCategory.CONCRETE, severity=ValidationSeverity.ERROR, execution_priority=50)
        meta_t1_p2 = RuleMetadata(rule_id="T1_R2", rule_name="T1_2", description="D", tier=ValidationTier.TIER_1_STRUCTURAL, category=ValidationCategory.CONCRETE, severity=ValidationSeverity.CRITICAL, execution_priority=100)
        meta_t1_p1 = RuleMetadata(rule_id="T1_R1", rule_name="T1_1", description="D", tier=ValidationTier.TIER_1_STRUCTURAL, category=ValidationCategory.CONCRETE, severity=ValidationSeverity.CRITICAL, execution_priority=10)

        self.registry.register_rule(DummyTestRule(meta_t3))
        self.registry.register_rule(DummyTestRule(meta_t1_p2))
        self.registry.register_rule(DummyTestRule(meta_t1_p1))

        ordered = self.registry.get_execution_order()
        self.assertEqual([r.rule_id for r in ordered], ["T1_R1", "T1_R2", "T3_R1"])

    def test_concurrent_registry_operations(self) -> None:
        def register_task(idx: int) -> None:
            meta = RuleMetadata(
                rule_id=f"THREAD_RULE_{idx}",
                rule_name=f"Thread Rule {idx}",
                description="Thread safety test",
                tier=ValidationTier.TIER_1_STRUCTURAL,
                category=ValidationCategory.CONCRETE,
                severity=ValidationSeverity.INFO,
            )
            self.registry.register_rule(DummyTestRule(meta))

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(register_task, range(100)))

        all_rules = self.registry.get_rules()
        self.assertEqual(len(all_rules), 100)

    def test_performance_benchmark_1000_rules(self) -> None:
        t0 = time.perf_counter()
        for i in range(1000):
            meta = RuleMetadata(
                rule_id=f"BENCH_RULE_{i:04d}",
                rule_name=f"Bench Rule {i}",
                description="Performance benchmark",
                tier=ValidationTier.TIER_3_RANGES_ENUMS if i % 2 == 0 else ValidationTier.TIER_1_STRUCTURAL,
                category=ValidationCategory.CONCRETE,
                severity=ValidationSeverity.ERROR,
                execution_priority=i % 100 + 1,
            )
            self.registry.register_rule(DummyTestRule(meta))
        t1 = time.perf_counter()

        registration_time_ms = (t1 - t0) * 1000.0

        t2 = time.perf_counter()
        tier_rules = self.registry.get_rules_for_tier(ValidationTier.TIER_3_RANGES_ENUMS)
        t3 = time.perf_counter()

        retrieval_time_ms = (t3 - t2) * 1000.0

        self.assertEqual(len(self.registry.get_rules()), 1000)
        self.assertEqual(len(tier_rules), 500)
        self.assertLess(registration_time_ms, 500.0, f"1000 rule registration took too long: {registration_time_ms:.2f} ms")
        self.assertLess(retrieval_time_ms, 20.0, f"500 rule retrieval and deterministic sort took too long: {retrieval_time_ms:.2f} ms")

        print(f"\n[BENCHMARK RESULT] 1,000 Rules Registration: {registration_time_ms:.2f} ms | Retrieval & Deterministic Sort: {retrieval_time_ms:.2f} ms")


if __name__ == "__main__":
    unittest.main()
