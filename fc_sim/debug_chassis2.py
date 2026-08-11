import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import Mesh
import Part

m = Mesh.Mesh("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
print("Facets:", m.CountFacets)
print("isSolid:", m.isSolid())
print("countComponents:", m.countComponents())

# Get separate components
comps = m.getSeparateComponents()
print("Number of components:", len(comps))
for i, c in enumerate(comps):
    print("Component %d: facets=%d, bbox=%s" % (i, c.CountFacets, c.BoundBox))

# Convert each component to solid
for i, c in enumerate(comps):
    try:
        # Build solid facet by facet
        faces = []
        for j in range(c.CountFacets):
            arr = c.Facets[j].Points
            pts = [Part.Vertex(p).Point for p in arr]
            w = Part.makePolygon(pts + [pts[0]])
            faces.append(Part.makeFace(w))
        shell = Part.makeShell(faces)
        if not shell.isValid():
            print("Comp %d: shell invalid" % i)
            continue
        solid = Part.makeSolid(shell)
        if not solid.isValid():
            print("Comp %d: solid invalid" % i)
            continue
        print("Comp %d: solid OK, vol=%.1f cm^3" % (i, solid.Volume))
    except Exception as e:
        print("Comp %d error:", i, e)