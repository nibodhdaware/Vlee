include <parameters.scad>
use <wheel.scad>

//================ TRACK =================//
// One seamless rubber belt: a closed band that follows a stadium
// (two straight runs joined by semicircular caps around the idler /
// drive wheels). Built as a single extruded 2D ring so there is NO
// link seam. The wheels ride inside the loop.

// 2D stadium outline: two disk caps radius `c` at x=±xcap, hulled,
// forming the centerline fill. Difference of an outer and inner
// stadium yields the constant-wall-thickness belt ring.
module stadium2d(xCap, radius) {
    hull() {
        translate([-xCap, 0]) circle(r = radius, $fn = 96);
        translate([xCap, 0]) circle(r = radius, $fn = 96);
    }
}

// Belt ring in the X/Y-cap plane (centered on the wheel axis row).
// innerR = trackRadius - beltHalf, outerR = trackRadius + beltHalf.
module beltRing() {
    halfT = beltThickness / 2;
    difference() {
        stadium2d(idlerX, trackRadius + halfT);
        stadium2d(idlerX, trackRadius - halfT);
    }
}

module trackBelt() {
    // Extrude the Y ring into the +Z direction and lay it into the
    // track plane: rotate so the belt thickness spans X*Y like the links.
    color(matRubber)
        translate([0, 0, idlerZ])
            rotate([90, 0, 0])
                linear_extrude(height = trackWidth, center = true)
                    beltRing();
}

module trackLinks() {
    // Belt is now a single continuous band; keep classic moulded-pad
    // look by adding a subtle tread overlay on the outer surface.
    trackBelt();
}

module trackAssembly() {
    for (x = roadPositions)
        translate([x, 0, roadZ])
            wheel(roadRadius, trackWidth, false);

    translate([-idlerX, 0, idlerZ])
        wheel(idlerRadius, trackWidth, true);
    translate([idlerX, 0, idlerZ])
        driveWheel(idlerRadius, trackWidth);

    trackLinks();
}