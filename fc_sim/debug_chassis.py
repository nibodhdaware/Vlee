import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import Mesh
import Part

m = Mesh.Mesh("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
print("Facets:", m.CountFacets)
print("isSolid:", m.isSolid())

# Check connected components
# Mesh.Mesh has getComponents? Let's see
print("Dir:", [x for x in dir(m) if not x.startswith('_')])

# Try to get components
comp = m.getComponents()
print("Components:", comp)