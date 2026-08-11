import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import Part
from meshutil import load_solid
from femtools.ccxtools import CcxTools


def make_doc(name):
    return App.newDocument(name)


# 1. bracket load path part
doc = App.newDocument("LoadPath")
bracket = load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
Part.show(bracket, "bracket")
doc.recompute()
sys.stderr.write("bracket in doc: %d objects\n" % len(doc.Objects))

# try to import the fem test utilities to see object creation helpers
try:
    import ObjectsFem
    sys.stderr.write("ObjectsFem OK: %s\n" % [x for x in dir(ObjectsFem) if not x.startswith("_")][:30])
except Exception as e:
    sys.stderr.write("ObjectsFem FAIL %r\n" % e)