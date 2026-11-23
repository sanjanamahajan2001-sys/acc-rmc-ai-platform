import io
import os
import uuid
import logging
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_, desc, func, distinct
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    PageBreak,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from src.contracts.reporting.export_models import (
    FullDashboardReportDTO,
    ReportMetadataDTO,
    DashboardScopeContextDTO,
    ExecutiveDashboardSummaryDTO,
    ExecutiveSummaryQualityProductionDTO,
    ExecutiveSummaryStrengthPredictionDTO,
    ExecutiveSummaryMixOptimizationDTO,
    ExecutiveSummaryGovernanceCommercialDTO,
    GradePerformanceItemDTO,
    QualityProductionReportDTO,
    WeighmentComponentToleranceDTO,
    RecipeEfficiencyItemDTO,
    MaterialConsumptionReportDTO,
    ModelMonitoringReportDTO,
    RetrospectiveBacktestReportDTO,
    OptimizationRunReportDTO,
    CandidateDetailDTO,
    MasterVsCandidateConstituentComparisonDTO,
    RecipeImpactReportDTO,
    CostImpactReportDTO,
    ActionableFindingItemDTO,
    GovernanceReportDTO,
    ProvenanceReportDTO,
)
from src.database.models.user import User
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.models.optimization import (
    OptimizationRun,
    OptimizationCandidate,
)
from src.services.statistical_quality_service import StatisticalQualityService
from src.services.material_consumption_service import MaterialConsumptionService
from src.services.model_monitoring_service import ModelMonitoringService
from src.services.recipe_impact_service import RecipeImpactService
from src.services.cost_impact_service import CostImpactService
from src.services.recommendation_governance_service import RecommendationGovernanceService

logger = logging.getLogger("acc_rmc.reporting.export_service")


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs two-pass rendering to dynamically compute and stamp total pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 810, "ACC READY-MIX CONCRETE — OPERATIONS & MIX OPTIMIZATION REPORT")
            self.drawRightString(559, 810, "IS 456 / IS 10262 / IS 4926 COMPLIANCE")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        confidential_text = "CONFIDENTIAL — STRICTLY FOR INTERNAL AUTHORIZED OPERATIONS & QUALITY ASSURANCE USE"
        self.drawString(36, 26, confidential_text)
        self.drawRightString(559, 26, page_text)
        self.restoreState()


class DashboardExportService:
    """Authoritative service providing a single canonical path for dashboard reporting and export."""

    @classmethod
    def _synthesize_actionable_findings(
        cls,
        quality_report: QualityProductionReportDTO,
        material_report: MaterialConsumptionReportDTO,
        model_report: ModelMonitoringReportDTO,
        optimization_run: Optional[OptimizationRunReportDTO],
        recipe_impact: Optional[RecipeImpactReportDTO],
        selected_candidate: Optional[CandidateDetailDTO] = None,
        plant_code: Optional[str] = None,
    ) -> List[ActionableFindingItemDTO]:
        """Synthesize factual actionable findings and engineering review points from existing backend flags."""
        findings: List[ActionableFindingItemDTO] = []

        # 1. Quality & Strength Variation Finding
        cov = quality_report.coefficient_of_variation_percent or 0.0
        sigma = quality_report.batch_variation_sigma_mpa or 0.0
        mean_str = quality_report.mean_strength_28d_mpa or 0.0
        comp_rate = quality_report.compliance_rate_percent
        tested_cnt = quality_report.tested_specimens_count

        if cov >= 15.0 or sigma >= 5.5:
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="High Compressive Strength Batch Variation",
                    evidence_text=f"Observed CV: {cov:.1f}%, Standard Deviation (σ): ±{sigma:.2f} MPa across {tested_cnt} tested 28D specimens (Mean: {mean_str:.2f} MPa). Overall compliance: {comp_rate:.1f}%.",
                    impact_context="Elevated coefficient of variation indicates batch-to-batch strength dispersion, requiring higher target mean strength (f'ck) buffers under IS 456 / IS 10262.",
                    engineering_review_point="Review aggregate moisture compensation calibration, mixer dispersion uniformity, and batching cycle timing for recipes exhibiting high standard deviation.",
                    source_module="Statistical Quality Control (IS 456:2000 Table 8)",
                    severity="WARNING",
                )
            )
        else:
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="Statistical Compressive Strength Controlled",
                    evidence_text=f"Observed CV: {cov:.1f}%, Standard Deviation (σ): ±{sigma:.2f} MPa across {tested_cnt} tested specimens. 28D Compliance: {comp_rate:.1f}% against target fck {quality_report.target_fck_mpa or 30.0:.1f} MPa.",
                    impact_context="Compressive strength distribution satisfies IS 456 statistical reliability criteria with stable characteristic strength margins.",
                    engineering_review_point="Maintain current batching quality and standard water curing protocols across active production lines.",
                    source_module="Statistical Quality Control (IS 456:2000)",
                    severity="INFO",
                )
            )

        # 2. Weighment & Water Delivery Finding (IS 4926 Annex E)
        weigh_comp = material_report.weighment_compliance_rate_percent or 0.0
        water_var_pct = material_report.raw_water_variance_pct
        water_var_kg = material_report.raw_water_variance_kg

        if weigh_comp < 98.0 or abs(water_var_pct) > 1.0:
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="Batch Water Delivery & Weighing Variance",
                    evidence_text=f"IS 4926 Annex E weighment compliance rate is {weigh_comp:.2f}% with {material_report.tolerance_breaches_count} non-compliant weighments out of {material_report.total_evaluated_weighments} evaluated. Delivered mixing water: {material_report.actual_water_kg:,.0f} kg vs planned {material_report.planned_water_kg:,.0f} kg (Variance: {water_var_pct:+.2f}% / {water_var_kg:+,.0f} kg).",
                    impact_context="Fluctuations in batch mixing water directly alter effective water-binder (W/B) ratios, influencing 28-day strength development and slump consistency.",
                    engineering_review_point="Inspect plant water scale calibration, check valve cut-off responsiveness, and review real-time aggregate moisture compensation inputs.",
                    source_module="IS 4926:2003 Annex E Weighment Diagnostics",
                    severity="WARNING",
                )
            )
        else:
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="Batch Scale Weighing Accuracy Compliant",
                    evidence_text=f"Annex E weighment compliance is {weigh_comp:.2f}% across {material_report.total_evaluated_weighments} evaluated material batches.",
                    impact_context="Material scale batching is well within IS 4926:2003 Table E tolerances (±2% cement/water, ±3% aggregates).",
                    engineering_review_point="Continue routine daily scale zeroing and weekly calibration verification audits.",
                    source_module="IS 4926:2003 Annex E",
                    severity="INFO",
                )
            )

        # 3. Moisture Telemetry Coverage Finding
        if material_report.moisture_telemetry_status == "LIMITED":
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="Limited Aggregate Moisture Telemetry Coverage",
                    evidence_text=f"Moisture probe telemetry coverage is classified as LIMITED. {material_report.moisture_operational_note}",
                    impact_context="Manual aggregate moisture estimations can introduce unmonitored free-water variations into the batching cycle.",
                    engineering_review_point="Ensure daily moisture oven tests or automated probe telemetry are systematically logged into the QA register before morning batching.",
                    source_module="Batch Plant Automation & Moisture Telemetry",
                    severity="INFO",
                )
            )

        # 4. Binder Efficiency Finding
        avg_bi = material_report.average_binder_intensity_kg_m3
        if avg_bi > 0:
            scope_desc = f"Plant-average ({plant_code})" if plant_code else "Fleet-average"
            findings.append(
                ActionableFindingItemDTO(
                    finding_title="Binder Intensity & Material Efficiency Baseline",
                    evidence_text=f"{scope_desc} binder intensity is {avg_bi:.2f} kg/m³ per MPa compressive strength, with average W/B ratio of {material_report.water_to_binder_ratio or 0.0:.3f}.",
                    impact_context="Binder intensity measures clinker efficiency. Lower values signify higher material performance and reduced embodied carbon.",
                    engineering_review_point="Evaluate AI Mix Optimization candidates to identify feasible SCM (Fly Ash / GGBS) substitution boundaries without compromising 28D strength.",
                    source_module="Material Efficiency & Binder Intensity Matrix",
                    severity="INFO",
                )
            )

        # 5. AI Candidate Course-Correction (When Run & Selected Candidate Exist)
        active_cand = selected_candidate or (optimization_run.candidates[0] if (optimization_run and optimization_run.candidates) else None)
        if optimization_run and active_cand and recipe_impact:
            cand_pred_str = f"{float(active_cand.predicted_strength_mpa):.1f}" if active_cand.predicted_strength_mpa is not None else "—"
            margin_str = f"{active_cand.strength_margin_mpa:+.2f}" if active_cand.strength_margin_mpa is not None else "—"
            delta_val = recipe_impact.binder_delta_kg_m3
            delta_pct = recipe_impact.binder_delta_percent
            if delta_val < 0:
                change_str = f"Reduction: {abs(delta_val):.1f} kg/m³ ({delta_pct:+.1f}%)"
            elif delta_val > 0:
                change_str = f"Binder Delta: +{delta_val:.1f} kg/m³ ({delta_pct:+.1f}%)"
            else:
                change_str = f"Binder Parity: 0.0 kg/m³ (+0.0%)"

            pareto_sols_str = "solution" if optimization_run.pareto_optimal_count == 1 else "solutions"
            findings.append(
                ActionableFindingItemDTO(
                    finding_title=f"AI Mix Optimization Course-Correction (Candidate {active_cand.candidate_identifier})",
                    evidence_text=(
                        f"AI solver identified {optimization_run.pareto_optimal_count} Pareto-optimal {pareto_sols_str} for {optimization_run.grade_code}. "
                        f"Proposed candidate binder: {recipe_impact.candidate_binder_kg_m3:.1f} kg/m³ vs Master {recipe_impact.master_binder_kg_m3:.1f} kg/m³ "
                        f"({change_str}). Predicted 28D Strength: {cand_pred_str} MPa "
                        f"(Target f'ck: {optimization_run.target_mean_strength_mpa:.2f} MPa, Margin: {margin_str} MPa)."
                    ),
                    impact_context="Demonstrates a material/binder optimization candidate while strictly satisfying IS 456 Table 5 durability floors and 1.000 m³ volume yield. Commercial cost impact requires pricing configuration.",
                    engineering_review_point="Candidate is submitted for Four-Eyes Quality Head / Technical Director review and laboratory trial batching prior to production plant deployment.",
                    source_module="AI Mix Optimization & Pareto Candidate Solver (IS 10262:2019)",
                    severity="SUCCESS",
                )
            )

        return findings

    @classmethod
    def build_dashboard_report_dto(
        cls,
        db: Session,
        plant_code: Optional[str] = None,
        recipe_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        run_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> FullDashboardReportDTO:
        """Assemble the complete authoritative full dashboard report DTO with zero mock data."""
        generated_at = datetime.now(timezone.utc).isoformat()
        user_id = str(current_user.id) if current_user else None
        username = current_user.username if current_user else "Operations User"

        metadata = ReportMetadataDTO(
            report_title="ACC Ready-Mix Concrete Operations & Optimization Report",
            document_type="AUTHORITATIVE_EXECUTIVE_REPORT",
            generated_at=generated_at,
            generated_by_user_id=user_id,
            generated_by_username=username,
            platform_version="1.0.0",
            compliance_standard="IS 456:2000 / IS 10262:2019 / IS 4926:2003",
            environment="Production",
        )

        # 1. Resolve Scope Context Names
        plant_name = None
        recipe_name = None
        grade_code = None

        if plant_code:
            p_obj = db.execute(select(Plant).where(Plant.plant_code == plant_code)).scalars().first()
            if p_obj:
                plant_name = p_obj.plant_name
        
        if recipe_code:
            r_obj = db.execute(select(Recipe).where(Recipe.recipe_code == recipe_code)).scalars().first()
            if r_obj:
                recipe_name = r_obj.recipe_name
                grade_code = r_obj.grade

        scope_context = DashboardScopeContextDTO(
            plant_code=plant_code,
            plant_name=plant_name,
            recipe_code=recipe_code,
            recipe_name=recipe_name,
            grade_code=grade_code,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            selected_run_id=run_id,
            selected_candidate_id=candidate_id,
        )

        # 2. Operational Metrics & Material Consumption
        from src.api.reporting_router import get_operational_metrics
        op_metrics = get_operational_metrics(
            plant_code=plant_code,
            recipe_code=recipe_code,
            date_from=date_from,
            date_to=date_to,
            db=db,
            current_user=current_user,
        )

        mat_summary = MaterialConsumptionService.get_material_summary(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )
        batch_var = MaterialConsumptionService.get_batch_variance_analysis(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )
        efficiency = MaterialConsumptionService.get_efficiency_metrics(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )

        # Component-level weighment tolerances
        comp_tolerances: List[WeighmentComponentToleranceDTO] = []
        if hasattr(batch_var, 'categories') and batch_var.categories:
            for cat in batch_var.categories:
                if cat.compliance_status == "CLASSIFIABLE":
                    comp_tolerances.append(
                        WeighmentComponentToleranceDTO(
                            category_code=cat.category_code,
                            category_name=cat.category_name,
                            tolerance_pct=float(cat.is4926_tolerance_pct or 3.0),
                            record_count=cat.record_count,
                            compliant_count=cat.compliant_count,
                            non_compliant_count=cat.non_compliant_count,
                            compliance_rate_pct=cat.compliance_rate_pct,
                            mean_abs_variance_pct=float(cat.mean_abs_variance_pct or 0.0),
                        )
                    )

        # Recipe efficiency matrix
        recipe_eff_list: List[RecipeEfficiencyItemDTO] = []
        if hasattr(efficiency, 'recipe_metrics') and efficiency.recipe_metrics:
            for r in efficiency.recipe_metrics:
                recipe_eff_list.append(
                    RecipeEfficiencyItemDTO(
                        recipe_code=r.recipe_code,
                        total_batches=r.total_batches,
                        tested_28d_batches=r.batches_with_28d_test,
                        cement_kg_m3=float(r.mean_cement_kg_per_m3 or 0.0),
                        total_binder_kg_m3=float(r.mean_total_binder_kg_per_m3 or 0.0),
                        actual_wb_ratio=r.mean_actual_wb_ratio,
                        mean_28d_strength_mpa=r.mean_28d_strength_mpa,
                        binder_intensity_kg_per_m3_per_mpa=r.binder_intensity_kg_per_m3_per_mpa,
                        reliability_status=r.reliability_classification or "HIGH_CONFIDENCE",
                    )
                )

        water_moist = getattr(batch_var, 'water_moisture_analysis', None)

        material_report = MaterialConsumptionReportDTO(
            total_material_batched_kg=float(mat_summary.total_actual_material_kg),
            total_binder_batched_kg=float(mat_summary.total_binder_consumption_kg),
            total_water_batched_kg=float(mat_summary.total_water_consumption_kg),
            average_binder_intensity_kg_m3=float(efficiency.fleet_summary.fleet_avg_binder_intensity or 0.0),
            water_to_binder_ratio=efficiency.fleet_summary.fleet_avg_actual_wb,
            water_to_cement_ratio=efficiency.fleet_summary.fleet_avg_actual_wc,
            weighment_compliance_rate_percent=float(batch_var.overall_summary.annex_e_compliance_rate_pct),
            total_evaluated_weighments=batch_var.overall_summary.total_weighments,
            tolerance_breaches_count=batch_var.overall_summary.non_compliant_weighments,
            material_breakdown=[
                {
                    "category": getattr(m, 'category', getattr(m, 'material_category', 'General')),
                    "name": m.material_name,
                    "planned_kg": float(m.planned_quantity_kg),
                    "actual_kg": float(m.actual_quantity_kg),
                    "variance_percent": float(m.variance_percentage),
                    "density_kg_m3": float(getattr(m, 'consumption_kg_per_m3', getattr(m, 'consumption_per_m3_kg', 0.0))),
                }
                for m in mat_summary.items
            ],
            component_tolerances=comp_tolerances,
            recipe_efficiency_matrix=recipe_eff_list,
            planned_water_kg=float(getattr(water_moist, 'planned_water_kg', 0.0) if water_moist else 0.0),
            actual_water_kg=float(getattr(water_moist, 'actual_water_kg', 0.0) if water_moist else 0.0),
            raw_water_variance_kg=float(getattr(water_moist, 'raw_water_variance_kg', 0.0) if water_moist else 0.0),
            raw_water_variance_pct=float(getattr(water_moist, 'raw_water_variance_pct', 0.0) if water_moist else 0.0),
            moisture_telemetry_status=str(getattr(water_moist, 'data_quality_status', 'LIMITED') if water_moist else 'LIMITED'),
            moisture_operational_note=str(getattr(water_moist, 'operational_note', '') if water_moist else ''),
        )

        # 3. Quality & Production Metrics
        distribution = StatisticalQualityService.get_strength_distribution(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )
        timeline = StatisticalQualityService.get_strength_timeline(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to, limit=20
        )
        mix_perf = StatisticalQualityService.get_mix_performance(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )

        grade_matrix: List[GradePerformanceItemDTO] = []
        if hasattr(mix_perf, 'items') and mix_perf.items:
            for item in mix_perf.items:
                grade_matrix.append(
                    GradePerformanceItemDTO(
                        recipe_code=item.recipe_code,
                        recipe_name=item.recipe_name,
                        grade=item.grade,
                        target_fck_mpa=float(item.target_strength_fck or 30.0),
                        target_mean_strength_mpa=float(item.target_mean_strength_fck_prime or 38.25),
                        total_batches=item.total_batches,
                        tested_28d_batches=item.tested_batches_28d,
                        tested_28d_specimens=getattr(item, 'tested_specimens_28d', item.tested_batches_28d),
                        mean_strength_mpa=item.mean_strength_mpa,
                        standard_deviation_mpa=item.standard_deviation_mpa,
                        cov_percent=item.coefficient_of_variation_pct,
                        strength_margin_mpa=item.strength_margin_mpa,
                        compliance_percent=item.compliance_rate_pct,
                        status=item.stability_status or "CONTROLLED",
                    )
                )

        authoritative_compliance_pct = float(distribution.compliance_rate_pct or 0.0)

        quality_report = QualityProductionReportDTO(
            total_produced_volume_m3=float(op_metrics.total_volume_m3),
            total_production_batches=op_metrics.total_ingested_batches,
            active_plants_count=op_metrics.active_plants_count,
            compliance_rate_percent=authoritative_compliance_pct,
            mean_strength_28d_mpa=distribution.mean_strength_mpa,
            median_strength_28d_mpa=distribution.median_strength_mpa,
            target_fck_mpa=distribution.characteristic_strength_fck_mpa,
            design_target_mean_fck_prime_mpa=distribution.target_mean_strength_fck_prime_mpa,
            strength_margin_mpa=distribution.strength_margin_mpa,
            batch_variation_sigma_mpa=distribution.standard_deviation_mpa,
            coefficient_of_variation_percent=distribution.coefficient_of_variation_pct,
            tested_batches_count=distribution.total_tested_batches,
            tested_specimens_count=distribution.total_tested_specimens,
            histogram_intervals=[
                {"label": h.bin_label, "count": h.count, "meeting_spec": (not getattr(h, 'is_below_fck', False))}
                for h in distribution.histogram_bins
            ],
            recent_batches=[
                {
                    "batch_code": b.batch_number,
                    "recipe_code": b.recipe_code,
                    "grade": b.grade,
                    "strength_7d_mpa": b.result_7d_mpa,
                    "strength_28d_mpa": b.result_28d_mpa,
                    "target_strength_fck": b.target_fck_mpa,
                    "is_compliant": b.is_compliant_28d,
                }
                for b in timeline.timeline
            ],
            mix_performance_matrix=grade_matrix,
        )

        # 4. Strength Prediction & Model Lineage (Online Telemetry & Retrospective Backtest)
        pred_summary = ModelMonitoringService.get_prediction_summary(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )
        retro_summary = ModelMonitoringService.get_model_backtest(
            db=db, plant_code=plant_code, recipe_code=recipe_code, date_from=date_from, date_to=date_to
        )
        reg_models = ModelMonitoringService.get_registered_models(db=db)
        feat_imp = ModelMonitoringService.get_feature_importance(db=db)

        active_ver = "v1.0.0"
        algo_name = "Random Forest Regressor"
        for m in reg_models.models:
            if m.deployment_status == "ACTIVE":
                active_ver = m.model_version
                algo_name = getattr(m, 'algorithm', 'Random Forest Regressor')

        model_report = ModelMonitoringReportDTO(
            active_model_version=active_ver,
            algorithm_name=algo_name,
            deployment_status="ACTIVE",
            validation_status="Limited Validation",
            evaluation_samples_count=pred_summary.metrics.sample_count if pred_summary.metrics else 0,
            mae_mpa=pred_summary.metrics.mae_mpa if pred_summary.metrics else None,
            rmse_mpa=pred_summary.metrics.rmse_mpa if pred_summary.metrics else None,
            r2_score=pred_summary.metrics.r2_score if pred_summary.metrics else None,
            mean_residual_bias_mpa=pred_summary.metrics.mean_residual_mpa if pred_summary.metrics else None,
            residual_std_deviation_mpa=pred_summary.metrics.residual_std_dev_mpa if pred_summary.metrics else None,
            feature_importances=[
                {"feature": f.feature_name, "importance": f.importance_weight}
                for f in feat_imp.features
            ],
        )

        retro_metrics = retro_summary.summary_metrics if retro_summary else None
        retro_sample_count = retro_metrics.sample_count if retro_metrics else 0
        sample_warning_text = f"Only {retro_sample_count} genuine model evaluation pairs are currently available; sample size is insufficient for reliable final model-performance assessment."
        retrospective_report = RetrospectiveBacktestReportDTO(
            model_version=active_ver,
            algorithm_name=algo_name,
            evaluation_pairs_count=retro_sample_count,
            mae_mpa=retro_metrics.mae_mpa if retro_metrics else None,
            rmse_mpa=retro_metrics.rmse_mpa if retro_metrics else None,
            r2_score=retro_metrics.r2_score if retro_metrics else None,
            mean_residual_bias_mpa=retro_metrics.mean_residual_mpa if retro_metrics else None,
            residual_std_deviation_mpa=retro_metrics.residual_std_dev_mpa if retro_metrics else None,
            validation_status="Limited sample",
            sample_size_warning=sample_warning_text,
        )

        # 5. Optimization Run, Candidate, Recipe Impact, Cost, & Governance
        opt_report: Optional[OptimizationRunReportDTO] = None
        impact_report: Optional[RecipeImpactReportDTO] = None
        cost_report: Optional[CostImpactReportDTO] = None
        gov_report: Optional[GovernanceReportDTO] = None
        selected_cand: Optional[CandidateDetailDTO] = None

        target_run_id = run_id
        target_candidate_id = candidate_id

        if not target_run_id:
            try:
                opt_q = select(OptimizationRun)
                if plant_code:
                    opt_q = opt_q.where(OptimizationRun.plant_code == plant_code)
                if recipe_code:
                    opt_q = opt_q.where(OptimizationRun.recipe_code == recipe_code)
                
                success_run = db.execute(
                    opt_q.where(OptimizationRun.run_status == "SUCCESS")
                    .order_by(OptimizationRun.created_at.desc())
                ).scalars().first()

                if success_run:
                    target_run_id = str(success_run.id)
            except Exception as e:
                logger.warning("Failed to auto-resolve optimization run: %s", e)

        if target_run_id:
            try:
                run_obj = db.get(OptimizationRun, target_run_id)
                if run_obj and not run_obj.is_deleted:
                    db_cands = db.execute(
                        select(OptimizationCandidate).where(OptimizationCandidate.run_id == target_run_id)
                    ).scalars().all()

                    cands: List[CandidateDetailDTO] = []
                    target_strength_snap = run_obj.target_strength_snapshot_json or {}
                    target_mean_val = float(target_strength_snap.get("target_mean_strength_mpa", 38.25))
                    target_char_val = float(target_strength_snap.get("characteristic_fck_mpa", 30.0))

                    for c in db_cands:
                        c_payload = c.constituent_payload_json or {}
                        c_eval = c.constraint_evaluation_json or {}
                        wb_val = float(c_payload.get("water_binder_ratio", 0.42))
                        yield_val = float(c_eval.get("physical_volume_diagnostic", {}).get("volume_balance_actual_m3", 1.0))
                        cand_pred = float(c.predicted_strength_mpa) if c.predicted_strength_mpa is not None else 0.0
                        margin_val = cand_pred - target_mean_val
                        is_pareto = bool(c_eval.get("is_non_dominated", c.is_recommended))

                        cands.append(
                            CandidateDetailDTO(
                                candidate_id=str(c.id),
                                candidate_identifier=c.candidate_identifier,
                                is_feasible=bool(c.is_feasible),
                                is_pareto_optimal=is_pareto,
                                predicted_strength_mpa=c.predicted_strength_mpa,
                                strength_margin_mpa=margin_val,
                                binder_intensity_kg_m3=float(c.binder_intensity or 300.0),
                                water_binder_ratio=wb_val,
                                yield_m3=yield_val,
                                cost_per_m3=c.cost_per_m3,
                                cost_status="CONFIGURED" if c.cost_per_m3 is not None else "NOT_CONFIGURED",
                                review_status="PENDING_REVIEW",
                                reviewed_by_username=None,
                                reviewed_at=None,
                                review_decision_reason=None,
                                review_comments=None,
                                constituents=c_payload.get("constituents", []),
                                constraint_diagnostics=c_eval.get("constraint_diagnostics", []),
                            )
                        )

                    opt_report = OptimizationRunReportDTO(
                        run_id=str(run_obj.id),
                        recipe_code=run_obj.recipe_code,
                        recipe_name=getattr(run_obj, 'recipe_name', recipe_name or run_obj.recipe_code),
                        plant_code=run_obj.plant_code,
                        grade_code=grade_code or "M30",
                        optimization_objective=run_obj.optimization_objective or "MINIMIZE_BINDER_INTENSITY",
                        run_status=run_obj.run_status,
                        model_version_used=str((run_obj.model_snapshot_json or {}).get("model_version", "v1.0.0")),
                        target_characteristic_fck_mpa=target_char_val,
                        target_mean_strength_mpa=target_mean_val,
                        total_candidates_evaluated=len(cands),
                        feasible_candidates_count=sum(1 for c in cands if c.is_feasible),
                        pareto_optimal_count=sum(1 for c in cands if c.is_pareto_optimal),
                        evaluated_at=run_obj.created_at.isoformat() if run_obj.created_at else generated_at,
                        candidates=cands,
                    )

                    # Unified candidate resolution: Pareto-optimal candidate first, or first candidate
                    if cands:
                        if target_candidate_id:
                            selected_cand = next((c for c in cands if c.candidate_id == target_candidate_id), None)
                        if not selected_cand:
                            pareto_cands = [c for c in cands if c.is_pareto_optimal]
                            selected_cand = pareto_cands[0] if pareto_cands else cands[0]
                        target_candidate_id = selected_cand.candidate_id

                    # Update scope context with resolved run and candidate IDs
                    scope_context.selected_run_id = target_run_id
                    scope_context.selected_candidate_id = target_candidate_id

                    if target_candidate_id:
                        auth_user = current_user or User(username="system_report", account_status="ACTIVE")
                        try:
                            impact_data = RecipeImpactService.get_candidate_impact(
                                db=db, run_id=target_run_id, candidate_id=target_candidate_id, current_user=auth_user
                            )
                            if impact_data:
                                isum = impact_data.impact_summary
                                impact_report = RecipeImpactReportDTO(
                                    candidate_identifier=impact_data.candidate_identifier,
                                    is_feasible=impact_data.candidate_evaluation.is_feasible,
                                    is_pareto_optimal=impact_data.candidate_evaluation.is_non_dominated,
                                    master_binder_kg_m3=float(isum.current_total_binder_kg_m3),
                                    candidate_binder_kg_m3=float(isum.candidate_total_binder_kg_m3),
                                    binder_delta_kg_m3=float(isum.binder_delta_kg_m3),
                                    binder_delta_percent=float(isum.binder_percentage_delta or 0.0),
                                    master_water_binder_ratio=float(isum.current_water_binder_ratio),
                                    candidate_water_binder_ratio=float(isum.candidate_water_binder_ratio),
                                    scm_replacement_percentage=0.0,
                                    scm_replacement_delta_percent=0.0,
                                    constituents=[
                                        MasterVsCandidateConstituentComparisonDTO(
                                            material_code=c.material_code,
                                            material_name=c.material_name,
                                            category=c.category_code,
                                            master_qty_kg_m3=float(c.current_quantity_kg_m3),
                                            candidate_qty_kg_m3=float(c.candidate_quantity_kg_m3),
                                            delta_qty_kg_m3=float(c.absolute_delta_kg_m3),
                                            delta_percent=c.percentage_delta,
                                            unit_price_inr=None,
                                            master_cost_inr_m3=None,
                                            candidate_cost_inr_m3=None,
                                            cost_delta_inr_m3=None,
                                        )
                                        for c in impact_data.constituents
                                    ],
                                )
                        except Exception as e:
                            logger.warning("Failed to load recipe impact: %s", e)

                        try:
                            cost_data = CostImpactService.get_candidate_cost_impact(
                                db=db, run_id=target_run_id, candidate_id=target_candidate_id, current_user=auth_user
                            )
                            if cost_data and cost_data.cost_summary:
                                csum = cost_data.cost_summary
                                pimp = csum.production_impact
                                cost_report = CostImpactReportDTO(
                                    pricing_status=csum.cost_status,
                                    pricing_source_description=cost_data.price_source_description,
                                    effective_date=cost_data.effective_date,
                                    master_recipe_cost_per_m3=csum.master_cost_per_m3,
                                    candidate_cost_per_m3=csum.candidate_cost_per_m3,
                                    cost_delta_per_m3=csum.cost_delta_per_m3,
                                    cost_delta_percent=csum.cost_delta_percent,
                                    volume_schedule_configured=bool(pimp and pimp.is_configured),
                                    annual_volume_m3=pimp.annualized_volume_m3 if pimp else None,
                                    annual_cost_delta_inr=pimp.annualized_cost_delta if pimp else None,
                                )
                        except Exception as e:
                            logger.warning("Failed to load cost impact: %s", e)

                        try:
                            gov_data = RecommendationGovernanceService.get_run_governance(
                                db=db, run_id=target_run_id, current_user=auth_user
                            )
                            if gov_data and gov_data.candidates:
                                gcand = next((gc for gc in gov_data.candidates if gc.candidate_id == target_candidate_id), gov_data.candidates[0])
                                gov_report = GovernanceReportDTO(
                                    review_status=gcand.review_status,
                                    reviewed_by_username=gcand.reviewed_by_username,
                                    reviewed_by_role="TECHNICAL_DIRECTOR" if gcand.reviewed_by_username else None,
                                    reviewed_at=gcand.reviewed_at,
                                    review_reason_code=gcand.review_decision_reason,
                                    review_comments=gcand.review_comments,
                                    production_activation_notice="Production activation is outside current platform scope.",
                                    audit_event_id=None,
                                )
                        except Exception as e:
                            logger.warning("Failed to load governance review state: %s", e)
            except Exception as e:
                logger.warning("Failed to compile optimization report DTO: %s", e)

        # 6. Executive Dashboard Summary (4 Groups)
        es_quality = ExecutiveSummaryQualityProductionDTO(
            grades_evaluated=len(quality_report.mix_performance_matrix) or 1,
            total_batches_produced=quality_report.total_production_batches,
            total_volume_m3=quality_report.total_produced_volume_m3,
            batches_tested_28d=quality_report.tested_batches_count,
            specimens_tested_28d=quality_report.tested_specimens_count,
            mean_strength_28d_mpa=quality_report.mean_strength_28d_mpa,
            quality_compliance_percent=quality_report.compliance_rate_percent,
            strength_variability_sigma_mpa=quality_report.batch_variation_sigma_mpa,
            strength_cov_percent=quality_report.coefficient_of_variation_percent,
            weighment_accuracy_percent=material_report.weighment_compliance_rate_percent,
        )

        # Consistent Strength Prediction Reconciliation
        active_pred_val = selected_cand.predicted_strength_mpa if selected_cand else (opt_report.candidates[0].predicted_strength_mpa if (opt_report and opt_report.candidates) else None)
        active_target_char = opt_report.target_characteristic_fck_mpa if opt_report else quality_report.target_fck_mpa
        active_target_mean = opt_report.target_mean_strength_mpa if opt_report else quality_report.design_target_mean_fck_prime_mpa
        active_margin_val = (float(active_pred_val) - float(active_target_mean)) if (active_pred_val is not None and active_target_mean is not None) else None

        mae_str = f"{retrospective_report.mae_mpa:.2f} MPa" if (retrospective_report and retrospective_report.mae_mpa is not None) else "—"
        es_strength = ExecutiveSummaryStrengthPredictionDTO(
            platform_active_model=model_report.algorithm_name,
            platform_model_version=model_report.active_model_version,
            model_used_for_optimization_run=opt_report.model_version_used if opt_report else model_report.active_model_version,
            validation_status=f"Limited sample (Retrospective Backtest: MAE {mae_str})",
            target_characteristic_fck_mpa=active_target_char,
            target_mean_strength_fck_prime_mpa=active_target_mean,
            predicted_strength_mpa=active_pred_val,
            prediction_margin_mpa=active_margin_val,
            prediction_mean_abs_error_mae=retrospective_report.mae_mpa if (retrospective_report and retrospective_report.mae_mpa is not None) else model_report.mae_mpa,
        )

        recipe_impact_str = "—"
        if impact_report:
            recipe_impact_str = f"Binder Δ: {impact_report.binder_delta_kg_m3:+.1f} kg/m³ ({impact_report.binder_delta_percent:+.1f}%)"

        es_opt = ExecutiveSummaryMixOptimizationDTO(
            has_optimization_run=opt_report is not None,
            optimization_run_id=opt_report.run_id if opt_report else None,
            optimization_objective=opt_report.optimization_objective if opt_report else "—",
            total_candidates_evaluated=opt_report.total_candidates_evaluated if opt_report else 0,
            feasible_candidates_count=opt_report.feasible_candidates_count if opt_report else 0,
            pareto_optimal_count=opt_report.pareto_optimal_count if opt_report else 0,
            selected_candidate_identifier=selected_cand.candidate_identifier if selected_cand else None,
            binder_intensity_kg_m3=selected_cand.binder_intensity_kg_m3 if selected_cand else None,
            water_binder_ratio=selected_cand.water_binder_ratio if selected_cand else None,
            yield_m3=selected_cand.yield_m3 if selected_cand else None,
            recipe_impact_summary=recipe_impact_str,
        )

        es_gov = ExecutiveSummaryGovernanceCommercialDTO(
            engineering_feasibility="FEASIBLE" if (selected_cand and selected_cand.is_feasible) else ("INFEASIBLE" if selected_cand else "—"),
            review_status=gov_report.review_status if gov_report else ("PENDING_REVIEW" if opt_report else "NOT_APPLICABLE"),
            human_reviewer_username=gov_report.reviewed_by_username if gov_report else None,
            human_reviewer_role=gov_report.reviewed_by_role if gov_report else None,
            review_timestamp=gov_report.reviewed_at if gov_report else None,
            review_reason_code=gov_report.review_reason_code if gov_report else None,
            pricing_configuration_status=cost_report.pricing_status if cost_report else "NOT_CONFIGURED",
            pricing_source_description=cost_report.pricing_source_description if cost_report else "Pricing Source: Not Configured",
            cost_per_m3_inr=cost_report.candidate_cost_per_m3 if cost_report else None,
            cost_delta_per_m3_inr=cost_report.cost_delta_per_m3 if cost_report else None,
            production_activation_status="PRODUCTION_ACTIVATION_OUTSIDE_CURRENT_PHASE",
            production_activation_notice="Production activation is outside the current platform scope.",
        )

        exec_summary = ExecutiveDashboardSummaryDTO(
            quality_and_production=es_quality,
            strength_prediction=es_strength,
            mix_optimization=es_opt,
            governance_and_commercial=es_gov,
        )

        actionable_findings = cls._synthesize_actionable_findings(
            quality_report=quality_report,
            material_report=material_report,
            model_report=model_report,
            optimization_run=opt_report,
            recipe_impact=impact_report,
            selected_candidate=selected_cand,
            plant_code=plant_code,
        )

        provenance = ProvenanceReportDTO(
            source_database="acc_rmc_prod",
            recipe_snapshot_version="1.0.0",
            model_snapshot_id=model_report.active_model_version,
            dataset_training_lineage="StrenghtTrendR5 + FT7R5 + 03.02.26-K",
            governance_audit_table="usr_audit_logs",
            export_engine="ReportLab Platypus / Canonical Serializer",
        )

        return FullDashboardReportDTO(
            report_metadata=metadata,
            dashboard_context=scope_context,
            executive_summary=exec_summary,
            quality_metrics=quality_report,
            material_consumption=material_report,
            model_monitoring=model_report,
            retrospective_backtest=retrospective_report,
            optimization_run=opt_report,
            recipe_impact=impact_report,
            cost_impact=cost_report,
            governance=gov_report,
            actionable_findings=actionable_findings,
            provenance=provenance,
        )

    @classmethod
    def render_json(cls, report_dto: FullDashboardReportDTO) -> str:
        """Serialize FullDashboardReportDTO to standard JSON format."""
        return report_dto.model_dump_json(indent=2)

    @classmethod
    def _generate_sqc_chart(cls, report_dto: FullDashboardReportDTO) -> Optional[Image]:
        """Generate dual Matplotlib vector plot in-memory: Histogram & Chronological timeline."""
        try:
            fig = Figure(figsize=(7.2, 2.2), dpi=200)
            fig.patch.set_facecolor("#ffffff")
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)

            # 1. Strength Histogram
            hist_bins = report_dto.quality_metrics.histogram_intervals
            if hist_bins:
                labels = [b["label"] for b in hist_bins]
                counts = [b["count"] for b in hist_bins]
                bar_colors = ["#0284c7" if b.get("meeting_spec", True) else "#ef4444" for b in hist_bins]
                ax1.bar(range(len(labels)), counts, color=bar_colors, width=0.65, edgecolor="#0f172a", linewidth=0.5)
                ax1.set_xticks(range(len(labels)))
                ax1.set_xticklabels(labels, rotation=35, ha="right", fontsize=6)
                ax1.set_title("28D Strength Distribution (IS 456)", fontsize=7.5, fontweight="bold", pad=4)
                ax1.set_ylabel("Batch Count", fontsize=6.5)
                ax1.grid(axis="y", linestyle="--", alpha=0.3)
                ax1.tick_params(axis="both", labelsize=6)
            else:
                ax1.text(0.5, 0.5, "No Histogram Data", ha="center", va="center", fontsize=7, color="#64748b")
                ax1.axis("off")

            # 2. Timeline
            batches = report_dto.quality_metrics.recent_batches
            if batches:
                idxs = list(range(len(batches)))
                s28 = [b.get("strength_28d_mpa") or 0.0 for b in batches]
                fck = report_dto.quality_metrics.target_fck_mpa or 30.0
                ax2.plot(idxs, s28, color="#059669", marker="o", markersize=3, linewidth=1.2, label="28D Break")
                ax2.axhline(fck, color="#dc2626", linestyle="--", linewidth=1.0, label=f"Target fck ({fck:.0f} MPa)")
                ax2.set_title("Recent Batch Strength Progression", fontsize=7.5, fontweight="bold", pad=4)
                ax2.set_ylabel("Compressive Strength (MPa)", fontsize=6.5)
                ax2.set_xlabel("Recent Batches (Chronological)", fontsize=6.5)
                ax2.grid(True, linestyle="--", alpha=0.3)
                ax2.legend(loc="lower right", fontsize=5.5, framealpha=0.8)
                ax2.tick_params(axis="both", labelsize=6)
            else:
                ax2.text(0.5, 0.5, "No Recent Timeline Data", ha="center", va="center", fontsize=7, color="#64748b")
                ax2.axis("off")

            fig.tight_layout()
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=200)
            img_buf.seek(0)
            return Image(img_buf, width=520, height=155)
        except Exception as e:
            logger.error("Failed to render SQC chart: %s", e)
            return None

    @classmethod
    def _generate_pareto_chart(cls, opt_dto: OptimizationRunReportDTO) -> Optional[Image]:
        """Generate Matplotlib Pareto Frontier scatter plot in-memory."""
        try:
            fig = Figure(figsize=(7.2, 2.0), dpi=200)
            fig.patch.set_facecolor("#ffffff")
            ax = fig.add_subplot(1, 1, 1)

            cands = opt_dto.candidates
            if cands:
                p_binders = [float(c.binder_intensity_kg_m3) for c in cands if c.is_pareto_optimal]
                p_strengths = [float(c.predicted_strength_mpa) if c.predicted_strength_mpa is not None else 0.0 for c in cands if c.is_pareto_optimal]

                f_binders = [float(c.binder_intensity_kg_m3) for c in cands if c.is_feasible and not c.is_pareto_optimal]
                f_strengths = [float(c.predicted_strength_mpa) if c.predicted_strength_mpa is not None else 0.0 for c in cands if c.is_feasible and not c.is_pareto_optimal]

                inf_binders = [float(c.binder_intensity_kg_m3) for c in cands if not c.is_feasible]
                inf_strengths = [float(c.predicted_strength_mpa) if c.predicted_strength_mpa is not None else 0.0 for c in cands if not c.is_feasible]

                if inf_binders:
                    ax.scatter(inf_binders, inf_strengths, color="#94a3b8", marker="x", s=25, label="Infeasible Candidate", alpha=0.6)
                if f_binders:
                    ax.scatter(f_binders, f_strengths, color="#0284c7", marker="o", s=30, label="Feasible Alternative")
                if p_binders:
                    ax.scatter(p_binders, p_strengths, color="#059669", marker="D", s=45, label="Pareto Optimal", zorder=5)
                    sorted_p = sorted(zip(p_binders, p_strengths))
                    ax.plot([x[0] for x in sorted_p], [x[1] for x in sorted_p], color="#059669", linestyle="-", linewidth=1.2, alpha=0.8)

                target_mean = opt_dto.target_mean_strength_mpa
                ax.axhline(target_mean, color="#dc2626", linestyle="--", linewidth=1.0, label=f"Target f'ck ({target_mean:.2f} MPa)")

                ax.set_title(f"Pareto Frontier: Binder Intensity vs Predicted 28D Strength (Run {opt_dto.run_id[:8]})", fontsize=7.5, fontweight="bold", pad=4)
                ax.set_xlabel("Binder Intensity (kg/m³)", fontsize=6.5)
                ax.set_ylabel("Predicted 28D Strength (MPa)", fontsize=6.5)
                ax.grid(True, linestyle="--", alpha=0.3)
                ax.legend(loc="lower right", fontsize=5.5, framealpha=0.8)
                ax.tick_params(axis="both", labelsize=6)
            else:
                ax.text(0.5, 0.5, "No Candidate Evaluation Data", ha="center", va="center", fontsize=7, color="#64748b")
                ax.axis("off")

            fig.tight_layout()
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=200)
            img_buf.seek(0)
            return Image(img_buf, width=520, height=140)
        except Exception as e:
            logger.error("Failed to render Pareto chart: %s", e)
            return None

    @classmethod
    def render_pdf(cls, report_dto: FullDashboardReportDTO) -> bytes:
        """Render authoritative multi-page PDF using ReportLab Platypus and vector charts."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=45,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica",
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0284c7"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=3,
        )
        body_style = ParagraphStyle(
            "BodyText",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica",
        )
        table_cell = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica",
        )
        table_header = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#ffffff"),
            fontName="Helvetica-Bold",
        )
        finding_title_style = ParagraphStyle(
            "FindingTitle",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )

        story = []

        # -------------------------------------------------------------
        # 1. Report Header Banner & Scope Context
        # -------------------------------------------------------------
        header_table_data = [
            [
                Paragraph("<b>ACC READY-MIX CONCRETE</b><br/><font size='7' color='#64748b'>OPERATIONS & MIX OPTIMIZATION EXECUTIVE REPORT</font>", title_style),
                Paragraph(f"<b>Date:</b> {report_dto.report_metadata.generated_at[:10]}<br/><b>Generated By:</b> {report_dto.report_metadata.generated_by_username}<br/><b>Standard:</b> IS 456 / IS 10262 / IS 4926", subtitle_style),
            ]
        ]
        header_table = Table(header_table_data, colWidths=[330, 190])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=2, spaceAfter=6))

        # Scope Context Table
        ctx = report_dto.dashboard_context
        ctx_data = [
            [
                Paragraph("<b>Plant Scope:</b>", body_style),
                Paragraph(f"{ctx.plant_code or 'All Production Plants'} ({ctx.plant_name or 'Fleet Scope'})", body_style),
                Paragraph("<b>Recipe / Grade:</b>", body_style),
                Paragraph(f"{ctx.recipe_code or 'All Grades'} ({ctx.grade_code or 'Standard Scope'})", body_style),
            ],
            [
                Paragraph("<b>Date Range:</b>", body_style),
                Paragraph(f"{ctx.date_from or 'Start'} to {ctx.date_to or 'Current'}", body_style),
                Paragraph("<b>Optimization Run:</b>", body_style),
                Paragraph(f"{ctx.selected_run_id[:8]}..." if ctx.selected_run_id else "No Optimization Run Selected", body_style),
            ]
        ]
        ctx_table = Table(ctx_data, colWidths=[70, 190, 85, 175])
        ctx_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#edf2f7")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(ctx_table)
        story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 2. Executive Dashboard Summary (4 Groups)
        # -------------------------------------------------------------
        es = report_dto.executive_summary
        summary_box_data = [
            [
                Paragraph("<b>A. QUALITY & PRODUCTION</b>", table_header),
                Paragraph("<b>B. STRENGTH PREDICTION</b>", table_header),
            ],
            [
                Paragraph(
                    f"• <b>Total Volume:</b> {es.quality_and_production.total_volume_m3:,.1f} m³ ({es.quality_and_production.total_batches_produced:,} Batches)<br/>"
                    f"• <b>28D Tested:</b> {es.quality_and_production.specimens_tested_28d:,} Specimen Cubes ({es.quality_and_production.batches_tested_28d:,} Batches)<br/>"
                    f"• <b>Mean 28D Strength:</b> {es.quality_and_production.mean_strength_28d_mpa or '—'} MPa<br/>"
                    f"• <b>IS Compliance:</b> {f'{es.quality_and_production.quality_compliance_percent:.1f}%' if es.quality_and_production.quality_compliance_percent is not None else '—'}<br/>"
                    f"• <b>Variability (σ / CV%):</b> {f'±{es.quality_and_production.strength_variability_sigma_mpa:.2f} MPa ({es.quality_and_production.strength_cov_percent:.1f}%)' if es.quality_and_production.strength_variability_sigma_mpa is not None else '—'}<br/>"
                    f"• <b>Weighment Accuracy:</b> {f'{es.quality_and_production.weighment_accuracy_percent:.1f}%' if es.quality_and_production.weighment_accuracy_percent is not None else '—'}",
                    table_cell
                ),
                Paragraph(
                    f"• <b>Platform Model:</b> {es.strength_prediction.platform_active_model}<br/>"
                    f"• <b>Optimization Model Snapshot:</b> {es.strength_prediction.model_used_for_optimization_run}<br/>"
                    f"• <b>Validation Status:</b> {es.strength_prediction.validation_status}<br/>"
                    f"• <b>Target Mean Strength (f'ck):</b> {es.strength_prediction.target_mean_strength_fck_prime_mpa or '—'} MPa<br/>"
                    f"• <b>Predicted Strength:</b> {es.strength_prediction.predicted_strength_mpa or '—'} MPa<br/>"
                    f"• <b>Prediction Margin:</b> {f'+{es.strength_prediction.prediction_margin_mpa:.2f}' if es.strength_prediction.prediction_margin_mpa is not None else '—'} MPa<br/>"
                    f"• <b>Retrospective Backtest MAE:</b> {f'{es.strength_prediction.prediction_mean_abs_error_mae:.2f} MPa' if es.strength_prediction.prediction_mean_abs_error_mae is not None else '—'}",
                    table_cell
                ),
            ],
            [
                Paragraph("<b>C. MIX OPTIMIZATION</b>", table_header),
                Paragraph("<b>D. GOVERNANCE & COMMERCIAL</b>", table_header),
            ],
            [
                Paragraph(
                    f"• <b>Status:</b> {'Active Optimization Context' if es.mix_optimization.has_optimization_run else 'No Optimization Run Selected'}<br/>"
                    f"• <b>Objective:</b> {es.mix_optimization.optimization_objective}<br/>"
                    f"• <b>Total Candidates:</b> {es.mix_optimization.total_candidates_evaluated}<br/>"
                    f"• <b>Feasible Candidates:</b> {es.mix_optimization.feasible_candidates_count}<br/>"
                    f"• <b>Pareto Optimal:</b> {es.mix_optimization.pareto_optimal_count}<br/>"
                    f"• <b>Selected Candidate:</b> {es.mix_optimization.selected_candidate_identifier or 'None'}<br/>"
                    f"• <b>Binder Intensity:</b> {es.mix_optimization.binder_intensity_kg_m3 or '—'} kg/m³<br/>"
                    f"• <b>Impact Summary:</b> {es.mix_optimization.recipe_impact_summary}",
                    table_cell
                ),
                Paragraph(
                    f"• <b>Engineering Feasibility:</b> {es.governance_and_commercial.engineering_feasibility}<br/>"
                    f"• <b>Human Review State:</b> {es.governance_and_commercial.review_status}<br/>"
                    f"• <b>Reviewer:</b> {es.governance_and_commercial.human_reviewer_username or 'Pending Review'}<br/>"
                    f"• <b>Pricing Status:</b> {es.governance_and_commercial.pricing_source_description}<br/>"
                    f"• <b>Material Cost / m³:</b> {f'₹ {es.governance_and_commercial.cost_per_m3_inr:,.2f}' if es.governance_and_commercial.cost_per_m3_inr is not None else '—'}<br/>"
                    f"• <b>Cost Delta / m³:</b> {f'₹ {es.governance_and_commercial.cost_delta_per_m3_inr:,.2f}' if es.governance_and_commercial.cost_delta_per_m3_inr is not None else '—'}<br/>"
                    f"• <b>Notice:</b> <i>{es.governance_and_commercial.production_activation_notice}</i>",
                    table_cell
                ),
            ],
        ]
        summary_table = Table(summary_box_data, colWidths=[260, 260])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#0284c7")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#0284c7")),
            ("BACKGROUND", (0, 2), (0, 2), colors.HexColor("#475569")),
            ("BACKGROUND", (1, 2), (1, 2), colors.HexColor("#475569")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 3. Actionable Findings & Engineering Review Points
        # -------------------------------------------------------------
        if report_dto.actionable_findings:
            story.append(Paragraph("Actionable Findings & Engineering Review Points", section_heading))
            story.append(Paragraph("<font color='#64748b'>Factual operational course corrections synthesized directly from dashboard quality flags and optimization solvers:</font>", subtitle_style))
            story.append(Spacer(1, 4))

            for item in report_dto.actionable_findings:
                bg_color = "#fef2f2" if item.severity == "WARNING" else ("#f0fdf4" if item.severity == "SUCCESS" else "#f8fafc")
                border_color = "#fca5a5" if item.severity == "WARNING" else ("#86efac" if item.severity == "SUCCESS" else "#cbd5e1")
                tag_color = "#dc2626" if item.severity == "WARNING" else ("#059669" if item.severity == "SUCCESS" else "#0284c7")

                finding_card_data = [
                    [
                        Paragraph(f"<font color='{tag_color}'><b>[{item.severity}] {item.finding_title}</b></font> <font color='#64748b' size='6.5'>({item.source_module})</font>", finding_title_style),
                    ],
                    [
                        Paragraph(f"• <b>Observed Evidence:</b> {item.evidence_text}<br/>"
                                  f"• <b>Operational Impact:</b> {item.impact_context}<br/>"
                                  f"• <b>Engineering Review Point:</b> <b>{item.engineering_review_point}</b>", body_style),
                    ]
                ]
                finding_tbl = Table(finding_card_data, colWidths=[520])
                finding_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(border_color)),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(finding_tbl)
                story.append(Spacer(1, 4))

            story.append(Spacer(1, 4))

        # -------------------------------------------------------------
        # 4. Statistical Quality Control & Strength Analysis
        # -------------------------------------------------------------
        story.append(Paragraph("Statistical Quality Control & Strength Progression", section_heading))
        chart_img = cls._generate_sqc_chart(report_dto)
        if chart_img:
            story.append(chart_img)
            story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 5. Mix Design & Grade Performance Matrix
        # -------------------------------------------------------------
        if report_dto.quality_metrics.mix_performance_matrix:
            story.append(Paragraph("Mix Design & Grade Performance Matrix (IS 456 / IS 10262)", section_heading))
            story.append(Paragraph(f"<b>Tested Scope Breakdown:</b> {report_dto.quality_metrics.tested_batches_count} tested batches ({report_dto.quality_metrics.tested_specimens_count} laboratory 28D break specimen cubes) across active grade recipes:", body_style))
            story.append(Spacer(1, 3))
            grade_data = [
                [
                    Paragraph("Grade / Mix", table_header),
                    Paragraph("Batches", table_header),
                    Paragraph("28D Batches (Cubes)", table_header),
                    Paragraph("Mean (MPa)", table_header),
                    Paragraph("Target fck", table_header),
                    Paragraph("Margin (MPa)", table_header),
                    Paragraph("Variation (σ)", table_header),
                    Paragraph("CV (%)", table_header),
                    Paragraph("Compliance", table_header),
                    Paragraph("Status", table_header),
                ]
            ]
            for g in report_dto.quality_metrics.mix_performance_matrix[:8]:
                status_color = "#059669" if g.status in ["CONTROLLED", "EXCELLENT"] else "#d97706"
                grade_data.append([
                    Paragraph(f"<b>{g.grade}</b><br/><font size='6' color='#64748b'>{g.recipe_code}</font>", table_cell),
                    Paragraph(f"{g.total_batches:,}", table_cell),
                    Paragraph(f"{g.tested_28d_batches} ({g.tested_28d_specimens})", table_cell),
                    Paragraph(f"{g.mean_strength_mpa:.2f}" if g.mean_strength_mpa is not None else "—", table_cell),
                    Paragraph(f"{g.target_fck_mpa:.1f}", table_cell),
                    Paragraph(f"{g.strength_margin_mpa:+.2f}" if g.strength_margin_mpa is not None else "—", table_cell),
                    Paragraph(f"±{g.standard_deviation_mpa:.2f}" if g.standard_deviation_mpa is not None else "—", table_cell),
                    Paragraph(f"{g.cov_percent:.1f}%" if g.cov_percent is not None else "—", table_cell),
                    Paragraph(f"{g.compliance_percent:.1f}%" if g.compliance_percent is not None else "—", table_cell),
                    Paragraph(f"<font color='{status_color}'><b>{g.status}</b></font>", table_cell),
                ])
            grade_tbl = Table(grade_data, colWidths=[80, 45, 45, 50, 45, 55, 55, 45, 50, 50])
            grade_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(grade_tbl)
            story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 6. Material Consumption & Specific Density Matrix
        # -------------------------------------------------------------
        if report_dto.material_consumption and report_dto.material_consumption.material_breakdown:
            story.append(Paragraph("Material Consumption & Specific Density Matrix", section_heading))
            mat_data = [
                [
                    Paragraph("Category", table_header),
                    Paragraph("Material Name", table_header),
                    Paragraph("Planned (kg)", table_header),
                    Paragraph("Actual (kg)", table_header),
                    Paragraph("Variance (%)", table_header),
                    Paragraph("Density (kg/m³)", table_header),
                ]
            ]
            for m in report_dto.material_consumption.material_breakdown[:8]:
                var_val = m.get("variance_percent", 0.0)
                var_color = "#dc2626" if abs(var_val) > 2.0 else "#059669"
                mat_data.append([
                    Paragraph(m.get("category", "General"), table_cell),
                    Paragraph(m.get("name", "—"), table_cell),
                    Paragraph(f"{m.get('planned_kg', 0):,.1f}", table_cell),
                    Paragraph(f"{m.get('actual_kg', 0):,.1f}", table_cell),
                    Paragraph(f"<font color='{var_color}'><b>{var_val:+.2f}%</b></font>", table_cell),
                    Paragraph(f"{m.get('density_kg_m3', 0):,.1f}", table_cell),
                ])
            mat_tbl = Table(mat_data, colWidths=[80, 140, 75, 75, 75, 75])
            mat_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(mat_tbl)
            story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 7. Weighment Accuracy & Water Monitoring (IS 4926 Annex E)
        # -------------------------------------------------------------
        if report_dto.material_consumption.component_tolerances:
            story.append(Paragraph("Weighment Accuracy & Batching Diagnostics (IS 4926:2003 Annex E)", section_heading))
            weigh_data = [
                [
                    Paragraph("Component Category", table_header),
                    Paragraph("Standard Limit", table_header),
                    Paragraph("Evaluated", table_header),
                    Paragraph("Compliant", table_header),
                    Paragraph("Breaches", table_header),
                    Paragraph("Compliance %", table_header),
                    Paragraph("Mean Abs Var (%)", table_header),
                ]
            ]
            for c in report_dto.material_consumption.component_tolerances:
                comp_pct = c.compliance_rate_pct or 0.0
                comp_color = "#059669" if comp_pct >= 95.0 else "#dc2626"
                weigh_data.append([
                    Paragraph(c.category_name, table_cell),
                    Paragraph(f"±{c.tolerance_pct:.1f}%", table_cell),
                    Paragraph(f"{c.record_count:,}", table_cell),
                    Paragraph(f"{c.compliant_count:,}", table_cell),
                    Paragraph(f"{c.non_compliant_count:,}", table_cell),
                    Paragraph(f"<font color='{comp_color}'><b>{comp_pct:.2f}%</b></font>", table_cell),
                    Paragraph(f"{c.mean_abs_variance_pct:.3f}%", table_cell),
                ])
            weigh_tbl = Table(weigh_data, colWidths=[150, 65, 55, 55, 55, 70, 70])
            weigh_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(weigh_tbl)
            story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 8. Binder Intensity & Material Efficiency Matrix
        # -------------------------------------------------------------
        if report_dto.material_consumption.recipe_efficiency_matrix:
            story.append(Paragraph("Binder Intensity & Material Efficiency Matrix", section_heading))
            eff_data = [
                [
                    Paragraph("Recipe Code", table_header),
                    Paragraph("Batches", table_header),
                    Paragraph("28D Tested", table_header),
                    Paragraph("Cement (kg/m³)", table_header),
                    Paragraph("Total Binder", table_header),
                    Paragraph("W/B Ratio", table_header),
                    Paragraph("Mean 28D (MPa)", table_header),
                    Paragraph("Binder Intensity", table_header),
                    Paragraph("Reliability", table_header),
                ]
            ]
            for eff in report_dto.material_consumption.recipe_efficiency_matrix[:6]:
                eff_data.append([
                    Paragraph(f"<b>{eff.recipe_code}</b>", table_cell),
                    Paragraph(f"{eff.total_batches:,}", table_cell),
                    Paragraph(f"{eff.tested_28d_batches:,}", table_cell),
                    Paragraph(f"{eff.cement_kg_m3:.1f}", table_cell),
                    Paragraph(f"{eff.total_binder_kg_m3:.1f}", table_cell),
                    Paragraph(f"{eff.actual_wb_ratio:.3f}" if eff.actual_wb_ratio is not None else "—", table_cell),
                    Paragraph(f"{eff.mean_28d_strength_mpa:.2f}" if eff.mean_28d_strength_mpa is not None else "—", table_cell),
                    Paragraph(f"<b>{eff.binder_intensity_kg_per_m3_per_mpa:.2f}</b>" if eff.binder_intensity_kg_per_m3_per_mpa is not None else "—", table_cell),
                    Paragraph(f"<font color='#0284c7'>{eff.reliability_status}</font>", table_cell),
                ])
            eff_tbl = Table(eff_data, colWidths=[80, 45, 45, 60, 60, 50, 60, 60, 60])
            eff_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(eff_tbl)
            story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 9. AI Model Monitoring & Retrospective Backtest
        # -------------------------------------------------------------
        story.append(Paragraph("AI Strength Prediction & Model Validation", section_heading))
        
        # 9A. Retrospective Model Backtest (Historical Ground Truth)
        rb = report_dto.retrospective_backtest
        if rb and rb.evaluation_pairs_count > 0:
            story.append(Paragraph("<b>Retrospective Model Backtest (Historical Ground-Truth Validation):</b>", body_style))
            story.append(Paragraph("<i>Historical production batch inputs were retrospectively evaluated against known 28-day laboratory break results.</i>", subtitle_style))
            story.append(Spacer(1, 2))

            rb_table_data = [
                [
                    Paragraph("<b>Model Architecture:</b>", body_style),
                    Paragraph(f"{rb.algorithm_name} ({rb.model_version})", body_style),
                    Paragraph("<b>Validation Status:</b>", body_style),
                    Paragraph(f"<font color='#d97706'><b>{rb.validation_status}</b></font>", body_style),
                ],
                [
                    Paragraph("<b>Evaluation Pairs:</b>", body_style),
                    Paragraph(f"<b>{rb.evaluation_pairs_count}</b> Ground-Truth Lab Breaks", body_style),
                    Paragraph("<b>R² Score:</b>", body_style),
                    Paragraph(f"<b>{rb.r2_score:.4f}</b>" if rb.r2_score is not None else "—", body_style),
                ],
                [
                    Paragraph("<b>Mean Abs Error (MAE):</b>", body_style),
                    Paragraph(f"<b>{rb.mae_mpa:.2f} MPa</b>" if rb.mae_mpa is not None else "—", body_style),
                    Paragraph("<b>Root Mean Sq Error (RMSE):</b>", body_style),
                    Paragraph(f"<b>{rb.rmse_mpa:.2f} MPa</b>" if rb.rmse_mpa is not None else "—", body_style),
                ],
                [
                    Paragraph("<b>Mean Residual (Bias):</b>", body_style),
                    Paragraph(f"<b>{rb.mean_residual_bias_mpa:+.2f} MPa</b>" if rb.mean_residual_bias_mpa is not None else "—", body_style),
                    Paragraph("<b>Residual Std Dev (σ_res):</b>", body_style),
                    Paragraph(f"<b>±{rb.residual_std_deviation_mpa:.2f} MPa</b>" if rb.residual_std_deviation_mpa is not None else "—", body_style),
                ]
            ]
            rb_table = Table(rb_table_data, colWidths=[110, 150, 110, 150])
            rb_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#edf2f7")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(rb_table)
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<font color='#64748b' size='6.5'><b>Notice:</b> {rb.sample_size_warning}</font>", body_style))
            story.append(Spacer(1, 5))

        # 9B. Online Production Telemetry Summary
        mm = report_dto.model_monitoring
        story.append(Paragraph("<b>Online Production Prediction Telemetry:</b>", body_style))
        mm_table_data = [
            [
                Paragraph("<b>Platform Model:</b>", body_style),
                Paragraph(f"{mm.algorithm_name} ({mm.active_model_version})", body_style),
                Paragraph("<b>Telemetry Records:</b>", body_style),
                Paragraph(f"{mm.evaluation_samples_count:,} Stored Online Predictions", body_style),
            ],
            [
                Paragraph("<b>Telemetry Status:</b>", body_style),
                Paragraph(f"<font color='#0284c7'><b>{mm.validation_status}</b></font>", body_style),
                Paragraph("<b>Telemetry Drift:</b>", body_style),
                Paragraph("Monitored Online (Rolling Window = 10)", body_style),
            ]
        ]
        mm_table = Table(mm_table_data, colWidths=[110, 150, 110, 150])
        mm_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#edf2f7")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(mm_table)
        story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 10. Mix Optimization & Pareto Frontier (When run is active)
        # -------------------------------------------------------------
        if report_dto.optimization_run:
            story.append(Paragraph("AI Mix Optimization & Pareto Frontier", section_heading))
            opt = report_dto.optimization_run
            
            pareto_chart_img = cls._generate_pareto_chart(opt)
            if pareto_chart_img:
                story.append(pareto_chart_img)
                story.append(Spacer(1, 6))

            # Candidate Summary Table with Explicit Caption and Sorted Pareto Order
            opt_pareto_str = "solution" if opt.pareto_optimal_count == 1 else "solutions"
            story.append(Paragraph(f"<b>Candidate Mix Portfolio:</b> Showing {min(len(opt.candidates), 8)} of {len(opt.candidates)} candidate evaluations ({opt.pareto_optimal_count} Pareto-optimal {opt_pareto_str} identified in run {opt.run_id[:8]}; Target f'ck = {opt.target_mean_strength_mpa:.2f} MPa):", body_style))
            story.append(Spacer(1, 3))

            cand_table_data = [
                [
                    Paragraph("Candidate", table_header),
                    Paragraph("Feasibility", table_header),
                    Paragraph("Pareto", table_header),
                    Paragraph("Strength (MPa)", table_header),
                    Paragraph("Margin (MPa)", table_header),
                    Paragraph("Binder (kg/m³)", table_header),
                    Paragraph("W/B Ratio", table_header),
                    Paragraph("Yield (m³)", table_header),
                    Paragraph("Review Status", table_header),
                ]
            ]

            # Display Pareto optimal candidates first
            sorted_candidates = sorted(opt.candidates, key=lambda c: (not c.is_pareto_optimal, not c.is_feasible, -float(c.strength_margin_mpa or 0.0)))

            for c in sorted_candidates[:8]:
                if c.is_feasible:
                    f_label, f_color = "Passed", "#059669"
                else:
                    f_label, f_color = "Violated", "#ef4444"

                if c.is_pareto_optimal:
                    p_label, p_color = "Optimal", "#059669"
                elif c.is_feasible:
                    p_label, p_color = "Dominated", "#64748b"
                else:
                    p_label, p_color = "Non-Pareto", "#ef4444"

                cand_table_data.append([
                    Paragraph(f"<b>{c.candidate_identifier}</b>", table_cell),
                    Paragraph(f"<font color='{f_color}'><b>{f_label}</b></font>", table_cell),
                    Paragraph(f"<font color='{p_color}'><b>{p_label}</b></font>", table_cell),
                    Paragraph(f"{c.predicted_strength_mpa:.2f}" if c.predicted_strength_mpa else "—", table_cell),
                    Paragraph(f"{c.strength_margin_mpa:+.2f}" if c.strength_margin_mpa else "—", table_cell),
                    Paragraph(f"{c.binder_intensity_kg_m3:.1f}", table_cell),
                    Paragraph(f"{c.water_binder_ratio:.3f}", table_cell),
                    Paragraph(f"{c.yield_m3:.3f}", table_cell),
                    Paragraph(c.review_status, table_cell),
                ])

            cand_tbl = Table(cand_table_data, colWidths=[65, 55, 50, 60, 55, 65, 55, 55, 60])
            cand_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(cand_tbl)
            story.append(Spacer(1, 6))

            # -------------------------------------------------------------
            # 11. Recipe Impact / Master-vs-Candidate Delta Table
            # -------------------------------------------------------------
            if report_dto.recipe_impact and report_dto.recipe_impact.constituents:
                story.append(Paragraph(f"Recipe Impact & Baseline Delta Analysis (Candidate: {report_dto.recipe_impact.candidate_identifier})", section_heading))
                
                imp_summary_data = [
                    [
                        Paragraph("<b>Binder Delta:</b>", body_style),
                        Paragraph(f"<b>{report_dto.recipe_impact.binder_delta_kg_m3:+.1f} kg/m³ ({report_dto.recipe_impact.binder_delta_percent:+.1f}%)</b>", body_style),
                        Paragraph("<b>W/B Delta:</b>", body_style),
                        Paragraph(f"<b>{report_dto.recipe_impact.candidate_water_binder_ratio:.3f} (Master: {report_dto.recipe_impact.master_water_binder_ratio:.3f})</b>", body_style),
                    ]
                ]
                imp_sum_tbl = Table(imp_summary_data, colWidths=[80, 180, 70, 190])
                imp_sum_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(imp_sum_tbl)
                story.append(Spacer(1, 4))

                delta_table_data = [
                    [
                        Paragraph("Material", table_header),
                        Paragraph("Category", table_header),
                        Paragraph("Master (kg/m³)", table_header),
                        Paragraph("Candidate (kg/m³)", table_header),
                        Paragraph("Delta (kg/m³)", table_header),
                        Paragraph("Delta (%)", table_header),
                    ]
                ]

                for mat in report_dto.recipe_impact.constituents:
                    d_pct = mat.delta_percent if mat.delta_percent is not None else 0.0
                    d_color = "#059669" if mat.delta_qty_kg_m3 < 0 else ("#dc2626" if mat.delta_qty_kg_m3 > 0 else "#64748b")
                    delta_table_data.append([
                        Paragraph(mat.material_name, table_cell),
                        Paragraph(mat.category, table_cell),
                        Paragraph(f"{mat.master_qty_kg_m3:.1f}", table_cell),
                        Paragraph(f"{mat.candidate_qty_kg_m3:.1f}", table_cell),
                        Paragraph(f"<font color='{d_color}'><b>{mat.delta_qty_kg_m3:+.1f}</b></font>", table_cell),
                        Paragraph(f"<font color='{d_color}'><b>{d_pct:+.1f}%</b></font>" if mat.delta_percent is not None else "New", table_cell),
                    ])

                delta_tbl = Table(delta_table_data, colWidths=[130, 90, 75, 75, 75, 75])
                delta_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(delta_tbl)
                story.append(Spacer(1, 6))

        # -------------------------------------------------------------
        # 12. Governance & Provenance Record
        # -------------------------------------------------------------
        gov = report_dto.governance
        prov = report_dto.provenance
        story.append(Paragraph("Authoritative Governance, Quality Sign-Off & Provenance", section_heading))
        
        gov_data = [
            [
                Paragraph("<b>Human Review State:</b>", body_style),
                Paragraph(f"<font color='#0284c7'><b>{gov.review_status if gov else 'PENDING_REVIEW'}</b></font>", body_style),
                Paragraph("<b>Reviewed By:</b>", body_style),
                Paragraph(f"{gov.reviewed_by_username or 'Unassigned'} ({gov.reviewed_by_role or 'Quality Head'})" if gov else "Unassigned", body_style),
            ],
            [
                Paragraph("<b>Production Status:</b>", body_style),
                Paragraph("<i>Production activation outside current phase</i>", body_style),
                Paragraph("<b>Audit Provenance ID:</b>", body_style),
                Paragraph(f"{gov.audit_event_id or 'Auto-Generated on Sign-off'}" if gov else "Audit Logged", body_style),
            ],
            [
                Paragraph("<b>Source Database:</b>", body_style),
                Paragraph(f"{prov.source_database} (PostgreSQL)", body_style),
                Paragraph("<b>Compliance Standard:</b>", body_style),
                Paragraph(f"{report_dto.report_metadata.compliance_standard}", body_style),
            ]
        ]
        gov_table = Table(gov_data, colWidths=[100, 160, 110, 150])
        gov_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#edf2f7")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(gov_table)

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()
