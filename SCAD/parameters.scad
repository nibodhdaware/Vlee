// Shared parameters for tracked wheelchair prototype
// NOTE: 1 unit = 1 cm (seat target 450 mm = 45 units above ground).
$fn = 48;

//================ MATERIALS =================//
// Frame: aluminum 6061-T6 (lightweight)
// Seat: carbon fiber T700 + honeycomb (ultralight)
// Suspension: rubber bushings (lightweight)
// Axles: aluminum 7075-T6 (1/3 weight of steel)
matSteel      = [0.35, 0.36, 0.38];   // hardware / fasteners only
matDarkSteel  = [0.25, 0.26, 0.28];
matRubber     = [0.12, 0.12, 0.14];   // track belt + bushings
matAluminum   = [0.55, 0.57, 0.60];   // primary frame material
matChrome     = [0.70, 0.72, 0.75];
matCarbon     = [0.15, 0.15, 0.18];   // (unused — seat now aluminum)
matLeather    = [0.45, 0.25, 0.12];   // leather cushion color

//================ TRACKS =================//
trackLength = 82;
trackWidth = 14;
trackCenterY = 28;

idlerRadius = 10;
idlerX = trackLength / 2;
idlerZ = 16;
roadRadius = 7;
roadZ = 13;  // road wheels roll on the belt's inner surface (belt upper edge at this height)
roadPositions = [-22, -6, 10, 24];

linkLength = 10;
linkWidth = trackWidth + 2;
linkThickness = 3;
linkGap = 1;
// Belt centerline clears the idler wheels plus link half-thickness,
// so the links ride on the wheels instead of clipping through them.
trackRadius = idlerRadius + linkThickness / 2;  // = 11.5
beltThickness = 3;
groundZ = idlerZ - trackRadius;  // bottom of track = ground level (4.5)

//================ HYDRAULIC JACK WHEEL =================//
trackTilt = 0;
liftPivotX = idlerX;
liftPivotZ = idlerZ;
// Electric linear actuator (24V DC, 500kg, 300mm stroke).
// 1/3 weight of hydraulic system.
hydrWheelRadius = 4;
hydrWheelWidth = 10;
hydrBarrelRadius = 4;        // smaller barrel (mini actuator)
hydrBarrelHeight = 12;       // shorter barrel
hydrRodRadius = 2;
// At full extension the jack wheel rests on the ground:
// mountZ 35 - groundZ 4.5 - wheelR 4 = 26.5
hydrExtend = 26.5;
hydrRetracted = 0;
hydrExtendAmount = hydrExtend;
hydrMountX = 10;   // jack mount x; moved forward (from 24) for first-stair clearance
hydrMountY = 0;

//================ CHASSIS =================//
chassisLength = 82;
chassisBottom = 35;
chassisHeight = 12;

//================ SEAT =================//
// Seat geometry: flat aluminium pan + leather cushion + slim backrest.
// Seat surface rides at 450 mm (45 units) above the ground.
// topZ = idlerZ + seatTopOffset = 49.5, ground at 4.5 -> seat 45 above ground.
seatPanLength = 66;
seatPanWidth = 66;
backShellHeight = 72;
headrestHeight = 16;
seatTopOffset = 45 - trackRadius;  // = 33.5
// Backrest recline (deg from vertical).
seatBackRecline = 8;

//================ FOOTREST =================//
footrestWidth = 34;
footrestLength = 28;
footrestThickness = 3;       // 3mm aluminum plate
footrestHeight = idlerZ + 12;
footrestFrontX = -30 - footrestLength / 2;  // plate center, extends forward from arm end

// Folding footplate pivots at the end of the L-bracket arm.
footPivotX = -30;                           // end of L-bracket horizontal arm
footPivotZ = idlerZ + seatTopOffset - 7;    // arm height (panB - 2)
footHeelGuard = true;                       // optional heel guard
footToeGuard = false;                       // optional toe guard (off by default)

//================ ARMRESTS =================//
armPivotX = idlerX - 14;                     // rear post at the seat back
armLength = 68;                              // full-length pad (covers seat depth)
armPadHeight = idlerZ + seatTopOffset + 19;  // pad top = elbow height (~19 above seat top)
armPadWidth = 8;
armPadThick = 4;
