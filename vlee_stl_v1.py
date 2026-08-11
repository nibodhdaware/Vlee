"""
Vlee B1000 Stair-Climb Animation — Blender 4.0
Built from the exported STL parts (SCAD assembly; 1 unit = 1 cm).
Run:  blender -b -P vlee_stl_v1.py
Output: renders_light/vlee_stl_v1.blend

The STL parts were exported from the OpenSCAD modules:
  * assembly-position STLs (already where prototype.scad puts them):
    01 armrest_pair, 02 bucket_seat, 03 chassis_axles,
    05 footrest_assembly, 06 hydraulic_jack
  * centered-part STLs (need explicit placement; axis:  x/z plane for wheels,
    y = wheel axis):
    04 drive_sprocket -> (+IDLER_X, +/-CY, IDLER_Z)
    07 idler_wheel    -> (-IDLER_X, +/-CY, IDLER_Z)
    08 road_wheel     -> (each ROAD_POS, +/-CY, ROAD_Z)
    09 seat bracket   -> built at y=24; shift/mirror to y=+-15
    10 suspension_beam-> built at y=28; mirror for the -y side
    11 bushing_unit   -> at each ROAD_POS, +/-CY
    12 track_belt     -> (0, +/-CY, 0)  [STL already has z=16 built-in]

6-phase stair-climb animation (1..420 frames, 30 fps, 14 s):
  1 APPROACH      f   1- 90 (0-3s)   chair backs up, rear (+x jack side)
                                     faces the stairs, rolls flat on ground.
  2 JACK LIFT     f  90-180 (3-6s)   rear jack pushes the REAR up; the FRONT
                               idler (-x end) stays planted on the ground;
                               the belt forms the hypotenuse; the seat stays
                               LEVEL via the front pivot joint (clear to see).
  3 ALIGN         f 180-240 (6-8s)   motorised jack wheels roll the chair in a
                               little, pressing the belt onto the stair angle.
  4 JACK RETRACT  f 240-270 (8-9s)   settle the track so it rests on the
                               stairs; front idler stays on the bottom step.
  5 CLIMB         f 270-360 (9-12s)  tracks drive the chair up all 5 steps,
                               seat stays LEVEL the whole way.
  6 TOP TRANS     f 360-420 (12-14s) at the landing the jack lifts, the chair
                               crests onto the flat, jacks retract + levelled.
The seat group counter-rotates (SEAT = -ROOT tilt) so it stays level.
"""
import bpy, math, os, bmesh

HERE    = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(HERE, "STL")

# ── SCAD parameters (parameters.scad) ─────────────────────────────────────
IDLER_X   = 41
IDLER_Z   = 16
TRACK_R   = 11.5
GROUND_Z  = 4.5
TRACK_CY  = 28
ROAD_Z    = 13
ROAD_POS  = [-22, -6, 10, 24]
SEAT_TOP  = IDLER_Z + (45 - TRACK_R)        # 49.5

# wheel radii (for rolling animation)
SPROCKET_R = IDLER_R = 10.0     # drive sprocket / idler pitch radius
ROAD_R     = 7.0
HYD_EXTEND = 26.5               # how far the jack rod travels (parameters.scad)

# Stair / climb geometry
STAIR_X     = 60
STAIR_TREAD = 32
STAIR_RISER = 16
STAIR_COUNT = 5
STAIR_ANGLE = math.atan2(STAIR_RISER, STAIR_TREAD)

# ── materials ─────────────────────────────────────────────────────────────
def mk_mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = (*rgb, 1)
    n.inputs["Roughness"].default_value = rough
    n.inputs["Metallic"].default_value = metal
    return m

M_ALUM    = mk_mat("Aluminum",   (0.55, 0.57, 0.60), 0.35, 0.9)
M_RUBBER  = mk_mat("Rubber",     (0.12, 0.12, 0.14), 0.85, 0.0)
M_LEATHER = mk_mat("Leather",    (0.45, 0.25, 0.12), 0.70, 0.0)
M_DARK    = mk_mat("DarkSteel",  (0.25, 0.26, 0.28), 0.40, 0.9)
M_GROUND  = mk_mat("Ground",     (0.25, 0.27, 0.30), 0.90, 0.0)
M_STAIR   = mk_mat("Stair",      (0.35, 0.37, 0.40), 0.15, 0.7)

def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

def make_empty(name, parent=None, loc=(0.0, 0.0, 0.0)):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def import_stl(name, parent, loc=(0, 0, 0), mat=None, scale=(1, 1, 1)):
    path = os.path.join(STL_DIR, name)
    bpy.ops.wm.stl_import(filepath=path)
    objs = [o for o in bpy.context.selected_objects
            if o.type == 'MESH'] or list(bpy.context.scene.objects)[-1:]
    for o in objs:
        o.location = loc
        o.scale = scale
        if mat:
            o.data.materials.append(mat)
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return objs[0]

def copy_mesh_half(src, cut_z, keep_above, newname):
    """Split the jack STL at a horizontal plane (its local z).

    keep_above=True  -> the barrel + brackets (static part)
    keep_above=False -> the piston rod + wheels (extendable part)
    """
    bm = bmesh.new()
    bm.from_mesh(src.data)
    geom = bm.verts[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, cut_z),
                           plane_no=(0, 0, 1),
                           clear_inner=keep_above, clear_outer=(not keep_above))
    for f in list(bm.faces):
        if (f.calc_center_median().z > cut_z) != keep_above:
            bmesh.ops.delete(bm, geom=[f], context='FACES')
    bm.normal_update()
    mesh = bpy.data.meshes.new(newname)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

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

# ── ASSEMBLY (matches prototype.scad) ─────────────────────────────────────
def build_vehicle():
    root = make_empty("VehicleRoot")

    # The seat group counter-rotates about the root origin so it stays level.
    seat = make_empty("seat_group", parent=root)

    wheels = []                             # (object, radius) for rolling spin

    #
    # Chassis + tracks (rotate rigidly with the body).
    #
    ch = make_empty("chassis", parent=root)
    import_stl("03_chassis_axles.stl", ch, (0, 0, 0), mat=M_DARK)

    for side, sy in [("L", -1), ("R", 1)]:
        trk = make_empty(f"track_{side}", parent=ch)
        y = sy * TRACK_CY
        import_stl("12_track_belt.stl",      trk, (0,   y, 0),          mat=M_RUBBER)
        idl = import_stl("07_idler_wheel.stl",
                         trk, (-IDLER_X, y, IDLER_Z), M_RUBBER)
        spr = import_stl("04_drive_sprocket.stl",
                         trk, ( IDLER_X, y, IDLER_Z), M_RUBBER)
        for rx in ROAD_POS:
            rw = import_stl("08_road_wheel.stl",
                            trk, (rx, y, ROAD_Z),      M_RUBBER)
            wheels.append((rw, ROAD_R))
        wheels.append((idl, IDLER_R))
        wheels.append((spr, SPROCKET_R))
        # suspension beam STL sits at y=28; mirror Y if on the -Y side
        import_stl("10_suspension_beam.stl", trk, (0, 0, 0), M_DARK,
                   scale=(1, sy, 1))
        for rx in ROAD_POS:
            import_stl("11_suspension_bushing_unit.stl",
                       trk, (rx, y, 0), M_RUBBER)

    # ---------------- Seat-side parts (stay level) ----------------
    # Seat brackets: STL built at y=24; place at y=+-15.
    for sy in (1, -1):
        br = import_stl("09_seat_L_bracket.stl", seat, (0, 0, 0), M_ALUM,
                        scale=(1, sy, 1))
        br.location.y = sy * (23 - 24)          # +-> -1, - -> +1  (kept close)
        # keep the clamp foot on the inner side after mirroring
        if sy < 0:
            br.rotation_euler = (0, 0, math.pi)

    seat_pan = import_stl("02_bucket_seat.stl", seat, (0, 0, 0), M_LEATHER)
    seat_pan.name = "seat_pan"
    import_stl("01_armrest_pair.stl",     seat, (0, 0, 0), M_ALUM)
    import_stl("05_footrest_assembly.stl", seat, (0, 0, 0), M_ALUM)

    # ---- Hydraulic jack: split into barrel (static) and rod+wheels ext ----
    jack_src = import_stl("06_hydraulic_jack.stl", seat, (0, 0, 0), M_ALUM)
    cutter = 30.0                       # just below the mounting brackets
    barrel_m = copy_mesh_half(jack_src, cutter, keep_above=True,
                              newname="jack_barrel_mesh")
    rod_m    = copy_mesh_half(jack_src, cutter, keep_above=False,
                              newname="jack_rod_mesh")
    bpy.data.objects.remove(jack_src, do_unlink=True)

    barrel = bpy.data.objects.new("jack_barrel", barrel_m)
    rod    = bpy.data.objects.new("jack_rod",    rod_m)
    bpy.context.collection.objects.link(barrel)
    bpy.context.collection.objects.link(rod)
    for o in (barrel, rod):
        o.location = (0, 0, 0)
        o.rotation_euler = (0, 0, math.pi)    # SCAD jack is z-up; STL z-up
        o.matrix_world = root.matrix_world
        o.parent = seat
        o.matrix_parent_inverse = seat.matrix_world.inverted()

    # Camera rig: a floating empty, animated so the Phase-5 tracking cam
    # follows the chair's climb.
    rig = make_empty("cam_rig5", parent=root)

    return {"root": root, "seat": seat, "pan": seat_pan,
            "wheels": wheels, "jack": rod, "rig": rig}

# ── world: stairs + ground ────────────────────────────────────────────────
def build_stairs():
    for i in range(STAIR_COUNT):
        x = STAIR_X + STAIR_TREAD / 2 + i * STAIR_TREAD
        z = GROUND_Z + (i + 1) * STAIR_RISER - STAIR_RISER / 2
        add_box(f"stair{i}", (x, 0, z),
                (STAIR_TREAD, 170, STAIR_RISER), M_STAIR)
    # top landing reached after the last step (z = GROUND_Z + 5*+16)
    land_z = GROUND_Z + STAIR_COUNT * STAIR_RISER          # 84.5
    add_box("Landing", (STAIR_X + STAIR_COUNT * STAIR_TREAD + 120, 0,
                        land_z - 4),
            (240, 170, 8), M_GROUND)

def build_ground():
    # belt bottom (GROUND_Z=4.5) is the floor; put slab just below it.
    add_box("Ground", (60, 0, GROUND_Z - 4), (900, 900, 8), M_GROUND)

# ── ANIMATION ─────────────────────────────────────────────────────────────
def animate(objs, scene):
    ROOT, SEAT = objs["root"], objs["seat"]
    scene.frame_start, scene.frame_end, scene.render.fps = 1, 420, 30

    BELT = IDLER_Z - TRACK_R            # belt-bottom height in ROOT coords
    TILT = -STAIR_ANGLE                 # +x (rear) up = negative Y tilt
    g    = GROUND_Z
    BASE = STAIR_X                      # x of the first riser
    SLOPE = STAIR_RISER / STAIR_TREAD

    def pivot_at(wx, gz, tilt):
        """ROOT location that pins the local front belt-bottom at (wx,gz)."""
        c, s = math.cos(tilt), math.sin(tilt)
        lx = -IDLER_X * c + BELT * s
        lz =  IDLER_X * s + BELT * c
        return (wx - lx, 0.0, gz - lz)

    def kpose(wx, gz, tilt, f):
        ROOT.location = pivot_at(wx, gz, tilt)
        ROOT.rotation_euler = (0, tilt, 0)
        SEAT.rotation_euler = (0, -tilt, 0)
        ROOT.keyframe_insert("location", frame=f)
        ROOT.keyframe_insert("rotation_euler", frame=f)
        SEAT.keyframe_insert("rotation_euler", frame=f)

    def ramp(fa, fb, n, way):
        for i in range(n):
            t = i / (n - 1)
            frame = fa + round(t * (fb - fa))
            way(t, frame)

    # Walking point along the stair-nose line: the belt underside should
    # stay on that line while climbing so the track "rides" the nosers.
    def nose_z(x):
        if x <= BASE: return g
        return g + (x - BASE) * SLOPE

    # ── Phase 1 (1-90, 0-3s) APPROACH ──────────────────────────────
    # Chair backs up flat on the ground; rear (jack/sprocket end) faces
    # the stairs and rolls until it stops just short of the first riser.
    ramp(1, 90, 8, lambda t, f: kpose(-90 + t * (BASE - 50), g, 0.0, f))

    # ── Phase 2 (90-180, 3-6s) JACK LIFT ───────────────────────────
    # Chair stops. Rear jack extends down against the ground, lifting the
    # REAR up; the front idler stays planted. Belt = hypotenuse of the
    # stair angle, seat stays LEVEL via the front pivot.
    ramp(90, 180, 12, lambda t, f: kpose(BASE - 50, g, t * TILT, f))

    # ── Phase 3 (180-240, 6-8s) ALIGN ──────────────────────────────
    # Motorised jack wheels roll the chair forward a little, pressing the
    # tilted belt up against the stair slope so the track angle matches.
    ramp(180, 240, 10, lambda t, f: kpose(BASE - 50 + t * 50, g, TILT, f))

    # ── Phase 4 (240-270, 8-9s) JACK RETRACT / SETTLE ──────────────
    # Jack retracts, the track settles so it rests fully on the stairs
    # while the front idler stays on the ground at the bottom step.
    ramp(240, 270, 6, lambda t, f: kpose(BASE, g, TILT, f))

    # ── Phase 5 (270-360, 9-12s) CLIMB ─────────────────────────────
    # Tracks drive the chair up all 5 steps along the stair slope;
    # the seat stays LEVEL the whole way.
    top_x = BASE + STAIR_COUNT * STAIR_TREAD      # 220
    ramp(270, 360, 20, lambda t, f:
         kpose(BASE + t * (STAIR_COUNT * STAIR_TREAD),
               nose_z(BASE + t * (STAIR_COUNT * STAIR_TREAD)),
               TILT, f))

    # ── Phase 6 (360-420, 12-14s) TOP TRANSITION ───────────────────
    # At the top landing the jack lifts the rear again, the chair crests
    # and rolls forward onto the flat, jack retracts, chair is level.
    top_z = g + STAIR_COUNT * STAIR_RISER         # 84.5
    ramp(360, 420, 12, lambda t, f:
         kpose(top_x + t * (STAIR_TREAD * 3), top_z, TILT * (1 - t), f))

    for obj in bpy.data.objects:
        if getattr(obj, "animation_data", None):
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

# ── cameras + lighting ────────────────────────────────────────────────────
def setup_cameras(scene):
    specs = [
        # Phase 1 approach: low side view from the left.
        ("CamP1", (-150, -150, 30), 28),
        # Phase 2 jack lift: rear 3/4 view, low angle.
        ("CamP2", (60, 110, 40), 35),
        # Phase 3 align: side.
        ("CamP3", (30, -130, 50), 35),
        # Phase 4 settle: close-up side.
        ("CamP4", (40, -90, 30), 50),
        # Phase 5 climb: tracking side.
        ("CamP5", (140, -150, 55), 40),
        # Phase 6 top: front-facing reveal.
        ("CamP6", (300, -120, 75), 45),
    ]
    p = bpy.data.objects.get("seat_pan")
    cams = []
    for name, loc, lens in specs:
        bpy.ops.object.camera_add(location=loc)
        c = bpy.context.object
        c.name = name
        c.data.lens = lens
        if p:                                     # keep the chair framed
            con = c.constraints.new(type='TRACK_TO')
            con.target = p
            con.track_axis = 'TRACK_NEGATIVE_Z'
            con.up_axis = 'UP_Y'
        cams.append(c)
    # bind each camera to a timeline marker (frame where it becomes active)
    bpy.ops.object.select_all(action='DESELECT')
    for f, cam, in zip([1, 90, 180, 240, 270, 360], cams):
        for m in scene.timeline_markers:
            scene.timeline_markers.remove(m)
        m = scene.timeline_markers.new(name=f"Cam{f}", frame=f)
        m.camera = cam
    scene.camera = cams[0]

def setup_lighting():
    bpy.ops.object.light_add(type="SUN", location=(-200, 100, 300))
    k = bpy.context.object; k.name = "KeyLight"
    k.data.energy = 5.0; k.data.color = (1.0, 0.95, 0.9)
    k.rotation_euler = (math.radians(50), math.radians(15), math.radians(-30))
    bpy.ops.object.light_add(type="AREA", location=(200, -50, 150))
    f = bpy.context.object; f.name = "FillLight"
    f.data.energy = 3000; f.data.size = 200; f.data.color = (0.9, 0.95, 1.0)
    f.rotation_euler = (math.radians(45), 0, math.radians(30))

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    out = os.path.join(HERE, "renders_light")
    os.makedirs(out, exist_ok=True)
    out = os.path.join(out, "vlee_stl_v1.blend")

    clear()
    objs = build_vehicle()
    build_stairs()
    build_ground()

    scene = bpy.context.scene
    animate(objs, scene)
    setup_cameras(scene)
    setup_lighting()

    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.15, 0.15, 0.15)
    scene.render.engine = "CYCLES"
    for vl in scene.view_layers:
        vl.cycles.use_denoising = False

    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("Done — saved " + out)

if __name__ == "__main__":
    main()