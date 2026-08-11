"""
Vlee B1000 — stair-climb demo rendered with PyVista + trimesh.

6-phase stair-climb animation (420 frames, 30 fps, 14 s):
  1 APPROACH     f  1- 90  chair rolls flat toward stairs (rear faces stairs)
  2 JACK LIFT    f 90-180  rear hydraulic pushes ground, lifts rear; idler stays
                           planted; belt = hypotenuse; seat stays level
  3 ALIGN        f180-240  jack wheels roll chair forward, belt pressed to stair angle
  4 JACK RETRACT f240-270  hydraulic retracts, track settles on stairs
  5 CLIMB        f270-360  tracks drive up all 5 steps, seat stays level
  6 TOP TRANS    f360-420  drive onto flat landing, track levels at end

Run:
    .venv/bin/python vlee_stl_pyvista.py
Output:
    renders_light/pyvista_demo/frame_%04d.png  +  climb_demo.mp4
"""
import math
import os
import shutil

import numpy as np
import pyvista as pv
import trimesh

HERE    = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(HERE, "STL")
MODE    = os.environ.get("VLEE_MODE", "a").strip().lower()
OUT     = os.path.join(HERE, "renders_light", "pyvista_demo_" + MODE)

# ── SCAD parameters (parameters.scad) ─────────────────────────────────────
TRACK_CY = 28
IDLER_X  = 41
IDLER_Z  = 16
TRACK_R  = 11.5
GROUND_Z = 4.5
ROAD_Z   = 13
ROAD_POS = [-22, -6, 10, 24]

IDLER_R    = 10.0
SPROCKET_R = 10.0
ROAD_R     = 7.0
HYD_EXTEND = 26.5

STAIR_X     = 60
STAIR_TREAD = 32
STAIR_RISER = 16
STAIR_COUNT = 5
STAIR_ANGLE = math.atan2(STAIR_RISER, STAIR_TREAD)

BASE    = STAIR_X
TOP_X   = BASE + STAIR_COUNT * STAIR_TREAD      # 220
TOP_Z   = GROUND_Z + STAIR_COUNT * STAIR_RISER  # 84.5

N_FRAMES = 420

# Render only a subset of frames when set (e.g. VLEE_TEST_FRAMES=270)
from_frame = int(os.environ.get("VLEE_FROM_FRAME", "1"))
to_frame   = int(os.environ.get("VLEE_TO_FRAME", str(N_FRAMES)))

# Track belt STL bottom is at z=3.0, but GROUND_Z=4.5 = IDLER_Z-TRACK_R.
# Shift belt up so its bottom aligns with the contact-point height.
BELT_Z_OFF = GROUND_Z - 3.0  # +1.5


# ── mesh helpers ──────────────────────────────────────────────────────────
def load_stl_trimesh(name, scale=None, z_rot=0):
    m = trimesh.load(os.path.join(STL_DIR, name), force="mesh", process=False)
    m = m.copy()
    if scale is not None:
        m.apply_transform(np.diag([scale[0], scale[1], scale[2], 1.0]))
    if z_rot:
        c, s = math.cos(z_rot), math.sin(z_rot)
        R = np.array([[c, -s, 0, 0],
                      [s,  c, 0, 0],
                      [0,  0, 1, 0],
                      [0,  0, 0, 1]], float)
        m.apply_transform(R)
    return m


def trimesh_to_pv(m):
    return pv.PolyData(m.vertices, np.hstack(
        (np.full((len(m.faces), 1), 3), m.faces)))


def clip_trimesh(m, z_cut, keep_above=True):
    face_z = m.vertices[m.faces].mean(axis=1)[:, 2]
    mask = (face_z >= z_cut) if keep_above else (face_z <= z_cut)
    new_faces = m.faces[mask]
    used = np.unique(new_faces)
    new_verts = m.vertices[used]
    remap = np.zeros(len(m.vertices), dtype=int)
    remap[used] = np.arange(len(used))
    return trimesh.Trimesh(vertices=new_verts, faces=remap[new_faces])


# ── scene graph ───────────────────────────────────────────────────────────
#  Tuple fields: (parent, filename, offset, spin_radius, y_side, color)
def build_parts():
    parts = [
        ("root", "03_chassis_axles.stl", (0, 0, 0), None, None, "#56595e"),
    ]
    for side, sy in (("L", -1), ("R", 1)):
        y = sy * TRACK_CY
        parts.append(("root", "12_track_belt.stl",      (0,        y, BELT_Z_OFF),  None,   sy, "#1b1b1e"))
        parts.append(("root", "07_idler_wheel.stl",     (-IDLER_X, y, IDLER_Z),     IDLER_R, sy, "#111112"))
        parts.append(("root", "04_drive_sprocket.stl",  ( IDLER_X, y, IDLER_Z),     SPROCKET_R, sy, "#111112"))
        for rx in ROAD_POS:
            parts.append(("root", "08_road_wheel.stl",  (rx, y, ROAD_Z),            ROAD_R, sy, "#111112"))
        parts.append(("root", "10_suspension_beam.stl", (0, 0, 0),                 None,   sy, "#56595c"))
        for rx in ROAD_POS:
            parts.append(("root", "11_suspension_bushing_unit.stl", (rx, y, 0),    None,   sy, "#1b1b1e"))
    for sy in (1, -1):
        parts.append(("seat", "09_seat_L_bracket.stl",  (0, -sy, 0),              None, sy, "#d8dae0"))
    parts.append(("seat", "02_bucket_seat.stl",         (0, 0, 0),               None, None, "#7a4a28"))
    parts.append(("seat", "01_armrest_pair.stl",        (0, 0, 0),               None, None, "#d8dae0"))
    parts.append(("seat", "05_footrest_assembly.stl",   (0, 0, 0),               None, None, "#d8dae0"))
    # NOTE: 06_hydraulic_jack is handled separately (split into barrel + rod)
    return parts


# ── motion ────────────────────────────────────────────────────────────────
# The jack rod slides along the seat (-z).  The wheel at the rod bottom must
# stay PLANTED on the flat ground while tilting, so its extension is coupled to
# the tilt, not a fixed max.  In ROOT frame the wheel-bottom point is at
# (MOUNT_X, BELT - ext); its world z equals GROUND_Z when
#     BELT - ext - lz = 0   ->   ext = BELT - lz
# Once the chair is over the stairs the rod must TUCK UP into the barrel
# (negative ext) so the wheel clears every step it passes.
MOUNT_X = float(os.environ.get("VLEE_MOUNT_X", "10.0"))  # jack mount x in seat coords
# The exported STL (SCAD/export_stl_hydraulic_jack.scad) bakes the mount at
# SCAD parameters.scad -> hydrMountX.  If that value changes, re-export the
# STL and update STL_JACK_X below to match the baked centroid x.
STL_JACK_X = 24.0  # baked position of 06_hydraulic_jack.stl (was hydrMountX=24)
TILT = -STAIR_ANGLE
SLOPE = STAIR_RISER / STAIR_TREAD

def planted_extension(tilt):
    """Extension that keeps the rod-bottom wheel ON the flat ground."""
    c, s = math.cos(tilt), math.sin(tilt)
    BELT = IDLER_Z - TRACK_R
    lz = IDLER_X * s + BELT * c
    return max(0.0, BELT - lz)

def tucked_extension():
    """Negative rod offset that lifts the wheel clear of any stair it passes."""
    # Rod STL bottom is z=4.5; barrel split at z=30.  Tucking the rod so its
    # bottom reaches z=24.5 (ext = -20) lifts the wheel to world z ~43, above
    # stair #1's solid (20.5..36.5) and #2's riser (36.5..52.5) while the SEAT
    # glide carries it across.  A tiny 3-unit poke above the barrel is visual
    # only (the barrel mesh keeps the jack's silhouette).
    return -20.0

def nose_z(x):
    if x <= BASE:
        return GROUND_Z
    return GROUND_Z + (x - BASE) * SLOPE

APPROACH_STOP = BASE - 75      # wheel stays x<60 while wx ≤ -15

# ── approach choreography ────────────────────────────────────────────────
# MODE "a"  retract-on-flat:  lift to full stair angle on flat ground with the
#            jack wheel planted, RETRACT fully BEFORE rolling forward, then roll
#            the tilted belt onto the slope and seat it on 3 noses.
# MODE "b"  wheel-rides-flat: lift on flat ground, then keep the jack wheel
#            planted while rolling toward the stairs, retracting only at the last
#            moment (wheel at ~x=57, still on flat) as the belt seats.
# MODE "c"  grip-first (physically defensible): drive flat until the belt's rear
#            cap butts the first riser, feed the belt to wrap nose 1 with the jack
#            leg PLANTED, roll forward (leg still planted + rolling) so the belt
#            rides up and seats on 3 noses, and only then tuck the leg.  The
#            chair is never left leaning unsupported on flat ground.
# (MODE is defined near the top, before STL_DIR/OUT are used.)

# frame bounds per mode
BUTT_X = BASE - 41                 # rear belt cap reaches stair-1 corner
if MODE == "a":
    PH = dict(APP=(1, 90), LIFT=(90, 150), RETRACT=(150, 180),
              SEAT=(180, 270), CLIMB=(270, 360), TOP=(360, 420))
elif MODE == "c":
    PH = dict(APP=(1, 90), GRIP=(90, 150), ROLL=(150, 210),
              SEATX=(210, 270), CLIMB=(270, 360), TOP=(360, 420))
else:  # "b"
    PH = dict(APP=(1, 90), LIFT=(90, 150), ROLL=(150, 200),
              RETRACT=(200, 270), CLIMB=(270, 360), TOP=(360, 420))

APP_START_X, APP_END_X = -140, APPROACH_STOP
ROLL_END_X = -5.0             # jack wheel world x ≈ 57, still clear of stair 1 (60)
# For mode "c" the approach ends where GRIP starts (chair held back so belt clears stair)
if MODE == "c":
    APP_END_X = BUTT_X - 40


def _smoothstep(t):
    """Cubic ease-in-out: smooth acceleration/deceleration."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def lerp(f, lo, hi, a, b):
    """Linear interpolation (kept for jack_extension continuity)."""
    t = 0.0 if hi == lo else (f - lo) / (hi - lo)
    return a + t * (b - a)


def pose_at(f):
    """Return (wx, gz, tilt) for frame f, with smooth easing at every
    phase boundary and per-step engagement during CLIMB."""

    # ── APP: approach flat ──────────────────────────────────────────────
    if f <= PH["APP"][1]:
        return (lerp(f, *PH["APP"], APP_START_X, APP_END_X), GROUND_Z, 0.0)

    # ── MODE-SPECIFIC PHASES ────────────────────────────────────────────
    if MODE == "a":
        if f <= PH["LIFT"][1]:
            t = _smoothstep(lerp(f, *PH["LIFT"], 0.0, 1.0))
            return (APP_END_X, GROUND_Z, t * TILT)
        if f <= PH["RETRACT"][1]:
            return (APP_END_X, GROUND_Z, TILT)
        if f <= PH["SEAT"][1]:
            return (lerp(f, *PH["SEAT"], APP_END_X, BASE), GROUND_Z, TILT)

    elif MODE == "c":
        # GRIP: tilt with smooth ease-in-out, chair held back so belt
        # (flat, spanning ±54 from seat center) doesn't overlap stair #1
        if f <= PH["GRIP"][1]:
            t = _smoothstep(lerp(f, *PH["GRIP"], 0.0, 1.0))
            return (BUTT_X - 40, GROUND_Z, t * TILT)
        # ROLL: slide forward onto noses, tilt fixed
        if f <= PH["ROLL"][1]:
            x = lerp(f, *PH["ROLL"], BUTT_X - 40, BASE)
            return (x, nose_z(x), TILT)
        # SEATX: settle + retract jack
        if f <= PH["SEATX"][1]:
            return (BASE, nose_z(BASE), TILT)

    else:  # mode b
        if f <= PH["LIFT"][1]:
            t = _smoothstep(lerp(f, *PH["LIFT"], 0.0, 1.0))
            return (APP_END_X, GROUND_Z, t * TILT)
        if f <= PH["ROLL"][1]:
            return (lerp(f, *PH["ROLL"], APP_END_X, ROLL_END_X), GROUND_Z, TILT)
        if f <= PH["RETRACT"][1]:
            return (lerp(f, *PH["RETRACT"], ROLL_END_X, BASE), GROUND_Z, TILT)

    # ── CLIMB: per-step engagement ──────────────────────────────────────
    # Each step: lift across the full step duration (no flat portion → no bounce).
    # Z is continuous across step boundaries.
    STEP_FRAMES = (PH["CLIMB"][1] - PH["CLIMB"][0]) / STAIR_COUNT  # 18
    if f <= PH["CLIMB"][1]:
        ef = f - PH["CLIMB"][0] - 1   # frame 271 → ef 0
        step_i = min(int(ef / STEP_FRAMES), STAIR_COUNT - 1)
        step_t = (ef - step_i * STEP_FRAMES) / (STEP_FRAMES - 1)  # last frame →1.0
        # x advances one tread per step
        wx = BASE + step_i * STAIR_TREAD + step_t * STAIR_TREAD
        # z: continuous lift across full step (smoothstep eases in/out)
        z = GROUND_Z + (step_i + _smoothstep(step_t)) * STAIR_RISER
        return (wx, z, TILT)

    # ── TOP: slide onto flat landing (tilt held, tracks level naturally) ──
    t = _smoothstep((f - PH["TOP"][0]) / (PH["TOP"][1] - PH["TOP"][0]))
    wx = TOP_X + t * (STAIR_TREAD * 3)
    return (wx, TOP_Z, TILT)


def jack_extension(f):
    """Rod extension: negative = tucked up, 0 = published neutral, positive =
    planted (wheel on flat ground)."""
    if MODE == "a":
        if f <= PH["LIFT"][1]:
            return planted_extension(pose_at(f)[2])
        if f <= PH["RETRACT"][1]:
            t = _smoothstep(lerp(f, *PH["RETRACT"], 0.0, 1.0))
            return planted_extension(TILT) + t * (tucked_extension() - planted_extension(TILT))
        return tucked_extension()
    if MODE == "c":
        # GRIP: tilt up, then retract jack within the same phase
        if f <= PH["GRIP"][1]:
            # Retract starting at GRIP+30, complete by GRIP end
            t = min(1.0, max(0.0, (f - (PH["GRIP"][0] + 30))
                              / (PH["GRIP"][1] - PH["GRIP"][0] - 30)))
            planted = planted_extension(pose_at(f)[2])
            tucked  = tucked_extension()
            return planted + t * t * (tucked - planted)
        # ROLL onward: jack fully tucked
        return tucked_extension()
    # mode b
    if f <= PH["LIFT"][1]:
        return planted_extension(pose_at(f)[2])
    if f <= PH["ROLL"][1]:
        return planted_extension(TILT)
    if f <= PH["RETRACT"][1]:
        t = _smoothstep(lerp(f, *PH["RETRACT"], 0.0, 1.0))
        return planted_extension(TILT) + t * (tucked_extension() - planted_extension(TILT))
    return tucked_extension()


def engaged_noses(f):
    """Nose indices whose corner lies under the belt bottom run (within tol)."""
    wx, gz, tilt = pose_at(f)
    tol = 1.5
    out = []
    for i in range(STAIR_COUNT + 1):
        nx = BASE + i * STAIR_TREAD
        nz = GROUND_Z + i * STAIR_RISER
        along = (nx - wx) / math.cos(-TILT)
        if along < -0.1 or along > 2 * IDLER_X + 0.1:
            continue
        bz = gz + along * math.sin(-TILT)
        if abs(bz - nz) <= tol:
            out.append(i)
    return out


# ── matrix helpers ────────────────────────────────────────────────────────
def ry(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s, 0],
                     [0, 1, 0, 0],
                     [-s, 0, c, 0],
                     [0, 0, 0, 1.]], float)


def translate(x, y, z):
    m = np.eye(4)
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    return m


def root_matrix(wx, gz, tilt):
    c, s = math.cos(tilt), math.sin(tilt)
    BELT = IDLER_Z - TRACK_R
    lx = -IDLER_X * c + BELT * s
    lz =  IDLER_X * s + BELT * c
    return translate(wx - lx, 0.0, gz - lz) @ ry(tilt)


# ── main ──────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT, exist_ok=True)
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found; frames only.")

    parts = build_parts()
    actors = []
    plot = pv.Plotter(off_screen=True, window_size=[1280, 720])
    plot.set_background("#26282c")

    # ── static scene ──────────────────────────────────────────────────────
    y_half = 50
    ground = pv.Box(bounds=(-200, 380, -y_half, y_half, 0, GROUND_Z))
    plot.add_mesh(ground, color="#3a3d42", smooth_shading=False)
    for i in range(STAIR_COUNT):
        x0 = BASE + i * STAIR_TREAD
        x1 = x0 + STAIR_TREAD
        z0 = GROUND_Z + i * STAIR_RISER
        z1 = z0 + STAIR_RISER
        step = pv.Box(bounds=(x0, x1, -y_half, y_half, z0, z1))
        plot.add_mesh(step, color="#5a5d62", smooth_shading=False)
    landing = pv.Box(bounds=(TOP_X, TOP_X + 200, -y_half, y_half, TOP_Z, TOP_Z + 10))
    plot.add_mesh(landing, color="#5a5d62", smooth_shading=False)

    # ── regular parts ─────────────────────────────────────────────────────
    for parent, fname, off, spin_r, sy, col in parts:
        z_rot = 0  # seat bracket mirrored via scale (1,sy,1) only
        mesh = load_stl_trimesh(fname, (1, sy, 1) if sy is not None else None, z_rot)
        actors.append((parent, fname, off, spin_r,
                       plot.add_mesh(trimesh_to_pv(mesh), color=col,
                                     smooth_shading=True, show_edges=False)))

    # ── hydraulic jack: split barrel (upper) / rod (lower) ────────────────
    # Jack STL x=[18,30] is already at the rear (+x). No z-rotation needed.
    jack_m = load_stl_trimesh("06_hydraulic_jack.stl")
    Z_CUT = 30.0
    barrel_m = clip_trimesh(jack_m, Z_CUT, keep_above=True)
    rod_m    = clip_trimesh(jack_m, Z_CUT, keep_above=False)
    barrel_col = "#d8dae0"
    rod_col    = "#b0b2b8"
    barrel_actor = plot.add_mesh(trimesh_to_pv(barrel_m), color=barrel_col,
                                 smooth_shading=True, show_edges=False)
    rod_actor    = plot.add_mesh(trimesh_to_pv(rod_m), color=rod_col,
                                 smooth_shading=True, show_edges=False)

    # cumulative arc for wheel spin
    arcs = [0.0] * (N_FRAMES + 1)
    prev = pose_at(1)
    for f in range(2, N_FRAMES + 1):
        px = pose_at(f)
        arcs[f] = arcs[f - 1] + math.hypot(px[0] - prev[0], px[1] - prev[1])
        prev = px

    # ── camera ────────────────────────────────────────────────────────────
    cam_x = (BASE + TOP_X) / 2
    cam_z = TOP_Z / 2
    plot.camera.position = (cam_x, -380, cam_z + 15)
    plot.camera.focal_point = (cam_x, 0, cam_z)
    plot.camera.up = (0, 0, 1)
    plot.camera.view_angle = 55

    # ── nose-engagement markers ────────────────────────────────────────────
    # A green sphere just in FRONT of the stair face at each corner currently
    # gripped by the belt run (y outside the solid stair blocks).
    markers = []
    for i in range(STAIR_COUNT + 1):
        nx = BASE + i * STAIR_TREAD
        nz = GROUND_Z + i * STAIR_RISER
        spr = pv.Sphere(radius=2.6, center=(nx, -(y_half + 2), nz + 0.4))
        act = plot.add_mesh(spr, color="#2ee84f", smooth_shading=True)
        act.SetVisibility(False)
        markers.append(act)

    # ── animate ───────────────────────────────────────────────────────────
    for f in range(from_frame, to_frame + 1):
        wx, gz, tilt = pose_at(f)
        root = root_matrix(wx, gz, tilt)
        seat = root @ ry(-tilt)

        spin = arcs[f]
        for parent, _, off, spin_r, actor in actors:
            if spin_r is not None:
                T = translate(*off) @ ry(spin / spin_r)
            else:
                T = translate(*off)
            actor.user_matrix = (root if parent == "root" else seat) @ T

        # Hydraulic: barrel stays with seat, rod slides down by extension.
        # The STL bakes the mount at STL_JACK_X; shift to honour MOUNT_X.
        ext = jack_extension(f)
        jx = MOUNT_X - STL_JACK_X
        barrel_actor.user_matrix = seat @ translate(jx, 0, 0)
        rod_actor.user_matrix = seat @ translate(jx, 0, -ext)

        # show only noses currently engaged
        engaged = set(engaged_noses(f))
        for i, a in enumerate(markers):
            a.SetVisibility(i in engaged)

        plot.render()
        plot.screenshot(os.path.join(OUT, "frame_%04d.png" % f))

    print("Done — frames in", OUT)
    plot.close()

    if shutil.which("ffmpeg"):
        import subprocess
        outmp4 = os.path.join(HERE, "renders_light",
                              "climb_demo_%s.mp4" % MODE)
        subprocess.run([
            "ffmpeg", "-y", "-framerate", "30", "-i",
            os.path.join(OUT, "frame_%04d.png"), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-profile:v", "main", outmp4],
            check=True)
        print("Movie:", outmp4)


if __name__ == "__main__":
    main()
