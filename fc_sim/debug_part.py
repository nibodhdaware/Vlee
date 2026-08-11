import sys
sys.path.insert(0, "/home/nibodhdaware/Developer/Vlee/fc_sim")
from meshutil import load_solid
for name, p in [("chassis", "/home/nibodhdaware/Developer/Vlee/STL/03_chassis_axles.stl"),
                ("bracket", "/home/nibodhdaware/Developer/Vlee/STL/09_seat_L_bracket.stl"),
                ("beam", "/home/nibodhdaware/Developer/Vlee/STL/10_suspension_beam.stl")]:
    try:
        s = load_solid(p)
        sys.stderr.write("%s ok vol=%.2f\n" % (name, s.Volume))
    except Exception as e:
        sys.stderr.write("%s FAIL %r\n" % (name, e))