"""Core Pydantic schemas — the data contracts of the whole pipeline.

Every pipeline stage consumes and produces these models. If you change a
schema, run `make wiki` (regenerates docs/wiki/schemas.md) and `make test`.

Units convention: SI-ish with explicit suffixes — kg, mm, hr, W, Wh, Nm, USD.
Never pass a bare float whose unit is ambiguous.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Requirements
# --------------------------------------------------------------------------

class EnvironmentType(StrEnum):
    indoor_industrial = "indoor_industrial"
    indoor_office = "indoor_office"
    outdoor = "outdoor"
    mixed = "mixed"


class LocomotionType(StrEnum):
    wheeled_4 = "wheeled_4"
    wheeled_2_caster = "wheeled_2_caster"
    tracked = "tracked"
    legged = "legged"  # out of MVP scope; documented for schema stability


class EngineeringAssumption(BaseModel):
    """A single explicit assumption made while filling a gap in the prompt."""

    field: str = Field(description="Which requirement/parameter this assumption covers")
    assumed_value: str
    rationale: str
    confidence: str = Field(default="medium", description="low | medium | high")


class Requirements(BaseModel):
    """Structured engineering requirements extracted from the user prompt."""

    prompt: str
    payload_kg: float = Field(gt=0)
    runtime_hr: float = Field(gt=0)
    max_dimensions_mm: tuple[float, float, float] = Field(
        description="(length, width, height) envelope limit"
    )
    environment: EnvironmentType
    max_cost_usd: float = Field(gt=0)
    locomotion_type: LocomotionType
    sensors_required: list[str]
    max_speed_m_s: float = Field(default=1.0, gt=0)
    max_ramp_deg: float = Field(default=8.0, ge=0)
    assumptions: list[EngineeringAssumption] = []
    unknowns: list[str] = Field(default=[], description="Open questions a human should confirm")


# --------------------------------------------------------------------------
# Architecture
# --------------------------------------------------------------------------

class MotorSpec(BaseModel):
    motor_class: str = Field(description="e.g. 'brushed DC gearmotor 12V'")
    count: int = Field(gt=0)
    rated_torque_nm: float = Field(gt=0)
    stall_torque_nm: float = Field(gt=0)
    rated_power_w: float = Field(gt=0)
    mass_kg: float = Field(gt=0, description="Mass per motor incl. gearbox")


class BatterySpec(BaseModel):
    chemistry: str = Field(description="e.g. 'LiFePO4'")
    nominal_voltage_v: float = Field(gt=0)
    capacity_wh: float = Field(gt=0)
    usable_fraction: float = Field(default=0.9, gt=0, le=1.0)
    mass_kg: float = Field(gt=0)


class ArchitectureSpec(BaseModel):
    """System architecture: the engineering decisions before any geometry."""

    drivetrain: str = Field(description="e.g. 'differential drive, 4 driven wheels'")
    wheel_count: int
    wheel_diameter_mm: float = Field(gt=0)
    chassis_topology: str = Field(description="e.g. 'single plate with bays and mast'")
    chassis_material: str
    chassis_material_density_kg_m3: float = Field(gt=0)
    chassis_material_yield_mpa: float = Field(gt=0)
    motor: MotorSpec
    battery: BatterySpec
    sensor_placement: dict[str, str] = Field(
        description="sensor name -> mounting location description"
    )
    electronics_avg_draw_w: float = Field(gt=0)
    rationale: list[str] = Field(default=[], description="Why these choices were made")


# --------------------------------------------------------------------------
# CAD
# --------------------------------------------------------------------------

class CADParams(BaseModel):
    """Parameters consumed by the parametric CadQuery chassis template.

    All dimensions in mm. Hard bounds enforced here so an out-of-range
    parameter set is rejected BEFORE the CAD kernel runs (risk R1).
    """

    chassis_length_mm: float = Field(ge=150, le=1200)
    chassis_width_mm: float = Field(ge=100, le=900)
    chassis_thickness_mm: float = Field(ge=3, le=25)
    corner_radius_mm: float = Field(default=15, ge=0, le=60)
    wheel_diameter_mm: float = Field(ge=40, le=400)
    wheel_width_mm: float = Field(ge=10, le=100)
    wheelbase_mm: float = Field(ge=100, le=1000, description="Front-rear axle distance")
    track_width_mm: float = Field(ge=80, le=900, description="Left-right wheel center distance")
    mast_height_mm: float = Field(ge=0, le=1500)
    mast_diameter_mm: float = Field(ge=10, le=100)
    battery_bay_mm: tuple[float, float, float] = Field(description="(L, W, H) of battery bay")
    electronics_bay_mm: tuple[float, float, float]
    mounting_hole_diameter_mm: float = Field(default=4.5, ge=2, le=12)
    template: str = Field(default="mobile_robot_base_v1")


class GeometryMetrics(BaseModel):
    """Measured properties of generatively-built geometry (generic mode)."""

    volume_mm3: float
    bbox_mm: tuple[float, float, float]
    is_valid_solid: bool
    material: str = "PLA (assumed default)"
    density_kg_m3: float = 1240.0
    est_mass_kg: float
    est_material_cost_usd: float
    fits_envelope: bool
    fits_print_bed: bool = Field(description="Fits a 256 mm cube consumer printer bed")
    generation_attempts: int = 1
    notes: list[str] = []


# --------------------------------------------------------------------------
# Simulation / engineering checks
# --------------------------------------------------------------------------

class SimulationInput(BaseModel):
    """Everything the deterministic check suite needs, in one place."""

    requirements: Requirements
    architecture: ArchitectureSpec
    cad_params: CADParams
    chassis_mass_kg: float = Field(gt=0, description="From CAD solid volume x density")


class CheckResult(BaseModel):
    name: str
    value: float
    unit: str
    threshold: float
    passed: bool
    formula: str = Field(description="The actual formula used — no black boxes")
    assumptions: list[str] = []


class GeometryCheckReport(BaseModel):
    """Check results + iteration history for a generative-mode design."""

    design_id: str
    checks: list[CheckResult]
    all_passed: bool
    iterations: list[str] = Field(
        description="Human-readable log of each optimization iteration")
    optimization_note: str
    limitations: list[str]


class SimulationResults(BaseModel):
    """Results of deterministic engineering checks. NOT FEA. NOT certified."""

    total_mass_kg: float
    loaded_mass_kg: float = Field(description="Total mass including payload")
    avg_power_draw_w: float
    estimated_runtime_hr: float
    runtime_margin: float = Field(description="estimated_runtime / required_runtime")
    required_wheel_torque_nm: float
    torque_margin: float = Field(description="rated motor torque / required torque per wheel")
    payload_margin: float
    cog_height_mm: float
    tip_angle_lateral_deg: float
    tip_angle_longitudinal_deg: float
    chassis_bending_stress_mpa: float
    chassis_safety_factor: float
    checks: list[CheckResult]
    limitations: list[str] = Field(
        description="Honest statement of what these numbers are and are not"
    )


# --------------------------------------------------------------------------
# Risk
# --------------------------------------------------------------------------

class RiskSeverity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskItem(BaseModel):
    id: str
    title: str
    severity: RiskSeverity
    description: str
    mitigation: str


class RiskReport(BaseModel):
    design_id: str
    items: list[RiskItem]
    overall_assessment: str
    generated_by: str = Field(default="deterministic-rules-v1")


# --------------------------------------------------------------------------
# BOM
# --------------------------------------------------------------------------

class BOMItem(BaseModel):
    part_number: str
    name: str
    category: str
    quantity: int = Field(gt=0)
    unit_cost_usd: float = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    supplier: str = Field(default="TBD", description="Placeholder until sourcing integration")
    notes: str = ""


class BOM(BaseModel):
    design_id: str
    items: list[BOMItem]
    total_cost_usd: float
    currency: str = "USD"
    pricing_disclaimer: str = (
        "Prices are curated estimates for budgeting only, not live supplier quotes."
    )


# --------------------------------------------------------------------------
# Pipeline state & artifacts
# --------------------------------------------------------------------------

class ArtifactRef(BaseModel):
    name: str
    path: str
    kind: str = Field(description="json | stl | step | csv | md")
    description: str = ""


class ArtifactManifest(BaseModel):
    design_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prompt: str
    artifacts: list[ArtifactRef]
    pipeline_version: str = "deterministic-mvp-0.1"
    notes: list[str] = []


class EngineeringReportState(BaseModel):
    """The full pipeline state — everything the report generator needs.

    This is also the shared state object a future LangGraph graph will pass
    between agent nodes; keep it serializable.
    """

    design_id: str
    prompt: str
    mode: str = Field(default="template", description="template | generative")
    requirements: Requirements | None = None
    architecture: ArchitectureSpec | None = None
    cad_params: CADParams | None = None
    geometry: GeometryMetrics | None = None
    geometry_checks: GeometryCheckReport | None = None
    cad_export_note: str = ""
    simulation: SimulationResults | None = None
    risk_report: RiskReport | None = None
    bom: BOM | None = None
    manifest: ArtifactManifest | None = None
