include <../parameters.scad>
use <../wheel.scad>
translate([0, 0, idlerZ])
    rotate([0, 90, 0])
        idlerWheel();
