"""Probe: soft torque hold at STAIR_ANGLE + sprocket drive + extreme friction."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
KP = 20000.0
KD = 100000.0  # very high damping
T_MAX = 30000.0
HOLD_T = 2000.0


def run():
    D.build_terrain(False, True, False)
    mass, cgx, _ = D.read_static()
    body = D.wheel_urdf(mass, cgx)
    joint_idx = {}
    for j in range(p.getNumJoints(body)):
        joint_idx[p.getJointInfo(body, j)[1].decode()] = j
    for side in (-1, 1):
        for pid in D.build_track(side):
            p.setCollisionFilterGroupMask(pid, -1, 0x00000002, -3)
            p.changeDynamics(pid, -1, lateralFriction=5.0, spinningFriction=1.0)
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=2.0)
    p.changeDynamics(body, -1, lateralFriction=2.0)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=10.0)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    T = 100.0
    V = 4.0

    rows = []
    t = 0.0
    lifting = False
    angle_locked = False
    while t < 30.0:
        for j in sprockets:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                    targetVelocity=V, force=T)
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, ang = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]
        pitch_vel = ang[1]

        if not lifting and pos[0] > 0.85 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  torque hold: handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not angle_locked:
            err = STAIR_ANGLE - pitch
            torque = KP * err - KD * pitch_vel
            torque = max(-T_MAX, min(T_MAX, torque))
            p.applyExternalTorque(body, -1, [0, torque, 0], p.WORLD_FRAME)
            if abs(err) < math.radians(0.2) and abs(pitch_vel) < 0.02:
                angle_locked = True
                print(f"  angle locked at pitch={math.degrees(pitch):+.1f}")

        elif lifting and angle_locked:
            p.applyExternalTorque(body, -1, [0, HOLD_T, 0], p.WORLD_FRAME)

        p.stepSimulation()
        t += D.DT
        if int(t * 20) != int((t - D.DT) * 20):
            rows.append([t, pos[0] * 100, pos[2] * 100, math.degrees(pitch)])

    print(f"torque hold: final x = {rows[-1][1]:.1f} cm, max_pitch = {max(r[3] for r in rows):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()