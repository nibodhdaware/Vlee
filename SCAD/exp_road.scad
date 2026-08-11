include <../parameters.scad>
use <../wheel.scad>
translate([0, 0, roadZ])
    rotate([0, 90, 0])
        roadWheel();
