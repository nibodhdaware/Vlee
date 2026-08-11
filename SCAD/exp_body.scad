// Chair body only (no tracks) — for articulated simulation
include <../parameters.scad>
use <../chassis.scad>
use <../suspension.scad>
use <../seat.scad>
use <../footrest.scad>
use <../hydraulic.scad>

chassis();
for (side = [-1, 1]) {
    suspensionBeam(side * trackCenterY);
    for (x = roadPositions)
        suspension(x, side * trackCenterY);
}
seatPedestal();
bucketSeat();
footrest();