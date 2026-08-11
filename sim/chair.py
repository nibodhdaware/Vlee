# Draw the tracked wheelchair geometry using raylib 3D primitives
import math
import raylib as rl
from params import *


def vec3(x, y, z):
    return rl.ffi.new('Vector3 *', {'x': float(x), 'y': float(y), 'z': float(z)})[0]

def color(r, g, b, a=255):
    return rl.ffi.new('Color *', {'r': r, 'g': g, 'b': b, 'a': a})[0]

def col_from_tuple(t, a=255):
    return color(int(t[0]*255), int(t[1]*255), int(t[2]*255), a)


def draw_wheel(pos, radius, width, is_drive=False):
    """Draw a wheel as stacked cylinders."""
    c = C_DARK_STEEL if is_drive else C_STEEL
    p = vec3(pos[0], pos[2], pos[1])
    rl.DrawCylinder(p, radius, radius, int(width), 24, col_from_tuple(c))
    rl.DrawCylinder(p, radius + 1.5, radius + 1.5, int(width), 24, col_from_tuple(C_RUBBER))
    rl.DrawCylinder(p, 3, 3, int(width) + 4, 12, col_from_tuple(C_CHROME))


def draw_track_link(x, z, angle=0):
    """Draw a single track link."""
    rad = math.radians(-angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    w = LINK_LENGTH + 2
    h = LINK_THICKNESS
    d = TRACK_WIDTH + 2
    hw, hd = w / 2, d / 2

    corners_x = [hw, hw, -hw, -hw]
    corners_z = [hd, -hd, -hd, hd]
    rx = [c * cos_a - cz * sin_a for c, cz in zip(corners_x, corners_z)]
    rz = [c * sin_a + cz * cos_a for c, cz in zip(corners_x, corners_z)]

    pad_c = col_from_tuple(C_TRACK_PAD)
    for i in range(4):
        j = (i + 1) % 4
        rl.DrawTriangle3D(
            vec3(x + rx[i], z + h / 2, rz[i]),
            vec3(x + rx[i], z - h / 2, rz[i]),
            vec3(x + rx[j], z - h / 2, rz[j]),
            pad_c)
        rl.DrawTriangle3D(
            vec3(x + rx[i], z + h / 2, rz[i]),
            vec3(x + rx[j], z - h / 2, rz[j]),
            vec3(x + rx[j], z + h / 2, rz[j]),
            pad_c)

    # Guide rib
    rl.DrawCube(vec3(x, z - h / 2 - 0.75, 0),
                LINK_LENGTH - 1, 1.5, 3, col_from_tuple(C_RUBBER))


def track_pos(d):
    """Return (x, z, angle) for a point at distance d along the belt loop."""
    arc_len = math.pi * TRACK_RADIUS
    seg1 = TRACK_LENGTH
    seg2 = TRACK_LENGTH + arc_len
    seg3 = 2 * TRACK_LENGTH + arc_len

    if d < seg1:
        return (-IDLER_X + d, IDLER_Z - TRACK_RADIUS, 0)
    elif d < seg2:
        frac = (d - seg1) / arc_len
        a = -90 + 180 * frac
        rad = math.radians(a)
        return (IDLER_X + TRACK_RADIUS * math.cos(rad),
                IDLER_Z + TRACK_RADIUS * math.sin(rad), a + 90)
    elif d < seg3:
        return (IDLER_X - (d - seg2), IDLER_Z + TRACK_RADIUS, 180)
    else:
        frac = (d - seg3) / arc_len
        a = 90 + 180 * frac
        rad = math.radians(a)
        return (-IDLER_X + TRACK_RADIUS * math.cos(rad),
                IDLER_Z + TRACK_RADIUS * math.sin(rad), a + 90)


def draw_track_belt():
    """Draw all track links."""
    pitch = LINK_LENGTH + 1
    arc_len = math.pi * TRACK_RADIUS
    total = 2 * TRACK_LENGTH + 2 * arc_len
    num_links = int(total / pitch)
    for i in range(num_links):
        x, z, angle = track_pos(i * pitch)
        draw_track_link(x, z, angle)


def draw_track_assembly():
    for x in ROAD_POSITIONS:
        draw_wheel((x, TRACK_CENTER_Y, ROAD_Z), ROAD_RADIUS, TRACK_WIDTH)
    draw_wheel((-IDLER_X, TRACK_CENTER_Y, IDLER_Z), IDLER_RADIUS, TRACK_WIDTH)
    draw_wheel((IDLER_X, TRACK_CENTER_Y, IDLER_Z), IDLER_RADIUS, TRACK_WIDTH, is_drive=True)
    draw_track_belt()


def draw_chassis():
    c = col_from_tuple(C_STEEL)
    for x in ROAD_POSITIONS + [-IDLER_X, IDLER_X]:
        rl.DrawCube(vec3(x, CHASSIS_BOTTOM + CHASSIS_HEIGHT / 2, 0),
                     6, CHASSIS_HEIGHT, TRACK_CENTER_Y * 2 + TRACK_WIDTH, c)
    for side in [-1, 1]:
        y = side * TRACK_CENTER_Y
        rl.DrawCube(vec3(0, CHASSIS_BOTTOM + CHASSIS_HEIGHT / 2, y),
                     CHASSIS_LENGTH, CHASSIS_HEIGHT, 6, c)


def draw_seat_pedestal():
    axle_z = IDLER_Z
    top_z = axle_z + PEDESTAL_HEIGHT
    cc = col_from_tuple(C_STEEL)
    bc = col_from_tuple(C_CHROME)
    pc = col_from_tuple(C_DARK_STEEL)
    for side in [-1, 1]:
        p = vec3(IDLER_X, side * 3, axle_z)
        rl.DrawCylinder(p, 9, 9, 5, 24, cc)
        p2 = vec3(IDLER_X, side * 3, axle_z + 10)
        rl.DrawCylinder(p2, 1.5, 1.5, 8, 12, bc)
    rl.DrawCylinderEx(vec3(IDLER_X, 0, axle_z), vec3(IDLER_X, 0, top_z),
                      COLUMN_RADIUS, COLUMN_RADIUS, 24, cc)
    rl.DrawCube(vec3(IDLER_X, 0, top_z + PLATE_THICKNESS / 2),
                PLATE_SIZE, PLATE_SIZE, PLATE_THICKNESS, pc)


def draw_bucket_seat():
    pedestal_top = IDLER_Z + PEDESTAL_HEIGHT + PLATE_THICKNESS
    ac = col_from_tuple(C_ALUMINUM)
    bc = col_from_tuple(C_CHROME)
    pan_cx = IDLER_X - 14 - SEAT_PAN_LENGTH / 2
    rl.DrawCube(vec3(pan_cx, 0, pedestal_top + 3.5),
                SEAT_PAN_LENGTH, SEAT_PAN_WIDTH, 7, ac)
    rl.DrawCube(vec3(IDLER_X - 14, 0, pedestal_top + 3.5 + BACK_HEIGHT / 2),
                SHELL_THICKNESS + 1, SEAT_PAN_WIDTH, BACK_HEIGHT, ac)
    rl.DrawCube(vec3(IDLER_X - 15, 0, pedestal_top + 3.5 + BACK_HEIGHT + HEADREST_HEIGHT / 2),
                SHELL_THICKNESS + 3, SEAT_PAN_WIDTH - 10, HEADREST_HEIGHT, ac)
    for sx in [-1, 1]:
        for sz in [-1, 1]:
            p = vec3(IDLER_X + sx * 14, 0, pedestal_top - 2.5)
            rl.DrawCylinder(p, 1.5, 1.5, 6, 12, bc)


def draw_footrest():
    c = col_from_tuple(C_STEEL)
    rl.DrawCube(vec3(-IDLER_X - 2, 0, FOOTREST_HEIGHT),
                FOOTREST_LENGTH, FOOTREST_WIDTH, 5, c)
    for side in [-1, 1]:
        rl.DrawCube(vec3(-IDLER_X + 6, side * 12, (IDLER_Z + FOOTREST_HEIGHT) / 2),
                    5, 5, abs(FOOTREST_HEIGHT - IDLER_Z), c)


def draw_hydraulic(extension):
    mount_z = CHASSIS_BOTTOM
    barrel_top = mount_z + HYDR_BARREL_HEIGHT / 2
    rod_bottom = mount_z - extension
    bc = col_from_tuple(C_STEEL)
    cc = col_from_tuple(C_CHROME)
    rc = col_from_tuple(C_RUBBER)
    dc = col_from_tuple(C_DARK_STEEL)

    for side in [-1, 1]:
        rl.DrawCube(vec3(HYDR_MOUNT_X, side * 4, mount_z),
                    12, 2, HYDR_BARREL_HEIGHT + 4, bc)
    p = vec3(HYDR_MOUNT_X, 0, mount_z)
    rl.DrawCylinder(p, HYDR_BARREL_RADIUS, HYDR_BARREL_RADIUS, HYDR_BARREL_HEIGHT, 24, bc)
    if extension > 0:
        rl.DrawCylinderEx(vec3(HYDR_MOUNT_X, 0, barrel_top),
                          vec3(HYDR_MOUNT_X, 0, rod_bottom),
                          HYDR_ROD_RADIUS, HYDR_ROD_RADIUS, 16, cc)
        for side in [-1, 1]:
            pw = vec3(HYDR_MOUNT_X, side * 7, rod_bottom)
            rl.DrawCylinder(pw, HYDR_WHEEL_RADIUS, HYDR_WHEEL_RADIUS, HYDR_WHEEL_WIDTH, 24, rc)
        pa = vec3(HYDR_MOUNT_X, 0, rod_bottom)
        rl.DrawCylinder(pa, 1.5, 1.5, 20, 12, dc)


def draw_stairs():
    c = col_from_tuple(C_STAIR)
    for i in range(NUM_STEPS):
        x = IDLER_X + 30 + i * STAIR_RUN
        z = GROUND_Z - STAIR_RISE * (i + 1)
        rl.DrawCube(vec3(x, 0, z), STAIR_RUN, STAIR_WIDTH, STAIR_RISE, c)


def draw_ground():
    c = col_from_tuple(C_GROUND)
    rl.DrawCube(vec3(0, 0, GROUND_Z - 0.5), 300, STAIR_WIDTH + 40, 1, c)
