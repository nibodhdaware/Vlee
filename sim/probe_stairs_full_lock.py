"""Probe: lock belt to chassis + constraint angle lock + forward force."""
import math
import pybullet as p

import dynamic_pybullet as D

STAIR_ANGLE = math.atan2(0.16, 0.32)
DRIVE_F = 25000.0
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

    ghost_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.1])
    ghost = p.createMultiBody(0, ghost_col, -1, [0, 0, 0])
    ghost_cid = None
    lock_cid = None
    pad_constraints = []

    rows = []
    t = 0.0
    lifting = False
    locked = False
    while t < 30.0:
        pos, quat = p.getBasePositionAndOrientation(body)
        lin, _ = p.getBaseVelocity(body)
        eul = p.getEulerFromQuaternion(quat)
        pitch = eul[1]

        if not lifting and pos[0] > 0.85 and abs(lin[0]) < 0.15:
            lifting = True
            print(f"  handoff at x={pos[0]*100:.1f}cm, pitch={math.degrees(pitch):+.1f}")

        if lifting and not locked:
            # Lock belt pads to chassis (rigid track)
            for pid in track_pads:
                cid = p.createConstraint(body, -1, pid, -1, p.JOINT_FIXED,
                                         [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
                pad_constraints.append(cid)
            # Create ghost + constraints for angle lock
            p.resetBasePositionAndOrientation(ghost, pos,
                                               p.getQuaternionFromAxisAngle([0, 1, 0], STAIR_ANGLE))
            ghost_cid = p.createConstraint(
                ghost, -1, -1, -1, p.JOINT_PRISMATIC,
                [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
            p.changeConstraint(ghost_cid, maxForce=1e6)
            lock_cid = p.createConstraint(
                body, -1, ghost, -1, p.JOINT_FIXED,
                [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
            locked = True
            print(f"  locked at pitch={math.degrees(pitch):+.1f}")

        if locked:
            p.resetBasePositionAndOrientation(ghost, [pos[0], 0, 0],
                                               p.getQuaternionFromAxisAngle([0, 1, 0], STAIR_ANGLE))
            p.applyExternalForce(ghost, -1, [DRIVE_F, 0, 0], [0, 0, 0], p.WORLD_FRAME)
        else:
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