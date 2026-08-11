import sys
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

# Find the result object in analysis group
for mbr in a.Group:
    print("Member:", mbr.Name, mbr.TypeId, getattr(mbr, "Label", ""))

# The result object should have type Fem::FemResultObject or similar
# Extract results
for mbr in a.Group:
    if "result" in mbr.TypeId.lower() or "Result" in mbr.TypeId:
        print("\n--- Result object ---")
        print("Type:", mbr.TypeId)
        print("Label:", mbr.Label)
        for p in mbr.PropertiesList:
            print("  Prop:", p, type(getattr(mbr, p, None)))
            val = getattr(mbr, p, None)
            if val is not None and hasattr(val, "__len__") and not isinstance(val, str):
                print("    len:", len(val))
            if val is not None and hasattr(val, "Keys"):
                print("    Keys:", val.Keys())

        # FemResult objects typically have a FemMesh with result arrays
        if hasattr(mbr, "FemMesh"):
            fm = mbr.FemMesh
            print("  FemMesh NodeCount:", fm.NodeCount)
            for attr in dir(fm):
                if "result" in attr.lower():
                    print("  FemMesh attr:", attr)
            # Try to get results via getResultData or similar
            if hasattr(fm, "getResultData"):
                print("  getResultData exists")
            if hasattr(fm, "NodeResult"):
                print("  NodeResult:", fm.NodeResult)
            if hasattr(fm, "ElementResult"):
                print("  ElementResult:", fm.ElementResult)

        # Also check if the mesh object itself has results
        if hasattr(mbr, "getResultData"):
            print("  getResultData on result obj")
            # Keys might be like "Displacement", "Stress", etc.
            # but getResultData might need a region/element
            pass

# Check the mesh object itself for results
print("\n--- Mesh object ---")
for p in m.PropertiesList:
    val = getattr(m, p, None)
    if "result" in p.lower() or "Result" in p:
        print("  Mesh prop:", p, type(val))
        if val and hasattr(val, "Keys"):
            print("    Keys:", val.Keys())

# Also try: Fem.FemResult.read or similar
import Fem
print("\n--- Fem module ---")
for attr in dir(Fem):
    if "result" in attr.lower():
        print("  ", attr)