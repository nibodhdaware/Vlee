import sys
import os
import shutil
import FreeCAD as App
import ObjectsFem
from femtools.ccxtools import FemToolsCcx

CCX_DIR = "/home/nibodhdaware/.local/share/flatpak/app/org.freecad.FreeCAD/x86_64/stable/aa6792b7683c709b78bf533d6c05d71fb339b13898339a12e06e86b006208ad0/files/bin"
LIB_DIR = "/home/nibodhdaware/.local/share/flatpak/app/org.freecad.FreeCAD/x86_64/stable/aa6792b7683c709b78bf533d6c05d71fb339b13898339a12e06e86b006208ad0/files/lib"
os.environ["PATH"] = CCX_DIR + ":" + os.environ.get("PATH", "")
os.environ["LD_LIBRARY_PATH"] = LIB_DIR + ":" + os.environ.get("LD_LIBRARY_PATH", "")
CCX_BIN = shutil.which("ccx") or os.path.join(CCX_DIR, "ccx")
WORK = "/home/nibodhdaware/Developer/Vlee/fc_sim/fem"

MATERIAL = {
    "Name": "AL6061-T6",
    "YoungsModulus": "68900 MPa",
    "PoissonRatio": "0.33",
    "Density": "2700 kg/m^3",
}

import FreeCAD as AppF
import ObjectsFem as _OF

import FreeCAD as AppF
import ObjectsFem as _OF
import meshutil


def setup_ccx_param():
    p = AppF.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/Ccx")
    p.SetString("ccxBinaryPath", CCX_BIN)


def run_static(obj, fixed_faces, load_faces, force_n, name, element_size=6.0):
    setup_ccx_param()
    os.makedirs(WORK, exist_ok=True)
    doc = App.ActiveDocument

    analysis = _OF.makeAnalysis(doc, "Analysis_" + name)

    solver = _OF.makeSolverCalculiXCcxTools(doc, "CalculiXCcxTools")
    solver.AnalysisType = "static"
    solver.GeometricalNonlinearity = "linear"
    solver.ThermoMechSteadyState = False
    solver.IterationsControlParameterTimeUse = False
    solver.SplitInputWriter = False
    solver.WorkingDir = ""
    analysis.addObject(solver)

    mat = _OF.makeMaterialSolid(doc, "Mat_" + name)
    mat.Material = dict(MATERIAL)
    analysis.addObject(mat)

    fixed = _OF.makeConstraintFixed(doc, "Fix_" + name)
    fixed.References = [(obj, f) for f in fixed_faces]
    analysis.addObject(fixed)

    force = _OF.makeConstraintForce(doc, "Load_" + name)
    force.References = [(obj, f) for f in load_faces]
    force.Force = "%.1f N" % force_n
    force.Reversed = True
    analysis.addObject(force)

    mesh = _OF.makeMeshGmsh(doc, "Mesh_" + name)
    mesh.Shape = obj
    mesh.ElementDimension = "3D"
    mesh.CharacteristicLengthMin = "1.0 mm"
    mesh.CharacteristicLengthMax = "%.1f mm" % element_size
    mesh.SecondOrderLinear = True
    analysis.addObject(mesh)

    doc.recompute()
    sys.stderr.write("%s: meshing...\n" % name)

    from femmesh.gmshtools import GmshTools
    gmsh_mesh = GmshTools(mesh)
    err = gmsh_mesh.create_mesh()
    if err:
        sys.stderr.write("%s: gmsh error %s\n" % (name, err))
        return None
    doc.recompute()
    sys.stderr.write("%s: mesh done nodes=%d\n" % (name, mesh.FemMesh.NodeCount))

    fea = FemToolsCcx(analysis, solver)
    fea.set_base_name(name)
    fea.setup_working_dir(WORK)
    ret = fea.run()
    sys.stderr.write("%s: done ret=%s\n" % (name, ret))
    return analysis