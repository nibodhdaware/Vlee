"""Probe: two-body model - just jack force, no drive, debug pitch."""
import math
import pybullet as p
import pybullet_data

STAIR_ANGLE = math.atan2(0.16, 0.32)
F_MAX = 12000.0
KP = 4000.0
JACK_X = -0.85
DT = 1/240.0
GRAVITY = -9.81


def build():
    p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, GRAVITY)
    p.setTimeStep(DT)
    p.loadURDF("plane.urdf")

    # Stairs
    rise, run, n = 0.16, 0.32, 4
    for i in range(n):
        x = 1.5 + run/2 + i*run
        z = (i + 0.5)*rise
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[run/2, 0.9, rise/2])
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[run/2, 0.9, rise/2],
                                  rgbaColor=[0.42, 0.44, 0.47, 1])
        p.createMultiBody(0, col, vis, [x, 0.0, z])

    # ==== BODY 1: TRACK FRAME ====
    tf_mass = 70.0
    tf_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.6, 0.3, 0.15])
    tf_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.6, 0.3, 0.15],
                                 rgbaColor=[0.3, 0.3, 0.35, 1])
    track_frame = p.createMultiBody(tf_mass, tf_col, tf_vis, [0, 0, 0.15])

    IDLER_R = 0.125
    SPROCKET_R = 0.104
    BELT_R = 0.115
    IDLER_X = 0.41
    REAR_X = -0.41
    TRACK_W = 0.54

    for side in (-1, 1):
        y = side * TRACK_W/2
        idler_col = p.createCollisionShape(p.GEOM_CYLINDER, radius=IDLER_R, height=0.06)
        idler_vis = p.createVisualShape(p.GEOM_CYLINDER, radius=IDLER_R, length=0.06,
                                        rgbaColor=[0.2, 0.2, 0.25, 1])
        idler = p.createMultiBody(2.0, idler_col, idler_vis, [IDLER_X, y, BELT_R])
        p.changeDynamics(idler, -1, lateralFriction=5.0)
        p.createConstraint(idler, -1, track_frame, -1, p.JOINT_FIXED,
                           [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
        spr_col = p.createCollisionShape(p.GEOM_CYLINDER, radius=SPROCKET_R, height=0.06)
        spr_vis = p.createVisualShape(p.GEOM_CYLINDER, radius=SPROCKET_R, length=0.06,
                                      rgbaColor=[0.15, 0.15, 0.2, 1])
        spr = p.createMultiBody(2.0, spr_col, spr_vis, [REAR_X, y, BELT_R])
        p.changeDynamics(spr, -1, lateralFriction=10.0)
        p.createConstraint(spr, -1, track_frame, -1, p.JOINT_FIXED,
                           [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])

    # Belt pads
    perim = 2*(IDLER_X - REAR_X) + 2*math.pi*BELT_R
    n_pads = 16
    spacing = perim / n_pads
    for i in range(n_pads):
        s = (i + 0.5)*spacing
        if s < IDLER_X - REAR_X:
            px = REAR_X + s; pz = 0.0; theta = 0.0
        elif s < IDLER_X - REAR_X + math.pi*BELT_R:
            a = (s - (IDLER_X - REAR_X)) / BELT_R
            px = IDLER_X - BELT_R*math.cos(a)
            pz = BELT_R - BELT_R*math.sin(a)
            theta = a
        elif s < 2*(IDLER_X - REAR_X) + math.pi*BELT_R:
            px = IDLER_X - (s - (IDLER_X - REAR_X) - math.pi*BELT_R)
            pz = 2*BELT_R; theta = math.pi
        else:
            a = (s - (2*(IDLER_X - REAR_X) + math.pi*BELT_R)) / BELT_R
            px = REAR_X + BELT_R*math.cos(a)
            pz = BELT_R + BELT_R*math.sin(a)
            theta = math.pi + a

        for side in (-1, 1):
            y = side * TRACK_W/2
            pad_col = p.createCollisionShape(p.GEOM_BOX,
                                             halfExtents=[spacing*0.95/2, 0.08, 0.011])
            pad_vis = p.createVisualShape(p.GEOM_BOX,
                                          halfExtents=[spacing*0.95/2, 0.08, 0.011],
                                          rgbaColor=[0.1, 0.1, 0.12, 1])
            q = p.getQuaternionFromAxisAngle([0, 1, 0], theta)
            pad = p.createMultiBody(0.15, pad_col, pad_vis, [px, y, pz], q)
            p.changeDynamics(pad, -1, lateralFriction=10.0, spinningFriction=2.0)
            p.createConstraint(pad, -1, track_frame, -1, p.JOINT_FIXED,
                               [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])

    # ==== BODY 2: CHASSIS ====
    ch_mass = 80.0
    ch_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.5, 0.4, 0.2])
    ch_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.5, 0.4, 0.2],
                                 rgbaColor=[0.4, 0.35, 0.3, 1])
    chassis = p.createMultiBody(ch_mass, ch_col, ch_vis, [0, 0, 0.55])

    # PIVOT at front idler
    pivot_cid = p.createConstraint(
        track_frame, -1, chassis, -1, p.JOINT_POINT2POINT,
        [0, 0, 0], [IDLER_X, 0, 0],
        [0, 0, 0], [IDLER_X, 0, 0.4])
    p.changeConstraint(pivot_cid, maxForce=1e6)

    return track_frame, chassis, IDLER_X, REAR_X


def run():
    track_frame, chassis, IDLER_X, REAR_X = build()

    t = 0.0
    lifting = False
    # Just apply jack force from start, no drive
    F = 8000.0
    while t < 5.0:
        pos_tf, quat_tf = p.getBasePositionAndOrientation(track_frame)
        pos_ch, quat_ch = p.getBasePositionAndOrientation(chassis)
        eul_tf = p.getEulerFromQuaternion(quat_tf)
        pitch_tf = eul_tf[1]
        eul_ch = p.getEulerFromQuaternion(quat_ch)
        pitch_ch = eul_ch[1]

        # Jack: UP on track_frame rear, DOWN on chassis rear
        p.applyExternalForce(track_frame, -1, [0, 0, F], [JACK_X, 0, 0.02], p.WORLD_FRAME)
        p.applyExternalForce(chassis, -1, [0, 0, -F], [JACK_X, 0, 0.55], p.WORLD_FRAME)

        p.stepSimulation()
        t += DT
        if int(t * 20) != int((t - DT) * 20):
            print(f"  t={t:.1f} tf_pitch={math.degrees(pitch_tf):+.2f} ch_pitch={math.degrees(pitch_ch):+.2f} tf_x={pos_tf[0]*100:.1f}")

    print(f"Final: tf_pitch={math.degrees(pitch_tf):+.2f} ch_pitch={math.degrees(pitch_ch):+.2f}")
    p.disconnect()


if __name__ == "__main__":
    run()