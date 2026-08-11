// Simplified export for Godot visual mesh
include <parameters.scad>
use <utils.scad>
use <chassis.scad>
use <suspension.scad>
use <seat.scad>
use <footrest.scad>
use <hydraulic.scad>

// Simplified track belts (just boxes instead of individual links)
for (side = [-1, 1]) {
    translate([0, groundZ + linkThickness/2, side * trackCenterY])
        cube([trackLength + 10, linkThickness, trackWidth], center=true);
}

// Chassis
chassis();

// Mechanical arm suspension
for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);
}

// Seat
seatPedestal();
bucketSeat();

// Footrest
footrest();

// Hydraulic jack wheel
hydraulicJackWheel();
