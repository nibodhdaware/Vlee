// src/sim.js
import * as THREE from "three";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as RAPIER from "@dimforge/rapier3d";
var IDLER_X = 41;
var IDLER_Z = 16;
var TRACK_R = 11.5;
var TRACK_CY = 28;
var GROUND_Z = 4.5;
var ROAD_Z = 13;
var ROAD_POS = [-22, -6, 10, 24];
var STAIR_X = 60;
var STAIR_TREAD = 32;
var STAIR_RISER = 16;
var STAIR_COUNT = 5;
var STAIR_ANGLE = Math.atan2(STAIR_RISER, STAIR_TREAD);
var BASE = STAIR_X;
var TOP_X = BASE + STAIR_COUNT * STAIR_TREAD;
var TOP_Z = GROUND_Z + STAIR_COUNT * STAIR_RISER;
var BELT_Z_OFF = GROUND_Z - 3;
var TILT = -STAIR_ANGLE;
var BELT = IDLER_Z - TRACK_R;
var PARAMS = {
  chassisMass: 80,
  // kg (chair, no rider)
  driveForce: 25e3,
  // dyn/impulse per tick at sprocket edge (ma)
  pitchTorque: 6e7,
  // servo torque standing in for hydraulic
  tiltTarget: TILT,
  maxForward: 8
  // m/s limit
};
var renderer;
var scene;
var camera;
var world;
var ed;
var chassis;
var chairGroup;
var spinMeshes = [];
var B = {};
async function loadSTLs() {
  const loader = new STLLoader();
  const files = [
    "01_armrest_pair.stl",
    "02_bucket_seat.stl",
    "03_chassis_axles.stl",
    "04_drive_sprocket.stl",
    "05_footrest_assembly.stl",
    "07_idler_wheel.stl",
    "08_road_wheel.stl",
    "09_seat_L_bracket.stl",
    "10_suspension_beam.stl",
    "11_suspension_bushing_unit.stl",
    "12_track_belt.stl"
  ];
  const geos = {};
  for (const f of files) {
    const g = await loader.loadAsync("stl/" + f);
    g.computeVertexNormals();
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
  const gb = bodies.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -5, 0));
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(999, 5, 999), gb);
  for (let i = 0; i < STAIR_COUNT; i++) {
    const x0 = BASE + i * STAIR_TREAD, z0 = GROUND_Z + i * STAIR_RISER;
    const sb = bodies.createRigidBody(
      RAPIER.RigidBodyDesc.fixed().setTranslation(x0 + STAIR_TREAD / 2, z0 + STAIR_RISER / 2, 0)
    );
    bodies.createCollider(RAPIER.ColliderDesc.cuboid(STAIR_TREAD / 2, STAIR_RISER / 2, 400), sb);
  }
  const lb = bodies.createRigidBody(
    RAPIER.RigidBodyDesc.fixed().setTranslation(TOP_X + 100, TOP_Z + 5, 0)
  );
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(120, 5, 400), lb);
  const cd = RAPIER.RigidBodyDesc.dynamic().setAdditionalMass(PARAMS.chassisMass).setTranslation(-150, 60, 0).setAngularDamping(0.6).setLinearDamping(0.1).setCcdEnabled(true);
  chassis = bodies.createRigidBody(cd);
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(45, 14, 10), chassis);
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(30, 18, 12), chassis);
  bodies.createCollider(RAPIER.ColliderDesc.cuboid(20, 6, 8), chassis);
  for (const s of [-1, 1]) {
    const coll = RAPIER.ColliderDesc.cuboid(IDLER_X, 2, 2.5).setTranslation(s * TRACK_CY / 2, 0.8, 0).setFriction(1);
    bodies.createCollider(coll, chassis);
  }
  return bodies;
}
function buildScene(geos) {
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setClearColor(2500652);
  renderer.setSize(1280, 720);
  camera = new THREE.PerspectiveCamera(55, 1280 / 720, 1, 4e3);
  scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(16777215, 4210784, 1.1));
  const dir = new THREE.DirectionalLight(16777215, 1.4);
  dir.position.set(150, 180, 80);
  scene.add(dir);
  const dir2 = new THREE.DirectionalLight(16777215, 0.5);
  dir2.position.set(-120, 80, -60);
  scene.add(dir2);
  const boxG = new THREE.BoxGeometry();
  const matGround = new THREE.MeshStandardMaterial({ color: 3816770, roughness: 0.95 });
  const g = new THREE.Mesh(boxG, matGround);
  g.scale.set(999, 10, 999);
  g.position.set(0, -5, 0);
  scene.add(g);
  const matStep = new THREE.MeshStandardMaterial({ color: 5922146, roughness: 0.9 });
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
  chairGroup = new THREE.Group();
  scene.add(chairGroup);
  const mat = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.72, metalness: 0.18 });
  const colors = {
    "01": 14211808,
    "02": 8014376,
    "03": 5658974,
    "04": 1118482,
    "05": 14211808,
    "07": 1118482,
    "08": 1118482,
    "09": 14211808,
    "10": 5658972,
    "11": 1776414,
    "12": 1776414
  };
  const put = (mesh, x, y, z) => {
    mesh.position.set(x, y, z);
    chairGroup.add(mesh);
    return mesh;
  };
  const belt = new THREE.Mesh(geos["12"], mat(colors["12"]));
  belt.position.set(0, 0, BELT_Z_OFF);
  chairGroup.add(belt);
  for (const side of [-1, 1]) {
    const wheel = (geo, col, x, z) => {
      const mesh = new THREE.Mesh(geo, mat(col));
      mesh.position.set(x, side * TRACK_CY / 2, z);
      chairGroup.add(mesh);
      spinMeshes.push(mesh);
      return mesh;
    };
    wheel(geos["07"], colors["07"], -IDLER_X / 1, IDLER_Z);
    wheel(geos["04"], colors["04"], IDLER_X, IDLER_Z);
    for (const rx of ROAD_POS) wheel(geos["08"], colors["08"], rx, ROAD_Z);
    const beam = new THREE.Mesh(geos["10"], mat(colors["10"]));
    beam.position.set(0, side * TRACK_CY / 2, 0);
    chairGroup.add(beam);
    const bushing = new THREE.Mesh(geos["11"], mat(colors["11"]));
    bushing.position.set(0, side * TRACK_CY / 2, 0);
    chairGroup.add(bushing);
  }
  B.seat = new THREE.Group();
  chairGroup.add(B.seat);
  const addSeat = (geo, col) => {
    const m = new THREE.Mesh(geo, mat(col));
    B.seat.add(m);
    return m;
  };
  addSeat(geos["09"], colors["09"]);
  addSeat(geos["02"], colors["02"]);
  addSeat(geos["01"], colors["01"]);
  addSeat(geos["05"], colors["05"]);
  const ax = new THREE.Mesh(geos["03"], mat(colors["03"]));
  chairGroup.add(ax);
  const cx = (BASE + TOP_X) / 2;
  camera.position.set(cx, 220, -380);
  camera.lookAt(cx, 120, 0);
}
var tick = 0;
var spin = 0;
function stepController() {
  const t = chassis.translation();
  const v = chassis.linvel();
  spin += v.x * 0.15;
  for (const m of spinMeshes) m.rotation.x = spin;
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
var PHASES = {
  DROP: [0, 90],
  APPR: [90, 210],
  TILT: [210, 300],
  DRIVE: [300, 700],
  LEVEL: [700, 780]
};
function phaseOf(tick2) {
  for (const [name, [a, b]] of Object.entries(PHASES)) {
    if (tick2 >= a && tick2 < b) return name;
  }
  return "LEVEL";
}
function step() {
  const t = chassis.translation();
  const ph = phaseOf(tick);
  let fx = 0, fy = 0, tau = 0, tx = 0, ty = 0, tz = 0;
  if (ph === "APPR") {
    fx = 3e3;
  } else if (ph === "TILT") {
    const p = Math.min(1, (tick - PHASES.TILT[0]) / (PHASES.TILT[1] - PHASES.TILT[0]));
    ty = -p * STAIR_ANGLE;
    tx = 0;
    const ang = chassis.rotation();
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
  } else if (ph === "DRIVE") {
    ty = -STAIR_ANGLE;
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
    const slope = STAIR_RISER / STAIR_TREAD;
    fx = 12e3;
    if (t.x > BASE) fy = -12e3 * slope;
  } else if (ph === "LEVEL") {
    ty = 0;
    tau = PARAMS.pitchTorque * clampAngle(ty - currentPitchAng());
    fx = t.x < TOP_X + 40 ? 8e3 : 0;
  }
  if (tick === PHASES.TILT[0]) {
  }
  const f = { x: fx, y: fy, z: 0 };
  if (fx || fy) chassis.applyImpulse(f, true);
  if (tau) chassis.applyTorqueImpulse({ x: 0, y: 0, z: tau }, true);
  world.step();
  tick++;
}
function currentPitchAng() {
  const q = chassis.rotation();
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
async function createSim() {
  await RAPIER.init();
  const geos = await loadSTLs();
  buildScene(geos);
  buildPhysics();
  return { step: () => {
    step();
    syncPose();
  }, render, camera, renderer, getTick: () => tick };
}
export {
  PARAMS,
  createSim
};
