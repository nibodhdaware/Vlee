import FreeCAD as App, Mesh, Part, sys
m = Mesh.Mesh("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
faces = []
for f_idx in range(m.CountFacets):
    p = m.Facets
    arr = m.Facets[f_idx].Points
    w = Part.makePolygon([Part.Vertex(v).Point for v in arr] + [Part.Vertex(arr[0]).Point])
    faces.append(Part.makeFace(w))
shell = Part.makeShell(faces)
sys.stderr.write("shell valid=%s\n" % shell.isValid())
solid = Part.makeSolid(shell)
sys.stderr.write("solid valid=%s solids=%d\n" % (solid.isValid(), len(solid.Solids)))
