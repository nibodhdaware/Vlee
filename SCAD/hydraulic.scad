include <parameters.scad>
use <track.scad>

//================ HYDRAULIC JACK WHEEL =================//
// Lightweight electric linear actuator. Aluminum construction.

module hydraulicJackWheel(extension = hydrExtendAmount) {
    mountZ = chassisBottom;
    barrelTopZ = mountZ + hydrBarrelHeight / 2;
    rodBottomZ = mountZ - extension;

    // Mounting bracket — aluminum plates.
    for (side = [-1, 1])
        color(matAluminum)
            translate([hydrMountX, side * 4, mountZ])
                cube([12, 2, hydrBarrelHeight + 4], center = true);

    // Barrel — aluminum.
    color(matAluminum)
        translate([hydrMountX, hydrMountY, barrelTopZ])
            cylinder(r = hydrBarrelRadius, h = hydrBarrelHeight, center = true, $fn = 24);

    // Piston rod — chrome steel.
    color(matChrome)
        translate([hydrMountX, hydrMountY, (barrelTopZ + rodBottomZ) / 2])
            cylinder(r = hydrRodRadius,
                     h = abs(barrelTopZ - rodBottomZ),
                     center = true, $fn = 16);

    // Two wheels at the bottom — aluminum hubs, rubber tyres.
    for (side = [-1, 1])
        translate([hydrMountX, hydrMountY + side * 7, rodBottomZ]) {
            color(matAluminum)
                rotate([90, 0, 0])
                    difference() {
                        cylinder(r = hydrWheelRadius, h = hydrWheelWidth, center = true, $fn = 24);
                        cylinder(r = hydrWheelRadius - 1.5, h = hydrWheelWidth + 1, center = true, $fn = 24);
                    }
        }

    // Axle connecting both wheels — aluminum.
    color(matAluminum)
        translate([hydrMountX, hydrMountY, rodBottomZ])
            rotate([90, 0, 0])
                cylinder(r = 1.5, h = 20, center = true, $fn = 12);
}

module tiltedTrack(y, angle = trackTilt) {
    translate([0, y, 0])
        translate([liftPivotX, 0, liftPivotZ])
            rotate([0, angle, 0])
                translate([-liftPivotX, 0, -liftPivotZ])
                    trackAssembly();
}
