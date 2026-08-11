# Vlee B1000 — Stair-Climb Mechanism Reference

Reference doc for reproducing & reasoning about the tracked-wheelchair stair
climb. Coordinates follow the SCAD/prototype model: **1 unit = 1 cm**, +x forward
(rear toward the stairs), +z up, wheels spin about y.

Authoritative sources in the repo:

| File | Role |
|---|---|
| `SCAD/parameters.scad` | all dimensions + materials |
| `SCAD/track.scad` | belt + wheel geometry |
| `SCAD/hydraulic.scad` | actuator + `tiltedTrack()` |
| `SCAD/animate.scad` | (older) pivot + tilt-from-extension |
| `SCAD/prototype.scad` | full assembly |
| `vlee_stl_v1.py` | Blender 4.0 reference animation |
| `vlee_stl_pyvista.py` | PyVista rewrite (current) |

---

## 1. Dimensions you need (from `parameters.scad`)

```
trackLength   = 82          -> idlerX = ±41 (wheel centres)
trackWidth    = 14
trackCenterY  = 28          (tracks sit at y = ±28)
idlerRadius   = 10          (idler + drive sprocket)
idlerX        = 41
idlerZ        = 16          (wheel-centre height)
roadRadius    = 7
roadZ         = 13
roadPositions = [-22, -6, 10, 24]
trackRadius   = 11.5        (= idlerRadius + linkThickness/2; belt centerline)
beltThickness = 3           -> belt OUTER cap radius = 13.0, inner = 10.0
groundZ       = 4.5         = idlerZ - trackRadius   (bottom of track)

liftPivotX    = idlerX      (pivot point; see Motion)
liftPivotZ    = idlerZ

chassisBottom = 35
chassisLength = 82

hydrMountX    = 24
hydrMountY    = 0
hydrExtend    = 26.5        (full stroke, cm)
hydrWheelRadius = 4
hydrBarrelHeight = 12
hydrRodRadius   = 2

seatTopOffset = 45 - trackRadius          # seat pan ends up 45 cm above ground
```

Assembly-positioned STLs (offsets baked in): `01 armrest_pair`, `02 bucket_seat`,
`03 chassis_axles`, `05 footrest_assembly`, `06 hydraulic_jack`.
Centered STLs (need explicit placement): `04 drive_sprocket` → `(+idlerX,±28,idlerZ)`,
`07 idler_wheel` → `(-idlerX,±28,idlerZ)`, `08 road_wheel` → `(roadPositions,±28,roadZ)`,
`09 seat bracket` (built at y=24, mirror to ±15), `10 suspension_beam`,
`11 bushing_unit`, `12 track_belt` → `(0,±28,0)`.

---

## 2. The 6-phase cycle

The chair backs toward the stairs (rear = +x = jack/sprocket side faces the
stairs). Frame ranges below are the 420-frame / 30 fps reference. Modes:

| Mode | Choreography | Frame table |
|---|---|---|
| `a` | lift full tilt on flat, retract on flat, roll the tilted belt onto the slope (legacy — leaning on flat is not physically real) | APP 1–90 · LIFT 90–150 · RETRACT 150–180 · SEAT 180–270 · CLIMB 270–360 · TOP 360–420 |
| `b` | lift, keep leg planted while rolling to x=57, tuck & seat (legacy) | APP 1–90 · LIFT 90–150 · ROLL 150–200 · RETRACT 200–270 · CLIMB 270–360 · TOP 360–420 |
| `c` | **preferred**: butt belt cap to first riser, wrap nose 1 with leg PLANTED, roll with leg planted+rolling until belt seats on 3 noses, then tuck leg and climb | APP 1–90 · GRIP 90–150 · ROLL 150–210 · SEATX 210–270 · CLIMB 270–360 · TOP 360–420 |

### P1 APPROACH  (f 1–90)   flat roll
Chair rolls flat on the ground, rear (+x) leading, stopping on level ground with
the front idler a comfortable margin ahead of the first riser and the jack wheel
still over flat floor.

### P2 JACK LIFT  (f 90–180)   tilt in place
The actuator extends **once**. Its wheels push the flat floor **down** at
`x = hydrMountX = 24`. The front **idler (−x) is planted** (it pivots), so the
rear (**+x**) rises. The whole track tilts up at the stair angle; the belt now
forms the hypotenuse of the (flat, riser, belt) triangle. The **seat
counter-rotates to stay level** (rotates −tilt about the front pivot).

### P3 ALIGN  (f 180–240)   roll the belt onto the slope
Still on flat ground, the extended jack wheels **roll the chair forward**, pressing
the tilted belt underside against the stair nose line until belt angle =
stair angle. No further extension/retraction here.

### P4 JACK RETRACT  (f 240–270)   settle
Actuator relaxes; the track settles so its straight bottom run rests on the stair
noses, the front idler still at the bottom step.

### P5 CLIMB  (f 270–360)   drive up
The tracks drive the chair up all N steps along the stair-nose line. The seat
stays **level** the whole way. The jack is now fully retracted and **stowed above
the belt — it plays no part during the climb.**

### P6 TOP TRANS  (f 360–420)   crest + level
At the landing the chair crests onto the flat and the track levels out to 0 tilt.
**No second hydraulic stroke** (confirmed correction — animate.scad's leveling
was superseded).

---

## 3. Kinematics (what the code actually computes)

Pivot pinning — the front belt-contact stays at world `(wx, gz)` while the body
rotates by `tilt`:

```
BELT = idlerZ - trackRadius              # 4.5  (belt-bottom height in ROOT space)
c, s = cos(tilt), sin(tilt)
lx   = -idlerX * c + BELT * s            # local offset of contact point
lz   =  idlerX * s + BELT * c
ROOT = translate(wx - lx, 0, gz - lz) @ ry(tilt)
SEAT = ROOT @ ry(-tilt)                  # level seat
WHEEL = ROOT @ translate(wheel_off) @ ry(spin / wheel_r)   # spin in place
```

Key numbered facts (verified in this analysis):

- Jack wheel **bottom at full extension** = `chassisBottom − hydrExtend − hydrWheelRadius`
  = `35 − 26.5 − 4 = 4.5 = groundZ` → just kisses flat ground. Retracted bottom =
  `31`, which hangs ~2 cm above the belt upper run.
- Barrel bracket bottom (`z=29`) == belt upper-run top (`idlerZ + 13 = 29`).
  The track↔hydraulic "gap" is **vertical adjacency, not a load gap**.
- Climb clearance: with the idler planted on nose *i*, the rear sprocket bottom
  clears the nose *i+1* by `+21` consistently, a margin that **grows on steeper
  stairs** (+30 @ 37°, +26 @ 33°, +24 @ 30° — all inclusive of the linear
  run-contact because the noses are collinear).
- Belt cap radius **13** vs stair riser **16**: the belt wraps ~3 cm less than the
  nose corner, so the riser edge bites the rubber at each transition. Survives by
  flex, but is the one dimension to watch on a real build.

---

## 4. Is the contact "enough"? (the small-touch concern)

The tilted belt hovering over the slope in P3 looks like only a sliver touches the
first nose. That sliver is NOT the climb load — it is only a position trigger:

1. **P3 ALIGN** — belt hovers above the slope (e.g. ~37 cm above the first nose at
   wx=-15); only the leading cap tip touches the first nose at the end of the roll.
   This tap just sets where the track lands; no climbing force is involved yet.
2. **P4 JACK RETRACT** — the belt drops straight onto the nose line. Since the belt
   is tilted at exactly the stair angle (both 26.6°), the **entire 82 cm straight
   bottom run seats onto the nose line simultaneously**, not at a point.

Quantified engagement during P5 CLIMB (verified numerically):

- Nose-to-nose along the slope = √(16² + 32²) = **35.8 cm**
- Belt straight bottom run = **82 cm**
- => up to **3 noses in contact at the same time** (planted one + two more);
  gap = 0.0 at every engaged nose.

Each stair corner is a **positive mechanical hook**: the belt wraps ~13 cm of the
16 cm rise edge and the rubber deforms around it, giving rack-and-hook engagement
rather than flat-face friction. 2–3 such hooks across a 14 cm belt width is ample;
even a single nose is climbable with this mechanism.

---

## 5. Why the track↔hydraulic gap does NOT need to align with the stairs

1. The jack only pushes **flat ground**, and only during P2/P3 (before the climb).
   Guaranteeing it a flat patch is the sole "alignment" that matters.
2. During P5/P6 the jack is retracted and stowed above the belt — it never contacts
   stairs. The climb is carried entirely by the belt bottom run riding the nose
   line.
3. What actually has to reach the stairs is the **belt length** (half-length 41),
   not the jack offset. Distance from jack (x=24) to belt cap (x=54) is purely
   packaging/load-routing.
4. Real physical limit is **motor torque / traction** on the track, not this gap.
   (Verify before finalizing: belt wrap angle × coefficient of friction needed to
   hold reach during P2/P3 and P5.)

---

## 6. Common traps when re-creating this in code

- **Jack z-rotation**: `06_hydraulic_jack.stl` bounds `x=[18,30]` are already at the
  rear — do **not** apply `rot_z(π)` (prevents mirroring it to the wrong side).
- **Seat bracket**: mirror with `scale(1, sy, 1)` only; a second `rot_z(π)` on the
  `sy<0` side undoes the mirror.
- **Jack split**: `06_hydraulic_jack.stl` barrel/rod meet at `z=30.0`;
  rod slides along **−z by the extension**; barrel is a static child of the seat
  group.
- **Belt bottom**: STL belt bottom is `z=3.0`, but `groundZ=4.5` → shift belt up
  `+1.5` so its bottom matches the contact height.
- **Wheel spin**: `translate(off) @ ry(spin/radius)` (spin in place), never
  `ry @ translate` (that orbits the origin).
- **Arc accumulation** for spin: integrate `hypot(dx, dz)` over the **contact
  point** `(px[0], px[1])`, not arbitrary indices.

---

## 8. Real-mechanics feasibility (gravity included)

The animations are pitch material only. These are the numbers a real chair
must satisfy (all derived from the BOM masses + SCAD geometry, 1:1 scale):

### Mass model (used below)
```
chassis empty:   77.4 kg   COM(root) x=+1.2, z=28.8
occupant:       120 kg     COM x≈+2..+6, z≈58          (seated)
total:          197 kg     COM x≈+1.7..+4.1, z≈46.5    (root frame)
```
`x=0` is between the idlers, belt half-length ±41, belt bottom 4.5 above the
ground plane. +x is rear (toward the stairs).

### Feasibility gates

| # | Check | Result | Verdict |
|---|---|---|---|
| 1 | Flat approach: COM x inside belt-run support [−41, +41] | +1.7..+4.1 in range | PASS |
| 2 | Jack-planted roll over nose 1/2: COM between front belt grip and rear jack wheel | COM ahead of front contact, inside | PASS* |
| 3 | **Friction on the slope** | required μ = tan 26.6° = **0.50**; rubber-on-edge 0.7–1.0 | PASS with 1.4–2× margin |
| 4 | **Drive torque (steady climb, two tracks)** | 43 N·m/track steady → **65 N·m** with 1.5× dynamic | 350 W MY1016ZL ≥ 65 N·m ✓ |
| 5 | **Climb power** | 108 W @ 0.2 m/s; 81 W @ 0.15 m/s | 2×350 W way over capacity |
| 6 | **Actuator lift load** (pivot = front idler x=−41, leg at x=24) | **130 kgf** at lift start (flat), 74 kgf at full tilt | 500 kgf actuator → 3.8–6.7× margin |
| 7 | Jack rod/barrel vs stair solids, exact mesh intersection, all 420 frames | **0 real contacts** | PASS |

\* Gate 2 is conditional: momentum of the roll and the belt-nose hook are what
keep the COM inside during the planted-leg phase; see the pitch note below.

### The one thing statics does NOT give you: mid-climb pitch

A frame-by-frame COM vs engaged-nose polygon shows the whole 82 cm belt run
does **not** reach a front-upper *and* rear-lower nose simultaneously at every
instant. During the 2-nose windows (~17–54 frames of the climb) the COM
projects up to **13–37 cm up-slope of the top tooth**. Two effects carry it
(so it is still a real machine, not a card-house):

1. **Rack-and-hook grip** — each nose wraps ~13 cm of the 16 cm rise; the teeth
   physically prevent down-slope slip regardless of μ.
2. **Belt wrap + drive torque** — the sprocket pull keeps the lower run tensioned
   against the noses; pitch is *held*, not *balanced*.

Practical consequence for the build: never operate the drive de-energised while
on stairs (add an electro-brake / hold position), and keep the occupant COM low
and centered. A longer belt (or a front flipper) would raise the 2↔3-nose duty
cycle — belt length is the lever you have left.

### Which demo to believe

Modes **a / b** are legacy choreographies and both retract/roll in ways that
only exist because the renderer pins the pose. **Mode c (`VLEE_MODE=c`) is the
physically defensible sequence**:
`butt (belt cap to first riser) → wrap nose 1 with jack PLANTED → roll forward
with the leg planted+rolling → belt seats on 3 noses → tuck the leg → climb`.
The chair never leans unsupported on flat ground. Renders to
`renders_light/climb_demo_c.mp4` (see §2 for the frame table).

---

## 9. Stair parameters used for rendering

```
STAIR_X     = 60     (first riser x)
STAIR_TREAD = 32     (run)
STAIR_RISER = 16     (rise)  -> angle 26.6°
STAIR_COUNT = 5
STAIR_ANGLE = atan2(16, 32)
```

For reference: steeper stairs (18/24 = 37°) clear even better on the rear-nose
check, so geometry is not the binding constraint for typical building stairs.