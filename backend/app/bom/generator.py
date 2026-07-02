"""BOM generation.

MVP: curated component classes with realistic budget-level unit prices.
Prices are estimates for planning, not live quotes — the BOM schema carries
that disclaimer. Future: Nexar/Octopart enrichment behind the
ALLOW_EXTERNAL_PART_SEARCH gate (see env-space).
"""

import csv
from pathlib import Path

from app.schemas import BOM, ArchitectureSpec, BOMItem, CADParams, Requirements


def generate_bom(
    design_id: str, req: Requirements, arch: ArchitectureSpec, cad: CADParams
) -> BOM:
    rows: list[tuple[str, str, str, int, float, str]] = [
        # (part_number, name, category, qty, unit_cost, notes)
        ("CHAS-AL-001", f"Chassis plate, Al 6061-T6, {cad.chassis_length_mm:.0f}x"
         f"{cad.chassis_width_mm:.0f}x{cad.chassis_thickness_mm:.0f} mm",
         "structure", 1, 45.00, "Waterjet or router cut per generated CAD"),
        ("MTR-DCG-024", arch.motor.motor_class, "drivetrain", arch.motor.count, 28.00,
         f"Rated {arch.motor.rated_torque_nm} Nm / stall {arch.motor.stall_torque_nm} Nm"),
        ("WHL-R120-30", f"Rubber wheel {cad.wheel_diameter_mm:.0f}x{cad.wheel_width_mm:.0f} mm, "
         "keyed hub", "drivetrain", arch.wheel_count, 9.00, ""),
        ("BAT-LFP-512", f"{arch.battery.chemistry} pack {arch.battery.nominal_voltage_v} V, "
         f"{arch.battery.capacity_wh:.0f} Wh, integrated BMS", "power", 1, 189.00,
         "Mechanically restrained in battery bay"),
        ("PWR-DCDC-01", "DC-DC converter 24V->5V/12V, 5A", "power", 1, 14.00, ""),
        ("CTL-MDRV-4CH", "4-channel brushed motor driver, 24V 10A", "electronics", 1, 35.00, ""),
        ("CTL-SBC-01", "Single-board computer (Raspberry Pi 5 class)", "electronics", 1, 80.00,
         "Runs navigation + inspection stack"),
        ("SNS-LID-2D", "2D lidar, 12 m range", "sensors", 1, 99.00, "Front chassis mount"),
        ("SNS-CAM-RGB", "RGB camera module, 1080p", "sensors", 1, 25.00, "Mast mount"),
        ("SNS-CAM-THM", "Thermal camera module (Lepton class)", "sensors", 1, 199.00,
         "Mast mount, for equipment hot-spot inspection"),
        ("SNS-IMU-9D", "9-DoF IMU breakout", "sensors", 1, 15.00, "Electronics bay"),
        ("HW-FAST-KIT", "Fastener kit M3/M4 (bolts, nuts, standoffs)", "hardware", 1, 12.00, ""),
        ("HW-WIRE-KIT", "Wiring, connectors, fuse holder, e-stop button", "hardware", 1, 24.00,
         "E-stop required for industrial environment"),
    ]

    if "thermal_camera" not in req.sensors_required:
        rows = [r for r in rows if r[0] != "SNS-CAM-THM"]
    if "lidar_2d" not in req.sensors_required:
        rows = [r for r in rows if r[0] != "SNS-LID-2D"]

    items = [
        BOMItem(
            part_number=pn, name=name, category=cat, quantity=qty,
            unit_cost_usd=cost, total_cost_usd=round(qty * cost, 2),
            supplier="TBD (curated estimate)", notes=notes,
        )
        for pn, name, cat, qty, cost, notes in rows
    ]
    total = round(sum(i.total_cost_usd for i in items), 2)
    return BOM(design_id=design_id, items=items, total_cost_usd=total)


def write_bom_csv(bom: BOM, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["part_number", "name", "category", "quantity",
                         "unit_cost_usd", "total_cost_usd", "supplier", "notes"])
        for i in bom.items:
            writer.writerow([i.part_number, i.name, i.category, i.quantity,
                             f"{i.unit_cost_usd:.2f}", f"{i.total_cost_usd:.2f}",
                             i.supplier, i.notes])
        writer.writerow([])
        writer.writerow(["TOTAL", "", "", "", "", f"{bom.total_cost_usd:.2f}", "",
                         bom.pricing_disclaimer])
