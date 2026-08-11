import sys, math, os
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import ObjectsFem
import meshutil
import fe_common as CEE


def facemap(solid):
    return [(i + 1, f.CenterOfMass, f.BoundBox) for i, f in enumerate(solid.Faces)]


def run(nick, solid, fixed_idx, load_idx, force_n, name, elem):
    doc = App.newDocument("Doc_" + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = solid
    doc.recompute()
    fixed = ["Face%d" % i for i in fixed_idx]
    loads = ["Face%d" % i for i in load_idx]
    sys.stderr.write("%s: fixed=%d load=%d\n" % (name, len(fixed), len(loads)))
    CEE.run_static(obj, fixed, loads, force_n, name, element_size=elem)
    return doc


bracket = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
fm = facemap(bracket)
AX, AZ = 41.0, 16.0
fixed_idx = []
load_idx = []
for (i, c, bb) in fm:
    d = math.hypot(c.x - AX, c.z - AZ)
    if 4.8 < d < 5.6:
        fixed_idx.append(i)  # clamp bore = where bracket bolts around drive axle
    if abs(c.z - 44.5) < 0.05 and bb.ZMax <= 44.6:
        load_idx.append(i)   # seat pan bearing surface (top of horizontal arm)
sys.stderr.write("bracket faces=%d fixed=%d load=%d\n" % (len(fm), len(fixed_idx), len(load_idx)))

if not load_idx:
    sys.exit("no load faces found")

run(None, bracket, fixed_idx, load_idx, 981.0, "bracket", 6.0)