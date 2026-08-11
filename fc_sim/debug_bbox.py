import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import meshutil

doc = App.newDocument("Chassis")
chassis_solids = meshutil.load_solid("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
print("Number of solids:", len(chassis_solids) if isinstance(chassis_solids, list) else 1)
if not isinstance(chassis_solids, list):
    chassis_solids = [chassis_solids]

for solid_idx, chassis in enumerate(chassis_solids):
    print("Solid %d volume:", solid_idx, chassis.Volume)
    print("Solid %d bbox:", solid_idx, chassis.BoundBox)