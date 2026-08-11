"""Probe: working P controller + belt lock + forward force."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
F_MAX = 12000.0
KP = 4000.0
DRIVE_F = 2000.0
T = 80.0
V = 5.0


def run():
    D.build_terrain(False, True, False)
    mass, cgx, _ = D.read_static()
    body = D.wheel_urdf(mass, cgx)
    joint_idx = {}
    for j in range(p.getNumJoints(body)):
        joint_idx[p.getJointInfo(body, j)[1].decode()] = j
    track_pads = []
    for side in (-1, 1):
        for pid in D.build_track(side):
            p.setCollisionFilterGroupMask(pid, -1, 0x00000002, -3)
            p.changeDynamics(pid, -1, lateralFriction=10.0, spinningFriction=2.0)
            track_pads.append(pid)
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=2.0)
    p.changeDynamics(body, -1, lateralFriction=2.0)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=10.0)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]

    rows = []
    t = 0.0
    lifting = False
    locked = False
    pad_constraints = []
    while t < 30.0:
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, _ = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]

        if not lifting and pos[0] > 0.85 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not locked:
            # Lock belt to chassis (rigid track)
            for pid in track_pads:
                cid = p.createConstraint(body, -1, pid, -1, p.JOINT_FIXED,
                                         [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
                pad_constraints.append(cid)
            locked = True
            print(f"  belt locked at pitch={math.degrees(pitch):+.1f}")

        if lifting:
            # P controller on force at front (worked before)
            err = STAIR_ANGLE - pitch
            if err > 0:
                F = min(F_MAX, KP * err)
                p.applyExternalForce(body, -1, [0, 0, F], [D.FRONT_X, 0, 0.02], p.WORLD_FRAME)
            # Forward force at front contact (no pitch torque)
            p.applyExternalForce(body, -1, [DRIVE_F, 0, 0], [D.FRONT_X, 0, 0.02], p.WORLD_FRAME)

        if not locked:
            for j in sprockets:
                p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                        targetVelocity=V, force=T)

        p.stepSimulation()
        t += D.DT
        if int(t * 20) != int((t - D.DT) * 20):
            rows.append([t, pos[0] * 100, pos[2] * 100, math.degrees(pitch)])

    print(f"final x = {rows[-1][1]:.1f} cm, max_pitch = {max(r[3] for r in rows):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()