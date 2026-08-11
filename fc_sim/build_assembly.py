import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
from meshutil import load

doc = App.newDocument("Assem")
chassis, c_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl", "chassis")
bracket, b_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl", "bracket")
beam, w_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/10_suspension_beam.stl", "beam")

combined = chassis.fuse(bracket).fuse(beam)
sys.stderr.write(
    "combined: solids=%d shells=%d vol=%.2f cm3 valid=%s\n"
    % (len(combined.Solids), len(combined.Shells), combined.Volume, combined.isValid())
)
Part.show(combined, "loadpath")
doc.recompute()
doc.saveAs("/home/nibodhdaware/Developer/Vlee/fc_sim/assembly.fcstd")
sys.stderr.write("saved assembly.fcstd\n")