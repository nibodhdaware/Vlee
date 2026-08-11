"""Probe: single body rigid track frame - pitch P-controller + drive at sprocket."""
import math
import pybullet as p
import pybullet_data

STAIR_ANGLE = math.atan2(0.16, 0.32)
F_MAX = 12000.0
KP = 4000.0
DRIVE_F = 4000.0
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

    # ==== SINGLE BODY: RIGID TRACK FRAME (chassis + idler + sprocket + belt) ====
    IDLER_X = 0.41
    REAR_X = -0.41
    BELT_R = 0.115
    IDLER_R = 0.125
    SPROCKET_R = 0.104
    TRACK_W = 0.54

    # Build collision/visual as single compound shape
    # Main box
    main_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.6, 0.3, 0.15])
    # Idler wheels
    idler_col = p.createCollisionShape(p.GEOM_CYLINDER, radius=IDLER_R, height=0.06)
    # Sprocket wheels
    spr_col = p.createCollisionShape(p.GEOM_CYLINDER, radius=SPROCKET_R, height=0.06)

    # Build compound collision
    col_ids = [
        main_col,
        idler_col, idler_col,  # left, right idler
        spr_col, spr_col,      # left, right sprocket
    ]
    # Transform positions relative to body center
    transforms = [
        [0, 0, 0],           # main box
        [IDLER_X, TRACK_W/2, BELT_R],   # left idler
        [IDLER_X, -TRACK_W/2, BELT_R],  # right idler
        [REAR_X, TRACK_W/2, BELT_R],    # left sprocket
        [REAR_X, -TRACK_W/2, BELT_R],   # right sprocket
    ]
    # Rotations: main=0, wheels=90deg about Y
    rots = [
        [0, 0, 0, 1],
        [0, 0.707, 0, 0.707],
        [0, 0.707, 0, 0.707],
        [0, 0.707, 0, 0.707],
        [0, 0.707, 0, 0.707],
    ]

    body = p.createMultiBody(160.0, col_ids, -1, [0, 0, 0.15],
                             [0, 0, 0, 1], transforms, rots)

    # Visual
    main_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.6, 0.3, 0.15],
                                   rgbaColor=[0.3, 0.3, 0.35, 1])
    idler_vis = p.createVisualShape(p.GEOM_CYLINDER, radius=IDLER_R, length=0.06,
                                    rgbaColor=[0.2, 0.2, 0.25, 1])
    spr_vis = p.createVisualShape(p.GEOM_CYLINDER, radius=SPROCKET_R, length=0.06,
                                  rgbaColor=[0.15, 0.15, 0.2, 1])
    vis_ids = [main_vis, idler_vis, idler_vis, spr_vis, spr_vis]
    for i, (v, t, r) in enumerate(zip(vis_ids, transforms, rots)):
        p.createMultiBody(0, -1, v, t, r, body, -1, [0,0,0], [0,0,0], [0,0,0])

    # Belt pads fixed to body
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
            p.createMultiBody(0.15, pad_col, pad_vis, [px, y, pz], q,
                              body, -1, [0,0,0], [0,0,0], [0,0,0])

    p.changeDynamics(body, -1, lateralFriction=2.0)

    return body, IDLER_X, REAR_X


def run():
    body, IDLER_X, REAR_X = build()

    rows = []
    t = 0.0
    lifting = False
    while t < 20.0:
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, ang = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]
        vx = lin[0]

        if not lifting and pos[0] > 0.82:
            lifting = True
            print(f"  handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting:
            err = STAIR_ANGLE - pitch
            if err > 0:
                F = min(F_MAX, KP * err)
            else:
                F = 8000.0
            F = max(0, min(F_MAX, F))
            p.applyExternalForce(body, -1, [0, 0, F], [IDLER_X, 0, 0.02], p.WORLD_FRAME)
            p.applyExternalForce(body, -1, [DRIVE_F, 0, 0], [REAR_X, 0, 0.02], p.WORLD_FRAME)

        p.stepSimulation()
        t += DT
        if int(t) != int(t - DT):
            print(f"  t={t:.1f} x={pos[0]*100:.1f} pitch={math.degrees(pitch):+.1f} v={vx:.2f} F={F if lifting else 0:.0f}")

    print(f"Final: x={pos[0]*100:.1f} cm, pitch={math.degrees(pitch):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()