import sys
import math
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
from meshutil import load_solid
import FreeCAD as App
import Part
import ObjectsFem
import fe_common as fc

# ---- load bracket solid (units mm) ----
bracket = load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
doc = App.newDocument("Bracket")
Part.show(bracket, "bracket")
doc.recompute()

faces = bracket.Faces
AXLE = (41.0, 16.0)  # barX, barZ  (axle axis along Y at x=41, z=16)

fixed = []
load_faces = []
for i, f in enumerate(faces):
    c = f.CenterOfMass
    # clamp bore: distance from axle axis (x=41,z=16 in XY plane) ~ bore r=5.2
    d = math.hypot(c.x - AXLE[0], c.z - AXLE[1])
    top = abs(c.z - 44.5) < 0.01 and abs(f.BoundBox.ZMax - 44.5) < 0.01
    if 4.8 < d < 5.8:
        fixed.append("Face%d" % (i + 1))
    if top:
        load_faces.append("Face%d" % (i + 1))

sys.stderr.write("fixed faces: %d\n" % len(fixed))
sys.stderr.write("load faces: %d\n" % len(load_faces))

CEE.run_static(doc.getObjects()[0] if False else None, fixed, load_faces,
               "981", "bracket", element_size=6.0)