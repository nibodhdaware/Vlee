include <parameters.scad>
use <utils.scad>

//================ SEAT SUPPORT FRAME (L-BRACKETS) =================//
// Two L-brackets carry the seat. Each one sits on the cross-bar that
// joins the two back drive sprockets. Aluminum construction.
// Suspension beams mount to the outboard side of each bracket riser.

module seatBracket(y, w = 6) {
    panB = idlerZ + seatTopOffset - 5;   // pan bottom
    barX = idlerX;                        // the drive cross-track bar (back sprockets)
    barZ = idlerZ;                        // bar height = sprocket axle height

    // Foot that clamps around the cross-track bar (wraps the axle).
    // Pinch bolt secures the clamp.
    color(matDarkSteel)
        translate([barX, y, barZ])
            rotate([90, 0, 0])
                difference() {
                    cube([12, 10, 14], center = true);
                    cylinder(r = 5.2, h = w + 6, center = true, $fn = 24);
                }
    // Pinch bolt through clamp
    color(matChrome)
        translate([barX, y, barZ + 6])
            cylinder(r = 1.2, h = 16, center = true, $fn = 12);

    // Vertical riser — up from the bar to the pan bottom. Aluminum.
    color(matAluminum)
        translate([barX, y, (barZ + panB) / 2])
            cube([5, w, panB - barZ], center = true);

    // Horizontal arm: out from the riser, under the pan, to the seat.
    armX2 = -30;
    color(matAluminum)
        translate([(barX + armX2) / 2, y, panB - 2])
            cube([barX - armX2, w - 1, 4], center = true);

    // Bolts up into the pan along the horizontal arm.
    for (bx = [20, 8, -6, -18])
        color(matChrome)
            translate([bx, y, panB + 2])
                rotate([0, bx == -18 ? -6 : 0, 0])
                    cylinder(r = 1.5, h = 6, center = true, $fn = 12);
}

//================ BUCKET SEAT =================//
// Aluminum seat with leather cushion:
//  - flat aluminium pan (3mm thick)
//  - leather cushion pad on top
//  - slim aluminium backrest panel with leather pad
//  - aluminium headrest

module roundedRectPlate(w, d, h, r, $fn = 32) {
    hull()
        for (sx = [-1, 1])
            for (sy = [-1, 1])
                translate([sx * (w / 2 - r), sy * (d / 2 - r), 0])
                    cylinder(r = r, h = h, center = true);
}

module bucketSeat() {
    topZ = idlerZ + seatTopOffset;
    backX = idlerX - 14;
    panCX = backX - seatPanLength / 2;
    L = seatPanLength;
    W = seatPanWidth;
    panH = 3;                            // aluminum pan (3mm thick)
    padH = 5;                            // leather cushion thickness
    corner = 9;

    // ---- Seat pan (aluminium plate, rounded corners). ----
    color(matAluminum)
        translate([panCX, 0, topZ - panH / 2])
            roundedRectPlate(L, W, panH, corner);

    // ---- Leather cushion pad (inset seating surface). ----
    color(matLeather)
        translate([panCX - 1, 0, topZ - padH / 2 - 0.5])
            roundedRectPlate(L - 10, W - 8, padH, corner - 2);

    // ---- Backrest panel: aluminium with leather pad. ----
    tilt = seatBackRecline;
    bw = W - 10;
    thick = 3;                          // aluminum (3mm thick)
    bh = backShellHeight;
    translate([backX, 0, topZ])
        rotate([0, tilt, 0]) {
            // main aluminium panel
            color(matAluminum)
                translate([-1, 0, bh / 2])
                    roundedRectPlate(thick, bw, bh, 2);

            // leather lumbar pad (lower back)
            color(matLeather)
                translate([-4.5, 0, 26])
                    roundedRectPlate(7, bw * 0.42, 16, 3);

            // headrest (aluminium)
            color(matAluminum)
                translate([-1, 0, bh + headrestHeight / 2 - 4])
                    roundedRectPlate(thick + 4, bw * 0.5, headrestHeight, 4);
        }
}
