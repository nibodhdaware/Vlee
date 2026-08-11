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

# List all properties
print("\nAll result properties:")
for p in result_obj.PropertiesList:
    val = getattr(result_obj, p, None)
    if val is not None and hasattr(val, "__len__") and not isinstance(val, str):
        print(f"  {p}: len={len(val)}")
    elif isinstance(val, str):
        print(f"  {p}: {val}")
    elif val is not None:
        print(f"  {p}: {type(val).__name__}")

# Extract von Mises
vm = result_obj.vonMises
print("\nvonMises count:", len(vm))
max_vm = max(vm)
print("Max von Mises:", max_vm, "MPa")

# Try to get displacement - check property names
disp_props = [p for p in result_obj.PropertiesList if "Displacement" in p]
print("Displacement props:", disp_props)

# Access via getattr
if disp_props:
    dx = getattr(result_obj, disp_props[0], None)
    dy = getattr(result_obj, disp_props[1] if len(disp_props) > 1 else None, None)
    dz = getattr(result_obj, disp_props[2] if len(disp_props) > 2 else None, None)
    if dx and dy and dz:
        max_disp = 0.0
        for i in range(len(dx)):
            d = math.sqrt(dx[i]**2 + dy[i]**2 + dz[i]**2)
            if d > max_disp:
                max_disp = d
        print("Max displacement:", max_disp, "mm")
    else:
        print("Could not get displacement arrays")

# Safety factor
yield_mpa = 276.0
sf = yield_mpa / max_vm if max_vm > 0 else float('inf')
print("\nYield strength (6061-T6):", yield_mpa, "MPa")
print("Safety factor:", sf)