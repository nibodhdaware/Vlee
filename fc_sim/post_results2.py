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

# After run, results should be on the mesh object
# Check FemMesh for results
femmesh = m.FemMesh
print("NodeCount:", femmesh.NodeCount)
print("FaceCount:", femmesh.FaceCount)
print("VolumeCount:", femmesh.VolumeCount)

# Check for result attributes
for attr in dir(femmesh):
    if "result" in attr.lower() or "Result" in attr:
        print("  attr:", attr)

# Results might be in NodeResult/ElementResult properties
# Try to access via FreeCAD FEM result object
# Check if analysis has a result object attached
for mbr in a.Group:
    print("Member:", mbr.Name, mbr.TypeId)

# The mesh object should now have results as Fem::FemResult
# Check its properties
for p in m.PropertiesList:
    if "result" in p.lower():
        print("Mesh prop:", p, getattr(m, p))

# In some versions, results are in the analysis object's Group
# Check the analysis for result members
for mbr in a.Group:
    if "result" in mbr.Name.lower() or "Result" in mbr.TypeId:
        print("Result member:", mbr.Name, mbr.TypeId)
        for pp in mbr.PropertiesList:
            print("  prop:", pp, getattr(mbr, pp, ""))

# Try to read results directly from .frd file using FemResult
import Fem
r = Fem.FemResult()
# FemResult can read from file
# But usually FemToolsCcx already loads it into the mesh
# Check m.FemMesh for results
print("\n--- Mesh FemMesh ---")
print("  NodeCount:", m.FemMesh.NodeCount)
# Get the results - they might be in the node/element results
# FreeCAD stores result as attribute on the FemMesh? 
# Check for result object on mesh
for p in m.PropertiesList:
    print("  prop:", p, type(getattr(m, p, None)))