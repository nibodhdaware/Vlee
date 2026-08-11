include <parameters.scad>

module wheel(r, width, idler = false) {
    rotate([90, 0, 0]) {
        color(matRubber)
            difference() {
                cylinder(r = r, h = width, center = true, $fn = 48);
                cylinder(r = r - 2.5, h = width + 1, center = true, $fn = 48);
            }

        color(matAluminum)
            cylinder(r = r - 3, h = width - 2, center = true, $fn = 32);

        color(matAluminum)
            cylinder(r = idler ? 5.5 : 4.5, h = width + 3, center = true, $fn = 24);

        for (i = [0 : 5])
            rotate([0, 0, i * 60])
                color(matAluminum)
                    cube([2.5, 3, width - 1], center = true);
    }
}

module driveWheel(r, width) {
    wheel(r, width, true);

    rotate([90, 0, 0])
        for (i = [0 : 11])
            rotate([0, 0, i * 30])
                color(matDarkSteel)
                    translate([r - 0.5, 0, 0])
                        cube([4, width + 2, 3.5], center = true);
}
