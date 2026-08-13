//================ VLEE ERGONOMIC JOYSTICK =================//
// A proper joystick: console base + gimbal + tilting stick + palm knob.
// Readable at a glance as a joystick, and operable one-handed by claw
// hands — you cup the palm dome and push; no finger work.
//
// Two products from the same parts:
//   1. vleeJoystick()  — the B1000's own joystick (console mounted).
//   2. palmKnob()      — replacement KNOB for PG Drives GC2/GC3/VR2/VSI
//      joysticks (shared MAID II gimbal) — SKU #1 for the existing fleet.
include <parameters.scad>
use <utils.scad>

// ---- knob (palm dome) ----
knobR        = 30;      // palm dome radius
knobH        = 22;      // dome height
knobSkirt    = 14;      // collar under the dome (hand slip guard)

// ---- stick ----
stickR       = 8;       // stem radius
stickLen     = 46;      // stem length (tilt arm above gimbal)
stickTilt    = 18;      // visual tilt of the stick (rests slightly forward)

// ---- gimbal + console base ----
gimbalR      = 16;      // spherical joint radius (hidden under boot)
bootH        = 18;      // rubber boot height above the console
consoleR     = 42;      // console/plate radius
consoleH     = 8;       // console plate thickness
baseH        = 16;      // base riser to the armrest

// Palm dome knob — cupped by the hand, no pinch grip needed.
module palmKnob() {
    // Skirt / collar — stops the hand sliding off.
    color(matAluminum)
        translate([0, 0, knobSkirt / 2])
            difference() {
                cylinder(r = knobR - 4, h = knobSkirt, center = true, $fn = 64);
                cylinder(r = stickR + 1, h = knobSkirt + 1, center = true, $fn = 32);
            }
    // Low dome — heel of hand rests on this.
    color(matRubber)
        translate([0, 0, knobSkirt])
            scale([1, 1, 0.75])
                sphere(r = knobR, $fn = 64);
    // Aluminum cap.
    color(matAluminum)
        translate([0, 0, knobSkirt + knobH * 0.5])
            scale([1, 1, 0.45])
                sphere(r = knobR, $fn = 64);
}

// The tilting stick — goes down into the gimbal.
module joystickStick() {
    color(matAluminum)
        translate([0, 0, stickLen / 2])
            rotate([stickTilt, 0, 0])
                cylinder(r = stickR, h = stickLen, center = true, $fn = 32);
}

// Console base with gimbal and rubber boot.
module joystickConsole() {
    // Base riser (to the armrest).
    color(matAluminum)
        translate([0, 0, baseH / 2])
            cylinder(r = consoleR - 6, h = baseH, center = true, $fn = 48);
    // Console plate.
    color(matDarkSteel)
        translate([0, 0, baseH + consoleH / 2])
            cylinder(r = consoleR, h = consoleH, center = true, $fn = 48);
    // Gimbal (spherical joint) — the thing the stick pivots in.
    color(matDarkSteel)
        translate([0, 0, baseH + consoleH + gimbalR * 0.6])
            sphere(r = gimbalR, $fn = 32);
    // Rubber boot over the gimbal — the classic joystick boot.
    color(matRubber)
        translate([0, 0, baseH + consoleH + bootH / 2])
            cylinder(r1 = gimbalR + 3, r2 = stickR + 2, h = bootH, $fn = 48);
}

// Speed dial on the console face.
module speedDial() {
    color(matChrome)
        translate([consoleR * 0.55, 0, baseH + consoleH / 2 + 2])
            rotate([0, 0, 0])
                cylinder(r = 8, h = 3, center = true, $fn = 32);
}

// Horn button on the console.
module hornButton() {
    color(matLeather)
        translate([-consoleR * 0.55, 0, baseH + consoleH / 2 + 3])
            cylinder(r = 7, h = 4, center = true, $fn = 32);
}

//================ PRODUCT 1: the B1000's own joystick =================//
module vleeJoystick() {
    joystickConsole();
    speedDial();
    hornButton();
    joystickStick();
    palmKnob();
}

// Self-render on open.
vleeJoystick();