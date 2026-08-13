include <parameters.scad>
use <utils.scad>

//================ RUBBER BUSHING SUSPENSION =================//
module suspension(x, y) {
    beamZ = idlerZ + trackRadius + 6;
    spindleZ = roadZ;
    gap = beamZ - spindleZ - 8;

    color(matDarkSteel)
        translate([x, y, beamZ - 1])
            cylinder(r = bushingRadius + 2, h = 2, center = true, $fn = 20);

    color(matRubber)
        translate([x, y, spindleZ + 4 + gap / 2])
            difference() {
                cylinder(r = bushingRadius, h = gap, center = true, $fn = 24);
                cylinder(r = 1.5, h = gap + 1, center = true, $fn = 16);
            }

    color(matDarkSteel)
        translate([x, y, spindleZ + 4])
            cylinder(r = bushingRadius + 2, h = 2, center = true, $fn = 20);

    translate([x, y, spindleZ])
        color(matDarkSteel)
            rotate([90, 0, 0])
                cylinder(r = 4, h = trackWidth + 4, center = true, $fn = 24);
}

//================ SUSPENSION BEAM (STRUCTURAL) =================//
module suspensionBeam(y) {
    beamZ = idlerZ + trackRadius + 6;
    beamStart = -idlerX + 8;
    beamEnd = idlerX - 12;
    beamLength = beamEnd - beamStart;

    // I-beam cross-section (structural profile, not a box)
    H = 20;                  // overall height (z)
    B = 12;                  // overall flange width (y)
    tf = 3;                  // flange thickness (z)
    tw = 3;                  // web thickness (y)
    webH = H - 2 * tf;

    gussetH = 25;
    gussetW = B + 4;
    gussetT = 4;

    color(matAluminum)
    union() {
        // I-beam: bottom flange, web, top flange (centered at beamZ)
        translate([(beamStart + beamEnd) / 2, y, beamZ - H/2 + tf/2])
            cube([beamLength, B, tf], center = true);
        translate([(beamStart + beamEnd) / 2, y, beamZ])
            cube([beamLength, tw, webH], center = true);
        translate([(beamStart + beamEnd) / 2, y, beamZ + H/2 - tf/2])
            cube([beamLength, B, tf], center = true);

        // Gusset at bracket end
        translate([beamEnd - gussetH/2, y, beamZ])
            cube([gussetH, gussetW, gussetT], center = true);

        // Vertical gusset plate at bracket end
        translate([beamEnd - gussetH/2, y, beamZ + gussetT/2 + (H - gussetT)/4])
            cube([gussetH, 3, (H - gussetT)/2], center = true);
    }
}