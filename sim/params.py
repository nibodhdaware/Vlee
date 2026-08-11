# Parameters matching the OpenSCAD prototype
import math

# ===================== TRACKS =====================
TRACK_LENGTH = 96
TRACK_WIDTH = 16
TRACK_CENTER_Y = 28

IDLER_RADIUS = 12
IDLER_X = TRACK_LENGTH / 2  # 48
IDLER_Z = 22
ROAD_RADIUS = 9
ROAD_Z = 16
ROAD_POSITIONS = [-28, -8, 8, 28]

LINK_LENGTH = 10
LINK_THICKNESS = 3
TRACK_RADIUS = IDLER_RADIUS + LINK_THICKNESS / 2 + 2  # 15.5
GROUND_Z = IDLER_Z - TRACK_RADIUS  # 6.5

# ===================== HYDRAULIC =====================
HYDR_WHEEL_RADIUS = 4
HYDR_WHEEL_WIDTH = 10
HYDR_BARREL_RADIUS = 5
HYDR_BARREL_HEIGHT = 14
HYDR_ROD_RADIUS = 2.5
HYDR_EXTEND = 42
HYDR_MOUNT_X = 28
HYDR_MOUNT_Y = 0

# ===================== CHASSIS =====================
CHASSIS_LENGTH = 92
CHASSIS_BOTTOM = 44
CHASSIS_HEIGHT = 14

# ===================== SEAT =====================
PEDESTAL_HEIGHT = 24
COLUMN_RADIUS = 6
PLATE_SIZE = 42
PLATE_THICKNESS = 5

SEAT_PAN_LENGTH = 72
SEAT_PAN_WIDTH = 72
BACK_HEIGHT = 76
HEADREST_HEIGHT = 18
SHELL_THICKNESS = 5

# ===================== FOOTREST =====================
FOOTREST_WIDTH = 38
FOOTREST_LENGTH = 36
FOOTREST_HEIGHT = IDLER_Z + 12

# ===================== STAIRS =====================
STAIR_RISE = 18
STAIR_RUN = 24
NUM_STEPS = 5
STAIR_WIDTH = 80
STAIR_ANGLE = 25  # degrees

# ===================== COLORS (R,G,B 0-1) =====================
C_STEEL = (0.35, 0.36, 0.38)
C_DARK_STEEL = (0.25, 0.26, 0.28)
C_RUBBER = (0.12, 0.12, 0.14)
C_ALUMINUM = (0.55, 0.57, 0.60)
C_CHROME = (0.70, 0.72, 0.75)
C_TRACK_PAD = (0.15, 0.15, 0.17)
C_STAIR = (0.45, 0.42, 0.40)
C_GROUND = (0.30, 0.30, 0.28)

# ===================== EASING =====================
def ease_in_out(t, lo, hi):
    """Bell curve: 0 -> 1 -> 0 over [lo, hi]"""
    n = (t - lo) / (hi - lo) if hi != lo else 0
    if n <= 0 or n >= 1:
        return 0
    return (1 - math.cos(n * math.pi)) / 2
