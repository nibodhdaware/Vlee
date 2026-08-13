include <parameters.scad>
use <utils.scad>
use <seat.scad>

//================ SEAT LEVELING MECHANISM =================//
// The seat pan pivots about a front hinge (under the occupant's knees)
// and a rear linear actuator counter-rotates the pan against the
// chassis pitch, keeping the seat level while the track climbs stairs.
//
//   angle = counter-rotation in DEGREES (positive = rear of pan rises)

hingeX = -30;                                    // front edge of L-bracket arms
hingeZ = idlerZ + seatTopOffset - 5 + 2.5;       // just above the arm top (44.5)
baseZ = idlerZ + seatTopOffset - 5;              // 44.5 arm top / base plate
platZ = baseZ + 3.5;                             // rotating platform top (48)

// Bottom of the rear actuator (fixed to the base).
actuatorBot = [20, 0, baseZ - 1.5];
// Top of the rear actuator (attached to the rotating platform).
actuatorTop = [20, 0, platZ - 1];

module levelerBase() {
    // Main base plate on the L-bracket arms.
    color(matAluminum)
        translate([0, 0, baseZ])
            cube([70, 60, 2], center = true);

    // Front hinge posts (fixed to base).
    for (s = [-1, 1])
        color(matDarkSteel)
            translate([hingeX, s * 22, hingeZ])
                cube([4, 6, 12], center = true);

    // Rear actuator lower clevis.
    color(matDarkSteel)
        translate([actuatorBot[0], 0, baseZ - 1.5])
            cube([6, 8, 3], center = true);
}

module capsule(a, b, r) {
    hull() {
        translate(a) sphere(r = r, $fn = 12);
        translate(b) sphere(r = r, $fn = 12);
    }
}

// Point p rotated about the hinge by -`angle` deg (about the Y axis),
// matching rotate([0, -angle, 0]) used by levelerPlatform.
function rotatedPoint(p, angle) =
    let (co = cos(angle), si = sin(angle),
         dx = p[0] - hingeX, dz = p[2] - hingeZ)
        [hingeX + dx * co - dz * si, 0, hingeZ + dx * si + dz * co];

module rearActuator(angle) {
    top = rotatedPoint(actuatorTop, angle);
    bot = actuatorBot;
    // Barrel (fixed side) + chrome rod (moving side).
    color(matAluminum) capsule(bot, top, 2.5);
    color(matChrome)   capsule(top, [bot[0] + (top[0] - bot[0]) * 0.45, 0,
                                     bot[2] + (top[2] - bot[2]) * 0.45], 1.5);
}

// Rotating platform carrying the seat (counter-rotates by `angle`).
module levelerPlatform(angle = 0) {
    translate([hingeX, 0, hingeZ])
        rotate([0, -angle, 0])
            translate([-hingeX, 0, -hingeZ]) {
                // Rotating platform.
                color(matAluminum)
                    translate([-6, 0, platZ])
                        cube([70, 56, 2], center = true);
                bucketSeat();
            }
}

// Complete leveler: fixed base + rotating platform carrying the seat.
module leveledSeat(angle = 0) {
    levelerBase();
    levelerPlatform(angle);
    rearActuator(angle);
}
