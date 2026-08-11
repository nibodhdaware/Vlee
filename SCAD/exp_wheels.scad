include <parameters.scad>
use <wheel.scad>

// Just the wheels, no track links (links drawn in Godot)
for (x = roadPositions)
    translate([x, 0, roadZ])
        wheel(roadRadius, trackWidth, false);

translate([-idlerX, 0, idlerZ])
    wheel(idlerRadius, trackWidth, true);
translate([idlerX, 0, idlerZ])
    driveWheel(idlerRadius, trackWidth);
