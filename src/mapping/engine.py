"""Header Resolution and Canonical Column Mapping Engine.

This module provides:
1. HeaderResolution and HeaderResolver implementing the 4-stage matching pipeline against CanonicalFieldRegistry.
2. CanonicalColumnMappingEngine mapping raw data rows into intermediate CanonicalRow and CanonicalDataset objects.
"""

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List, Optional, Tuple
from src.database.dictionary import CanonicalFieldDefinition, CanonicalFieldID, get_canonical_dictionary
from src.logging import get_logger
from src.mapping.contracts import CanonicalDataset, CanonicalRow, MappingAuditRecord
from src.mapping.models import ImportProfile
from src.mapping.unit_converter import PrimitiveTypeNormalizer, UnitNormalizer

logger = get_logger("src.mapping.engine", component="mapping")


class HeaderResolution:
    """Resolution result for a single external header title."""

    def __init__(
        self,
        original_header: str,
        canonical_field_id: Optional[CanonicalFieldID],
        resolution_strategy: str,
        similarity_score: float,
        is_candidate: bool = False,
    ) -> None:
        self.original_header = original_header
        self.canonical_field_id = canonical_field_id
        self.resolution_strategy = resolution_strategy
        self.similarity_score = similarity_score
        self.is_candidate = is_candidate


class HeaderResolver:
    """Multi-stage Header Resolver executing 4-stage matching pipeline against CanonicalFieldRegistry."""

    def __init__(self) -> None:
        self._registry = get_canonical_dictionary()
        self._canonical_fields = self._registry.get_all_fields()
        # Compile common regex patterns targeting canonical definitions
        self._regex_rules: List[Tuple[re.Pattern, str]] = [
            (re.compile(r"(?i)^batch[_\s#]*no", re.IGNORECASE), "FIELD_BATCH_ID"),
            (re.compile(r"(?i)^(actual[_\s]*)?cement(\s*\d+)?", re.IGNORECASE), "FIELD_ACTUAL_CEMENT_KG"),
            (re.compile(r"(?i)^(actual[_\s]*)?water", re.IGNORECASE), "FIELD_ACTUAL_WATER_KG"),
            (re.compile(r"(?i)^(actual[_\s]*)?admix(ture)?(\s*\d+)?", re.IGNORECASE), "FIELD_ACTUAL_ADMIXTURE_KG"),
            (re.compile(r"(?i)^(actual[_\s]*)?sand(\s*\d+)?", re.IGNORECASE), "FIELD_ACTUAL_SAND_KG"),
            (re.compile(r"(?i)^10\s*mm(\s*agg(regate)?)?", re.IGNORECASE), "FIELD_ACTUAL_AGGREGATE_10MM_KG"),
            (re.compile(r"(?i)^20\s*mm(\s*agg(regate)?)?", re.IGNORECASE), "FIELD_ACTUAL_AGGREGATE_20MM_KG"),
            (re.compile(r"(?i)^(actual[_\s]*)?fly[_\s]*ash", re.IGNORECASE), "FIELD_ACTUAL_FLYASH_KG"),
            (re.compile(r"(?i)^plant(\s*(code|name|id))?", re.IGNORECASE), "FIELD_PLANT_CODE"),
            (re.compile(r"(?i)^challan(\s*no\.?)?(\s*\(editable\))?", re.IGNORECASE), "FIELD_DELIVERY_NOTE_ID"),
            (re.compile(r"(?i)^28[_\s]*day[_\s]*streng?th", re.IGNORECASE), "FIELD_CUBE_STRENGTH_28D_MPA"),
            (re.compile(r"(?i)^28d[_\s]*strength", re.IGNORECASE), "FIELD_CUBE_STRENGTH_28D_MPA"),
            (re.compile(r"(?i)^slump", re.IGNORECASE), "FIELD_SLUMP_MM"),
        ]

    def resolve_header(self, header: str) -> HeaderResolution:
        """Resolve external column title using 4-stage matching pipeline."""
        clean_header = header.strip()
        header_lower = clean_header.lower()
        canonical_fields = self._registry.get_all_fields()

        # Stage 1: Exact Match (Score 1.00)
        for f_def in canonical_fields:
            if header_lower == f_def.field_id.value.lower() or header_lower == f_def.canonical_name.lower():
                return HeaderResolution(clean_header, f_def.field_id, "EXACT", 1.00)

        # Stage 2: Alias Resolution (Score 0.98)
        for f_def in canonical_fields:
            for alias in f_def.excel_aliases + f_def.api_aliases:
                if header_lower == alias.lower():
                    return HeaderResolution(clean_header, f_def.field_id, "ALIAS", 0.98)

        # Stage 3: Regex Pattern Matching (Score 0.95)
        for pattern, fid_val in self._regex_rules:
            if pattern.search(clean_header):
                for f_def in canonical_fields:
                    if f_def.field_id.value == fid_val:
                        return HeaderResolution(clean_header, f_def.field_id, "REGEX", 0.95)

        # Stage 4: Fuzzy Match (Levenshtein Score 0.85 - 0.94 candidate, <0.85 unmapped)
        best_score = 0.0
        best_fid: Optional[CanonicalFieldID] = None
        for f_def in canonical_fields:
            # Check similarity against canonical_name, display_name, and field_id
            s1 = SequenceMatcher(None, header_lower, f_def.canonical_name.lower()).ratio()
            s2 = SequenceMatcher(None, header_lower, f_def.display_name.lower()).ratio()
            s3 = SequenceMatcher(None, header_lower, f_def.field_id.value.lower()).ratio()
            score = max(s1, s2, s3)
            if score > best_score:
                best_score = score
                best_fid = f_def.field_id

        if best_score >= 0.85:
            return HeaderResolution(clean_header, best_fid, "FUZZY", round(best_score, 2), is_candidate=True)

        return HeaderResolution(clean_header, None, "UNMAPPED", round(best_score, 2))


class CanonicalColumnMappingEngine:
    """Thread-safe engine mapping raw row dicts to intermediate CanonicalRow and CanonicalDataset objects."""

    def __init__(self) -> None:
        self._registry = get_canonical_dictionary()

    def map_row(
        self,
        raw_row: Dict[str, Any],
        profile: Optional[ImportProfile] = None,
        row_index: int = 0,
        sheet_name: Optional[str] = None,
    ) -> CanonicalRow:
        """Map raw external data row dict to intermediate CanonicalRow with audit trail."""
        resolver = HeaderResolver()
        fields: Dict[str, Any] = {}
        audit_records: List[MappingAuditRecord] = []

        profile_map: Dict[str, str] = {}
        unit_map: Dict[str, str] = {}
        prof_id = profile.id if profile else None
        prof_ver = profile.profile_version if profile else None

        if profile and profile.mappings:
            for m in profile.mappings:
                profile_map[m.external_header.lower()] = m.target_canonical_id
                if m.unit_override:
                    unit_map[m.external_header.lower()] = m.unit_override

        for col_idx, (header, raw_val) in enumerate(raw_row.items()):
            header_clean = header.strip()
            header_lower = header_clean.lower()

            target_cid_str: Optional[str] = None
            strategy = "EXACT"
            score = 1.00

            if header_lower in profile_map:
                target_cid_str = profile_map[header_lower]
                strategy = "PROFILE"
                score = 1.00
            else:
                res: HeaderResolution = resolver.resolve_header(header_clean)
                if res.canonical_field_id:
                    target_cid_str = res.canonical_field_id.value
                    strategy = res.resolution_strategy
                    score = res.similarity_score

            if not target_cid_str:
                audit = MappingAuditRecord(
                    original_header=header_clean,
                    canonical_field_id="UNMAPPED",
                    resolution_strategy="UNMAPPED",
                    similarity_score=0.00,
                    original_value=raw_val,
                    original_unit=None,
                    canonical_value=None,
                    canonical_unit=None,
                    profile_id=prof_id,
                    profile_version=prof_ver,
                    sheet_name=sheet_name,
                    row_index=row_index,
                    column_index=col_idx,
                )
                audit_records.append(audit)
                continue

            c_def = None
            # Lookup using CanonicalFieldID enum or string value
            try:
                cid_enum = CanonicalFieldID(target_cid_str)
                if self._registry.has_field(cid_enum):
                    c_def = self._registry.get_field(cid_enum)
            except ValueError:
                if self._registry.has_field(target_cid_str):
                    c_def = self._registry.get_field(target_cid_str)

            target_unit = c_def.unit if c_def else None
            from_unit = unit_map.get(header_lower)
            orig_val, orig_unit, canon_val, canon_unit = UnitNormalizer.convert(raw_val, from_unit, target_unit)
            typed_val = PrimitiveTypeNormalizer.normalize_value(canon_val, c_def)

            fields[target_cid_str] = typed_val

            audit = MappingAuditRecord(
                original_header=header_clean,
                canonical_field_id=target_cid_str,
                resolution_strategy=strategy,
                similarity_score=score,
                original_value=orig_val,
                original_unit=orig_unit,
                canonical_value=typed_val,
                canonical_unit=canon_unit,
                profile_id=prof_id,
                profile_version=prof_ver,
                sheet_name=sheet_name,
                row_index=row_index,
                column_index=col_idx,
            )
            audit_records.append(audit)

        return CanonicalRow(row_index=row_index, fields=fields, audit_records=audit_records)

    def map_dataset(
        self,
        raw_rows: List[Dict[str, Any]],
        profile: ImportProfile,
        sheet_name: Optional[str] = None,
    ) -> CanonicalDataset:
        """Map collection of raw row dicts to CanonicalDataset."""
        mapped_rows = [self.map_row(row, profile=profile, row_index=idx, sheet_name=sheet_name) for idx, row in enumerate(raw_rows)]
        return CanonicalDataset(
            profile_id=profile.id,
            profile_version=profile.profile_version,
            rows=mapped_rows,
        )
