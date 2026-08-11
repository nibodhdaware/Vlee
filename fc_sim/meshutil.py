import sys
import FreeCAD as App
import Part
import Mesh


def mesh_to_solid(mesh):
    faces = []
    for i in range(mesh.CountFacets):
        arr = mesh.Facets[i].Points
        pts = [Part.Vertex(p).Point for p in arr]
        w = Part.makePolygon(pts + [pts[0]])
        faces.append(Part.makeFace(w))
    shell = Part.makeShell(faces)
    if not shell.isValid():
        raise RuntimeError("shell invalid")
    solid = Part.makeSolid(shell)
    if not solid.isValid():
        raise RuntimeError("solid invalid")
    return solid


def load_solid(stl_path):
    m = Mesh.Mesh(stl_path)
    if not m.isSolid():
        raise RuntimeError("%s not watertight" % stl_path)
    comps = m.getSeparateComponents()
    if len(comps) == 1:
        return mesh_to_solid(m)
    # Multiple components - return list of solids
    solids = []
    for c in comps:
        solids.append(mesh_to_solid(c))
    return solids