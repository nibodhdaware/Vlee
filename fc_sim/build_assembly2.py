import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
from meshutil import load_solid

chassis = load_solid("/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl")
bracket = load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
beam = load_solid("/home/nibodhdaware/Developer/Vlee/STL/10_suspension_beam.stl")
sys.stderr.write("loaded: chassis=%.1f bracket=%.1f beam=%.1f cm3\n" % (chassis.Volume, bracket.Volume, beam.Volume))

fused = chassis.fuse(bracket).fuse(beam)
sys.stderr.write("fused solids=%d shells=%d vol=%.2f valid=%s\n" % (len(fused.Solids), len(fused.Shells), fused.Volume, fused.isValid()))

import FreeCAD as App
doc = App.newDocument("Assem")
feat = Part.show(fused, "loadpath")
doc.recompute()
doc.saveAs("/home/nibodhdaware/Developer/Vlee/fc_sim/assembly.fcstd")
sys.stderr.write("saved\n")