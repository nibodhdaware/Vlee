// Chair with visible track links (tread pattern)
include <../parameters.scad>
use <../utils.scad>
use <../chassis.scad>
use <../suspension.scad>
use <../seat.scad>
use <../footrest.scad>
use <../hydraulic.scad>

// Track belt with visible tread segments
module trackBeltWithTreads(side) {
    pitch = linkLength + linkGap;
    arcLen = 3.14159265 * trackRadius;
    total = 2 * trackLength + 2 * arcLen;
    numLinks = floor(total / pitch);

    // Simplified: just place tread pads along the path
    for (i = [0 : numLinks - 1]) {
        d = i * pitch;
        // Bottom straight
        if (d < trackLength) {
            translate([-idlerX + d, side * trackCenterY, groundZ + linkThickness/2])
                cube([linkLength + 1, trackWidth, linkThickness], center=true);
        }
        // Top straight
        else if (d < trackLength + arcLen) {
            // Arc section - skip for simplicity, just do top straight
        }
        else if (d < 2 * trackLength + arcLen) {
            translate([idlerX - (d - trackLength - arcLen), side * trackCenterY, groundZ + linkThickness/2 + 2 * trackRadius])
                cube([linkLength + 1, trackWidth, linkThickness], center=true);
        }
    }

    // Side rails (continuous belt visual)
    for (lr = [-1, 1]) {
        translate([0, side * (trackCenterY + lr * (trackWidth/2 - 1)), groundZ + linkThickness/2])
            cube([trackLength * 2 + arcLen * 2, 1, linkThickness], center=true);
    }

    // Guide ribs on top/bottom
    translate([0, side * trackCenterY, groundZ + linkThickness/2 + 1.5])
        cube([trackLength * 2 + arcLen * 2, 6, 3], center=true);
}

// Full assembly
chassis();

for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);
    trackBeltWithTreads(side);
}

seatPedestal();
bucketSeat();
footrest();
hydraulicJackWheel();
