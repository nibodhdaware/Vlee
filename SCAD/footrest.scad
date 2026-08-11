include <parameters.scad>
use <utils.scad>

//================ FOOTREST =================//
// Folding footrest: one continuous aluminum plate hinged at the end of the
// L-bracket arm. Lightweight aluminum construction.

module footrest() {
    halfL = footrestLength / 2;
    cx = footrestFrontX;
    cz = footrestHeight - footrestThickness / 2;

    // Clevis wings at the end of the L-bracket arm.
    for (side = [-1, 1])
        color(matDarkSteel)
            translate([footPivotX, side * 3, footPivotZ])
                cube([4, 4, footrestThickness + 2], center = true);

    // Vertical brackets from arm down to the plate. Aluminum.
    bracketH = footPivotZ - cz;
    for (side = [-1, 1])
        color(matAluminum)
            translate([footPivotX, side * 3, (footPivotZ + cz) / 2])
                cube([3, 3, bracketH], center = true);

    // Folding cleat behind the plate rear edge.
    color(matAluminum)
        translate([cx + halfL - 2, 0, cz])
            cube([6, 4, footrestThickness], center = true);

    // Pivot pin through cleat and wings.
    color(matChrome)
        translate([footPivotX, 0, footPivotZ])
            rotate([90, 0, 0])
                cylinder(r = 1.5, h = 12, center = true, $fn = 12);

    // Plate — aluminum.
    color(matAluminum)
        translate([cx, 0, cz])
            cube([footrestLength, footrestWidth, footrestThickness], center = true);

    // Optional heel guard.
    if (footHeelGuard)
        color(matAluminum)
            translate([cx + halfL - 1.5, 0, cz + 2.5])
                cube([4, footrestWidth - 6, 7], center = true);

    // Optional toe guard.
    if (footToeGuard)
        color(matAluminum)
            translate([cx - halfL + 1.5, 0, cz + 3])
                cube([4, footrestWidth - 4, 8], center = true);
}
