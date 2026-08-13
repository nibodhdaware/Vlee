// Side-profile comparison: seat leveling during stair climb.
include <parameters.scad>
use <utils.scad>
use <chassis.scad>
use <suspension.scad>
use <footrest.scad>
use <seat.scad>
use <leveler.scad>

stairAngle = atan2(16, 32);

// Level reference line fixed in the world (bright red).
color([1.0, 0.15, 0.15])
    translate([0, 0, 49.5])
        cube([140, 2, 1], center = true);

// Chassis group pitched at stair angle.
translate([-idlerX, 0, groundZ])
    rotate([0, -stairAngle, 0])
        translate([idlerX, 0, -groundZ]) {
            chassis();
            for (side = [-1, 1]) {
                suspensionBeam(side * trackCenterY);
                for (x = roadPositions)
                    suspension(x, side * trackCenterY);
            }
            for (sy = [-1, 1])
                seatBracket(sy * 15);
            levelerBase();
            levelerPlatform(-stairAngle);
            rearActuator(-stairAngle);
        }

footrest();
