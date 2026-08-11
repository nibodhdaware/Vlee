import FreeCAD as App, Mesh, Part, sys
m = Mesh.Mesh()
m.addFacet([[0,0,0],[10,0,0],[10,10,0]])
m.addFacet([[0,0,0],[10,10,0],[0,10,0]])
s = Part.Shape(m)
sys.stderr.write("tiny ok type=%s\n" % s.ShapeType)
