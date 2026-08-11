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
print("ret:", ret)

# try to read results via FEM post
# FemMesh object has results
print("Mesh NodeCount:", m.FemMesh.NodeCount)
print("Mesh ElementCount:", m.FemMesh.ElementCount)
# Check if results are attached
if hasattr(m.FemMesh, "Nodes") and hasattr(m.FemMesh.Nodes, "__len__"):
    print("Nodes accessible")

# In FreeCAD, results are typically read back into the analysis object's result object
# Look for result objects
for mbr in a.Group:
    print("Member:", mbr.Name, mbr.TypeId, getattr(mbr, "Label", ""))

# Check if analysis has result object
print("Analysis props:", [p for p in a.PropertiesList if "Result" in p or "result" in p])