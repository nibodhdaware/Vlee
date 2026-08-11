"""Probe: jack tilt + direct wheel drive (no belt pads)."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
KP = 30000.0
KD = 20000.0
F_MAX = 60000.0
JACK_X = -1.2
HOLD_F = 8000.0


def run():
    D.build_terrain(False, True, False)
    mass, cgx, _ = D.read_static()
    body = D.wheel_urdf(mass, cgx)
    joint_idx = {}
    for j in range(p.getNumJoints(body)):
        joint_idx[p.getJointInfo(body, j)[1].decode()] = j

    # Skip building belt - use URDF wheels directly
    for name, j in joint_idx.items():
        if "sprocket" not in name and "idler" not in name and "road" not in name:
            p.setJointMotorControl2(body, j, p.VELOCITY_CONTROL, force=0)
    for name, j in joint_idx.items():
        p.changeDynamics(body, j, lateralFriction=1.2)
    p.changeDynamics(body, -1, lateralFriction=1.2)
    for name, j in joint_idx.items():
        if "sprocket" in name:
            p.changeDynamics(body, j, lateralFriction=3.0)
    sprockets = [j for n, j in joint_idx.items() if "sprocket" in n]
    idlers = [j for n, j in joint_idx.items() if "idler" in n]
    T = 150.0
    V = 5.0

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

        if not lifting and pos[0] > 0.95 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  rear jack: handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not angle_locked:
            err = STAIR_ANGLE - pitch
            if err > 0:
                F = KP * err - KD * pitch_vel
            else:
                angle_locked = True
                lock_cid = p.createConstraint(
                    body, -1, -1, -1, p.JOINT_FIXED,
                    [0, 0, 0], [0, 0, 0], [0, 0, 0],
                    p.getQuaternionFromAxisAngle([0, 1, 0], STAIR_ANGLE))
                print(f"  angle locked at pitch={math.degrees(pitch):+.1f}")
                F = 0
            F = max(0, min(F_MAX, F))
            if F > 0:
                p.applyExternalForce(body, -1, [0, 0, F], [JACK_X, 0, 0.02], p.WORLD_FRAME)

        elif lifting and angle_locked:
            p.applyExternalForce(body, -1, [0, 0, HOLD_F], [JACK_X, 0, 0.02], p.WORLD_FRAME)

        p.stepSimulation()
        t += D.DT
        if int(t * 20) != int((t - D.DT) * 20):
            rows.append([t, pos[0] * 100, pos[2] * 100, math.degrees(pitch)])

    print(f"rear jack: final x = {rows[-1][1]:.1f} cm, max_pitch = {max(r[3] for r in rows):+.1f}")
    p.disconnect()


if __name__ == "__main__":
    run()