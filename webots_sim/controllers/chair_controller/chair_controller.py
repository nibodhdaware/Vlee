"""Tracked Wheelchair stair-climbing mechanism.

Mechanism (as designed):
  - The chassis pivots around the FRONT sprocket (drive sprocket).
  - The hydraulic at the REAR pushes a wheel against the ground, tilting the
    tracks up so the belt aligns with the stair slope.
  - Forward drive pushes the chair; the tilted belt grips and climbs the stairs.
  - Once the tracks have engaged, the hydraulic retracts and the tracks level.

Controls:
  1 = extend hydraulic (tilt tracks up toward stair slope)
  2 = retract hydraulic (tracks level)
  W  = drive forward        S = drive backward
  R  = reset
"""
import os
import math

from controller import Supervisor
from controller import Keyboard

# Guaranteed startup heartbeat
with open(os.path.join(os.path.dirname(__file__), "chair_controller.log"), "w") as f:
    f.write("controller STARTED\n")

robot = Supervisor()
timestep = int(robot.getBasicTimeStep())
keyboard = robot.getKeyboard()
keyboard.enable(timestep)

STAIR_ANGLE = 0.541  # ~31 deg = atan(0.03/0.05) stair slope
TILT_SPEED = 0.8     # rad/s

left_tilt = robot.getMotor("left_tilt")
right_tilt = robot.getMotor("right_tilt")
ls = robot.getPositionSensor("left_tilt_sensor")
rs = robot.getPositionSensor("right_tilt_sensor")
left_tilt.setPosition(float("inf"))
right_tilt.setPosition(float("inf"))
left_tilt.setVelocity(0.0)
right_tilt.setVelocity(0.0)
ls.enable(timestep)
rs.enable(timestep)

body = robot.getFromDef("chair")          # the top node (Robot body)

FORCE = 12.0
target_theta = 0.0
driving = 0.0

print("Tracked chair controller started")
print("  1=hydraulic extend   2=retract   W=forward   S=back   R=reset")

# Check if robot is valid
print(f"Robot node: {robot.getName()}")
print(f"Basic timestep: {timestep}")

while robot.step(timestep) != -1:
    theta = ls.getValue()
    print(f"step theta={theta:.3f}")
    
    with open(os.path.join(os.path.dirname(__file__), "chair_controller.log"), "a") as f:
        f.write(f"step theta={theta:.3f}\n")