"""Static (quasi-static) stability & force analysis for the tracked
wheelchair prototype.

Pure Python + numpy (no physics engine). Geometry mirrors
SCAD/parameters.scad (1 unit = 1 cm); component masses come from
BOM_weight.csv.

Run:    python3 sim/static_analysis.py [driver_kg]
Out:    sim/static_report.csv , sim/static_report.txt

Conventions:
  x : longitudinal, +x points toward the FRONT (idler at x=+41)
  z : height above ground  (belt bottom z=0, idler hub at z=11.5)
  y : lateral              (track centerline at y=+/-27, belt outer edge y=34)
"""
import csv
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

G = 9.81

# ----------------------------------------------------------------------
# GEOMETRY  (from SCAD/parameters.scad, 1 unit = 1 cm)
# ----------------------------------------------------------------------
TRACK_LENGTH = 82.0       # idler-to-sprocket wheelbase
IDLER_X = 41.0            # front idler x = +41
REAR_X = -41.0            # rear sprocket / seat-back x = -41
TRACK_CENTER_Y = 27.0     # trackCenterY
TRACK_WIDTH = 14.0        # linkWidth
BELT_OUTER_Y = TRACK_CENTER_Y + TRACK_WIDTH / 2.0    # 34 cm -> roll base edge

HUB_Z = 11.5              # 16 - 4.5 : wheel hub height above the ground plane
SEAT_Z = 45.0             # seat surface above ground

SPROCKET_R = 9.5          # drive sprocket radius (cm) -> torque arm
ETA = 0.85                # drivetrain efficiency


def load_bom():
    """Component masses from BOM_weight.csv."""
    path = os.path.join(ROOT, "BOM_weight.csv")
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                m = float(r["Total Weight (kg)"])
            except (ValueError, TypeError):
                continue
            if m <= 0:
                continue
            rows.append({"cat": (r["Component"] or "").strip(), "kg": m})
    return rows


def cat_cg(name):
    """Centroid (x, y, z) cm for a BOM row. x +front, z above ground, y lateral."""
    n = name.lower()
    if "belt" in n:
        return np.array([0.0, 0.0, 10.0])
    if "idler" in n:
        return np.array([IDLER_X, TRACK_CENTER_Y, HUB_Z])
    if "sprocket" in n:
        return np.array([REAR_X, TRACK_CENTER_Y, HUB_Z])
    if "road wheel" in n:
        return np.array([0.0, 0.0, HUB_Z])
    if "bearing" in n:
        return np.array([0.0, 0.0, HUB_Z])
    if "bushing" in n:
        return np.array([-8.0, TRACK_CENTER_Y, 20.0])
    if "axle" in n:
        return np.array([-2.0, 0.0, HUB_Z + 1.0])
    if "l-bracket" in n:
        return np.array([4.0, 0.0, 32.0])
    if "suspension beam" in n:
        return np.array([-6.0, 0.0, 22.0])
    if "seat pan" in n:
        return np.array([-14.0, 0.0, 47.0])
    if "seat bolt" in n or "fastener" in n:
        return np.array([-16.0, 0.0, 47.0])
    if "cushion" in n:
        return np.array([-16.0, 0.0, 44.0])
    if "backrest" in n:
        return np.array([-34.0, 0.0, 63.0])
    if "lumbar" in n:
        return np.array([-34.0, 0.0, 52.0])
    if "headrest" in n:
        return np.array([-34.0, 0.0, 78.0])
    if "armrest" in n:
        return np.array([-20.0, 0.0, 60.0])
    if "joystick" in n or "imu" in n:
        return np.array([-18.0, 0.0, 58.0])
    if "footrest" in n or "foot" in n:
        return np.array([-8.0, 0.0, 26.0])
    if "actuator" in n or "jack" in n:
        return np.array([24.0, 0.0, 18.0])
    if "motor" in n:
        return np.array([30.0, 0.0, 14.0])
    if "frame" in n or "cross" in n or "chassis" in n:
        return np.array([-2.0, 0.0, 40.0])
    return np.array([0.0, 0.0, 30.0])


def mass_model(driver_kg=75.0):
    """Total mass (kg) and CG [x, y, z] in cm."""
    x = y = z = 0.0
    m_total = 0.0
    for r in BOM:
        kg = r["kg"]
        m_total += kg
        c = cat_cg(r["cat"])
        x += kg * c[0]
        y += kg * c[1]
        z += kg * c[2]
    if driver_kg > 0:
        m_total += driver_kg
        x += driver_kg * (-16.0)
        y += driver_kg * 0.0
        z += driver_kg * 52.0
    return m_total, np.array([x, y, z]) / m_total


def longitudinal_tip(cg):
    """Pitch tip-over angles in deg, about the front and rear edges of the
    belt footprint. The toe will tilt off edge when the CG falls outside."""
    x, _, zz = cg
    arm_rear = x - REAR_X                 # nose-up (climb): rear pivot arm
    arm_front = IDLER_X - x               # nose-down (descend): front pivot arm
    theta_up = math.degrees(math.atan(arm_rear / zz))
    theta_down = math.degrees(math.atan(arm_front / zz))
    return theta_down, theta_up


def lateral_roll(cg):
    """Max lateral slope before rolling over the low-side track edge."""
    _, y, zz = cg
    arm = BELT_OUTER_Y - abs(y)
    return math.degrees(math.atan(arm / zz))


def drive_requirements(m_total, alpha_deg, accel=0.2):
    """Linear drive force + torque to sustain a given grade."""
    a = math.radians(alpha_deg)
    W = m_total * G
    F_slope = W * math.sin(a)
    F_roll = W * math.cos(a) * 0.02
    F_net = F_slope + F_roll + m_total * accel
    T_per = F_net * (SPROCKET_R / 100.0) / 2.0 / ETA
    return W, F_slope, F_net, T_per, math.tan(a)


def main():
    driver_kg = float(sys.argv[1]) if len(sys.argv) > 1 else 75.0
    global BOM
    BOM = load_bom()
    m_total, cg = mass_model(driver_kg)
    x, y, zz = cg
    td, tu = longitudinal_tip(cg)
    roll = lateral_roll(cg)

    # grade effort at the documented stair geometry (28 deg) and ramp 1:12
    W10, Fs10, Fn10, T10, mu10 = drive_requirements(m_total, 10.0)
    Ws, Fss, Fns, T_stair, mu_stair = drive_requirements(m_total, 28.0)

    rows = [
        ["weight_total_kg", f"{m_total:.1f}", "kg", "vehicle + driver"],
        ["weight_N", f"{m_total * G:.0f}", "N", "mg"],
        ["cg_x_cm", f"{x:.1f}", "cm", "+front (of CG)"],
        ["cg_y_cm", f"{y:.1f}", "cm", "+right"],
        ["cg_z_cm", f"{zz:.1f}", "cm", "above ground"],
        ["pitch_down_max_deg", f"{tu:.1f}", "deg", "nose-down (descend)"],
        ["pitch_up_max_deg", f"{td:.1f}", "deg", "nose-up (climb)"],
        ["roll_max_deg", f"{roll:.1f}", "deg", "lateral"],
        ["drive_F_ramp_N", f"{Fn10:.1f}", "N", "needed on 10% grade, a=0.2"],
        ["drive_T_motor_Nm", f"{T10:.1f}", "N·m", "per motor (r=9.5cm, eta .85)"],
        ["drive_mu_needed", f"{mu10:.3f}", "-", "traction required"],
        ["F_slope_stair_28_N", f"{Fss:.1f}", "N", "stair incline force"],
        ["T_motor_stair_28_Nm", f"{T_stair:.1f}", "N·m", "per motor"],
    ]

    lines = []
    lines.append("=" * 72)
    lines.append("  STATIC (QUASI-STATIC) ANALYSIS - VLEE TRACKED WHEELCHAIR")
    lines.append("=" * 72)
    lines.append(f"  Vehicle mass         : {m_total:6.1f} kg  (driver {driver_kg:.0f} kg)")
    lines.append(f"  Total weight         : {m_total * G:6.0f} N")
    lines.append(f"  CG    x={x:5.1f} cm  y={y:4.1f} cm  z={zz:4.1f} cm")
    lines.append("")
    lines.append("  TIP-OVER SAFETY (static base)")
    lines.append(f"    max nose-down pitch (descending) : {td:5.1f} deg")
    lines.append(f"    max nose-up   pitch (climbing)   : {tu:5.1f} deg")
    lines.append(f"    max lateral roll (side slope)    : {roll:5.1f} deg")
    lines.append("")
    lines.append("  DRIVE BASIS")
    lines.append(f"    10% ramp: need {Fn10:.0f} N at wheels, "
                 f"{T10:.1f} N·m/motor")
    lines.append(f"    stair 28 deg     : need {Fns:.0f} N at wheels, "
                 f"{T_stair:.1f} N·m/motor")
    lines.append(f"    motor torque AVL: ~27 N·m continuous (350W @ 120rpm)")
    lines.append(f"{'='*72}")
    txt = "\n".join(lines)

    with open(os.path.join(HERE, "static_report.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "value", "unit", "note"])
        w.writerows(rows)
    with open(os.path.join(HERE, "static_report.txt"), "w") as f:
        f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()