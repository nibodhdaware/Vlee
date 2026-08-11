include <parameters.scad>

module beamBetween(p1, p2, width, height) {
    dx = p2[0] - p1[0];
    dz = p2[2] - p1[2];
    length = sqrt(dx * dx + dz * dz);
    angle = atan2(dz, dx);

    translate([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2])
        rotate([0, -angle, 0])
            cube([length, width, height], center = true);
}
