import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil

doc = App.newDocument("Chassis")
chassis_solids = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
if not isinstance(chassis_solids, list):
    chassis_solids = [chassis_solids]

for solid_idx, chassis in enumerate(chassis_solids):
    obj = doc.addObject("Part::Feature", "chassis_%d" % solid_idx)
    obj.Shape = chassis
    doc.recompute()
    print("\n=== Chassis %d ===" % solid_idx)
    for i, face in enumerate(obj.Shape.Faces):
        c = face.CenterOfMass
        # Print ALL faces for this component to understand geometry
        if c.z < 25:  # lower portion
            print("  Face%d: center=(%.1f, %.1f, %.1f) area=%.1f" % (i+1, c.x, c.y, c.z, face.Area))