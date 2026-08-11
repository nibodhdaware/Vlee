// Simplified export for Godot visual mesh - OBJ format
include <parameters.scad>
use <utils.scad>
use <chassis.scad>
use <suspension.scad>
use <seat.scad>
use <footrest.scad>
use <hydraulic.scad>

// Simplified track belts
for (side = [-1, 1]) {
    translate([0, groundZ + linkThickness/2, side * trackCenterY])
        cube([trackLength + 10, linkThickness, trackWidth], center=true);
}

chassis();

for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);
}

seatPedestal();
bucketSeat();
footrest();
hydraulicJackWheel();
