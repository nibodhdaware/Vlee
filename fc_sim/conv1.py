import FreeCAD as App, Mesh, Part, sys
m = Mesh.Mesh("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
sys.stderr.write("loaded facets=%d\n" % m.CountFacets)
s = Part.Shape(m)
sys.stderr.write("shape type=%s shells=%d solids=%d valid=%s\n" % (s.ShapeType, len(s.Shells), len(s.Solids), s.isValid()))
