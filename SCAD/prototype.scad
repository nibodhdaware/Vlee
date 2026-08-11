// Tracked wheelchair prototype
include <parameters.scad>
use <utils.scad>
use <wheel.scad>
use <track.scad>
use <chassis.scad>
use <suspension.scad>
use <seat.scad>
use <footrest.scad>
use <armrest.scad>
use <hydraulic.scad>

// Tracks
tiltedTrack(trackCenterY);
tiltedTrack(-trackCenterY);

// Chassis
chassis();

// Mechanical arm suspension — independent beam above each track
// Beams mount to L-bracket risers via L-shaped brackets.
for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);

    // L-shaped bracket: riser (x=41, y=±15) → outboard (x=41, y=±28) → beam (x=29, y=±28).
    beamZ = idlerZ + trackRadius + 6;
    // Vertical arm along Y: from riser outboard to beam y-position
    color(matAluminum)
        translate([idlerX, side * 15 + side * (trackCenterY - 15) / 2, beamZ])
            cube([4, trackCenterY - 15, 4], center = true);
    // Horizontal arm along X: from outboard (x=41) to beam end (x=29)
    color(matAluminum)
        translate([idlerX - 6, side * trackCenterY, beamZ])
            cube([12, 5, 4], center = true);
}

// Seat — carried by two L-brackets rising from the sprocket cross-bar
for (sy = [-1, 1])
    seatBracket(sy * 15);

// Cross-bar connecting the two L-bracket arms (armrest support). Aluminum.
panB = idlerZ + seatTopOffset - 5;
color(matAluminum)
    translate([armPivotX, 0, panB - 2])
        cube([4, seatPanWidth - 8, 4], center = true);

// Hydraulic mounting cross-brace between the L-bracket arms. Aluminum.
color(matAluminum) {
    translate([hydrMountX, 0, chassisBottom])
        cube([5, seatPanWidth - 36, 4], center = true);
    for (sy = [-1, 1])
        translate([hydrMountX, sy * 15, (chassisBottom + panB - 2) / 2])
            cube([3, 4, panB - 2 - chassisBottom], center = true);
}

bucketSeat();

// Footrest
footrest();

// Armrests with joystick
armrests();

// Hydraulic jack wheel
hydraulicJackWheel();
