import * as THREE from "three";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as RAPIER from "@dimforge/rapier3d";

// ── geometry (cm) — mirrors vlee_stl_pyvista.py ────────────────────────────
// pyvista frames: x = along stairs (+ toward stairs), y = across, z = up.
// three frames:   x = along, y = up (world), z = across.
// Mapping for parts: (px, py, pz) -> (px, pz, py).  Tilt is about the across
// axis -> three rotates about z.
const IDLER_X  = 41, IDLER_Z = 16, TRACK_R = 11.5, TRACK_CY = 28;
const GROUND_Z = 4.5, ROAD_Z = 13, ROAD_POS = [-22, -6, 10, 24];
const STAIR_X = 60, STAIR_TREAD = 32, STAIR_RISER = 16, STAIR_COUNT = 5;
const STAIR_ANGLE = Math.atan2(STAIR_RISER, STAIR_TREAD);
const BASE = STAIR_X, TOP_X = BASE + STAIR_COUNT * STAIR_TREAD;
const TOP_Z = GROUND_Z + STAIR_COUNT * STAIR_RISER;
const BELT_Z_OFF = GROUND_Z - 3.0;           // belt STL bottom z=3.0 -> GROUND_Z
const MOUNT_X = 10.0;                        // jack mount (decision)
const TILT = -STAIR_ANGLE;                   // pyvista tilt -> three rot about z

const BELT = IDLER_Z - TRACK_R;              // belt bottom run height in chair frame

// world: three axes. gravity -y.
// A helper the recorder uses to persist chosen params
export const PARAMS = {
  chassisMass: 80,     // kg (chair, no rider)
  driveForce: 25000,   // dyn/impulse per tick at sprocket edge (ma)
  pitchTorque: 6e7,    // servo torque standing in for hydraulic
  tiltTarget: TILT,
  maxForward: 8.0,     // m/s limit
};

let renderer, scene, camera;
let world, ed;                 // rapier world, event defaults
let chassis;                   // rapier body
let chairGroup;
let spinMeshes = [];

// physics bodies we save
const B = {};

function susXYZ(x, y, z) { return new THREE.Vector3(x, y, z); }

async function loadSTLs() {
  const loader = new STLLoader();
  const files = [
    "01_armrest_pair.stl", "02_bucket_seat.stl", "03_chassis_axles.stl",
    "04_drive_sprocket.stl", "05_footrest_assembly.stl", "07_idler_wheel.stl",
    "08_road_wheel.stl", "09_seat_L_bracket.stl", "10_suspension_beam.stl",
    "11_suspension_bushing_unit.stl", "12_track_belt.stl",
  ];
  const geos = {};
  for (const f of files) {
    const g = await loader.loadAsync("stl/" + f);
    g.computeVertexNormals();
    // map pyvista (x,y,z) -> three (x, z, y): geometry is drawn in pyvista coords
    g.rotateX(-Math.PI / 2);
    geos[f.slice(0, 2)] = g;
  }
  return geos;
}

async function buildPhysics() {
  await RAPIER.init();
  world = new RAPIER.World({ x: 0, y: -981, z: 0 });
  const bodies = world.bodies;
  ed = new RAPIER.EventQueue(false);

  // static ground
  const gb = bodies.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -5, 0));
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(999, 5, 999), gb);

  // stairs
  for (let i = 0; i < STAIR_COUNT; i++) {
    const x0 = BASE + i * STAIR_TREAD, z0 = GROUND_Z + i * STAIR_RISER;
    const sb = bodies.createRigidBody(
      RAPIER.RigidBodyDesc.fixed().setTranslation(x0 + STAIR_TREAD / 2, z0 + STAIR_RISER / 2, 0));
    bodies.createCollider(RAPIER.ColliderDesc.cuboid(STAIR_TREAD / 2, STAIR_RISER / 2, 400), sb);
  }
  const lb = bodies.createRigidBody(
    RAPIER.RigidBodyDesc.fixed().setTranslation(TOP_X + 100, TOP_Z + 5, 0));
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(120, 5, 400), lb);

  // ---- chair ----
  const cd = RAPIER.RigidBodyDesc.dynamic()
    .setAdditionalMass(PARAMS.chassisMass)
    .setTranslation(-150, 60, 0)          // start dropped high
    .setAngularDamping(0.6)
    .setLinearDamping(0.1)
    .setCcdEnabled(true);
  chassis = bodies.createRigidBody(cd);
  // main approximation collider (real mass visual from STL; collision from boxes)
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(45, 14, 10), chassis);           // track frame
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(30, 18, 12), chassis);           // seat mass
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(20, 6, 8), chassis);             // foot
  // belt-bottom run: thin slab per side so stairs noses can wedge under
  for (const s of [-1, 1]) {
    const coll = RAPIER.ColliderDesc
      .cuboid(IDLER_X, 2, 2.5)
      .setTranslation(s * TRACK_CY / 2, 0.8, 0)
      .setFriction(1.0);
    bodies.createCollider(coll, chassis);
  }
  return bodies;
}

function buildScene(geos) {
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setClearColor(0x26282c);
  renderer.setSize(1280, 720);
  camera = new THREE.PerspectiveCamera(55, 1280 / 720, 1, 4000);
  scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x404060, 1.1));
  const dir = new THREE.DirectionalLight(0xffffff, 1.4);
  dir.position.set(150, 180, 80);
  scene.add(dir);
  const dir2 = new THREE.DirectionalLight(0xffffff, 0.5);
  dir2.position.set(-120, 80, -60);
  scene.add(dir2);

  const boxG = new THREE.BoxGeometry();
  const matGround = new THREE.MeshStandardMaterial({ color: 0x3a3d42, roughness: 0.95 });
  const g = new THREE.Mesh(boxG, matGround);
  g.scale.set(999, 10, 999); g.position.set(0, -5, 0);
  scene.add(g);

  const matStep = new THREE.MeshStandardMaterial({ color: 0x5a5d62, roughness: 0.9 });
  for (let i = 0; i < STAIR_COUNT; i++) {
    const x0 = BASE + i * STAIR_TREAD, z0 = GROUND_Z + i * STAIR_RISER;
    const m = new THREE.Mesh(boxG, matStep);
    m.scale.set(STAIR_TREAD, STAIR_RISER, 800);
    m.position.set(x0 + STAIR_TREAD / 2, z0 + STAIR_RISER / 2, 0);
    scene.add(m);
  }
  const landing = new THREE.Mesh(boxG, matStep);
  landing.scale.set(240, 10, 800);
  landing.position.set(TOP_X + 120, TOP_Z + 5, 0);
  scene.add(landing);

  // ── chair assembly (three coords; parts already axis-mapped) ──────────
  chairGroup = new THREE.Group();
  scene.add(chairGroup);

  const mat = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.72, metalness: 0.18 });
  const colors = {
    "01": 0xd8dae0, "02": 0x7a4a28, "03": 0x56595e, "04": 0x111112,
    "05": 0xd8dae0, "07": 0x111112, "08": 0x111112, "09": 0xd8dae0,
    "10": 0x56595c, "11": 0x1b1b1e, "12": 0x1b1b1e,
  };
  const put = (mesh, x, y, z) => { mesh.position.set(x, y, z); chairGroup.add(mesh); return mesh; };

  // two belt halves visual (STL belt already spans full plane? just place once)
  const belt = new THREE.Mesh(geos["12"], mat(colors["12"]));
  belt.position.set(0, 0, BELT_Z_OFF);
  chairGroup.add(belt);

  for (const side of [-1, 1]) {
    // wheels: adapter so wheel spin axis = x
    const wheel = (geo, col, x, z) => {
      const mesh = new THREE.Mesh(geo, mat(col));
      mesh.position.set(x, side * TRACK_CY / 2, z);
      chairGroup.add(mesh);
      spinMeshes.push(mesh);
      return mesh;
    };
    wheel(geos["07"], colors["07"], -IDLER_X / 1, IDLER_Z);   // idler front
    wheel(geos["04"], colors["04"], IDLER_X, IDLER_Z);         // sprocket rear
    for (const rx of ROAD_POS) wheel(geos["08"], colors["08"], rx, ROAD_Z);
    const beam = new THREE.Mesh(geos["10"], mat(colors["10"]));
    beam.position.set(0, side * TRACK_CY / 2, 0);
    chairGroup.add(beam);
    const bushing = new THREE.Mesh(geos["11"], mat(colors["11"]));
    bushing.position.set(0, side * TRACK_CY / 2, 0);
    chairGroup.add(bushing);
  }

  // seat group stays level (compensates tilt) — matches pyvista seat=root@ry(-tilt)
  B.seat = new THREE.Group();
  chairGroup.add(B.seat);
  const addSeat = (geo, col) => {
    const m = new THREE.Mesh(geo, mat(col));
    B.seat.add(m);
    return m;
  };
  addSeat(geos["09"], colors["09"]);   // brackets
  addSeat(geos["02"], colors["02"]);   // bucket
  addSeat(geos["01"], colors["01"]);   // armrests
  addSeat(geos["05"], colors["05"]);   // footrest
  const ax = new THREE.Mesh(geos["03"], mat(colors["03"]));
  chairGroup.add(ax);

  // camera
  const cx = (BASE + TOP_X) / 2;
  camera.position.set(cx, 220, -380);
  camera.lookAt(cx, 120, 0);
}

let tick = 0;
let spin = 0;

function stepController() {
  const t = chassis.translation();
  const v = chassis.linvel();
  // clamp spin visual
  spin += v.x * 0.15;
  for (const m of spinMeshes) m.rotation.x = spin;

  // seat compensation: keep seat group world-level = chair tilt inverse
  const r = chassis.rotation();
  B.seat.quaternion.set(-r.x, -r.y, -r.z, r.w);
}

function syncPose() {
  const t = chassis.translation();
  const r = chassis.rotation();
  chairGroup.position.set(t.x, t.y, t.z);
  chairGroup.quaternion.set(r.x, r.y, r.z, r.w);
  stepController();
}

let tAcc = 0;

// phases for a believable climb: DROP (settle), APPR (roll to stairs),
// TILT (pitch servo to STAIR_ANGLE, belt onto noses), DRIVE (sprocket force
// up the slope), LEVEL (on landing).
const PHASES = {
  DROP:  [0, 90],
  APPR:  [90, 210],
  TILT:  [210, 300],
  DRIVE: [300, 700],
  LEVEL: [700, 780],
};

function phaseOf(tick) {
  for (const [name, [a, b]] of Object.entries(PHASES)) {
    if (tick >= a && tick < b) return name;
  }
  return "LEVEL";
}

function step() {
  const t = chassis.translation();
  const ph = phaseOf(tick);
  let fx = 0, fy = 0, tau = 0, tx = 0, ty = 0, tz = 0;

  if (ph === "APPR") {
    // roll toward stairs, belt stays flat on ground
    fx = 3000;
  } else if (ph === "TILT") {
    // ease tilt to STAIR_ANGLE (hydraulic servo), stop forward
    const p = Math.min(1, (tick - PHASES.TILT[0]) / (PHASES.TILT[1] - PHASES.TILT[0]));
    ty = -p * STAIR_ANGLE;              // target pitch (nose up = rotate +z?)
    tx = 0;
    // proportional pitch servo toward target about world z
    const ang = chassis.rotation();
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
  } else if (ph === "DRIVE") {
    ty = -STAIR_ANGLE;
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
    // drive along the stair slope: force at rear sprocket pointing forward+down
    const slope = STAIR_RISER / STAIR_TREAD;
    fx = 12000;
    if (t.x > BASE) fy = -12000 * slope;
  } else if (ph === "LEVEL") {
    ty = 0;
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
    fx = t.x < TOP_X + 40 ? 8000 : 0;
  }

  if (tick === PHASES.TILT[0]) { /* marker */ }
  const f = { x: fx, y: fy, z: 0 };
  if (fx || fy) chassis.applyImpulse(f, true);
  if (tau) chassis.applyTorqueImpulse({ x: 0, y: 0, z: tau }, true);

  world.step();
  tick++;
}

function currentPitchAng() {
  const q = chassis.rotation();
  // euler z from quaternion
  return Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
}

function clampAngle(a) {
  if (a > Math.PI) a -= 2 * Math.PI;
  if (a < -Math.PI) a += 2 * Math.PI;
  return a;
}

function render() {
  renderer.render(scene, camera);
}

export async function createSim() {
  await RAPIER.init();
  const geos = await loadSTLs();
  buildScene(geos);
  buildPhysics();
  return { step: () => { step(); syncPose(); }, render, camera, renderer, getTick: () => tick };
}