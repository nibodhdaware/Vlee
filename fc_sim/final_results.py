import sys, math
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil
import ObjectsFem as O
from femtools.ccxtools import FemToolsCcx

doc = App.newDocument("Post")
bracket = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
obj = doc.addObject("Part::Feature", "br")
obj.Shape = bracket
doc.recompute()

a = O.makeAnalysis(doc, "A")
s = O.makeSolverCalculiXCcxTools(doc, "Solver")
s.AnalysisType = "static"
a.addObject(s)

mat = O.makeMaterialSolid(doc, "Mat")
mat.Material = {"Name": "AL6061-T6", "YoungsModulus": "68900 MPa", "PoissonRatio": "0.33"}
a.addObject(mat)

fix = O.makeConstraintFixed(doc, "Fix")
fix.References = [(obj, "Face1")]
a.addObject(fix)

frc = O.makeConstraintForce(doc, "Load")
frc.References = [(obj, "Face2")]
frc.Force = "981.0 N"
frc.Reversed = True
a.addObject(frc)

m = O.makeMeshGmsh(doc, "Mesh")
m.Shape = obj
m.ElementDimension = "3D"
m.CharacteristicLengthMin = "1.0 mm"
m.CharacteristicLengthMax = "6.0 mm"
m.SecondOrderLinear = True
a.addObject(m)
doc.recompute()

from femmesh.gmshtools import GmshTools
GmshTools(m).create_mesh()
doc.recompute()

fea = FemToolsCcx(a, s)
fea.set_base_name("bracket")
fea.setup_working_dir("/home/nibodhdaware/Developer/Vlee/fc_sim/fem")
ret = fea.run()

result_obj = None
for mbr in a.Group:
    if "Result" in mbr.TypeId or "result" in mbr.TypeId.lower():
        result_obj = mbr
        break

print("Result object:", result_obj.Name, result_obj.Label)

vm = result_obj.vonMises
max_vm = max(vm)
print("Max von Mises:", max_vm, "MPa")

# Displacement - check both arrays
if hasattr(result_obj, "DisplacementLengths"):
    disp_len = result_obj.DisplacementLengths
    print("DisplacementLengths count:", len(disp_len))
    print("Max displacement (scalar):", max(disp_len), "mm")

if hasattr(result_obj, "DisplacementVectors"):
    disp_vec = result_obj.DisplacementVectors
    print("DisplacementVectors count:", len(disp_vec))
    if len(disp_vec) > 0:
        # Each vector might be a tuple/list of 3
        print("First vector:", disp_vec[0])
        if isinstance(disp_vec[0], (list, tuple)):
            max_d = max(math.sqrt(v[0]**2 + v[1]**2 + v[2]**2) for v in disp_vec)
            print("Max displacement (vector):", max_d, "mm")

yield_mpa = 276.0
sf = yield_mpa / max_vm if max_vm > 0 else float('inf')
print("\nYield (6061-T6):", yield_mpa, "MPa")
print("Safety factor:", sf)