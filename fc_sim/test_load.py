import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
import FreeCAD as App
import Part
from meshutil import load

doc = App.newDocument("Assem")
chassis, c_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl", "chassis")
sys.stderr.write("STEP1 OK\n")
bracket, b_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl", "bracket")
sys.stderr.write("STEP2 OK\n")
beam, w_feat = load(doc, "/home/nibodhdaware/Developer/Vlee/STL/10_suspension_beam.stl", "beam")
sys.stderr.write("STEP3 OK\n")