include <parameters.scad>
use <utils.scad>

//================ ARMRESTS =================//
// Full-length padded armrests. Aluminum construction with leather pads.

module armrestUnit(side) {
    y = side * (seatPanWidth / 2 - 4);
    padTopZ = armPadHeight;
    padZ = padTopZ - armPadThick / 2;
    baseZ = idlerZ + seatTopOffset - 5 - 2;
    padCX = armPivotX - armLength / 2 - 2;

    // Rear post — aluminum, rises at the seat back.
    color(matAluminum)
        translate([armPivotX, y, (baseZ + padZ) / 2])
            cube([3, 3, padZ - baseZ], center = true);

    // Horizontal rail — aluminum, from the post forward.
    color(matAluminum)
        translate([padCX, y, padZ - 2])
            cube([armLength + 4, 2, 2], center = true);

    // Padded top — leather.
    color(matLeather)
        translate([padCX, y, padTopZ - armPadThick / 2])
            cube([armLength, armPadWidth, 2], center = true);

    // Joystick on the front of the right armrest.
    if (side == 1) {
        jx = armPivotX - armLength - 1;
        color(matDarkSteel)
            translate([jx, y, padTopZ + 4])
                cube([6, 6, 6], center = true);
        color(matChrome)
            translate([jx + 2.5, y, padTopZ + 8.5])
                cylinder(r = 1.2, h = 4, center = true, $fn = 12);
        color(matRubber)
            translate([jx + 2.5, y, padTopZ + 11])
                sphere(r = 1.6, $fn = 16);
    }
}

module armrests() {
    armrestUnit(-1);
    armrestUnit(1);
}