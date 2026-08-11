import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
from meshutil import load_solid

bracket = load_solid("/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl")
faces = bracket.Faces
sys.stderr.write("total faces: %d\n" % len(faces))
for i, f in enumerate(faces):
    c = f.CenterOfMass
    bb = f.BoundBox
    sys.stderr.write("F%d c=(%.1f,%.1f,%.1f) area=%.1f zmin=%.1f zmax=%.1f xmin=%.1f xmax=%.1f\n"
                     % (i + 1, c.x, c.y, c.z, f.Area, bb.ZMin, bb.ZMax, bb.XMin, bb.XMax))