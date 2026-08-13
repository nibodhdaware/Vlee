// Render: seat + footrest = ONE level body connected ONLY at the front
// idler pivot. The track running gear pitches to the stair angle about
// that same axle. Two completely separate bodies.
include <parameters.scad>
use <utils.scad>
use <chassis.scad>
use <suspension.scad>
use <track.scad>
use <hydraulic.scad>
use <seat.scad>
use <footrest.scad>

stairAngle = atan2(16, 32);

// PIVOT: the front idler axle (the planted, stationary end).
pivotX = -idlerX;   // -41
pivotZ = idlerZ;    // 16

// Level reference line fixed in the world at seat-pan top height.
color([1.0, 0.15, 0.15])
    translate([0, 0, idlerZ + seatTopOffset])
        cube([150, 2, 1], center = true);

// ============ TRACK BODY: pitches about the pivot ============
translate([pivotX, 0, pivotZ])
    rotate([0, -stairAngle, 0])
        translate([-pivotX, 0, -pivotZ]) {
            chassis();
            for (side = [-1, 1]) {
                suspensionBeam(side * trackCenterY);
                for (x = roadPositions)
                    suspension(x, side * trackCenterY);
                // outboard mounting brackets (beam to track)
                beamZ = idlerZ + trackRadius + 6;
                color(matAluminum)
                    translate([idlerX, side * 15 + side * (trackCenterY - 15) / 2, beamZ])
                        cube([4, trackCenterY - 15, 4], center = true);
                color(matAluminum)
                    translate([idlerX - 6, side * trackCenterY, beamZ])
                        cube([12, 5, 4], center = true);
            }
            for (side = [-1, 1])
                trackAssembly(side);
            hydraulicJackWheel();
        }

// ============ SEAT BODY: stays level, hangs off the pivot ============
// Same production seat brackets, pan, backrest and footrest — drawn as
// ONE level body that connects to the frame only at the front pivot.
for (sy = [-1, 1])
    seatBracket(sy * 15);
bucketSeat();
footrest();
