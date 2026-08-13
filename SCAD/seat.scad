include <parameters.scad>
use <utils.scad>

//================ SEAT SUPPORT FRAME (L-BRACKETS) =================//
// Two L-brackets carry the seat. Each pivots on the FRONT idler
// cross-track axle (x = -idlerX) — the same axle the tracks tilt
// about when climbing. The seat + footrest are one body that hangs
// off this pivot and stays level while the tracks pitch underneath.
// Suspension beams mount to the track frame, NOT to the seat.

module seatBracket(y, w = 6) {
    panB = idlerZ + seatTopOffset - 5;   // pan bottom
    barX = -idlerX;                       // front idler cross-track axle = the pivot
    barZ = idlerZ;                        // axle height
    armBackX = idlerX - 14 + 2;           // reach back under the backrest

    // Hub that pivots on the front idler cross-track axle.
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

    // Vertical riser — up from the pivot axle to the pan bottom. Aluminum.
    color(matAluminum)
        translate([barX, y, (barZ + panB) / 2])
            cube([5, w, panB - barZ], center = true);

    // Horizontal arm: from the riser back, under the pan, to the backrest.
    color(matAluminum)
        translate([(barX + armBackX) / 2, y, panB - 2])
            cube([armBackX - barX, w - 1, 4], center = true);

    // Bolts up into the pan along the horizontal arm.
    for (bx = [-28, -14, 0])
        color(matChrome)
            translate([bx, y, panB + 2])
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
