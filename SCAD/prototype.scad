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

// Mechanical arm suspension — independent beam above each track.
// The beams are part of the TRACK frame (they pivot with it). Each
// beam's front flange bears on the front idler axle (the tilt pivot);
// its rear end ties to the drive sprocket axle below. Nothing here
// touches the seat.
for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);

    // Drive-end bracket: beam rear (x=29) down to the drive axle (x=41).
    beamZ = idlerZ + trackRadius + 6;
    // Vertical arm: drive axle up to the beam, at y=±28.
    color(matAluminum)
        translate([idlerX - 2, side * trackCenterY, (idlerZ + beamZ) / 2])
            cube([4, 5, beamZ - idlerZ], center = true);
    // Horizontal arm: from the axle bracket back to the beam end.
    color(matAluminum)
        translate([idlerX - 6, side * trackCenterY, beamZ])
            cube([12, 5, 4], center = true);
}

// Seat — two L-brackets pivoting on the FRONT idler cross-track axle.
// The seat + footrest hang off this pivot and stay level while the
// track frame pitches underneath during a stair climb.
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
