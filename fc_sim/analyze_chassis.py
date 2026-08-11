import sys, math, csv, os
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil
import ObjectsFem as O
from femtools.ccxtools import FemToolsCcx
from femmesh.gmshtools import GmshTools

# CSV log
csv_path = "/home/nibodhdaware/Developer/Vlee/fc_sim/fea_results.csv"
_write_header = not os.path.exists(csv_path)

def log_result(name, max_vm, max_disp, sf, notes=""):
    global _write_header
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if _write_header:
            w.writerow(["part", "load_N", "max_von_mises_MPa", "max_disp_mm", "safety_factor", "yield_MPa", "notes"])
            _write_header = False
        w.writerow([name, 981, f"{max_vm:.2f}", f"{max_disp:.4f}", f"{sf:.2f}", 276, notes])

# CCX setup
CCX_DIR = "/home/nibodhdaware/.local/share/flatpak/app/org.freecad.FreeCAD/x86_64/stable/aa6792b7683c709b78bf533d6c05d71fb339b13898339a12e06e86b006208ad0/files/bin"
LIB_DIR = "/home/nibodhdaware/.local/share/flatpak/app/org.freecad.FreeCAD/x86_64/stable/aa6792b7683c709b78bf533d6c05d71fb339b13898339a12e06e86b006208ad0/files/lib"
import os, shutil
os.environ["PATH"] = CCX_DIR + ":" + os.environ.get("PATH", "")
os.environ["LD_LIBRARY_PATH"] = LIB_DIR + ":" + os.environ.get("LD_LIBRARY_PATH", "")
CCX_BIN = shutil.which("ccx") or os.path.join(CCX_DIR, "ccx")
WORK = "/home/nibodhdaware/Developer/Vlee/fc_sim/fem"
os.makedirs(WORK, exist_ok=True)
MATERIAL = {"Name": "AL6061-T6", "YoungsModulus": "68900 MPa", "PoissonRatio": "0.33", "Density": "2700 kg/m^3"}

def setup_ccx_param():
    import FreeCAD as AppF
    p = AppF.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
    p.SetString("ccxBinaryPath", CCX_BIN)

def run_static(obj, fixed_faces, load_faces, force_n, name, element_size=6.0):
    setup_ccx_param()
    doc = App.ActiveDocument
    analysis = O.makeAnalysis(doc, "Analysis_" + name)
    solver = O.makeSolverCalculiXCcxTools(doc, "CalculiXCcxTools")
    solver.AnalysisType = "static"
    solver.GeometricalNonlinearity = "linear"
    analysis.addObject(solver)
    mat = O.makeMaterialSolid(doc, "Mat_" + name)
    mat.Material = dict(MATERIAL)
    analysis.addObject(mat)
    fixed = O.makeConstraintFixed(doc, "Fix_" + name)
    fixed.References = [(obj, f) for f in fixed_faces]
    analysis.addObject(fixed)
    force = O.makeConstraintForce(doc, "Load_" + name)
    force.References = [(obj, f) for f in load_faces]
    force.Force = "%.1f N" % force_n
    force.Reversed = True
    analysis.addObject(force)
    mesh = O.makeMeshGmsh(doc, "Mesh_" + name)
    mesh.Shape = obj
    mesh.ElementDimension = "3D"
    mesh.CharacteristicLengthMin = "1.0 mm"
    mesh.CharacteristicLengthMax = "%.1f mm" % element_size
    mesh.SecondOrderLinear = True
    analysis.addObject(mesh)
    doc.recompute()
    sys.stderr.write("%s: meshing...\n" % name)
    GmshTools(mesh).create_mesh()
    doc.recompute()
    sys.stderr.write("%s: mesh done nodes=%d\n" % (name, mesh.FemMesh.NodeCount))
    fea = FemToolsCcx(analysis, solver)
    fea.set_base_name(name)
    fea.setup_working_dir(WORK)
    ret = fea.run()
    sys.stderr.write("%s: done ret=%s\n" % (name, ret))
    if not ret:
        return None, None, None
    # Extract results
    result_obj = None
    for mbr in analysis.Group:
        if "Result" in mbr.TypeId or "result" in mbr.TypeId.lower():
            result_obj = mbr
            break
    if result_obj is None:
        return None, None, None
    vm = result_obj.vonMises
    max_vm = max(vm) if vm else 0
    # Displacement
    max_disp = 0.0
    if hasattr(result_obj, "DisplacementLengths"):
        disp_len = result_obj.DisplacementLengths
        max_disp = max(disp_len) if disp_len else 0
    sf = 276.0 / max_vm if max_vm > 0 else float('inf')
    return max_vm, max_disp, sf

# ---------- CHASSIS ANALYSIS ----------
doc = App.newDocument("Chassis")
chassis_solids = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
if not isinstance(chassis_solids, list):
    chassis_solids = [chassis_solids]

for solid_idx, chassis in enumerate(chassis_solids):
    obj = doc.addObject("Part::Feature", "chassis_%d" % solid_idx)
    obj.Shape = chassis
    doc.recompute()

    # Face mapping
    print("Chassis %d faces:" % solid_idx, obj.Shape.Faces.__len__())
    # Bracket clamp: left axle at x≈-41, right axle at x≈+41, both at z≈11-12, y≈±7.7
    axle_x = -41.0 if solid_idx == 0 else 41.0
    bracket_y = 7.7
    bracket_z = 12.0 if solid_idx == 0 else 11.5
    bracket_faces_pos = []
    bracket_faces_neg = []
    ground_faces = []

    for i, face in enumerate(obj.Shape.Faces):
        c = face.CenterOfMass
        # Bracket clamp at y≈+7.7 and y≈-7.7
        if abs(c.y - bracket_y) < 2 and abs(c.x - axle_x) < 5 and abs(c.z - bracket_z) < 3:
            dist = math.sqrt((c.x-axle_x)**2 + (c.z-bracket_z)**2)
            if 3.0 < dist < 7.0:
                bracket_faces_pos.append("Face%d" % (i+1))
        if abs(c.y + bracket_y) < 2 and abs(c.x - axle_x) < 5 and abs(c.z - bracket_z) < 3:
            dist = math.sqrt((c.x-axle_x)**2 + (c.z-bracket_z)**2)
            if 3.0 < dist < 7.0:
                bracket_faces_neg.append("Face%d" % (i+1))
        # Ground contact: lowest z faces
        if c.z < 10.5:  # z≈9 is bottom
            ground_faces.append("Face%d" % (i+1))

    print("Axle x=%.0f: bracket +Y faces: %s" % (axle_x, bracket_faces_pos))
    print("Axle x=%.0f: bracket -Y faces: %s" % (axle_x, bracket_faces_neg))
    print("Ground faces:", ground_faces[:10], "...")

    # Run: load at +Y bracket, fixed at ground
    if bracket_faces_pos and ground_faces:
        vm, disp, sf = run_static(obj, ground_faces, bracket_faces_pos, 981.0, "chassis_axle%d_posY" % solid_idx, 6.0)
        if vm:
            log_result("chassis_axle%d_posY" % solid_idx, vm, disp, sf, "981N at y=+15 clamp, fixed at ground")
            print("chassis %d +Y: VM=%.1f MPa, disp=%.4f mm, SF=%.2f" % (solid_idx, vm, disp, sf))

    # Run: load at -Y bracket, fixed at ground
    if bracket_faces_neg and ground_faces:
        vm, disp, sf = run_static(obj, ground_faces, bracket_faces_neg, 981.0, "chassis_axle%d_negY" % solid_idx, 6.0)
        if vm:
            log_result("chassis_axle%d_negY" % solid_idx, vm, disp, sf, "981N at y=-15 clamp, fixed at ground")
            print("chassis %d -Y: VM=%.1f MPa, disp=%.4f mm, SF=%.2f" % (solid_idx, vm, disp, sf))

    # Also test combined: both brackets loaded, ground fixed
    if bracket_faces_pos and bracket_faces_neg and ground_faces:
        vm, disp, sf = run_static(obj, ground_faces, bracket_faces_pos + bracket_faces_neg, 981.0, "chassis_axle%d_both" % solid_idx, 6.0)
        if vm:
            log_result("chassis_axle%d_both" % solid_idx, vm, disp, sf, "981N each at y=±15 clamp, fixed at ground")
            print("chassis %d both: VM=%.1f MPa, disp=%.4f mm, SF=%.2f" % (solid_idx, vm, disp, sf))