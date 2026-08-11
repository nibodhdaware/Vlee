# Tracked wheelchair — physics simulation
# Run: python physics_sim.py
import math
import raylib as rl
from params import *
from chair import *

SCREEN_W = 1280
SCREEN_H = 720

def col(r, g, b, a=255):
    return rl.ffi.new('Color *', {'r': r, 'g': g, 'b': b, 'a': a})[0]

rl.InitWindow(SCREEN_W, SCREEN_H, b"Tracked Wheelchair - Physics Sim")
rl.SetTargetFPS(60)

cam = rl.ffi.new('Camera3D *', {
    'position': {'x': 0.0, 'y': 80.0, 'z': 200.0},
    'target':   {'x': 0.0, 'y': 30.0, 'z': 0.0},
    'up':       {'x': 0.0, 'y': 0.0, 'z': 1.0},
    'fovy': 45.0,
    'projection': rl.CAMERA_PERSPECTIVE
})[0]

# ===================== PHYSICS STATE =====================
# Chair position and orientation
chair_x = 0.0        # horizontal position
chair_z = 0.0        # vertical position (height)
chair_angle = 0.0    # tilt angle in degrees (positive = rear up, front down)

# Velocities
chair_vx = 0.0
chair_vz = 0.0
chair_va = 0.0       # angular velocity (deg/s)

# Hydraulic state
hydr_extension = 0.0  # current extension in mm
hydr_target = 0.0     # target extension
hydr_speed = 80.0     # mm/s extension speed

# Physics constants
GRAVITY = -400.0       # mm/s² downward
MASS = 50.0            # kg (total chair + passenger weight)
INERTIA = 8000.0       # moment of inertia (kg·mm²)
FRICTION = 0.7         # ground friction coefficient
BOUNCE = 0.2           # restitution

# Pivot geometry
PIVOT_X = IDLER_X      # front sprocket is the pivot point
PIVOT_Z = IDLER_Z

# Hydraulic geometry
HYDR_ARM = PIVOT_X - HYDR_MOUNT_X  # horizontal distance from pivot to hydraulic

# Track contact points (simplified as 4 points along the bottom of each track)
# These are the points that can touch the ground or stairs
TRACK_CONTACTS_X = [-IDLER_X, -28, -8, 8, 28, IDLER_X]

# Stair geometry
def stair_height_at(x):
    """Return the height of the stair surface at horizontal position x."""
    for i in range(NUM_STEPS):
        step_left = IDLER_X + 30 + i * STAIR_RUN
        step_right = step_left + STAIR_RUN
        if step_left <= x <= step_right:
            return GROUND_Z - STAIR_RISE * (i + 1)
    return GROUND_Z

def stair_normal_at(x):
    """Return the normal vector of the stair surface at x."""
    for i in range(NUM_STEPS):
        step_left = IDLER_X + 30 + i * STAIR_RUN
        step_right = step_left + STAIR_RUN
        if step_left <= x <= step_right:
            # Flat surface, normal points up
            return (0.0, 0.0, 1.0)
    # Ground
    return (0.0, 0.0, 1.0)

# ===================== CONTROLS =====================
hydr_extending = False
hydr_retracting = False
drive_forward = False
drive_backward = False

# ===================== SIMULATION =====================
def get_track_contact_world(contact_idx, chair_x, chair_z, chair_angle):
    """Get world-space position of a track contact point."""
    # Contact point in chair-local coordinates
    local_x = TRACK_CONTACTS_X[contact_idx]
    local_z = GROUND_Z - chair_z  # relative to chair center

    # Rotate by chair angle around pivot
    rad = math.radians(chair_angle)
    # Transform: first translate to pivot, rotate, translate back
    dx = local_x - PIVOT_X
    dz = local_z - PIVOT_Z
    world_x = chair_x + PIVOT_X + dx * math.cos(rad) - dz * math.sin(rad)
    world_z = chair_z + PIVOT_Z + dx * math.sin(rad) + dz * math.cos(rad)
    return world_x, world_z

def get_hydraulic_contact_world(chair_x, chair_z, chair_angle):
    """Get world-space position of the hydraulic wheel contact point."""
    local_x = HYDR_MOUNT_X
    local_z = GROUND_Z - chair_z - hydr_extension

    rad = math.radians(chair_angle)
    dx = local_x - PIVOT_X
    dz = local_z - PIVOT_Z
    world_x = chair_x + PIVOT_X + dx * math.cos(rad) - dz * math.sin(rad)
    world_z = chair_z + PIVOT_Z + dx * math.sin(rad) + dz * math.cos(rad)
    return world_x, world_z

def simulate(dt):
    global chair_x, chair_z, chair_angle
    global chair_vx, chair_vz, chair_va
    global hydr_extension

    # --- Update hydraulic ---
    if hydr_extending:
        hydr_extension = min(hydr_extension + hydr_speed * dt, HYDR_EXTEND)
    if hydr_retracting:
        hydr_extension = max(hydr_extension - hydr_speed * dt, 0)

    # --- Compute forces ---

    # 1. Gravity on center of mass
    # Center of mass is roughly at chair center
    force_gravity_z = MASS * GRAVITY

    # 2. Hydraulic force: when extending, pushes against ground
    # The hydraulic wheels contact the ground. When extending,
    # they push down, ground pushes back up.
    # This creates a torque around the pivot.
    hydr_force = 0
    if hydr_extension > 0:
        hw_x, hw_z = get_hydraulic_contact_world(chair_x, chair_z, chair_angle)
        ground_z = stair_height_at(hw_x)
        penetration = ground_z - hw_z  # positive = penetrating ground

        if penetration > 0 and hydr_extending:
            # Ground pushes back up — this is the lifting force
            hydr_force = penetration * 5000  # spring constant
            # Torque around pivot: force * horizontal arm
            arm_x = hw_x - (chair_x + PIVOT_X)
            torque_hydr = hydr_force * arm_x
        elif penetration > 0:
            # Just sitting on ground
            hydr_force = penetration * 3000
            arm_x = hw_x - (chair_x + PIVOT_X)
            torque_hydr = hydr_force * arm_x
        else:
            torque_hydr = 0
    else:
        torque_hydr = 0

    # 3. Track contact forces
    # Each track contact point that touches ground/stairs gets a contact force
    total_contact_force_z = 0
    total_torque = 0

    for i in range(len(TRACK_CONTACTS_X)):
        cx, cz = get_track_contact_world(i, chair_x, chair_z, chair_angle)
        ground_z = stair_height_at(cx)
        penetration = ground_z - cz

        if penetration > 0:
            # Contact force (spring + damping)
            contact_force = penetration * 4000  # spring
            contact_force -= chair_vz * 200      # damping

            # Friction force (horizontal)
            friction_force = -chair_vx * FRICTION * 1000

            total_contact_force_z += contact_force

            # Torque around pivot
            arm_x = cx - (chair_x + PIVOT_X)
            total_torque += contact_force * arm_x

    # 4. Drive force (when driving forward/backward)
    drive_force_x = 0
    if drive_forward:
        drive_force_x = 2000  # N
    elif drive_backward:
        drive_force_x = -2000

    # --- Integrate ---
    # Linear acceleration
    accel_x = drive_force_x / MASS
    accel_z = (force_gravity_z + total_contact_force_z + hydr_force) / MASS

    # Angular acceleration
    # Gravity torque: weight acts at center of mass (roughly PIVOT_X from pivot)
    gravity_torque = MASS * GRAVITY * 0  # center of mass at pivot = no torque
    total_angular_torque = total_torque + torque_hydr + gravity_torque

    # Damping
    damping_torque = -chair_va * 500
    total_angular_torque += damping_torque

    angular_accel = total_angular_torque / INERTIA

    # Euler integration
    chair_vx += accel_x * dt
    chair_vz += accel_z * dt
    chair_va += angular_accel * dt

    # Damping
    chair_vx *= 0.98
    chair_vz *= 0.98
    chair_va *= 0.98

    chair_x += chair_vx * dt
    chair_z += chair_vz * dt
    chair_angle += chair_va * dt

    # Clamp angle
    chair_angle = max(-45, min(45, chair_angle))

    # Don't let chair fall through ground
    if chair_z < 0:
        chair_z = 0
        chair_vz = max(0, chair_vz)

# ===================== MAIN LOOP =====================
while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()

    # --- Input ---
    if rl.IsKeyPressed(rl.KEY_ONE):
        hydr_extending = True
        hydr_retracting = False
    if rl.IsKeyPressed(rl.KEY_TWO):
        hydr_retracting = True
        hydr_extending = False
    if rl.IsKeyReleased(rl.KEY_ONE) and hydr_extending:
        hydr_extending = False
    if rl.IsKeyReleased(rl.KEY_TWO) and hydr_retracting:
        hydr_retracting = False

    drive_forward = rl.IsKeyDown(rl.KEY_UP)
    drive_backward = rl.IsKeyDown(rl.KEY_DOWN)

    if rl.IsKeyPressed(rl.KEY_R):
        chair_x = 0; chair_z = 0; chair_angle = 0
        chair_vx = 0; chair_vz = 0; chair_va = 0
        hydr_extension = 0

    # --- Physics ---
    simulate(dt)

    # --- Draw ---
    rl.BeginDrawing()
    rl.ClearBackground(col(20, 22, 28))
    rl.BeginMode3D(cam)

    draw_ground()
    draw_stairs()

    # Draw chair
    rl.rlPushMatrix()
    rl.rlTranslatef(chair_x, 0, chair_z)

    # Pivot around front sprocket
    rl.rlPushMatrix()
    rl.rlTranslatef(PIVOT_X, 0, PIVOT_Z)
    rl.rlRotatef(-chair_angle, 0, 1, 0)
    rl.rlTranslatef(-PIVOT_X, 0, -PIVOT_Z)

    for side in [-1, 1]:
        rl.rlPushMatrix()
        rl.rlTranslatef(0, side * TRACK_CENTER_Y, 0)
        draw_track_assembly()
        rl.rlPopMatrix()

    draw_chassis()
    draw_seat_pedestal()
    draw_bucket_seat()
    draw_footrest()
    draw_hydraulic(hydr_extension)

    rl.rlPopMatrix()  # end pivot
    rl.rlPopMatrix()  # end translate

    rl.EndMode3D()

    # ===================== HUD =====================
    rl.DrawRectangle(10, 10, 340, 180, col(0, 0, 0, 160))
    rl.DrawText(b"PHYSICS SIMULATION", 20, 20, 16, col(245, 245, 245))
    rl.DrawText(b"[1] Extend hydraulic", 20, 48, 14, col(200, 200, 200))
    rl.DrawText(b"[2] Retract hydraulic", 20, 68, 14, col(200, 200, 200))
    rl.DrawText(b"[UP/DOWN] Drive", 20, 88, 14, col(200, 200, 200))
    rl.DrawText(b"[R] Reset", 20, 108, 14, col(200, 200, 200))
    rl.DrawText(b"Hydraulic: " + str(int(hydr_extension)).encode() + b"mm", 20, 138, 14, col(80, 180, 80))
    rl.DrawText(b"Tilt: " + str(round(chair_angle, 1)).encode() + b" deg", 20, 158, 14, col(80, 180, 80))
    rl.DrawText(b"Height: " + str(round(chair_z, 1)).encode() + b"mm", 20, 178, 14, col(80, 180, 80))

    rl.EndDrawing()

rl.CloseWindow()
