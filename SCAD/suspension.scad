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

    wall = 3;
    boxH = 20;
    boxW = 12;

    gussetH = 25;
    gussetW = boxW + 4;
    gussetT = 4;

    flangeLen = 12;
    flangeH = boxH + 8;
    flangeW = boxW + 8;
    axleR = 5.5;

    color(matAluminum)
    union() {
        // Main beam tube
        translate([(beamStart + beamEnd) / 2, y, beamZ])
            difference() {
                cube([beamLength, boxW, boxH], center = true);
                cube([beamLength - 2*wall, boxW - 2*wall, boxH - 2*wall], center = true);
            }

        // Gusset at bracket end
        translate([beamEnd - gussetH/2, y, beamZ])
            cube([gussetH, gussetW, gussetT], center = true);

        // Vertical gusset plate at bracket end
        translate([beamEnd - gussetH/2, y, beamZ + gussetT/2 + (boxH - gussetT)/4])
            cube([gussetH, 3, (boxH - gussetT)/2], center = true);

        // Flange at chassis end - C-channel base
        translate([beamStart - flangeLen/2, y, beamZ])
            cube([flangeLen, flangeW, flangeH], center = true);

        // Flange notch (axle clearance U-shape)
        translate([beamStart - flangeLen/2 + 3, y, beamZ])
            difference() {
                cube([flangeLen - 6, flangeW, flangeH], center = true);
                cube([flangeLen - 6 - 2*wall, flangeW - 2*wall, flangeH - 2*wall], center = true);
                translate([-2, 0, -flangeH/2 + axleR + 2])
                    rotate([90, 0, 0])
                        cylinder(r = axleR, h = flangeW + 4, center = true, $fn = 24);
            }
    }
}