// =========================================================================
// COMPLETE TWO-PART PROTOTYPE ENCLOSURE (DEEP LOWER CASE + UPPER LID)
// Designed for: Dual Stacked 700mAh LiPos + Pico 2 W + Sensors WITH Header Pins
// Units: Millimeters (mm) | Render Quality: $fn = 80
// =========================================================================

$fn = 80;

// Set to true to preview the lid sitting on top of the lower case;
// Keep false to lay parts flat side-by-side for 3D printing (STL export).
show_assembled = false;

// --- ENCLOSURE DIMENSIONS ---
case_l   = 58.0;        // X-axis length (along forearm)
case_w   = 50.0;        // Y-axis width (across wrist)
case_h   = 40.0;        // Total Z-height (accommodates stacked LiPos + black headers)
split_z  = 33.0;        // Lower case height (33mm deep tub) + Upper lid (7mm tall)
wall     = 2.0;         // Structural wall thickness
corner_r = 6.0;         // Outer vertical corner fillet radius
tol      = 0.25;        // 3D printing fit tolerance

// --- ERGONOMIC WRIST CURVATURE ---
wrist_r  = 65.0;        // Radius of human wrist contour on bottom face
arch_h   = 2.3;         // Center arch depth

// --- INTERNAL COMPONENT POCKETS & CUTOUTS ---
max_win_l = 14.0;       // MAX30102 optical skin window length
max_win_w = 10.0;       // MAX30102 optical skin window width
max_pcb_l = 18.8;       // MAX30102 PCB pocket length (extra clearance for header solder)
max_pcb_w = 14.8;       // MAX30102 PCB pocket width

pcb_ledge_z = 17.5;     // Z-height of internal shelf for Pico 2 W & MPU-6050 (above batteries)
usb_port_z  = 20.0;     // Z-height of USB / TP4056 cutout on left wall

// --- TOP INTERFACE (BUTTON & BUZZER) ---
btn_hole_d = 16.4;      // Reset button cutout diameter
btn_pos_x  = 10.0;      // Button X offset
buzzer_x   = -14.0;     // 12mm Piezo buzzer X offset
buzzer_d   = 12.4;      // Piezo buzzer retaining ring inner diameter

// --- STRAP SLOTS (DYNAMIC BACKPACK STYLE) ---
strap_slot_l = 26.0;    // 25mm Velcro strap width + 1mm clearance
strap_slot_w = 4.0;     // Slot thickness
strap_bar_t  = 3.2;     // Reinforced outer bar diameter

// =========================================================================
// RENDER LAYOUT
// =========================================================================

if (show_assembled) {
    color("SteelBlue") bottom_shell();
    color("LightSlateGray") translate([0, 0, 0.2]) top_shell();
    color("Crimson") translate([btn_pos_x, 0, case_h - wall - 1.2]) button_cap();
} else {
    // 1. DEEP LOWER CASE (Print upright with "Support on build plate only")
    translate([0, 0, 0])
        bottom_shell();

    // 2. UPPER LID (Flipped 180 deg so flat top face prints on bed with zero supports)
    translate([0, case_w + 22, case_h])
        rotate([180, 0, 0])
        top_shell();

    // 3. CAPTIVE TACTILE BUTTON CAP
    translate([case_l/2 + 18, 0, 0])
        button_cap();
}


// =========================================================================
// MODULE: OUTER ERGONOMIC BLANK
// =========================================================================
module ergonomic_outer_blank() {
    difference() {
        hull() {
            translate([0, 0, 1.5])
                rounded_rect(case_l, case_w, case_h - 4.0, corner_r);
            translate([0, 0, case_h - 2.5])
                rounded_rect(case_l - 3.0, case_w - 3.0, 2.5, corner_r - 1.5);
        }
        wrist_cutout(offset_r = 0);
    }
}

module wrist_cutout(offset_r = 0) {
    translate([0, 0, -(wrist_r - arch_h) + offset_r])
        rotate([0, 90, 0])
        cylinder(r = wrist_r, h = case_l + 30, center = true);
}

module rounded_rect(l, w, h, r) {
    hull() {
        for (x = [-l/2 + r, l/2 - r])
            for (y = [-w/2 + r, w/2 - r])
                translate([x, y, 0])
                    cylinder(r = r, h = h);
    }
}

// =========================================================================
// MODULE: DEEP LOWER PART (BOTTOM SHELL, Z = 0 to 33.0mm)
// =========================================================================
module bottom_shell() {
    difference() {
        union() {
            // Lower case body up to split_z (33.0mm)
            intersection() {
                ergonomic_outer_blank();
                translate([0, 0, split_z/2])
                    cube([case_l + 20, case_w + 20, split_z], center = true);
            }
            // Dynamic Velcro Strap Wings at wrist base
            strap_wings();

            // Top Male Interlocking Lip (Z = 33.0 to 34.6mm)
            difference() {
                translate([0, 0, split_z - 0.1])
                    rounded_rect(case_l - wall, case_w - wall, 1.7, corner_r - wall/2);
                translate([0, 0, split_z - 0.2])
                    rounded_rect(case_l - wall*2, case_w - wall*2, 2.0, corner_r - wall);
            }
        }

        // Deep Internal Cavity (follows curved floor up to Z = 33mm)
        difference() {
            translate([0, 0, wall])
                rounded_rect(case_l - wall*2, case_w - wall*2, split_z + 5, corner_r - wall);
            wrist_cutout(offset_r = wall);
        }

        // MAX30102 Optical Sensor Skin-Flush Window (Bottom Center)
        translate([0, 0, arch_h])
            cube([max_win_l, max_win_w, 10], center = true);

        // MAX30102 Internal Recessed Seat
        translate([0, 0, arch_h + wall + 1.2])
            cube([max_pcb_l, max_pcb_w, 3.2], center = true);

        // Side Cutout for Pico 2 W USB / TP4056 Charging Port (Left Wall)
        translate([-case_l/2, 0, usb_port_z])
            cube([wall*4, 14.0, 6.5], center = true);

        // Pilot Holes in Upper Corner Bosses for M2 Screws coming from Top Lid
        corner_screw_holes(is_bottom = true);
    }

    // Internal Structural Features inside Lower Case
    intersection() {
        ergonomic_outer_blank();
        union() {
            // Corner Screw Bosses (with pilot holes in top 10mm)
            difference() {
                corner_bosses(h = split_z);
                corner_screw_holes(is_bottom = true);
            }

            // Support Ledges at Z = 17.5mm (above stacked 700mAh batteries) for Pico 2 W & MPU-6050
            for (y_sign = [-1, 1]) {
                translate([0, y_sign * (case_w/2 - wall - 1.4), pcb_ledge_z])
                    cube([case_l - 16, 2.8, 1.8], center = true);
            }

            // MAX30102 Bottom Pocket Retaining Collar
            difference() {
                translate([0, 0, arch_h + 2.0])
                    cube([max_pcb_l + 2.4, max_pcb_w + 2.4, 4.0], center = true);
                translate([0, 0, arch_h + 2.0])
                    cube([max_pcb_l, max_pcb_w, 4.5], center = true);
            }
        }
    }
}

// =========================================================================
// MODULE: UPPER PART (TOP LID, Z = 33.0 to 40.0mm)
// =========================================================================
module top_shell() {
    difference() {
        // Upper lid outer body above split_z (33.0mm to 40.0mm)
        intersection() {
            ergonomic_outer_blank();
            translate([0, 0, split_z + (case_h - split_z)/2])
                cube([case_l + 20, case_w + 20, case_h - split_z], center = true);
        }

        // Inner roof hollow
        translate([0, 0, split_z - 1.0])
            rounded_rect(case_l - wall*2, case_w - wall*2, case_h - split_z - wall + 1.0, corner_r - wall);

        // Female alignment groove (snaps onto Lower Part lip)
        difference() {
            translate([0, 0, split_z - 0.1])
                rounded_rect(case_l - wall + tol*2, case_w - wall + tol*2, 1.9, corner_r - wall/2);
            translate([0, 0, split_z - 0.2])
                rounded_rect(case_l - wall*2 - tol*2, case_w - wall*2 - tol*2, 2.1, corner_r - wall);
        }

        // Tactile Reset Button Hole
        translate([btn_pos_x, 0, case_h - wall - 2])
            cylinder(d = btn_hole_d, h = 10);

        // 3x Acoustic Vent Slots for 12mm Piezo Buzzer
        for (i = [-1 : 1]) {
            translate([buzzer_x, i * 3.5, case_h - wall - 1])
                hull() {
                    translate([-3, 0, 0]) cylinder(d = 1.8, h = 6);
                    translate([ 3, 0, 0]) cylinder(d = 1.8, h = 6);
                }
        }

        // Debossed "RESET ALERT" Label on Top Face
        translate([btn_pos_x, -13.5, case_h - 0.6])
            linear_extrude(1.0)
            text("RESET ALERT", size = 3.2, font = "Arial:style=Bold", halign = "center", valign = "center");

        // Top M2 Counterbored Through-Holes
        corner_screw_holes(is_bottom = false);
    }

    // Internal Upper Lid Features (Corner Bosses + Buzzer Ring + Button Collar)
    intersection() {
        ergonomic_outer_blank();
        union() {
            difference() {
                corner_bosses(h = case_h);
                translate([0, 0, split_z/2])
                    cube([case_l + 10, case_w + 10, split_z + 0.2], center = true);
                corner_screw_holes(is_bottom = false);
            }
            // 12mm Piezo Buzzer Retaining Ring
            translate([buzzer_x, 0, case_h - wall - 3.0])
                difference() {
                    cylinder(d = buzzer_d + 2.4, h = 3.0);
                    translate([0, 0, -0.1]) cylinder(d = buzzer_d, h = 3.2);
                }
            // Tactile Button Guide Collar
            translate([btn_pos_x, 0, case_h - wall - 2.8])
                difference() {
                    cylinder(d = btn_hole_d + 3.2, h = 2.8);
                    translate([0, 0, -0.1]) cylinder(d = btn_hole_d + 0.2, h = 3.0);
                }
        }
    }
}

// =========================================================================
// MODULE: DYNAMIC FABRIC STRAP WINGS
// =========================================================================
module strap_wings() {
    for (y_side = [-1, 1]) {
        translate([0, y_side * (case_w/2 + 2.2), 3.2]) {
            difference() {
                hull() {
                    translate([0, -y_side * 2.5, 0])
                        cube([strap_slot_l + 6.0, 2.0, 5.0], center = true);
                    translate([0, y_side * (strap_slot_w/2 + strap_bar_t/2), -1.0])
                        rotate([0, 90, 0])
                        cylinder(d = 4.2, h = strap_slot_l + 4.0, center = true);
                }
                translate([0, y_side * 0.8, -0.5])
                    cube([strap_slot_l, strap_slot_w, 12.0], center = true);
            }
        }
    }
}

// =========================================================================
// MODULE: CAPTIVE TACTILE BUTTON CAP
// =========================================================================
module button_cap() {
    difference() {
        union() {
            cylinder(d = btn_hole_d + 2.2, h = 1.2);
            cylinder(d = btn_hole_d - tol*2, h = 4.8);
        }
        translate([0, 0, 14.8])
            sphere(r = 11.0);
        translate([0, 0, -0.1])
            cylinder(d = 4.2, h = 1.8);
    }
}

// =========================================================================
// HELPER MODULES: CORNER BOSSES & TOP-DOWN M2 SCREW HOLES
// =========================================================================
module corner_bosses(h) {
    for (x = [-case_l/2 + corner_r, case_l/2 - corner_r])
        for (y = [-case_w/2 + corner_r, case_w/2 - corner_r])
            translate([x, y, 0])
                cylinder(d = 6.2, h = h);
}

module corner_screw_holes(is_bottom = true) {
    for (x = [-case_l/2 + corner_r, case_l/2 - corner_r])
        for (y = [-case_w/2 + corner_r, case_w/2 - corner_r])
            translate([x, y, 0]) {
                if (is_bottom) {
                    // Self-tapping M2 pilot hole (1.75mm) in top 10mm of Lower Case bosses
                    translate([0, 0, split_z - 10.0])
                        cylinder(d = 1.75, h = 11.0);
                } else {
                    // M2 clearance hole (2.2mm) + recessed screw head counterbore in Upper Lid
                    translate([0, 0, split_z - 0.5])
                        cylinder(d = 2.2, h = case_h - split_z + 1.0);
                    translate([0, 0, case_h - 2.2])
                        cylinder(d = 4.2, h = 3.0);
                }
            }
}