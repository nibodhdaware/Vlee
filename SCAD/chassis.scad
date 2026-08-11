include <parameters.scad>

module crossTrackAxle(x, z, driven = false) {
    // Aluminum axles — 1/3 weight of steel
    color(matAluminum)
        translate([x, 0, z])
            rotate([90, 0, 0])
                cylinder(r = driven ? 5 : 4,
                         h = trackCenterY * 2 + 8,
                         center = true, $fn = 24);

    for (side = [-1, 1])
        color(matDarkSteel)
            translate([x, side * trackCenterY, z])
                rotate([90, 0, 0])
                    cylinder(r = 7, h = 10, center = true, $fn = 24);
}

module chassis() {
    // No cross-members — footrest and hydraulic mount to L-bracket
    // arm cross-braces under the seat instead.

    // Aluminum axles.
    crossTrackAxle(-idlerX, idlerZ, false);
    crossTrackAxle(idlerX, idlerZ, true);
}
