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

# Find the result object
result_obj = None
for mbr in a.Group:
    if "Result" in mbr.TypeId or "result" in mbr.TypeId.lower():
        result_obj = mbr
        break

if result_obj is None:
    print("ERROR: No result object found")
    sys.exit(1)

print("Result object:", result_obj.Name, result_obj.Label)

# Extract von Mises
vm = result_obj.vonMises
print("vonMises count:", len(vm))
max_vm = max(vm)
print("Max von Mises:", max_vm, "MPa")

# Extract displacement magnitude
dx = result_obj.NodeDisplacementX
dy = result_obj.NodeDisplacementY
dz = result_obj.NodeDisplacementZ
max_disp = 0.0
for i in range(len(dx)):
    d = math.sqrt(dx[i]**2 + dy[i]**2 + dz[i]**2)
    if d > max_disp:
        max_disp = d
print("Max displacement:", max_disp, "mm")

# Safety factor (6061-T6 yield ~276 MPa)
yield_mpa = 276.0
sf = yield_mpa / max_vm if max_vm > 0 else float('inf')
print("Yield strength (6061-T6):", yield_mpa, "MPa")
print("Safety factor:", sf)

# Also print stress component stats for reference
print("\nStress components (max abs):")
for comp in ["NodeStressXX", "NodeStressYY", "NodeStressZZ", "NodeStressXY", "NodeStressXZ", "NodeStressYZ"]:
    vals = getattr(result_obj, comp)
    print(f"  {comp}: max={max(vals):.2f}, min={min(vals):.2f}")