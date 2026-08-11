// Stair-climbing animation — correct triangular pivot mechanism
// Press F5 to play. The entire assembly pivots around the front drive sprocket.
include <parameters.scad>
use <utils.scad>
use <wheel.scad>
use <track.scad>
use <chassis.scad>
use <suspension.scad>
use <seat.scad>
use <footrest.scad>
use <hydraulic.scad>

// ===================== STAIRS =====================//
stairRise  = 18;
stairRun   = 24;
numSteps   = 5;
stairWidth = 80;

module stairs() {
    for (i = [0 : numSteps - 1])
        color([0.45, 0.42, 0.40])
            translate([idlerX + 30 + i * stairRun, 0, groundZ - stairRise * (i + 1)])
                cube([stairRun, stairWidth, stairRise], center = true);
}

// ===================== PIVOT GEOMETRY =====================//
// Everything pivots around the front drive sprocket
pivotX = idlerX;   // 48
pivotZ = idlerZ;   // 22

// Hydraulic arm: horizontal distance from pivot to hydraulic mount
hydrArm = pivotX - hydrMountX;  // 48 - 10 = 38

// Tilt angle from hydraulic extension: tan(angle) = extension / arm
function tiltFromExtension(ext) = ext > 0 ? atan2(ext, hydrArm) : 0;

// ===================== ANIMATION CURVES =====================//
function easeInOut(t, lo, hi) =
    let(n = (t - lo) / (hi - lo))
    n <= 0 ? 0 : n >= 1 ? 0 : (1 - cos(n * 180)) / 2;

// Phase timing:
//   0.00 – 0.15 : idle
//   0.15 – 0.35 : hydraulic extends → chair tilts (triangle forms)
//   0.35 – 0.50 : align tracks to stair edge
//   0.50 – 0.80 : hydraulic retracts, tracks land on stairs, climb
//   0.80 – 0.95 : level out at top
//   0.95 – 1.00 : idle at top

animHydrPct = easeInOut($t, 0.15, 0.35) - easeInOut($t, 0.50, 0.80);
animHydrExt = animHydrPct * hydrExtend;
animTilt = tiltFromExtension(max(0, animHydrExt));

// Climbing translation
animClimbX = ($t < 0.50) ? 0
           : ($t < 0.80) ? ($t - 0.50) / 0.30 * numSteps * stairRun * 0.5
           :                numSteps * stairRun * 0.5;

animClimbZ = ($t < 0.50) ? 0
           : ($t < 0.80) ? ($t - 0.50) / 0.30 * numSteps * stairRise * 0.5
           :                numSteps * stairRise * 0.5;

// ===================== ASSEMBLY =====================//
// The entire chair pivots around the front drive sprocket
translate([animClimbX, 0, animClimbZ]) {
    // Pivot around front sprocket — rear lifts when hydraulic extends
    translate([pivotX, 0, pivotZ])
        rotate([0, -animTilt, 0])
            translate([-pivotX, 0, -pivotZ]) {
                // Tracks
                tiltedTrack(trackCenterY);
                tiltedTrack(-trackCenterY);

                // Chassis
                chassis();

                // Suspension
                for (side = [-1, 1]) {
                    suspensionBeam(side * trackCenterY);
                    for (x = roadPositions)
                        suspension(x, side * trackCenterY);
                }

                // Seat
                seatPedestal();
                bucketSeat();

                // Footrest
                footrest();

                // Hydraulic — driven by animation
                hydraulicJackWheel(animHydrExt);
            }
}

// Stairs (static)
stairs();

// Ground plane
color([0.30, 0.30, 0.28])
    translate([0, 0, groundZ - 0.5])
        cube([200, stairWidth + 20, 1], center = true);
