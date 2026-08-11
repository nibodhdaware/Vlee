import sys, math, csv, os
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil
import ObjectsFem as O
from femtools.ccxtools import FemToolsCcx
from femmesh.gmshtools import GmshTools

csv_path = "/home/nibodhdaware/Developer/Vlee/fc_sim/fea_results.csv"
_write_header = not os.path.exists(csv_path)

def log_result(name, load_n, max_vm, max_disp, sf, notes=""):
    global _write_header
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if _write_header:
            w.writerow(["part", "load_N", "max_von_mises_MPa", "max_disp_mm", "safety_factor", "yield_MPa", "notes"])
            _write_header = False
        w.writerow([name, load_n, f"{max_vm:.2f}", f"{max_disp:.4f}", f"{sf:.2f}", 276, notes])

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
    result_obj = None
    for mbr in analysis.Group:
        if "Result" in mbr.TypeId or "result" in mbr.TypeId.lower():
            result_obj = mbr
            break
    if result_obj is None:
        return None, None, None
    vm = result_obj.vonMises
    max_vm = max(vm) if vm else 0
    max_disp = 0.0
    if hasattr(result_obj, "DisplacementLengths"):
        disp_len = result_obj.DisplacementLengths
        max_disp = max(disp_len) if disp_len else 0
    sf = 276.0 / max_vm if max_vm > 0 else float('inf')
    return max_vm, max_disp, sf

# ---------- SUSPENSION BEAM (part 10) ----------
doc = App.newDocument("Beam")
beam = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/10_suspension_beam.stl")
obj = doc.addObject("Part::Feature", "beam")
obj.Shape = beam
doc.recompute()

print("Beam faces:", obj.Shape.Faces.__len__())
print("Beam bbox:", obj.Shape.BoundBox)

# Beam: x[-33..29], y[25.5..30.5], z[30.5..36.5] - long along X
# End at x≈29 connects to seat bracket (right side, y≈28)
# End at x≈-33 connects to chassis axle
beam_faces_bracket_end = []  # x ≈ 29 (right end)
beam_faces_chassis_end = []  # x ≈ -33 (left end)

for i, face in enumerate(obj.Shape.Faces):
    c = face.CenterOfMass
    # Bracket end: x near +29 (right end of beam)
    if c.x > 25:
        beam_faces_bracket_end.append("Face%d" % (i+1))
    # Chassis end: x near -33 (left end of beam)
    if c.x < -30:
        beam_faces_chassis_end.append("Face%d" % (i+1))

print("Beam bracket-end faces (x≈29):", beam_faces_bracket_end)
print("Beam chassis-end faces (x≈-33):", beam_faces_chassis_end)

# Case 1: Load at bracket end (seat load transmitted), fixed at chassis end
if beam_faces_bracket_end and beam_faces_chassis_end:
    vm, disp, sf = run_static(obj, beam_faces_chassis_end, beam_faces_bracket_end, 981.0, "beam_loaded_at_bracket", 4.0)
    if vm:
        log_result("beam_loaded_at_bracket", 981, vm, disp, sf, "981N at bracket end (x=29), fixed at chassis end (x=-33)")
        print("beam bracket-loaded: VM=%.1f MPa, disp=%.4f mm, SF=%.2f" % (vm, disp, sf))

# Case 2: Load at chassis end (ground reaction), fixed at bracket end
if beam_faces_bracket_end and beam_faces_chassis_end:
    vm, disp, sf = run_static(obj, beam_faces_bracket_end, beam_faces_chassis_end, 981.0, "beam_loaded_at_chassis", 4.0)
    if vm:
        log_result("beam_loaded_at_chassis", 981, vm, disp, sf, "981N at chassis end (x=-33), fixed at bracket end (x=29)")
        print("beam chassis-loaded: VM=%.1f MPa, disp=%.4f mm, SF=%.2f" % (vm, disp, sf))