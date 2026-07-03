# Schemas

The typed contracts every pipeline stage speaks. See docs/wiki/mental-model.md for how data flows through them.

<!-- AUTO-GENERATED:START -->
## Schema reference (auto-generated from `app/schemas/models.py`)

### BOM

| Field | Type | Notes |
|---|---|---|
| `design_id` | `<class 'str'>` |  |
| `items` | `list[app.schemas.models.BOMItem]` |  |
| `total_cost_usd` | `<class 'float'>` |  |
| `currency` | `<class 'str'>` |  |
| `pricing_disclaimer` | `<class 'str'>` |  |

### ArchitectureSpec

System architecture: the engineering decisions before any geometry.

| Field | Type | Notes |
|---|---|---|
| `drivetrain` | `<class 'str'>` | e.g. 'differential drive, 4 driven wheels' |
| `wheel_count` | `<class 'int'>` |  |
| `wheel_diameter_mm` | `<class 'float'>` |  |
| `chassis_topology` | `<class 'str'>` | e.g. 'single plate with bays and mast' |
| `chassis_material` | `<class 'str'>` |  |
| `chassis_material_density_kg_m3` | `<class 'float'>` |  |
| `chassis_material_yield_mpa` | `<class 'float'>` |  |
| `motor` | `<class 'app.schemas.models.MotorSpec'>` |  |
| `battery` | `<class 'app.schemas.models.BatterySpec'>` |  |
| `sensor_placement` | `dict[str, str]` | sensor name -> mounting location description |
| `electronics_avg_draw_w` | `<class 'float'>` |  |
| `rationale` | `list[str]` | Why these choices were made |

### ArtifactManifest

| Field | Type | Notes |
|---|---|---|
| `design_id` | `<class 'str'>` |  |
| `created_at` | `<class 'datetime.datetime'>` |  |
| `prompt` | `<class 'str'>` |  |
| `artifacts` | `list[app.schemas.models.ArtifactRef]` |  |
| `pipeline_version` | `<class 'str'>` |  |
| `notes` | `list[str]` |  |

### ArtifactRef

| Field | Type | Notes |
|---|---|---|
| `name` | `<class 'str'>` |  |
| `path` | `<class 'str'>` |  |
| `kind` | `<class 'str'>` | json | stl | step | csv | md |
| `description` | `<class 'str'>` |  |

### BatterySpec

| Field | Type | Notes |
|---|---|---|
| `chemistry` | `<class 'str'>` | e.g. 'LiFePO4' |
| `nominal_voltage_v` | `<class 'float'>` |  |
| `capacity_wh` | `<class 'float'>` |  |
| `usable_fraction` | `<class 'float'>` |  |
| `mass_kg` | `<class 'float'>` |  |

### BOMItem

| Field | Type | Notes |
|---|---|---|
| `part_number` | `<class 'str'>` |  |
| `name` | `<class 'str'>` |  |
| `category` | `<class 'str'>` |  |
| `quantity` | `<class 'int'>` |  |
| `unit_cost_usd` | `<class 'float'>` |  |
| `total_cost_usd` | `<class 'float'>` |  |
| `supplier` | `<class 'str'>` | Placeholder until sourcing integration |
| `notes` | `<class 'str'>` |  |

### CADParams

Parameters consumed by the parametric CadQuery chassis template.

| Field | Type | Notes |
|---|---|---|
| `chassis_length_mm` | `<class 'float'>` |  |
| `chassis_width_mm` | `<class 'float'>` |  |
| `chassis_thickness_mm` | `<class 'float'>` |  |
| `corner_radius_mm` | `<class 'float'>` |  |
| `wheel_diameter_mm` | `<class 'float'>` |  |
| `wheel_width_mm` | `<class 'float'>` |  |
| `wheelbase_mm` | `<class 'float'>` | Front-rear axle distance |
| `track_width_mm` | `<class 'float'>` | Left-right wheel center distance |
| `mast_height_mm` | `<class 'float'>` |  |
| `mast_diameter_mm` | `<class 'float'>` |  |
| `battery_bay_mm` | `tuple[float, float, float]` | (L, W, H) of battery bay |
| `electronics_bay_mm` | `tuple[float, float, float]` |  |
| `mounting_hole_diameter_mm` | `<class 'float'>` |  |
| `template` | `<class 'str'>` |  |

### CheckResult

| Field | Type | Notes |
|---|---|---|
| `name` | `<class 'str'>` |  |
| `value` | `<class 'float'>` |  |
| `unit` | `<class 'str'>` |  |
| `threshold` | `<class 'float'>` |  |
| `passed` | `<class 'bool'>` |  |
| `formula` | `<class 'str'>` | The actual formula used — no black boxes |
| `assumptions` | `list[str]` |  |

### EngineeringAssumption

A single explicit assumption made while filling a gap in the prompt.

| Field | Type | Notes |
|---|---|---|
| `field` | `<class 'str'>` | Which requirement/parameter this assumption covers |
| `assumed_value` | `<class 'str'>` |  |
| `rationale` | `<class 'str'>` |  |
| `confidence` | `<class 'str'>` | low | medium | high |

### EngineeringReportState

The full pipeline state — everything the report generator needs.

| Field | Type | Notes |
|---|---|---|
| `design_id` | `<class 'str'>` |  |
| `prompt` | `<class 'str'>` |  |
| `mode` | `<class 'str'>` | template | generative |
| `requirements` | `app.schemas.models.Requirements | None` |  |
| `architecture` | `app.schemas.models.ArchitectureSpec | None` |  |
| `cad_params` | `app.schemas.models.CADParams | None` |  |
| `geometry` | `app.schemas.models.GeometryMetrics | None` |  |
| `geometry_checks` | `app.schemas.models.GeometryCheckReport | None` |  |
| `cad_export_note` | `<class 'str'>` |  |
| `simulation` | `app.schemas.models.SimulationResults | None` |  |
| `risk_report` | `app.schemas.models.RiskReport | None` |  |
| `bom` | `app.schemas.models.BOM | None` |  |
| `manifest` | `app.schemas.models.ArtifactManifest | None` |  |

### GeometryCheckReport

Check results + iteration history for a generative-mode design.

| Field | Type | Notes |
|---|---|---|
| `design_id` | `<class 'str'>` |  |
| `checks` | `list[app.schemas.models.CheckResult]` |  |
| `all_passed` | `<class 'bool'>` |  |
| `iterations` | `list[str]` | Human-readable log of each optimization iteration |
| `optimization_note` | `<class 'str'>` |  |
| `limitations` | `list[str]` |  |

### GeometryMetrics

Measured properties of generatively-built geometry (generic mode).

| Field | Type | Notes |
|---|---|---|
| `volume_mm3` | `<class 'float'>` |  |
| `bbox_mm` | `tuple[float, float, float]` |  |
| `is_valid_solid` | `<class 'bool'>` |  |
| `material` | `<class 'str'>` |  |
| `density_kg_m3` | `<class 'float'>` |  |
| `est_mass_kg` | `<class 'float'>` |  |
| `est_material_cost_usd` | `<class 'float'>` |  |
| `fits_envelope` | `<class 'bool'>` |  |
| `fits_print_bed` | `<class 'bool'>` | Fits a 256 mm cube consumer printer bed |
| `generation_attempts` | `<class 'int'>` |  |
| `notes` | `list[str]` |  |

### MotorSpec

| Field | Type | Notes |
|---|---|---|
| `motor_class` | `<class 'str'>` | e.g. 'brushed DC gearmotor 12V' |
| `count` | `<class 'int'>` |  |
| `rated_torque_nm` | `<class 'float'>` |  |
| `stall_torque_nm` | `<class 'float'>` |  |
| `rated_power_w` | `<class 'float'>` |  |
| `mass_kg` | `<class 'float'>` | Mass per motor incl. gearbox |

### Requirements

Structured engineering requirements extracted from the user prompt.

| Field | Type | Notes |
|---|---|---|
| `prompt` | `<class 'str'>` |  |
| `payload_kg` | `<class 'float'>` |  |
| `runtime_hr` | `<class 'float'>` |  |
| `max_dimensions_mm` | `tuple[float, float, float]` | (length, width, height) envelope limit |
| `environment` | `<enum 'EnvironmentType'>` |  |
| `max_cost_usd` | `<class 'float'>` |  |
| `locomotion_type` | `<enum 'LocomotionType'>` |  |
| `sensors_required` | `list[str]` |  |
| `max_speed_m_s` | `<class 'float'>` |  |
| `max_ramp_deg` | `<class 'float'>` |  |
| `assumptions` | `list[app.schemas.models.EngineeringAssumption]` |  |
| `unknowns` | `list[str]` | Open questions a human should confirm |

### RiskItem

| Field | Type | Notes |
|---|---|---|
| `id` | `<class 'str'>` |  |
| `title` | `<class 'str'>` |  |
| `severity` | `<enum 'RiskSeverity'>` |  |
| `description` | `<class 'str'>` |  |
| `mitigation` | `<class 'str'>` |  |

### RiskReport

| Field | Type | Notes |
|---|---|---|
| `design_id` | `<class 'str'>` |  |
| `items` | `list[app.schemas.models.RiskItem]` |  |
| `overall_assessment` | `<class 'str'>` |  |
| `generated_by` | `<class 'str'>` |  |

### SimulationInput

Everything the deterministic check suite needs, in one place.

| Field | Type | Notes |
|---|---|---|
| `requirements` | `<class 'app.schemas.models.Requirements'>` |  |
| `architecture` | `<class 'app.schemas.models.ArchitectureSpec'>` |  |
| `cad_params` | `<class 'app.schemas.models.CADParams'>` |  |
| `chassis_mass_kg` | `<class 'float'>` | From CAD solid volume x density |

### SimulationResults

Results of deterministic engineering checks. NOT FEA. NOT certified.

| Field | Type | Notes |
|---|---|---|
| `total_mass_kg` | `<class 'float'>` |  |
| `loaded_mass_kg` | `<class 'float'>` | Total mass including payload |
| `avg_power_draw_w` | `<class 'float'>` |  |
| `estimated_runtime_hr` | `<class 'float'>` |  |
| `runtime_margin` | `<class 'float'>` | estimated_runtime / required_runtime |
| `required_wheel_torque_nm` | `<class 'float'>` |  |
| `torque_margin` | `<class 'float'>` | rated motor torque / required torque per wheel |
| `payload_margin` | `<class 'float'>` |  |
| `cog_height_mm` | `<class 'float'>` |  |
| `tip_angle_lateral_deg` | `<class 'float'>` |  |
| `tip_angle_longitudinal_deg` | `<class 'float'>` |  |
| `chassis_bending_stress_mpa` | `<class 'float'>` |  |
| `chassis_safety_factor` | `<class 'float'>` |  |
| `checks` | `list[app.schemas.models.CheckResult]` |  |
| `limitations` | `list[str]` | Honest statement of what these numbers are and are not |
<!-- AUTO-GENERATED:END -->
