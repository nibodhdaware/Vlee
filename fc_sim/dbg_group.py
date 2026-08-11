import sys, math, os
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil

doc = App.newDocument("Dbg")
bracket = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
obj = doc.addObject("Part::Feature", "br")
obj.Shape = bracket
doc.recompute()
import ObjectsFem as O

a = O.makeAnalysis(doc, "A")
s = O.makeSolverCalculiXCcxTools(doc, "Solver")
a.addObject(s)
sys.stderr.write("solver added ok\n")
m = O.makeMeshGmsh(doc, "M")
m.Shape = obj
a.addObject(m)
sys.stderr.write("mesh added; group len=%d\n" % len(a.Group))
for x in a.Group:
    sys.stderr.write("  member: %s %s\n" % (x.Name, x.TypeId))
sys.stderr.write("done\n")