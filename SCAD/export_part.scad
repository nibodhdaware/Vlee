// Export individual parts as STL for Godot import
include <parameters.scad>
use <utils.scad>
use <wheel.scad>
use <track.scad>
use <chassis.scad>
use <suspension.scad>
use <seat.scad>
use <footrest.scad>
use <hydraulic.scad>

// ===================== PART 1: Single track assembly =====================
// Right track (Y=0 for export, Godot will position it)
trackAssembly();

// ===================== PART 2: Chassis =====================
// Uncomment to export chassis:
// chassis();

// ===================== PART 3: Seat pedestal =====================
// Uncomment to export seat:
// seatPedestal();
// bucketSeat();

// ===================== PART 4: Footrest =====================
// Uncomment to export footrest:
// footrest();

// ===================== PART 5: Hydraulic =====================
// Uncomment to export hydraulic:
// hydraulicJackWheel();
