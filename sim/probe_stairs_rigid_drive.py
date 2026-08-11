"""Probe: front lift with ramped target angle to STAIR_ANGLE, belt rigid."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
KP = 15000.0
KD = 40000.0
T_MAX = 20000.0
HOLD_T = 3000.0
DRIVE_F = 10000.0
RAMP_TIME = 2.0  # seconds to ramp from 0 to STAIR_ANGLE


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
    for name, j in joint_idx.items():
        if "sprocket" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
        p.changeDynamics(body, j, lateralFriction=1.2)
    p.changeDynamics(body, -1, lateralFriction=1.2)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=5.0)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    T = 150.0
    V = 5.0

    rows = []
    t = 0.0
    lifting = False
    angle_locked = False
    pad_constraints = []
    while t < 30.0:
        for j in sprockets:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL,
                                    targetVelocity=V, force=T)
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, ang = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]
        pitch_vel = ang[1]

        if not lifting and pos[0] > 0.95 and abs(lin[0]) < 0.15:
            lifting = True
            lift_start_t = t
            print(f"  front lift: handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not angle_locked:
            # Ramped target angle
            ramp_progress = min(1.0, (t - lift_start_t) / RAMP_TIME)
            target = STAIR_ANGLE * ramp_progress
            err = target - pitch
            torque = KP * err - KD * pitch_vel
            torque = max(-T_MAX, min(T_MAX, torque))
            if int(t*10)%50==0:
                print(f"  t={t:.1f} pitch={math.degrees(pitch):+.1f} target={math.degrees(target):+.1f} torque={torque:.0f}")
            p.applyExternalTorque(body, -1, [0, torque, 0], p.WORLD_FRAME)

            if ramp_progress >= 1.0 and abs(err) < math.radians(0.5) and abs(pitch_vel) < 0.05:
                angle_locked = True
                print(f"  angle locked at pitch={math.degrees(pitch):+.1f}")
                for pid in track_pads:
                    cid = p.createConstraint(body, -1, pid, -1, p.JOINT_FIXED,
                                             [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
                    pad_constraints.append(cid)

        elif lifting and angle_locked:
            p.applyExternalTorque(body, -1, [0, HOLD_T, 0], p.WORLD_FRAME)
            p.applyExternalForce(body, -1, [DRIVE_F, 0, 0], [0, 0, 0], p.WORLD_FRAME)

        p.stepSimulation()
        t += D.DT
        if int(t * 20) != int((t - D.DT) * 20):
            rows.append([t, pos[0] * 100, pos[2] * 100, math.degrees(pitch)])

    print(f"front lift: final x = {rows[-1][1]:.1f} cm, max_pitch = {max(r[3] for r in rows):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()