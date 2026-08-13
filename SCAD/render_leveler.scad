// Render: seat leveling mechanism during stair climb.
// The track/chassis group is pitched at the stair angle while the
// seat counter-rotates (via the leveler) to stay level.
include <parameters.scad>
use <utils.scad>
use <chassis.scad>
use <suspension.scad>
use <footrest.scad>
use <seat.scad>
use <leveler.scad>

stairAngle = atan2(16, 32);   // 26.57 deg

// Pitch the whole running gear + leveler base about the front idler contact.
translate([-idlerX, 0, groundZ])
    rotate([0, -stairAngle, 0])
        translate([idlerX, 0, -groundZ]) {
            chassis();
            for (side = [-1, 1]) {
                suspensionBeam(side * trackCenterY);
                for (x = roadPositions)
                    suspension(x, side * trackCenterY);
            }
            // Seat frame brackets + leveler base ride with the chassis.
            for (sy = [-1, 1])
                seatBracket(sy * 15);
            levelerBase();
            // Seat platform counter-rotates within the pitched frame
            // (+stairAngle relative to the -stairAngle chassis) -> level.
            levelerPlatform(-stairAngle);
            rearActuator(-stairAngle);
            footrest();
        }
