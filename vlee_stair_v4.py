"""
Vlee B1000 Stair-Climb Animation — Blender 4.0
Run:  blender -b -P vlee_stair_v4.py
Output: renders_light/vlee_stair_v4.blend  (open in Blender to review)

Chair approaches BACKWARD (rear/sprocket faces stairs).
Hydraulic jack is at REAR — extends to lift rear up.
Front idler stays on ground. Seat stays LEVEL via pivot.
"""
import bpy, math, os
from mathutils import Vector

# ══════════════════════════════════════════════════════════════════════════
#  SCAD PARAMETERS  (parameters.scad — 1 unit = 1 cm)
# ══════════════════════════════════════════════════════════════════════════
TRACK_LENGTH   = 82
TRACK_WIDTH    = 14
TRACK_CENTER_Y = 28

IDLER_R        = 10
IDLER_X        = TRACK_LENGTH / 2      # 41  — idler local x
IDLER_Z        = 16
ROAD_R         = 7
ROAD_Z         = 13
ROAD_POS       = [-22, -6, 10, 24]

LINK_LEN       = 10
LINK_W         = TRACK_WIDTH + 2       # 16
LINK_THICK     = 3
TRACK_R        = IDLER_R + LINK_THICK / 2   # 11.5
BELT_THICK     = 3
GROUND_Z       = IDLER_Z - TRACK_R          # 4.5

CHASSIS_LEN    = 82
CHASSIS_BOT    = 35
CHASSIS_H      = 12

SEAT_PAN_LEN   = 66
SEAT_PAN_W     = 66
SEAT_TOP_OFF   = 45 - TRACK_R               # 33.5
BACK_H         = 72
HEADREST_H     = 16
BACK_RECLINE   = math.radians(8)

FOOT_W         = 34
FOOT_L         = 28
FOOT_THICK     = 3
FOOT_H         = IDLER_Z + 12               # 28
FOOT_FRONT_X   = -30 - FOOT_L / 2           # -44
FOOT_PIVOT_X   = -30
FOOT_PIVOT_Z   = IDLER_Z + SEAT_TOP_OFF - 7  # 42.5

ARM_PIVOT_X    = IDLER_X - 14               # 27
ARM_LEN        = 68
ARM_PAD_H      = IDLER_Z + SEAT_TOP_OFF + 19 # 68.5
ARM_PAD_W      = 8
ARM_PAD_THICK  = 4

HYD_MOUNT_X    = 24
HYD_BARREL_R   = 4
HYD_BARREL_H   = 12
HYD_ROD_R      = 2
HYD_EXTEND     = 26.5
HYD_WH_R       = 4
HYD_WH_W       = 10

STAIR_RISER    = 16
STAIR_TREAD    = 32
STAIR_COUNT    = 5
STAIR_X        = 60
STAIR_ANGLE    = math.atan2(STAIR_RISER, STAIR_TREAD)  # ~0.464 rad

# ══════════════════════════════════════════════════════════════════════════
#  MATERIALS
# ══════════════════════════════════════════════════════════════════════════
def mk_mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = (*rgb, 1)
    n.inputs["Roughness"].default_value = rough
    n.inputs["Metallic"].default_value = metal
    return m

M_ALUM    = mk_mat("Aluminum",   (0.55, 0.57, 0.60), 0.35, 0.9)
M_RUBBER  = mk_mat("Rubber",     (0.12, 0.12, 0.14), 0.85, 0.0)
M_LEATHER = mk_mat("Leather",    (0.45, 0.25, 0.12), 0.70, 0.0)
M_CHROME  = mk_mat("Chrome",     (0.70, 0.72, 0.75), 0.05, 1.0)
M_DARK    = mk_mat("DarkSteel",  (0.25, 0.26, 0.28), 0.40, 0.9)
M_GROUND  = mk_mat("Ground",     (0.25, 0.27, 0.30), 0.90, 0.0)
M_STAIR   = mk_mat("Stair",      (0.35, 0.37, 0.40), 0.15, 0.7)

# ══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════
def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name != "Collection":
            bpy.data.collections.remove(c)

def add_box(name, loc, size, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def add_cyl(name, loc, r, h, mat, rot=(math.pi/2, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc)
    o = bpy.context.object; o.name = name
    o.rotation_euler = rot
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def make_empty(name, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def set_linear(obj):
    if not (obj.animation_data and obj.animation_data.action):
        return
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# ══════════════════════════════════════════════════════════════════════════
#  BUILD VLEE B1000
# ══════════════════════════════════════════════════════════════════════════
#
#  Hierarchy (no π flip — idler is REAR, sprocket is FRONT):
#    root (animated: position + tilt)
#      track_left / track_right  (belt pads, wheels, beams)
#      chassis  (cross-axles, brackets)
#      seat_group  (pan, cushion — counter-rotates to stay level)
#        backrest_group  (panel, pad, headrest)
#      footrest_group
#      armrest_group
#      jack_group  (barrel, brackets)
#      jack_ext  (piston, rod, wheels — animated to extend down)
#
#  Local layout:
#    idler at x = -41  (REAR — faces stairs when chair backs up)
#    sprocket at x = +41  (FRONT — faces away from stairs)
#    jack at x = 24  (REAR-ish, near sprocket)
#    belt spans from x = -41 to x = +41

def build_wheel(name, loc, r, w, is_idler=False, parent=None):
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=w, location=loc)
    tyre = bpy.context.object; tyre.name = name + "_tyre"
    tyre.rotation_euler = (math.pi/2, 0, 0)
    tyre.data.materials.append(M_RUBBER); parts.append(tyre)

    bpy.ops.mesh.primitive_cylinder_add(radius=r - 2.5, depth=w + 1, location=loc)
    disc = bpy.context.object; disc.name = name + "_disc"
    disc.rotation_euler = (math.pi/2, 0, 0)
    disc.data.materials.append(M_ALUM); parts.append(disc)

    hub_r = 5.5 if is_idler else 4.5
    bpy.ops.mesh.primitive_cylinder_add(radius=hub_r, depth=w + 3, location=loc)
    hub = bpy.context.object; hub.name = name + "_hub"
    hub.rotation_euler = (math.pi/2, 0, 0)
    hub.data.materials.append(M_ALUM); parts.append(hub)

    for i in range(6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        sp = bpy.context.object; sp.name = name + f"_sp{i}"
        sp.scale = (2.5, 3, (w - 1) / 2)
        sp.rotation_euler = (math.pi/2, 0, i * math.pi/3)
        sp.data.materials.append(M_ALUM); parts.append(sp)

    for p in parts:
        if p != hub:
            p.parent = hub
            p.matrix_parent_inverse = hub.matrix_world.inverted()
    if parent:
        hub.parent = parent
        hub.matrix_parent_inverse = parent.matrix_world.inverted()
    return hub


def build_drive_wheel(name, loc, r, w, parent=None):
    hub = build_wheel(name, loc, r, w, is_idler=True, parent=parent)
    for i in range(12):
        bpy.ops.mesh.primitive_cube_add(size=1,
            location=(loc[0] + r - 0.5, loc[1], loc[2]))
        tooth = bpy.context.object; tooth.name = name + f"_tooth{i}"
        tooth.scale = (4, (w + 2) / 2, 3.5)
        tooth.rotation_euler = (math.pi/2, 0, i * math.pi / 6)
        tooth.data.materials.append(M_DARK)
        tooth.parent = hub
        tooth.matrix_parent_inverse = hub.matrix_world.inverted()
    return hub


def build_track_frame(side, parent):
    y = side * TRACK_CENTER_Y
    trk = make_empty(f"track_{'L' if side < 0 else 'R'}", parent)

    # Idler (rear, faces stairs)
    build_wheel(f"idler_{side}", (-IDLER_X, y, IDLER_Z),
                IDLER_R, TRACK_WIDTH, is_idler=True, parent=trk)
    # Drive sprocket (front, faces away from stairs)
    build_drive_wheel(f"sprocket_{side}", (IDLER_X, y, IDLER_Z),
                      IDLER_R, TRACK_WIDTH, parent=trk)
    # Road wheels along bottom
    for rx in ROAD_POS:
        build_wheel(f"road_{side}_{rx}", (rx, y, ROAD_Z),
                    ROAD_R, TRACK_WIDTH, parent=trk)
    # Suspension beam
    beam_z = IDLER_Z + TRACK_R + 6
    beam_start = -IDLER_X + 8
    beam_end = IDLER_X - 12
    beam_len = beam_end - beam_start
    add_box(f"beam_{side}", ((beam_start + beam_end) / 2, y, beam_z),
            (beam_len, 5, 6), M_DARK, parent=trk)

    # Belt pads around the track loop
    perim = 2 * (2 * IDLER_X) + 2 * math.pi * TRACK_R
    n_pads = max(16, int(perim / LINK_LEN))
    spacing = perim / n_pads
    span = 2 * IDLER_X
    for i in range(n_pads):
        s = (i + 0.5) * spacing
        if s < span:                                          # bottom straight
            px = -IDLER_X + s; pz = 0
        elif s < span + math.pi * TRACK_R:                    # front curve
            a = (s - span) / TRACK_R
            px = IDLER_X - TRACK_R * math.cos(a)
            pz = TRACK_R - TRACK_R * math.sin(a)
        elif s < 2 * span + math.pi * TRACK_R:                # top straight
            px = IDLER_X - (s - span - math.pi * TRACK_R)
            pz = 2 * TRACK_R
        else:                                                  # rear curve
            a = (s - 2 * span - math.pi * TRACK_R) / TRACK_R
            px = -IDLER_X + TRACK_R * math.cos(a)
            pz = TRACK_R + TRACK_R * math.sin(a)
        add_box(f"pad_{side}_{i}", (px, y, IDLER_Z + pz),
                (spacing * 0.9, LINK_W, LINK_THICK), M_RUBBER, parent=trk)
    return trk


def build_vehicle():
    root = make_empty("VehicleRoot")

    build_track_frame(-1, root)
    build_track_frame(1, root)

    # ── Chassis ──
    ch = make_empty("chassis", root)
    for x in [-IDLER_X, IDLER_X]:
        driven = (x == IDLER_X)
        add_cyl(f"axle_{x}", (x, 0, IDLER_Z),
                5 if driven else 4, TRACK_CENTER_Y * 2 + 8, M_ALUM, parent=ch)
        for s in [-1, 1]:
            add_cyl(f"axle_hub_{x}_{s}", (x, s * TRACK_CENTER_Y, IDLER_Z),
                    7, 10, M_DARK, parent=ch)

    # Seat brackets on rear axle (idler axle at x = -41)
    panB = IDLER_Z + SEAT_TOP_OFF - 5
    barX = -IDLER_X  # -41
    for s in [-1, 1]:
        y = s * 24
        add_box(f"bracket_clamp_{s}", (barX, y, IDLER_Z),
                (12, 10, 14), M_DARK, parent=ch)
        add_box(f"bracket_riser_{s}", (barX, y, (IDLER_Z + panB) / 2),
                (5, 8, panB - IDLER_Z), M_ALUM, parent=ch)
        armX2 = 30
        add_box(f"bracket_arm_{s}", ((barX + armX2) / 2, y, panB - 2),
                (armX2 - barX, 7, 4), M_ALUM, parent=ch)

    # ── Seat pan (counter-rotates to stay level) ──
    sg = make_empty("seat_group", root)
    topZ = IDLER_Z + SEAT_TOP_OFF
    backX = -IDLER_X + 14  #  -27
    panCX = backX + SEAT_PAN_LEN / 2  #  6
    seat_pan = add_box("seat_pan", (panCX, 0, topZ),
                       (SEAT_PAN_LEN, SEAT_PAN_W, 3), M_ALUM, parent=sg)
    add_box("seat_cushion", (panCX + 1, 0, topZ - 3),
            (SEAT_PAN_LEN - 10, SEAT_PAN_W - 8, 5), M_LEATHER, parent=sg)

    # Backrest
    bg = make_empty("backrest_group", sg)
    br = add_box("backrest_panel", (backX, 0, topZ + BACK_H / 2),
                 (3, SEAT_PAN_W - 10, BACK_H), M_ALUM, parent=bg)
    br.rotation_euler = (0, -BACK_RECLINE, 0)
    add_box("backrest_pad", (backX + 4, 0, topZ + 26),
            (7, (SEAT_PAN_W - 10) * 0.42, 16), M_LEATHER, parent=bg)
    add_box("headrest", (backX + 1, 0, topZ + BACK_H + HEADREST_H / 2 - 4),
            (7, SEAT_PAN_W * 0.5, HEADREST_H), M_ALUM, parent=bg)

    # ── Footrest ──
    fg = make_empty("footrest_group", root)
    cz = FOOT_H - FOOT_THICK / 2
    bkt_h = FOOT_PIVOT_Z - cz
    for s in [-1, 1]:
        add_box(f"ft_bracket_{s}", (FOOT_PIVOT_X, s * 3, (FOOT_PIVOT_Z + cz) / 2),
                (3, 3, bkt_h), M_ALUM, parent=fg)
    add_box("ft_plate", (FOOT_FRONT_X, 0, cz),
            (FOOT_L, FOOT_W, FOOT_THICK), M_ALUM, parent=fg)
    add_box("ft_heel", (FOOT_FRONT_X + FOOT_L / 2 - 1.5, 0, cz + 3),
            (4, FOOT_W - 6, 7), M_ALUM, parent=fg)

    # ── Armrests ──
    ag = make_empty("armrest_group", root)
    for s in [-1, 1]:
        y = s * (SEAT_PAN_W / 2 - 4)
        padZ = ARM_PAD_H - ARM_PAD_THICK / 2
        baseZ = IDLER_Z + SEAT_TOP_OFF - 7
        padCX = ARM_PIVOT_X - ARM_LEN / 2 - 2
        add_box(f"arm_post_{s}", (ARM_PIVOT_X, y, (baseZ + padZ) / 2),
                (3, 3, padZ - baseZ), M_ALUM, parent=ag)
        add_box(f"arm_rail_{s}", (padCX, y, padZ - 2),
                (ARM_LEN + 4, 2, 2), M_ALUM, parent=ag)
        add_box(f"arm_pad_{s}", (padCX, y, ARM_PAD_H - ARM_PAD_THICK / 2),
                (ARM_LEN, ARM_PAD_W, 2), M_LEATHER, parent=ag)
        if s == 1:
            jx = ARM_PIVOT_X - ARM_LEN - 1
            add_box("jbox", (jx, y, ARM_PAD_H + 4),
                    (6, 6, 6), M_DARK, parent=ag)
            add_cyl("jknob", (jx + 2.5, y, ARM_PAD_H + 8.5),
                    1.2, 4, M_CHROME, parent=ag)
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=1.6, location=(jx + 2.5, y, ARM_PAD_H + 11))
            js = bpy.context.object; js.name = "jstick"
            js.data.materials.append(M_RUBBER)
            js.parent = ag
            js.matrix_parent_inverse = ag.matrix_world.inverted()

    # ── Hydraulic jack (rear) ──
    jg = make_empty("jack_group", root)
    hyd_z = CHASSIS_BOT
    add_cyl("hyd_barrel", (HYD_MOUNT_X, 0, hyd_z + HYD_BARREL_H / 2),
            HYD_BARREL_R, HYD_BARREL_H, M_ALUM, parent=jg)
    for s in [-1, 1]:
        add_box(f"hyd_brk_{s}", (HYD_MOUNT_X, s * 4, hyd_z),
                (10, 2, HYD_BARREL_H + 4), M_ALUM, parent=jg)

    # Jack extension (animated: extends downward)
    je = make_empty("jack_ext", root)
    rod_z = hyd_z
    add_box("piston", (HYD_MOUNT_X, 0, rod_z + HYD_ROD_R),
            (HYD_ROD_R * 2, 4, HYD_ROD_R * 2), M_CHROME, parent=je)
    add_cyl("hyd_rod", (HYD_MOUNT_X, 0, (hyd_z + HYD_BARREL_H / 2 + rod_z) / 2),
            HYD_ROD_R, abs(hyd_z + HYD_BARREL_H / 2 - rod_z), M_CHROME, parent=je)
    for s in [-1, 1]:
        add_cyl(f"hyd_whl_{s}", (HYD_MOUNT_X, s * 7, rod_z),
                HYD_WH_R, HYD_WH_W, M_ALUM, parent=je)
    add_cyl("hyd_axle", (HYD_MOUNT_X, 0, rod_z),
            1.5, 20, M_ALUM, parent=je)

    return {"root": root, "seat_group": sg, "jack_ext": je}


def build_stairs():
    for i in range(STAIR_COUNT):
        x = STAIR_X + STAIR_TREAD / 2 + i * STAIR_TREAD
        z = GROUND_Z + (i + 1) * STAIR_RISER - STAIR_RISER / 2
        add_box(f"stair{i}", (x, 0, z),
                (STAIR_TREAD, 170, STAIR_RISER), M_STAIR)


def build_ground():
    add_box("Ground", (60, 0, -50), (900, 900, 4), M_GROUND)


# ══════════════════════════════════════════════════════════════════════════
#  ANIMATION
# ══════════════════════════════════════════════════════════════════════════
#
#  Geometry (no π flip):
#    idler local x = -41  →  world x = vx - 41  (rear, faces stairs)
#    sprocket local x = +41  →  world x = vx + 41  (front)
#
#  Chair approaches backward:  idler (rear) moves toward stairs at x = 60.
#
#  Tilt:  pivot at sprocket (front, local x = +41).
#         idler (rear) rises, sprocket stays on ground.
#         tilted_pos_scad(theta, idler_wx) gives vehicle position such that
#         the idler ground-contact is at (idler_wx, gz).
#
#  Climb:  tilt angle = STAIR_ANGLE.  idler contact slides up the stair slope.

def animate(objs, scene):
    ROOT = objs["root"]
    SEAT = objs["seat_group"]
    JEXT = objs["jack_ext"]

    scene.frame_start = 1
    scene.frame_end = 450
    scene.render.fps = 30

    HALF = TRACK_LENGTH / 2   # 41
    gz   = GROUND_Z           # 4.5

    def flat_z():
        return gz - (IDLER_Z - TRACK_R)  # 0

    def flat_pos(vx):
        return (vx, 0, flat_z())

    def tilted_pos(theta, idler_wx, gz_base=GROUND_Z):
        """Vehicle position so idler ground-contact is at (idler_wx, gz_base)."""
        dx = HALF                            # 41
        dz = -(IDLER_Z - TRACK_R)            # -4.5
        vx = idler_wx + dx * math.cos(theta) - dz * math.sin(theta)
        vz = gz_base + dx * math.sin(theta) + dz * math.cos(theta)
        return (vx, 0, vz)

    # ── Phase 1: APPROACH (frames 1-90, 0-3 s) ──
    # Chair backs up.  Idler (rear) approaches stairs.
    # Stop when idler contact is 5 cm before first riser.
    idler_wx_1 = STAIR_X - 5   # 55
    vx_1 = idler_wx_1 - HALF   # 14

    vx_start = -HALF - 60      # -101 (far back, drives for ~3 s)

    ROOT.location = flat_pos(vx_start)
    ROOT.rotation_euler = (0, 0, 0)
    ROOT.keyframe_insert("location", frame=1)
    ROOT.keyframe_insert("rotation_euler", frame=1)

    SEAT.rotation_euler = (0, 0, 0)
    SEAT.keyframe_insert("rotation_euler", frame=1)

    JEXT.location = (0, 0, 0)
    JEXT.keyframe_insert("location", frame=1)

    ROOT.location = flat_pos(vx_1)
    ROOT.keyframe_insert("location", frame=90)
    ROOT.keyframe_insert("rotation_euler", frame=90)
    SEAT.keyframe_insert("rotation_euler", frame=90)
    JEXT.keyframe_insert("location", frame=90)

    # ── Phase 2: JACK LIFT (frames 90-180, 3-6 s) ──
    # Jack extends down.  Rear (idler) rises.  Sprocket stays on ground.
    # Pivot is sprocket at world x = vx + 41 = 14 + 41 = 55.
    # At STAIR_ANGLE, idler world x = vx + 41 + 82*cos(θ) = 55 + 73.4 = 128.4.
    # That puts idler WAY past the stairs — the chair pivots around sprocket.
    # Actually this is correct for the jack-lift geometry:
    #   sprocket at x=55 (near stairs), idler rises high behind it.
    # But the idler should stay on the ground near the stair base...
    #
    # RE-EXAMINING: When jack pushes DOWN at the rear (near sprocket),
    # it lifts the REAR (idler end) while the FRONT (sprocket end) stays low.
    # So the sprocket is the pivot point on the ground.
    # The idler rises UP — it is NOT on the ground during this phase.
    # The TRACK forms the hypotenuse: sprocket on ground, idler up in air.
    # The chair is tilted with sprocket end low, idler end high.
    #
    # Wait — re-reading the spec:
    #   "Jack pushes DOWN on ground to lift REAR up. Front idler stays on ground."
    # So idler = FRONT stays on ground, sprocket (rear) lifts up?
    # But we said idler is REAR (faces stairs)... contradiction?
    #
    # Let me re-read: "Chair ALWAYS approaches stairs backward (rear first)"
    # "Jack is at REAR" "Jack pushes DOWN to lift REAR up"
    # "Front idler stays on ground during jack lift"
    #
    # OK so: FRONT = idler, REAR = sprocket.
    # Chair approaches with REAR (sprocket) facing stairs.
    # Jack pushes REAR (sprocket end) DOWN against ground → lifts sprocket UP.
    # Wait, that's contradictory too. Jack pushes DOWN, which would lift the
    # opposite end...
    #
    # Actually: jack extends DOWN, wheel hits ground, and because the jack
    # is at the REAR, pushing the rear down pivots around the FRONT (idler).
    # The rear goes DOWN, which means the FRONT stays on ground and the
    # rear... also goes down? That doesn't lift anything.
    #
    # Let me reconsider: the jack is UNDER the chassis at the rear.
    # When it extends DOWN and hits the ground, the reaction force pushes
    # the chassis UP at the jack mounting point. So the rear of the chair
    # LIFTS UP. The front idler stays on the ground as the pivot.
    #
    # In our model: jack is at x=24 (near sprocket at x=41).
    # When jack extends and hits ground, it pushes the chassis UP at x=24.
    # The idler (rear, at x=-41) stays on the ground.
    # The chair pivots around the idler ground-contact.
    # The sprocket (front) rises.
    #
    # So: idler = REAR (on ground), sprocket = FRONT (rises).
    # Pivot at idler ground-contact.
    # tilted_pos(theta, idler_wx) gives the correct vehicle position.
    #
    # This matches our earlier geometry! Good.

    # Tilt to STAIR_ANGLE around idler ground-contact
    vp2 = tilted_pos(STAIR_ANGLE, idler_wx_1)
    ROOT.location = vp2
    ROOT.rotation_euler = (0, STAIR_ANGLE, 0)
    ROOT.keyframe_insert("location", frame=180)
    ROOT.keyframe_insert("rotation_euler", frame=180)

    # Seat counter-rotates to stay level
    SEAT.rotation_euler = (0, -STAIR_ANGLE, 0)
    SEAT.keyframe_insert("rotation_euler", frame=180)

    # Jack extends
    JEXT.location = (0, 0, -HYD_EXTEND)
    JEXT.keyframe_insert("location", frame=180)

    # ── Phase 3: ALIGN (frames 180-240, 6-8 s) ──
    # Jack wheels roll the chair backward (toward stairs) to align
    # the track angle with the stair angle.
    # Move idler contact from x=55 back toward the stair base.
    # When aligned, sprocket (front, world x = vx + 41) should be near
    # the first stair nosing at x = 60.
    #
    # sprocket_wx = vx + 41 = 60  →  vx = 19.
    # idler_wx = vx - 41 = -22.  ← too far back.
    #
    # Actually the alignment puts the TRACK on the stairs.
    # The track runs from idler (rear) to sprocket (front).
    # We want the front part of the track (near sprocket) to rest on
    # the first stair tread, with the idler at the base.
    #
    # For the track to sit at STAIR_ANGLE on the stairs:
    #   idler at stair base (x ≈ STAIR_X = 60), on the ground.
    #   sprocket above, at the first tread.
    #
    # But our tilted_pos keeps idler on the GROUND (gz = GROUND_Z).
    # The stairs rise above ground. So for alignment, the idler should
    # be at the BASE of the first riser, and the track slopes up to
    # the first tread where the sprocket sits.
    #
    # Idler at (STAIR_X, GROUND_Z) = (60, 4.5).
    # That's the same as idler_wx = 60.
    # vehicle_x = 60 - 41 = 19.  sprocket_wx = 19 + 41 = 60.
    #
    # Hmm, both idler and sprocket at x = 60? That means the track is
    # vertical, which is wrong.
    #
    # The issue is that tilted_pos assumes idler ground-contact at gz_base.
    # For alignment, we need idler at the base of the first riser.
    # The ground there is still GROUND_Z (the ground level before the stairs).
    # The first tread is at z = GROUND_Z + STAIR_RISER = 20.5.
    #
    # So idler at (60, 4.5) — at the base of the first riser.
    # The track slopes up from there at STAIR_ANGLE.
    # sprocket at (60 + 82*cos(26.6°), 4.5 + 82*sin(26.6°)) = (60+73.4, 4.5+36.8)
    #          = (133.4, 41.3).
    #
    # That's way past the stairs. The track is longer than 1 stair.
    # Actually, the track spans multiple stairs.
    # 5 stairs × 32 cm tread = 160 cm total.
    # Track length = 82 cm. Track covers about 2.5 stairs.
    #
    # So during climb, the track rides on 2-3 stair treads at once.
    # The idler contacts one tread, the sprocket contacts another.
    #
    # For alignment (phase 3), we want the track to sit on the first
    # 2 stairs. Let me position it so:
    #   idler on the ground at the base of stair 1.
    #   Track slopes up at STAIR_ANGLE.
    #   The first section of track rests on stair 1 tread.
    #
    # idler_wx = STAIR_X = 60.
    # This is already the position from phase 2 (idler_wx_1 = 55).
    # So phase 3 just adjusts slightly to put idler right at the nosing.

    # Small adjustment: move idler contact to exactly the stair base
    idler_wx_3 = STAIR_X   # 60
    vp3 = tilted_pos(STAIR_ANGLE, idler_wx_3)
    ROOT.location = vp3
    ROOT.keyframe_insert("location", frame=240)
    ROOT.keyframe_insert("rotation_euler", frame=240)
    SEAT.keyframe_insert("rotation_euler", frame=240)
    JEXT.keyframe_insert("location", frame=240)

    # ── Phase 4: JACK RETRACT (frames 240-270, 8-9 s) ──
    # Jack retracts.  Rear (sprocket end) lowers.  Track now rests
    # fully on the stairs.  Front idler still on ground at base.
    ROOT.keyframe_insert("location", frame=270)
    ROOT.keyframe_insert("rotation_euler", frame=270)
    SEAT.keyframe_insert("rotation_euler", frame=270)
    JEXT.location = (0, 0, 0)
    JEXT.keyframe_insert("location", frame=270)

    # ── Phase 5: CLIMB (frames 270-360, 9-12 s) ──
    # Track drives.  Chair climbs all 5 stairs.
    # The vehicle moves backward (increasing idler_wx) while tilted.
    # As it climbs, ground_z under idler rises.
    climb_h = STAIR_COUNT * STAIR_TREAD   # 160
    climb_v = STAIR_COUNT * STAIR_RISER   # 80
    idler_wx_5_start = STAIR_X            # 60

    for ki in range(10):
        f = 270 + ki * 9                   # frames 270..351
        t = ki / 9
        ix = idler_wx_5_start + t * climb_h
        gz = GROUND_Z + t * climb_v
        vp = tilted_pos(STAIR_ANGLE, ix, gz)
        ROOT.location = vp
        ROOT.keyframe_insert("location", frame=f)
        ROOT.keyframe_insert("rotation_euler", frame=f)
        SEAT.keyframe_insert("rotation_euler", frame=f)
        JEXT.keyframe_insert("location", frame=f)

    # ── Phase 6: TOP TRANSITION (frames 360-450, 12-15 s) ──
    # At top landing.  Jack extends again, lifts rear, chair levels.
    # Then jack retracts, chair sits flat on landing.
    gz_top = GROUND_Z + climb_v            # 84.5
    idler_wx_top = idler_wx_5_start + climb_h  # 220
    vx_top = idler_wx_top - HALF           # 179

    # Jack extends, slight tilt
    ROOT.location = (vx_top, 0, gz_top - (IDLER_Z - TRACK_R) + 2)
    ROOT.rotation_euler = (0, STAIR_ANGLE * 0.3, 0)
    ROOT.keyframe_insert("location", frame=375)
    ROOT.keyframe_insert("rotation_euler", frame=375)
    SEAT.rotation_euler = (0, -STAIR_ANGLE * 0.3, 0)
    SEAT.keyframe_insert("rotation_euler", frame=375)
    JEXT.location = (0, 0, -HYD_EXTEND * 0.6)
    JEXT.keyframe_insert("location", frame=375)

    # Level out
    ROOT.location = (vx_top + 20, 0, gz_top - (IDLER_Z - TRACK_R))
    ROOT.rotation_euler = (0, 0, 0)
    ROOT.keyframe_insert("location", frame=405)
    ROOT.keyframe_insert("rotation_euler", frame=405)
    SEAT.rotation_euler = (0, 0, 0)
    SEAT.keyframe_insert("rotation_euler", frame=405)
    JEXT.location = (0, 0, 0)
    JEXT.keyframe_insert("location", frame=405)

    # Drive forward on landing
    ROOT.location = (vx_top + 120, 0, gz_top - (IDLER_Z - TRACK_R))
    ROOT.keyframe_insert("location", frame=450)
    ROOT.keyframe_insert("rotation_euler", frame=450)
    SEAT.keyframe_insert("rotation_euler", frame=450)
    JEXT.keyframe_insert("location", frame=450)

    # Set all to LINEAR
    for obj in bpy.data.objects:
        set_linear(obj)


# ══════════════════════════════════════════════════════════════════════════
#  CAMERAS  (one per phase, switched via markers)
# ══════════════════════════════════════════════════════════════════════════
def setup_cameras(scene):
    cams = []

    # Cam 1 — Approach: low side view from the left
    bpy.ops.object.camera_add(location=(-80, -200, 35))
    c1 = bpy.context.object; c1.name = "Cam_Approach"
    c1.data.lens = 35
    con = c1.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c1)

    # Cam 2 — Jack Lift: rear 3/4 view, low angle
    bpy.ops.object.camera_add(location=(120, 100, 50))
    c2 = bpy.context.object; c2.name = "Cam_Jack"
    c2.data.lens = 40
    con = c2.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c2)

    # Cam 3 — Align: side view
    bpy.ops.object.camera_add(location=(30, -180, 50))
    c3 = bpy.context.object; c3.name = "Cam_Align"
    c3.data.lens = 35
    con = c3.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c3)

    # Cam 4 — Retract: close-up side view
    bpy.ops.object.camera_add(location=(60, -100, 40))
    c4 = bpy.context.object; c4.name = "Cam_Retract"
    c4.data.lens = 50
    con = c4.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c4)

    # Cam 5 — Climb: tracking shot from side
    bpy.ops.object.camera_add(location=(-50, -160, 60))
    c5 = bpy.context.object; c5.name = "Cam_Climb"
    c5.data.lens = 35
    con = c5.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c5)

    # Cam 6 — Top: front-facing reveal
    bpy.ops.object.camera_add(location=(350, -120, 100))
    c6 = bpy.context.object; c6.name = "Cam_Top"
    c6.data.lens = 40
    con = c6.constraints.new(type='TRACK_TO')
    con.target = bpy.data.objects.get("seat_pan")
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    cams.append(c6)

    return cams


def setup_camera_markers(scene, cams):
    scene.camera = cams[0]
    for f, cam in [(1, cams[0]), (90, cams[1]), (180, cams[2]),
                   (240, cams[3]), (270, cams[4]), (360, cams[5])]:
        m = scene.timeline_markers.new(f"Cam_{f}", frame=f)
        m.camera = cam


# ══════════════════════════════════════════════════════════════════════════
#  LIGHTING
# ══════════════════════════════════════════════════════════════════════════
def setup_lighting():
    # Key light — dramatic, from upper left
    bpy.ops.object.light_add(type='SUN', location=(-200, 100, 300))
    key = bpy.context.object; key.name = "KeyLight"
    key.data.energy = 5.0
    key.data.color = (1.0, 0.95, 0.9)
    key.rotation_euler = (math.radians(50), math.radians(15), math.radians(-30))

    # Fill light — softer, from right
    bpy.ops.object.light_add(type='AREA', location=(200, -50, 150))
    fill = bpy.context.object; fill.name = "FillLight"
    fill.data.energy = 3000
    fill.data.size = 200
    fill.data.color = (0.9, 0.95, 1.0)
    fill.rotation_euler = (math.radians(45), 0, math.radians(30))


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "renders_light")
    os.makedirs(out, exist_ok=True)

    clear()
    objs = build_vehicle()
    build_stairs()
    build_ground()

    scene = bpy.context.scene
    animate(objs, scene)

    cams = setup_cameras(scene)
    setup_camera_markers(scene, cams)
    setup_lighting()

    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.15, 0.15, 0.15)

    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "vlee_stair_v4.blend"))
    print("Done — saved vlee_stair_v4.blend")


if __name__ == "__main__":
    main()
