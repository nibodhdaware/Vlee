"""Probe: pitch-torque servo on the base, emulating the hydraulic tilting the
track assembly about the idler contact point. Target STAIR_ANGLE when the front
idler contacts the stair riser."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)   # sim stair geometry (build_terrain)
KP = 8000.0                            # Nm per rad
KD = 1500.0                            # Nm per rad/s
TORQUE_MAX = 6000.0                    # Nm


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
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=1.0)
    p.changeDynamics(body, -1, lateralFriction=1.0)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=1.8)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    T = 27.0 / 2.0
    V = 6.0

    rows = []
    t = 0.0
    lifting = False
    while t < 30.0:
        for j in sprockets:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                    targetVelocity=V, force=T)
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, ang = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]
        pitch_vel = ang[1]

        # Engage when front idler contacts riser (nose x ~1.5m, chair x ~1.0m)
        if not lifting and pos[0] > 0.95 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  torque servo: handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting:
            err = STAIR_ANGLE - pitch
            torque = KP * err - KD * pitch_vel
            torque = max(-TORQUE_MAX, min(TORQUE_MAX, torque))
            p.applyExternalTorque(body, -1, [0, torque, 0], p.WORLD_FRAME)

        p.stepSimulation()
        t += D.DT
        if int(t * 20) != int((t - D.DT) * 20):
            rows.append([t, pos[0] * 100, pos[2] * 100, math.degrees(pitch)])

    print(f"torque servo: final x = {rows[-1][1]:.1f} cm, max_pitch = {max(r[3] for r in rows):+.1f}")
    for r in rows[::2]:
        if r[1] > 80:
            print(f"  {r[1]:.0f}/{r[3]:+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()