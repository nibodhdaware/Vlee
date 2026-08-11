"""Dynamic rigid-body simulation of the VLEE tracked wheelchair in PyBullet.

The chair is a full dynamic body built from a generated URDF: the chassis
carries the BOM mass (read from sim/static_report.csv), and per side there are
4 road wheels + a free-spinning front idler + a rear drive sprocket, all on
revolute joints. Drive torque is applied directly to the two sprocket joints,
which roll the tracks and pull the chair.

Run:
    python3 sim/dynamic_pybullet.py            # flat, forward drive
    python3 sim/dynamic_pybullet.py --bump     # drive over a curb
    python3 sim/dynamic_pybullet.py --stairs   # climb the test stair
    python3 sim/dynamic_pybullet.py --gui      # show GUI while running

Metrics logged to sim/dynamic_log.csv; a stability summary is printed.
"""
import argparse
import csv
import math
import os

import pybullet as p
import pybullet_data

HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------
# Geometry (cm -> SI). All hub centres sit on the belt arc circles so the
# belt path is a stadium loop around the chassis.
# ----------------------------------------------------------------------
BELT_R = 0.115       # belt centreline radius around each wheel ring
IDLER_R = 0.100      # front free-spinning wheel (inside the belt)
SPROCKET_R = 0.104   # rear driven wheel = belt inner radius (grips belt)
ROAD_R = 0.070       # small ground wheels that press the belt down
WHEEL_W = 0.160      # wheel/track width per side
TRACK_Y = 0.27       # lateral position of each track centre
FRONT_X = 0.41       # idler hub x (belt arc centre, front)
REAR_X = -0.41       # sprocket hub x (belt arc centre, rear)
ROAD_X = [-0.22, -0.06, 0.10, 0.24]
HUB_Z = BELT_R       # hub height above the belt mid-thickness line

# Belt outer surface: bottom straight runs flush with the ground (z=0);
# front arc centre (FRONT_X, BELT_R), rear arc centre (REAR_X, BELT_R).
PAD_L = 0.040        # belt pad length along the loop
PAD_H = 0.022        # belt thickness (radial)
PAD_W = 0.160        # belt lateral width
PAD_M = 0.12         # kg per belt pad (chain + pad mass)

# Stadium-loop arc length: 2 straight runs + 2 semicircles.
def _perimeter():
    return 2 * (FRONT_X - REAR_X) + 2 * math.pi * BELT_R

def belt_path(s):
    """Stadium loop point (x, z, tangent-dx, tangent-dz) at arc length s."""
    L = FRONT_X - REAR_X
    B = BELT_R
    if s < L:                                   # bottom straight (ground)
        return REAR_X + s, 0.0, 1.0, 0.0
    s -= L
    if s < math.pi * B:                         # front semicircle
        a = -math.pi / 2 + s / B
        return FRONT_X + B * math.cos(a), B + B * math.sin(a), -math.sin(a), math.cos(a)
    s -= math.pi * B
    if s < L:                                   # top straight
        return FRONT_X - s, 2 * B, -1.0, 0.0
    s -= L
    a = math.pi / 2 + s / B                     # rear semicircle
    return REAR_X + B * math.cos(a), B + B * math.sin(a), -math.sin(a), math.cos(a)

DT = 1.0 / 240.0
GRAVITY = -9.81


def read_static():
    """Mass + CG from static_report.csv (keeps both sims on the same model)."""
    mass, cgx, cgz = 205.0, -0.05, 0.35
    path = os.path.join(HERE, "static_report.csv")
    if os.path.exists(path):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                if r["key"] == "weight_total_kg":
                    mass = float(r["value"])
                elif r["key"] == "cg_x_cm":
                    cgx = float(r["value"]) / 100.0
                elif r["key"] == "cg_z_cm":
                    cgz = float(r["value"]) / 100.0
    return mass, cgx, cgz


def build_terrain(bump, stairs, gui):
    if gui:
        p.connect(p.GUI)
    else:
        p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, GRAVITY)
    p.setTimeStep(DT)
    p.loadURDF("plane.urdf")

    if bump:
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[1.2, 0.9, 0.12])
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[1.2, 0.9, 0.12],
                                  rgbaColor=[0.55, 0.53, 0.50, 1])
        p.createMultiBody(0, col, vis, [2.0, 0.0, 0.12])

    if stairs:
        rise, run, n = 0.16, 0.32, 4
        for i in range(n):
            x = 1.5 + run / 2 + i * run
            z = (i + 0.5) * rise
            col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[run / 2, 0.9, rise / 2])
            vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[run / 2, 0.9, rise / 2],
                                      rgbaColor=[0.42, 0.44, 0.47, 1])
            p.createMultiBody(0, col, vis, [x, 0.0, z])


def wheel_urdf(mass, cgx):
    """Generate wheelchair.urdf in sim/ and load it. Returns body id.
    The wheels are the belt rings: each hub sits at the belt arc centre
    (BELT_R above the belt mid-thickness line); the belt wraps them."""
    def link(name, mass_v, r):
        return f"""  <link name="{name}">
    <inertial>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <mass value="{mass_v}"/>
      <inertia ixx="0.0025" ixy="0" ixz="0" iyy="0.0025" iyz="0" izz="0.01"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0" rpy="1.5708 0 0"/>
      <geometry><cylinder radius="{r}" length="0.16"/></geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="1.5708 0 0"/>
      <geometry><cylinder radius="{r}" length="0.16"/></geometry>
    </collision>
  </link>"""

    def joint(name, x, y, hub_z, r):
        # hub centre sits on the belt arc circle, NOT on the ground: the belt
        # wraps the wheel ring with radius BELT_R around this hub.
        return f"""  <joint name="{name}" type="continuous">
    <parent link="base_link"/>
    <child link="{name}"/>
    <origin xyz="{x} {y} {hub_z}" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
  </joint>"""

    parts = ['<?xml version="1.0"?>', '<robot name="vlee">']
    parts.append(f"""  <link name="base_link">
    <inertial>
      <origin xyz="0 0 0.30" rpy="0 0 0"/>
      <mass value="{mass - 8.0}"/>
      <inertia ixx="3.5" ixy="0" ixz="0" iyy="2.5" iyz="0" izz="3.0"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0.30" rpy="0 0 0"/>
      <geometry><box size="0.62 0.16 0.10"/></geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0.30" rpy="0 0 0"/>
      <geometry><box size="0.62 0.16 0.10"/></geometry>
    </collision>
  </link>""")

    for side in (-1, 1):
        y = side * TRACK_Y
        for x in ROAD_X:
            nm = f"road_{'L' if side < 0 else 'R'}_{x:.2f}".replace("-", "m")
            parts.append(link(nm, 0.6, ROAD_R))
            parts.append(joint(nm, x, y, PAD_H / 2 + ROAD_R, ROAD_R))
        nm = "idler_L" if side < 0 else "idler_R"
        parts.append(link(nm, 0.6, IDLER_R))
        parts.append(joint(nm, FRONT_X, y, BELT_R, IDLER_R))
        nm = "sprocket_L" if side < 0 else "sprocket_R"
        parts.append(link(nm, 0.6, SPROCKET_R))
        parts.append(joint(nm, REAR_X, y, BELT_R, SPROCKET_R))
    parts.append("</robot>")

    path = os.path.join(HERE, "wheelchair.urdf")
    with open(path, "w") as f:
        f.write("\n".join(parts))
    return p.loadURDF(path, basePosition=[cgx, 0.0, 0.0])


def _rot_y(theta):
    return p.getQuaternionFromAxisAngle([0.0, 1.0, 0.0], theta)


def _local_of(world, center, quat):
    """Express world point in a body frame defined by center + rotation quat
    about the y axis only (fast closed-form, no numpy needed)."""
    dx = world[0] - center[0]
    dz = world[2] - center[2]
    c, s = quat[1], quat[2]  # sin/cos of half-angle encoding? reconstruct theta
    theta = 2.0 * math.atan2(quat[2], quat[3])  # cos(a/2)=q[3], sin=q[2]
    cth, sth = math.cos(theta), math.sin(theta)
    lx = dx * cth + dz * sth
    lz = -dx * sth + dz * cth
    return [lx, world[1] - center[1], lz]


def build_track(side):
    """One side's belt: a closed stadium-loop chain of pad links on revolute
    joints. Returns the list of pad body ids. The driven sprocket wheel grips
    the pads by friction and circulates the belt around the ring."""
    y_lat = side * TRACK_Y
    per = _perimeter()
    n_pads = max(4, int(round(per / PAD_L)))
    spacing = per / n_pads
    half_len = spacing * 0.96

    centers, quats, pad_ids = [], [], []
    for i in range(n_pads):
        px, pz, tx, tz = belt_path((i + 0.5) * spacing)
        theta = math.atan2(tz, tx)
        centers.append((px, y_lat, pz))
        quats.append(_rot_y(theta))
        col = p.createCollisionShape(p.GEOM_BOX,
                                     halfExtents=[half_len, PAD_W / 2, PAD_H / 2])
        vis = p.createVisualShape(p.GEOM_BOX,
                                  halfExtents=[half_len, PAD_W / 2, PAD_H / 2],
                                  rgbaColor=[0.15, 0.15, 0.17, 1])
        pid = p.createMultiBody(PAD_M, col, vis, centers[-1], quats[-1])
        p.changeDynamics(pid, -1, lateralFriction=1.2, spinningFriction=0.02)
        pad_ids.append(pid)

    # hinge each pad to the next (wrap-around closes the loop).
    # This build has no JOINT_REVOLUTE constraint: emulate the revolute hinge
    # about the world-Y axis with TWO point-to-point pins on the axis.
    pin_span = 0.05  # length of the shared hinge axis (into the track)
    for i in range(n_pads):
        j = (i + 1) % n_pads
        seam_s = (i + 1) * spacing
        sx, sz, _, _ = belt_path(seam_s)
        for d in (0.0, pin_span):
            pt = [sx, y_lat + d, sz]
            p.createConstraint(
                pad_ids[i], -1, pad_ids[j], -1, p.JOINT_POINT2POINT, [0, 1, 0],
                _local_of(pt, centers[i], quats[i]),
                _local_of(pt, centers[j], quats[j]),
                [0, 0, 0, 1], [0, 0, 0, 1])
    return pad_ids


def run(scenario, gui, torque, max_time):
    build_terrain(scenario == "bump", scenario == "stairs", gui)
    mass, cgx, _ = read_static()
    body = wheel_urdf(mass, cgx)

    joint_idx = {}
    for j in range(p.getNumJoints(body)):
        info = p.getJointInfo(body, j)
        joint_idx[info[1].decode()] = j

    # ---- build the caterpillar belts (closed pad chains) --------------
    track_pads = []
    for side in (-1, 1):
        pads = build_track(side)
        for pid in pads:
            # pads must not collide with each other (they jam); only with
            # terrain and the wheels. group=2, mask=all minus bit-1 (pads)
            p.setCollisionFilterGroupMask(pid, -1, 0x00000002, -3)
        track_pads.extend(pads)

    # idlers/road wheels roll freely
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=1.0)   # rubber is grippy
    # ground grip
    p.changeDynamics(body, -1, lateralFriction=1.0)
    # sprocket grips the belt strongly to drive it
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=1.8)

    # drive sprockets via capped-velocity control; force caps motor torque
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    T_mot = torque / 2.0  # each of two motors carries half the load torque
    V_DRIVE = 6.0         # target wheel spin, rad/s (~0.5 m/s at track radius)

    print(f"scenario={scenario}  mass={mass:.1f} kg  torque={torque:.1f} N·m")
    print(f"per-motor {T_mot:.1f} N·m on {len(sprockets)} sprocket joints "
          f"x {len(track_pads)} belt pads")

    log = []
    t = 0.0
    while t < max_time:
        for j in sprockets:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                    targetVelocity=V_DRIVE, force=T_mot)
        p.stepSimulation()
        t += DT
        pos, quat = p.getBasePositionAndOrientation(body)
        orn = p.getEulerFromQuaternion(quat)
        lin, _ = p.getBaseVelocity(body)

        if int(t * 20) != int((t - DT) * 20):
            log.append([
                round(t, 3),
                round(pos[0] * 100, 1),
                round(pos[2] * 100, 1),
                round(math.degrees(orn[1]), 2),
                round(lin[0], 2),
                round(torque, 1),
            ])

    cols = ["time_s", "x_cm", "z_cm", "pitch_deg", "vx_ms", "torque_Nm"]
    with open(os.path.join(HERE, "dynamic_log.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(log)

    ps = [r[3] for r in log]
    xs = [r[1] for r in log]
    print(f"max pitch   : {max(ps):5.1f} deg")
    print(f"final x     : {xs[-1]:5.1f} cm")
    print(f"CSV: sim/dynamic_log.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bump", action="store_true")
    ap.add_argument("--stairs", action="store_true")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--torque", type=float, default=27.0)
    ap.add_argument("--time", type=float, default=8.0)
    a = ap.parse_args()
    scenario = "stairs" if a.stairs else ("bump" if a.bump else "flat")
    run(scenario, a.gui, a.torque, a.time)