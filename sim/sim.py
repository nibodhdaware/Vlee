# Tracked wheelchair stair-climbing simulation
# Run: python sim.py
import math
import raylib as rl
from params import *
from chair import *

SCREEN_W = 1280
SCREEN_H = 720

def col(r, g, b, a=255):
    return rl.ffi.new('Color *', {'r': r, 'g': g, 'b': b, 'a': a})[0]

def col_tuple(t, a=255):
    return col(int(t[0]*255), int(t[1]*255), int(t[2]*255), a)

rl.InitWindow(SCREEN_W, SCREEN_H, b"Tracked Wheelchair Simulation")
rl.SetTargetFPS(60)

cam = rl.ffi.new('Camera3D *', {
    'position': {'x': 80.0, 'y': 200.0, 'z': 250.0},
    'target':   {'x': 0.0,  'y': 0.0,   'z': 40.0},
    'up':       {'x': 0.0,  'y': 0.0,   'z': 1.0},
    'fovy': 45.0,
    'projection': rl.CAMERA_PERSPECTIVE
})[0]

t = 0.0
speed = 0.3
paused = False
show_hydraulic = True

C_BLACK_A = col(0, 0, 0, 160)
C_BG      = col(20, 22, 28)
C_WHITE   = col(245, 245, 245)
C_LGRAY   = col(200, 200, 200)
C_YELLOW  = col(253, 249, 0)
C_GRAY    = col(130, 130, 130)
C_BAR_BG  = col(40, 40, 40)
C_BAR_FG  = col(80, 180, 80)

# ===================== GEOMETRY CONSTANTS =====================
# Pivot: front drive sprocket (everything rotates around this point)
PIVOT_X = IDLER_X    # 48
PIVOT_Z = IDLER_Z    # 22

# Hydraulic is at the rear of the chassis
# When it extends, it pushes against the ground and lifts the rear
# The triangle: pivot (front) --- hydraulic (rear) --- ground contact
HYDR_GROUND_X = HYDR_MOUNT_X  # where hydraulic meets ground horizontally
HYDR_ARM = PIVOT_X - HYDR_GROUND_X  # horizontal distance from pivot to hydraulic

# How many degrees the chair tilts per mm of hydraulic extension
# tan(angle) = extension / arm, so angle = atan(extension / arm)
def tilt_from_extension(ext):
    """Compute tilt angle (degrees) from hydraulic extension."""
    if ext <= 0:
        return 0
    return math.degrees(math.atan2(ext, HYDR_ARM))

# Stair alignment: front of tracks must touch the stair edge
# When tilted, the front of the tracks drops by:
#   dz = (trackLength) * sin(tilt)  (front droops)
# The rear rises by:
#   dz = (trackLength) * sin(tilt)  (rear lifts)
# For the tracks to land on the stairs, the chair must also translate

while not rl.WindowShouldClose():
    if rl.IsKeyPressed(rl.KEY_SPACE):
        paused = not paused
    if rl.IsKeyPressed(rl.KEY_H):
        show_hydraulic = not show_hydraulic
    if rl.IsKeyDown(rl.KEY_LEFT):
        speed = max(0.05, speed - 0.01)
    if rl.IsKeyDown(rl.KEY_RIGHT):
        speed = min(2.0, speed + 0.01)
    if rl.IsKeyPressed(rl.KEY_R):
        t = 0.0

    if not paused:
        t += rl.GetFrameTime() * speed
        if t > 1.0:
            t -= 1.0

    # ===================== ANIMATION CURVES =====================
    # Phase 1 (0.00-0.15): Idle
    # Phase 2 (0.15-0.35): Hydraulic extends, chair tilts (triangle forms)
    # Phase 3 (0.35-0.50): Align tracks to stairs
    # Phase 4 (0.50-0.80): Hydraulic retracts, tracks land on stairs, chair climbs
    # Phase 5 (0.80-0.95): Level out at top
    # Phase 6 (0.95-1.00): Idle at top

    # Hydraulic extension: extends during phase 2, retracts during phase 4
    hydr_pct = ease_in_out(t, 0.15, 0.35) - ease_in_out(t, 0.50, 0.80)
    hydr_ext = hydr_pct * HYDR_EXTEND

    # Tilt angle: driven by hydraulic extension
    tilt = tilt_from_extension(max(0, hydr_ext))

    # ===================== CHAIR POSITION =====================
    # The chair needs to translate so the tracks land on the stairs.
    # When tilted, the front of the tracks drops toward the stair.
    # We need to figure out where the tracks touch the first step.
    
    # First step position
    step1_x = IDLER_X + 30  # front edge of first step
    step1_z = GROUND_Z - STAIR_RISE  # top of first step

    # When tilted by `tilt` degrees around the pivot:
    # The rear idler (at -IDLER_X from center, PIVOT_Z height) moves to:
    #   new_z = PIVOT_Z + (-IDLER_X - PIVOT_X) * sin(-tilt_rad)
    #   ... complex geometry. Simplify:
    # We want the bottom of the tracks (at ground level) to touch the stair edge.
    # The track bottom is at GROUND_Z. When tilted, the lowest point of the track
    # shifts. For small angles, the front drops and rear rises.
    
    # Approach: translate the chair so the track bottom aligns with the stair edge
    tilt_rad = math.radians(tilt)

    # During climbing (phase 4), translate along the stairs
    if t < 0.50:
        climb_x = 0
        climb_z = 0
    elif t < 0.80:
        progress = (t - 0.50) / 0.30
        climb_x = progress * (NUM_STEPS * STAIR_RUN * 0.5)
        climb_z = progress * (NUM_STEPS * STAIR_RISE * 0.5)
    else:
        climb_x = NUM_STEPS * STAIR_RUN * 0.5
        climb_z = NUM_STEPS * STAIR_RISE * 0.5

    # ===================== DRAW =====================
    rl.BeginDrawing()
    rl.ClearBackground(C_BG)
    rl.BeginMode3D(cam)

    draw_ground()
    draw_stairs()

    # Draw the chair — everything pivots around the front sprocket
    rl.rlPushMatrix()

    # Translate for climbing
    rl.rlTranslatef(climb_x, 0, climb_z)

    # Pivot around the front sprocket — rear lifts when hydraulic extends
    rl.rlPushMatrix()
    rl.rlTranslatef(PIVOT_X, 0, PIVOT_Z)
    rl.rlRotatef(-tilt, 0, 1, 0)  # negative = rear lifts
    rl.rlTranslatef(-PIVOT_X, 0, -PIVOT_Z)

    # Draw all parts — they all rotate together
    for side in [-1, 1]:
        rl.rlPushMatrix()
        rl.rlTranslatef(0, side * TRACK_CENTER_Y, 0)
        draw_track_assembly()
        rl.rlPopMatrix()

    draw_chassis()
    draw_seat_pedestal()
    draw_bucket_seat()
    draw_footrest()
    if show_hydraulic:
        draw_hydraulic(hydr_ext)

    rl.rlPopMatrix()  # end pivot
    rl.rlPopMatrix()  # end climb translate

    rl.EndMode3D()

    # ===================== HUD =====================
    rl.DrawRectangle(10, 10, 320, 130, C_BLACK_A)
    rl.DrawText(b"TRACKED WHEELCHAIR SIM", 20, 20, 16, C_WHITE)
    phase = (b"Idle" if t < 0.15
             else b"Extending hydraulic" if t < 0.35
             else b"Aligning to stairs" if t < 0.50
             else b"Climbing" if t < 0.80
             else b"Leveling" if t < 0.95
             else b"Done")
    rl.DrawText(b"Phase: " + phase, 20, 44, 14, C_LGRAY)
    rl.DrawText(b"Hydraulic: " + str(int(hydr_ext)).encode() + b"mm", 20, 64, 14, C_LGRAY)
    rl.DrawText(b"Tilt: " + str(round(tilt, 1)).encode() + b" deg", 20, 84, 14, C_LGRAY)
    rl.DrawText(b"Speed: " + str(round(speed, 2)).encode() + b"x", 20, 104, 14, C_LGRAY)
    status = b"PAUSED" if paused else b"PLAYING"
    rl.DrawText(b"[SPACE] " + status, 20, 124, 14, C_YELLOW)

    rl.DrawRectangle(10, SCREEN_H - 50, 380, 40, C_BLACK_A)
    rl.DrawText(b"[SPACE] Pause  [R] Reset  [H] Hydraulic  [<->] Speed", 20, SCREEN_H - 40, 12, C_GRAY)

    bar_w = 300
    bar_x = (SCREEN_W - bar_w) / 2
    rl.DrawRectangle(int(bar_x), SCREEN_H - 20, bar_w, 10, C_BAR_BG)
    rl.DrawRectangle(int(bar_x), SCREEN_H - 20, int(bar_w * t), 10, C_BAR_FG)

    rl.EndDrawing()

rl.CloseWindow()
