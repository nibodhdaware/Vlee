"""Probe: dynamic_pybullet model + belt lock after pitch + drive from start."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
F_MAX = 12000.0
KP = 4000.0
DRIVE_F = 10000.0


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
            track_pads.append(pid)
            p.changeDynamics(pid, -1, lateralFriction=1.2, spinningFriction=0.02)
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=1.0)
    p.changeDynamics(body, -1, lateralFriction=1.0)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=1.8)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    T = 13.5
    V = 6.0

    rows = []
    t = 0.0
    lifting = False
    locked = False
    pad_constraints = []
    while t < 30.0:
        # DRIVE FROM START (like original probe_stairs.py)
        for j in sprockets:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                    targetVelocity=V, force=T)

        pos, quat = p.getBasePositionAndOrientation(body)
        lin, ang = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]

        if not lifting and pos[0] > 0.85 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not locked:
            err = STAIR_ANGLE - pitch
            if err > 0:
                F = min(F_MAX, KP * err)
                p.applyExternalForce(body, -1, [0, 0, F], [D.FRONT_X, 0, 0.02], p.WORLD_FRAME)
            else:
                locked = True
                for pid in track_pads:
                    cid = p.createConstraint(body, -1, pid, -1, p.JOINT_FIXED,
                                             [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
                    pad_constraints.append(cid)
                print(f"  BELT LOCKED at pitch={math.degrees(pitch):+.1f}")

        if locked:
            # Pitch PD controller to hold STAIR_ANGLE
            err = STAIR_ANGLE - pitch
            pitch_vel = ang[1]
            hold_torque = 5000.0 * err - 2000.0 * pitch_vel
            hold_torque = max(-10000.0, min(10000.0, hold_torque))
            p.applyExternalTorque(body, -1, [0, hold_torque, 0], p.WORLD_FRAME)
            # Drive: horizontal force at body CG (world frame force, body-frame position)
            p.applyExternalForce(body, -1, [DRIVE_F, 0, 0], [0, 0, 0], p.WORLD_FRAME)

        p.stepSimulation()
        t += D.DT
        if int(t) != int(t - D.DT):
            print(f"  t={t:.1f} x={pos[0]*100:.1f} pitch={math.degrees(pitch):+.1f} v={lin[0]:.2f} locked={locked}")

    print(f"Final: x={pos[0]*100:.1f} cm, pitch={math.degrees(pitch):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()