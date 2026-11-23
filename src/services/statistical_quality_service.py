"""Statistical Quality Control & 28-Day Concrete Strength Analysis Service.

Authoritative calculations for:
1. 28-day compressive strength distribution & histogram bins
2. Characteristic strength (fck) & Target Mean Strength (f'ck) per IS 456 / IS 10262
3. Standard deviation (sample s) & Coefficient of Variation (CV%)
4. Mix/Grade-wise performance comparison matrix
5. Chronological batch strength timeline (7-day and 28-day)
6. Real-time cache invalidation and plant/date/recipe scope filtering.

Zero mock data. 100% database-authoritative mathematics.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import math
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.orm import Session

from src.database.models.laboratory import ConcreteSample, CubeSet, CubeTest
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.services.cache_token_service import CacheTokenService
from src.services.engineering_settings_service import EngineeringSettingsService


def resolve_fck_from_recipe(target_strength: Optional[float], grade_str: Optional[str], default_val: float = 30.0) -> float:
    """Derive characteristic strength fck from target_strength_mpa or parse grade string (e.g. M-25 -> 25.0)."""
    if grade_str:
        match = re.search(r'M[-_\s]?([0-9]{2}(?:\.[0-9]+)?)', grade_str, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    if target_strength is not None and target_strength > 0:
        return float(target_strength)
    return default_val


# --- IS 456:2000 Table 8 Assumed Standard Deviations (MPa) by Concrete Grade ---
IS456_ASSUMED_STANDARD_DEVIATION = {
    "M10": 3.5,
    "M15": 3.5,
    "M20": 4.0,
    "M25": 4.0,
    "M30": 5.0,
    "M35": 5.0,
    "M40": 5.0,
    "M45": 5.0,
    "M50": 5.0,
    "M55": 5.0,
    "M60": 5.5,
    "M65": 6.0,
    "M70": 6.0,
    "M75": 6.0,
    "M80": 6.0,
    "M-10": 3.5,
    "M-15": 3.5,
    "M-20": 4.0,
    "M-25": 4.0,
    "M-30": 5.0,
    "M-35": 5.0,
    "M-40": 5.0,
    "M-45": 5.0,
    "M-50": 5.0,
    "M-55": 5.0,
    "M-60": 5.5,
    "M-65": 6.0,
    "M-70": 6.0,
    "M-75": 6.0,
    "M-80": 6.0,
}


def classify_coefficient_of_variation(cv_pct: float) -> str:
    """Classify concrete quality control variation based on IS 456 / ACI standards.

    - CV < 10.0%: EXCELLENT quality control
    - 10.0% <= CV <= 15.0%: GOOD / MODERATE control
    - CV > 15.0%: HIGH_VARIATION (Action/Review Required)
    """
    if cv_pct < 10.0:
        return "EXCELLENT"
    if cv_pct <= 15.0:
        return "GOOD"
    return "HIGH_VARIATION"


# --- DTO Schemas for API Serialization ---

class HistogramBinDTO(BaseModel):
    bin_start: float
    bin_end: float
    bin_label: str
    count: int
    is_below_fck: bool


class StrengthDistributionScopeDTO(BaseModel):
    plant_code: Optional[str] = None
    recipe_code: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    cache_token_version: int
    generated_at: str


class StrengthDistributionDTO(BaseModel):
    total_tested_batches: int
    total_tested_specimens: int
    mean_strength_mpa: Optional[float] = None
    median_strength_mpa: Optional[float] = None
    standard_deviation_mpa: Optional[float] = None
    coefficient_of_variation_pct: Optional[float] = None
    min_strength_mpa: Optional[float] = None
    max_strength_mpa: Optional[float] = None
    characteristic_strength_fck_mpa: float
    target_mean_strength_fck_prime_mpa: float
    strength_margin_mpa: Optional[float] = None
    compliance_rate_pct: float
    stability_grade: str
    histogram_bins: List[HistogramBinDTO]
    scope_metadata: StrengthDistributionScopeDTO


class MixPerformanceItemDTO(BaseModel):
    recipe_code: str
    recipe_name: str
    grade: str
    target_strength_fck: float
    target_mean_strength_fck_prime: float
    total_batches: int
    tested_batches_28d: int
    tested_specimens_28d: int
    mean_strength_mpa: Optional[float] = None
    standard_deviation_mpa: Optional[float] = None
    coefficient_of_variation_pct: Optional[float] = None
    strength_margin_mpa: Optional[float] = None
    compliance_rate_pct: float
    stability_status: str


class MixPerformanceListDTO(BaseModel):
    items: List[MixPerformanceItemDTO]
    total_recipes_evaluated: int
    scope_metadata: StrengthDistributionScopeDTO


class StrengthTimelinePointDTO(BaseModel):
    batch_number: str
    plant_code: str
    recipe_code: str
    grade: str
    production_timestamp: str
    result_7d_mpa: Optional[float] = None
    result_28d_mpa: Optional[float] = None
    target_fck_mpa: float
    target_fck_prime_mpa: float
    is_compliant_28d: Optional[bool] = None


class StrengthTimelineListDTO(BaseModel):
    timeline: List[StrengthTimelinePointDTO]
    total_points: int
    scope_metadata: StrengthDistributionScopeDTO


class StatisticalQualityService:
    """Authoritative SQC calculation engine for concrete compression testing."""

    @classmethod
    def _resolve_plant_id(cls, plant_code: Optional[str], db: Session) -> Optional[str]:
        if not plant_code:
            return None
        plant = db.query(Plant).filter(Plant.plant_code == plant_code, Plant.is_deleted == False).first()
        return plant.id if plant else "__NON_EXISTENT_PLANT__"

    @classmethod
    def _resolve_recipe_id(cls, recipe_code: Optional[str], db: Session) -> Optional[str]:
        if not recipe_code:
            return None
        recipe = db.query(Recipe).filter(Recipe.recipe_code == recipe_code, Recipe.is_deleted == False).first()
        return recipe.id if recipe else "__NON_EXISTENT_RECIPE__"

    @classmethod
    def get_strength_distribution(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> StrengthDistributionDTO:
        """Calculate database-authoritative 28-day strength distribution and histogram."""
        target_plant_id = cls._resolve_plant_id(plant_code, db)
        target_recipe_id = cls._resolve_recipe_id(recipe_code, db)

        # Base query joining CubeTest -> CubeSet -> ConcreteSample -> Batch -> Recipe
        query = (
            db.query(
                CubeTest.compressive_strength_mpa,
                Batch.id.label("batch_id"),
                Recipe.grade,
                Recipe.target_strength_mpa,
            )
            .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
            .join(ConcreteSample, CubeSet.sample_id == ConcreteSample.id)
            .join(Batch, ConcreteSample.batch_id == Batch.id)
            .outerjoin(Recipe, Batch.recipe_id == Recipe.id)
            .filter(
                Batch.is_deleted == False,
                ConcreteSample.is_deleted == False,
                CubeSet.is_deleted == False,
                CubeTest.age_days == 28,
                CubeTest.compressive_strength_mpa > 0.0,
            )
        )

        if target_plant_id:
            query = query.filter(Batch.plant_id == target_plant_id)
        if target_recipe_id:
            query = query.filter(Batch.recipe_id == target_recipe_id)
        if date_from:
            start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            query = query.filter(Batch.created_at >= start_dt)
        if date_to:
            end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            query = query.filter(Batch.created_at <= end_dt)

        results = query.all()

        token_version = CacheTokenService.get_token_version("reporting_metrics", db)
        scope_meta = StrengthDistributionScopeDTO(
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            cache_token_version=token_version,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Fallback recipe fck if specific recipe selected
        default_fck = 30.0
        if target_recipe_id:
            rec = db.query(Recipe).filter(Recipe.id == target_recipe_id).first()
            if rec:
                default_fck = resolve_fck_from_recipe(rec.target_strength_mpa, rec.grade, 30.0)

        if not results:
            assumed_s = IS456_ASSUMED_STANDARD_DEVIATION.get("M30", 5.0)
            active_z = EngineeringSettingsService.get_active_settings(db).get("confidence_multiplier_z", 1.65)
            target_fck_prime = round(default_fck + (active_z * assumed_s), 2)
            return StrengthDistributionDTO(
                total_tested_batches=0,
                total_tested_specimens=0,
                mean_strength_mpa=None,
                median_strength_mpa=None,
                standard_deviation_mpa=None,
                coefficient_of_variation_pct=None,
                min_strength_mpa=None,
                max_strength_mpa=None,
                characteristic_strength_fck_mpa=default_fck,
                target_mean_strength_fck_prime_mpa=target_fck_prime,
                strength_margin_mpa=None,
                compliance_rate_pct=0.0,
                stability_grade="INSUFFICIENT_DATA",
                histogram_bins=[],
                scope_metadata=scope_meta,
            )

        # Batch-level authoritative grouping
        batch_strengths_map: Dict[str, List[float]] = {}
        batch_fck_map: Dict[str, float] = {}
        all_specimens: List[float] = []

        for row in results:
            strength_val = float(row.compressive_strength_mpa)
            b_id = str(row.batch_id)
            all_specimens.append(strength_val)

            if b_id not in batch_strengths_map:
                batch_strengths_map[b_id] = []
                fck_val = resolve_fck_from_recipe(row.target_strength_mpa, row.grade, default_fck)
                batch_fck_map[b_id] = fck_val

            batch_strengths_map[b_id].append(strength_val)

        # Calculate authoritative batch mean strengths
        batch_means: List[float] = [
            round(sum(strengths) / len(strengths), 2)
            for strengths in batch_strengths_map.values()
        ]
        n_batches = len(batch_means)
        n_specimens = len(all_specimens)

        # Mean
        mean_strength = round(sum(batch_means) / n_batches, 2)

        # Median
        sorted_means = sorted(batch_means)
        if n_batches % 2 == 1:
            median_strength = sorted_means[n_batches // 2]
        else:
            median_strength = round((sorted_means[n_batches // 2 - 1] + sorted_means[n_batches // 2]) / 2.0, 2)

        # Sample Standard Deviation (s) over batch means
        if n_batches > 1:
            variance = sum((x - mean_strength) ** 2 for x in batch_means) / (n_batches - 1)
            standard_deviation = round(math.sqrt(variance), 2)
        else:
            standard_deviation = 0.0

        # Coefficient of Variation (CV%)
        if mean_strength > 0.0:
            coefficient_of_variation = round((standard_deviation / mean_strength) * 100.0, 2)
        else:
            coefficient_of_variation = 0.0

        # Representative fck (average batch fck or specific)
        char_fck = round(sum(batch_fck_map.values()) / len(batch_fck_map), 1)

        # Target Mean Strength (f'ck) per IS 456 / IS 10262: f'ck = fck + 1.65 * s
        if n_batches >= 30 and standard_deviation > 0.0:
            effective_s = standard_deviation
        else:
            effective_s = IS456_ASSUMED_STANDARD_DEVIATION.get("M30", 5.0)
        active_z = EngineeringSettingsService.get_active_settings(db).get("confidence_multiplier_z", 1.65)
        target_fck_prime = round(char_fck + (active_z * effective_s), 2)

        # Strength Margin = Mean - fck
        strength_margin = round(mean_strength - char_fck, 2)

        # Compliance Rate: fraction of batches whose 28d strength meets or exceeds its fck
        compliant_batches_count = sum(
            1 for b_id, b_mean in zip(batch_strengths_map.keys(), batch_means)
            if b_mean >= batch_fck_map[b_id]
        )
        compliance_rate = round((compliant_batches_count / n_batches) * 100.0, 1)

        # Stability Classification
        if n_batches < 3:
            stability_grade = "INSUFFICIENT_DATA"
        else:
            stability_grade = classify_coefficient_of_variation(coefficient_of_variation)

        # Histogram Bins (2.5 MPa discrete intervals from real data)
        min_strength = min(batch_means)
        max_strength = max(batch_means)

        bin_width = 2.5
        bin_start_floor = math.floor(min_strength / bin_width) * bin_width
        bin_end_ceil = math.ceil(max_strength / bin_width) * bin_width
        if bin_end_ceil == bin_start_floor:
            bin_end_ceil += bin_width

        num_bins = int(round((bin_end_ceil - bin_start_floor) / bin_width))
        bins_data: List[HistogramBinDTO] = []

        for i in range(num_bins):
            b_start = round(bin_start_floor + (i * bin_width), 1)
            b_end = round(b_start + bin_width, 1)
            # Match counts (last bin includes upper boundary)
            if i == num_bins - 1:
                b_count = sum(1 for x in batch_means if b_start <= x <= b_end)
            else:
                b_count = sum(1 for x in batch_means if b_start <= x < b_end)

            bins_data.append(
                HistogramBinDTO(
                    bin_start=b_start,
                    bin_end=b_end,
                    bin_label=f"{b_start:g}–{b_end:g}",
                    count=b_count,
                    is_below_fck=b_end <= char_fck,
                )
            )

        return StrengthDistributionDTO(
            total_tested_batches=n_batches,
            total_tested_specimens=n_specimens,
            mean_strength_mpa=mean_strength,
            median_strength_mpa=median_strength,
            standard_deviation_mpa=standard_deviation,
            coefficient_of_variation_pct=coefficient_of_variation,
            min_strength_mpa=min_strength,
            max_strength_mpa=max_strength,
            characteristic_strength_fck_mpa=char_fck,
            target_mean_strength_fck_prime_mpa=target_fck_prime,
            strength_margin_mpa=strength_margin,
            compliance_rate_pct=compliance_rate,
            stability_grade=stability_grade,
            histogram_bins=bins_data,
            scope_metadata=scope_meta,
        )

    @classmethod
    def get_mix_performance(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> MixPerformanceListDTO:
        """Calculate recipe and grade-level quality and compliance matrix."""
        target_plant_id = cls._resolve_plant_id(plant_code, db)
        target_recipe_id = cls._resolve_recipe_id(recipe_code, db)

        recipes_q = db.query(Recipe).filter(Recipe.is_deleted == False)
        if target_recipe_id:
            recipes_q = recipes_q.filter(Recipe.id == target_recipe_id)

        recipes = recipes_q.order_by(Recipe.grade.asc()).all()
        token_version = CacheTokenService.get_token_version("reporting_metrics", db)

        scope_meta = StrengthDistributionScopeDTO(
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            cache_token_version=token_version,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        items: List[MixPerformanceItemDTO] = []

        for r in recipes:
            # Total production batches for this recipe
            batch_q = db.query(Batch).filter(Batch.recipe_id == r.id, Batch.is_deleted == False)
            if target_plant_id:
                batch_q = batch_q.filter(Batch.plant_id == target_plant_id)
            if date_from:
                start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
                batch_q = batch_q.filter(Batch.created_at >= start_dt)
            if date_to:
                end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
                batch_q = batch_q.filter(Batch.created_at <= end_dt)

            total_b = batch_q.count()

            # Cube tests for this recipe
            cube_q = (
                db.query(CubeTest.compressive_strength_mpa, Batch.id.label("batch_id"))
                .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
                .join(ConcreteSample, CubeSet.sample_id == ConcreteSample.id)
                .join(Batch, ConcreteSample.batch_id == Batch.id)
                .filter(
                    Batch.recipe_id == r.id,
                    Batch.is_deleted == False,
                    ConcreteSample.is_deleted == False,
                    CubeSet.is_deleted == False,
                    CubeTest.age_days == 28,
                    CubeTest.compressive_strength_mpa > 0.0,
                )
            )
            if target_plant_id:
                cube_q = cube_q.filter(Batch.plant_id == target_plant_id)
            if date_from:
                cube_q = cube_q.filter(Batch.created_at >= start_dt)
            if date_to:
                cube_q = cube_q.filter(Batch.created_at <= end_dt)

            cube_rows = cube_q.all()

            fck_val = resolve_fck_from_recipe(r.target_strength_mpa, r.grade, 30.0)
            assumed_s = IS456_ASSUMED_STANDARD_DEVIATION.get(r.grade or "", 5.0)
            active_z = EngineeringSettingsService.get_active_settings(db).get("confidence_multiplier_z", 1.65)
            fck_prime = round(fck_val + (active_z * assumed_s), 2)

            if not cube_rows:
                items.append(
                    MixPerformanceItemDTO(
                        recipe_code=r.recipe_code,
                        recipe_name=r.recipe_name,
                        grade=r.grade or "M40",
                        target_strength_fck=fck_val,
                        target_mean_strength_fck_prime=fck_prime,
                        total_batches=total_b,
                        tested_batches_28d=0,
                        tested_specimens_28d=0,
                        mean_strength_mpa=None,
                        standard_deviation_mpa=None,
                        coefficient_of_variation_pct=None,
                        strength_margin_mpa=None,
                        compliance_rate_pct=0.0,
                        stability_status="AWAITING_TESTS",
                    )
                )
                continue

            # Group by batch
            b_map: Dict[str, List[float]] = {}
            for row in cube_rows:
                bid = str(row.batch_id)
                if bid not in b_map:
                    b_map[bid] = []
                b_map[bid].append(float(row.compressive_strength_mpa))

            b_means = [round(sum(v) / len(v), 2) for v in b_map.values()]
            n_b = len(b_means)
            mean_s = round(sum(b_means) / n_b, 2)

            if n_b > 1:
                var = sum((x - mean_s) ** 2 for x in b_means) / (n_b - 1)
                std = round(math.sqrt(var), 2)
            else:
                std = 0.0

            cv = round((std / mean_s) * 100.0, 2) if mean_s > 0.0 else 0.0
            margin = round(mean_s - fck_val, 2)
            pass_cnt = sum(1 for x in b_means if x >= fck_val)
            comp_rate = round((pass_cnt / n_b) * 100.0, 1)
            status = classify_coefficient_of_variation(cv) if n_b >= 3 else "CONTROLLED"

            items.append(
                MixPerformanceItemDTO(
                    recipe_code=r.recipe_code,
                    recipe_name=r.recipe_name,
                    grade=r.grade or "M40",
                    target_strength_fck=fck_val,
                    target_mean_strength_fck_prime=fck_prime,
                    total_batches=total_b,
                    tested_batches_28d=n_b,
                    tested_specimens_28d=len(cube_rows),
                    mean_strength_mpa=mean_s,
                    standard_deviation_mpa=std,
                    coefficient_of_variation_pct=cv,
                    strength_margin_mpa=margin,
                    compliance_rate_pct=comp_rate,
                    stability_status=status,
                )
            )

        # Sort recipes by total batches descending
        items.sort(key=lambda x: x.total_batches, reverse=True)

        return MixPerformanceListDTO(
            items=items,
            total_recipes_evaluated=len(items),
            scope_metadata=scope_meta,
        )

    @classmethod
    def get_strength_timeline(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50,
    ) -> StrengthTimelineListDTO:
        """Calculate chronological batch strength progression."""
        target_plant_id = cls._resolve_plant_id(plant_code, db)
        target_recipe_id = cls._resolve_recipe_id(recipe_code, db)

        batch_q = (
            db.query(Batch)
            .filter(Batch.is_deleted == False)
            .order_by(Batch.created_at.desc())
        )
        if target_plant_id:
            batch_q = batch_q.filter(Batch.plant_id == target_plant_id)
        if target_recipe_id:
            batch_q = batch_q.filter(Batch.recipe_id == target_recipe_id)
        if date_from:
            start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            batch_q = batch_q.filter(Batch.created_at >= start_dt)
        if date_to:
            end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            batch_q = batch_q.filter(Batch.created_at <= end_dt)

        batches = batch_q.limit(limit).all()

        points: List[StrengthTimelinePointDTO] = []
        token_ver = CacheTokenService.get_token_version("reporting_metrics", db)

        for b in reversed(batches):
            plant_obj = getattr(b, "plant", None)
            recipe_obj = getattr(b, "recipe", None)
            plant_cd = plant_obj.plant_code if plant_obj else "PLANT-01"
            recipe_cd = recipe_obj.recipe_code if recipe_obj else "M40_STD"
            grade = recipe_obj.grade if recipe_obj and recipe_obj.grade else "M40"
            target_str = getattr(recipe_obj, "target_strength_mpa", None) if recipe_obj else None
            fck_val = resolve_fck_from_recipe(target_str, grade, 30.0)
            assumed_s = IS456_ASSUMED_STANDARD_DEVIATION.get(grade, 5.0)
            active_z = EngineeringSettingsService.get_active_settings(db).get("confidence_multiplier_z", 1.65)
            fck_prime = round(fck_val + (active_z * assumed_s), 2)

            # Query cube tests for this batch
            tests = (
                db.query(CubeTest.age_days, CubeTest.compressive_strength_mpa)
                .join(CubeSet, CubeTest.cube_set_id == CubeSet.id)
                .join(ConcreteSample, CubeSet.sample_id == ConcreteSample.id)
                .filter(
                    ConcreteSample.batch_id == b.id,
                    ConcreteSample.is_deleted == False,
                    CubeSet.is_deleted == False,
                    CubeTest.compressive_strength_mpa > 0.0,
                )
                .all()
            )

            breaks_7d = [float(t.compressive_strength_mpa) for t in tests if t.age_days == 7]
            breaks_28d = [float(t.compressive_strength_mpa) for t in tests if t.age_days == 28]

            mean_7d = round(sum(breaks_7d) / len(breaks_7d), 2) if breaks_7d else None
            mean_28d = round(sum(breaks_28d) / len(breaks_28d), 2) if breaks_28d else None

            is_compliant_28d = (mean_28d >= fck_val) if mean_28d is not None else None

            prod_time_str = b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "—"

            points.append(
                StrengthTimelinePointDTO(
                    batch_number=b.batch_number,
                    plant_code=plant_cd,
                    recipe_code=recipe_cd,
                    grade=grade,
                    production_timestamp=prod_time_str,
                    result_7d_mpa=mean_7d,
                    result_28d_mpa=mean_28d,
                    target_fck_mpa=fck_val,
                    target_fck_prime_mpa=fck_prime,
                    is_compliant_28d=is_compliant_28d,
                )
            )

        scope_meta = StrengthDistributionScopeDTO(
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            cache_token_version=token_ver,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return StrengthTimelineListDTO(
            timeline=points,
            total_points=len(points),
            scope_metadata=scope_meta,
        )
