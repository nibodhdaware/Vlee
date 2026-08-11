"""Probe: which hydraulic lift side pitches the nose up?

Applies a vertical external force to the base at the front idler hub
(+x) and at the rear sprocket hub (-x) and records the resulting pitch
sign. This decides where the hydraulic press foot goes for the climb.
"""
import os
import math
import pybullet as p

import dynamic_pybullet as D


def fresh():
    D.build_terrain(False, False, False)
    mass, cgx, _ = D.read_static()
    body = D.wheel_urdf(mass, cgx)
    D.p.changeDynamics(body, -1, lateralFriction=1.0)
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
    return body, [j for n, j in joint_idx.items() if "sprocket" in n]


def pitch(body):
    _, q = p.getBasePositionAndOrientation(body)
    return math.degrees(p.getEulerFromQuaternion(q)[1])


def settle(body, n=300):
    for _ in range(n):
        p.stepSimulation()


def trial(body, fx, fz, label):
    """Apply +z force of 9 kN at world (fx, 0, fz) for 1.0 s, log pitch."""
    T = 60 * D.DT
    t = 0.0
    hist = []
    while t < 1.0:
        p.applyExternalForce(body, -1, [0, 0, 1200.0], [fx, 0.0, fz], p.WORLD_FRAME)
        p.stepSimulation()
        t += D.DT
        if t >= 0.4:
            hist.append(pitch(body))
    print(f"{label}: pitch minsig={min(hist):+.2f} max={max(hist):+.2f} end={hist[-1]:+.2f}")


def trial(body, fx, fz, label, sign=1.0):
    """Apply vertical force sign*1200 N at world (fx, 0, fz) for 1.0 s."""
    T = 60 * D.DT
    t = 0.0
    hist = []
    while t < 1.0:
        p.applyExternalForce(body, -1, [0, 0, sign * 1200.0], [fx, 0.0, fz], p.WORLD_FRAME)
        p.stepSimulation()
        t += D.DT
        if t >= 0.4:
            hist.append(pitch(body))
    print(f"{label}: pitch min={min(hist):+.2f} max={max(hist):+.2f} end={hist[-1]:+.2f}")


if __name__ == "__main__":
    cases = [
        ("FRONT press DOWN(var)", D.FRONT_X, -1.0),
        ("REAR press DOWN", D.REAR_X, -1.0),
    ]
    for label, fx, sign in cases:
        body, sp = fresh()
        for _ in range(200):
            p.stepSimulation()
        trial(body, fx, D.BELT_R, label, sign)
        p.disconnect()