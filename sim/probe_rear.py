"""Verify: upward force at the REAR (-X) raises the back while the
front idler (+X) stays on the ground, and print signed pitch + end heights.
"""
import math
import pybullet as p

import dynamic_pybullet as D


def fresh():
    D.build_terrain(False, False, False)
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
    return body


def report(body, label):
    pos, quat = p.getBasePositionAndOrientation(body)
    eul = p.getEulerFromQuaternion(quat)
    pitch = math.degrees(eul[1])
    # world position of a point that is at local (x,0,z) in the base frame
    def w(x, z):
        return p.multiplyTransforms(pos, quat, [x, 0, z], [0,0,0,1])[0]
    rz = w(D.REAR_X, 0.0)[2]
    fz = w(D.FRONT_X, 0.0)[2]
    print(f"{label}  pitch={pitch:+.1f}  rear_z_at_back={rz*100:6.1f}cm  front_z_at_nose={fz*100:6.1f}cm")


if __name__ == "__main__":
    body = fresh()
    for _ in range(300):
        p.stepSimulation()
    report(body, "baseline   ")
    # press the BACK end up (apply upward force at rear)
    for _ in range(120):
        p.applyExternalForce(body, -1, [0, 0, 3000.0], [D.REAR_X, 0, 0.02], p.WORLD_FRAME)
        p.stepSimulation()
    report(body, "after rear-up")
    p.disconnect()