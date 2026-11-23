"""Dataset Lineage, Fingerprinting & Resource Pre-Flight Guard Services.

Provides:
- DatasetFingerprintService: Computes deterministic SHA-256 signatures over batch IDs and features.
- TrainingResourceGuardService: Non-technical pre-flight memory and resource safety evaluation.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from src.ml.training.contracts import MLBatchObservation


@dataclass
class DatasetLineageDescriptor:
    """Immutable audit record linking training runs to source data."""
    dataset_fingerprint: str
    observation_count: int
    batch_ids: List[str]
    plant_codes: List[str]
    recipe_codes: List[str]
    feature_schema_version: str = "1.0.0"


@dataclass
class ResourcePreflightReport:
    """Pre-flight resource availability verdict before initiating training."""
    allowed: bool
    total_ram_mb: float
    available_ram_mb: float
    estimated_training_ram_mb: float
    safety_headroom_mb: float
    swap_total_mb: float
    swap_free_mb: float
    cpu_count: int
    reason: str


def _read_meminfo() -> Dict[str, float]:
    """Read total, available, free memory and swap in MB from Linux /proc/meminfo or system defaults."""
    res = {
        "MemTotal": 2048.0,
        "MemAvailable": 1024.0,
        "MemFree": 1024.0,
        "SwapTotal": 0.0,
        "SwapFree": 0.0,
    }

    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip().split()[0]
                    if k in res:
                        res[k] = round(float(v) / 1024.0, 2)  # kB to MB

            if "MemAvailable" not in res or res["MemAvailable"] == 0.0:
                res["MemAvailable"] = res.get("MemFree", 512.0)
        except Exception:
            pass

    return res


class DatasetFingerprintService:
    """Generates immutable cryptographic fingerprints for dataset lineage."""

    @staticmethod
    def generate_lineage_descriptor(
        observations: List[MLBatchObservation],
        feature_schema_version: str = "1.0.0",
    ) -> DatasetLineageDescriptor:
        """Compute deterministic SHA-256 fingerprint over batch IDs and feature hashes."""
        sorted_obs = sorted(observations, key=lambda o: o.batch_id)
        batch_ids = [o.batch_id for o in sorted_obs]
        plants = sorted(list(set(o.plant_code for o in sorted_obs)))
        recipes = sorted(list(set(o.recipe_code for o in sorted_obs)))

        canonical_representation = [
            {
                "id": o.batch_id,
                "num": o.batch_number,
                "plant": o.plant_code,
                "recipe": o.recipe_code,
                "binder": o.total_binder_kg_m3,
                "wb": o.water_binder_ratio,
                "target": o.target_28d_strength_mpa,
            }
            for o in sorted_obs
        ]

        raw_bytes = json.dumps(canonical_representation, sort_keys=True).encode("utf-8")
        fingerprint = hashlib.sha256(raw_bytes).hexdigest()

        return DatasetLineageDescriptor(
            dataset_fingerprint=fingerprint,
            observation_count=len(sorted_obs),
            batch_ids=batch_ids,
            plant_codes=plants,
            recipe_codes=recipes,
            feature_schema_version=feature_schema_version,
        )


class TrainingResourceGuardService:
    """Safely assesses host memory headroom before initiating model training."""

    @staticmethod
    def evaluate_preflight(
        observation_count: int,
        estimated_training_ram_mb: float = 250.0,
        required_safety_headroom_mb: float = 350.0,
    ) -> ResourcePreflightReport:
        """Evaluate if server has sufficient available RAM to train without triggering OOM."""
        mem = _read_meminfo()
        total_mb = mem["MemTotal"]
        avail_mb = mem["MemAvailable"]
        swap_total = mem["SwapTotal"]
        swap_free = mem["SwapFree"]

        # Scale estimated memory with dataset size (baseline + dynamic)
        dynamic_req_mb = estimated_training_ram_mb + (observation_count * 0.05)
        total_needed_mb = dynamic_req_mb + required_safety_headroom_mb

        if avail_mb < total_needed_mb:
            msg = (
                f"Host available memory ({avail_mb:.1f} MB) is below safe pre-flight budget "
                f"({total_needed_mb:.1f} MB = {dynamic_req_mb:.1f} MB training + {required_safety_headroom_mb:.1f} MB headroom). "
                f"Training refused to protect production server stability."
            )
            return ResourcePreflightReport(
                allowed=False,
                total_ram_mb=total_mb,
                available_ram_mb=avail_mb,
                estimated_training_ram_mb=round(dynamic_req_mb, 2),
                safety_headroom_mb=required_safety_headroom_mb,
                swap_total_mb=swap_total,
                swap_free_mb=swap_free,
                cpu_count=os.cpu_count() or 1,
                reason=msg,
            )

        return ResourcePreflightReport(
            allowed=True,
            total_ram_mb=total_mb,
            available_ram_mb=avail_mb,
            estimated_training_ram_mb=round(dynamic_req_mb, 2),
            safety_headroom_mb=required_safety_headroom_mb,
            swap_total_mb=swap_total,
            swap_free_mb=swap_free,
            cpu_count=os.cpu_count() or 1,
            reason="Server resources satisfy safe training pre-flight requirements.",
        )
