"""Render PIXEL-T Sign In Sequence Diagram (FINAL VERIFIED) to PNG.

Based on independent deep audit of:
  - frontend/src/pages/auth/Login.tsx
  - frontend/src/context/AuthContext.tsx
  - frontend/src/services/auth.ts
  - frontend/src/components/auth/PublicOnlyRoute.tsx
  - frontend/src/components/auth/ProtectedRoute.tsx
  - frontend/src/components/auth/AdminRoute.tsx
  - frontend/src/routes/AppRoutes.tsx

UML conventions:
  - Solid arrow = synchronous call
  - Dashed arrow = return / response
  - Activation bar (narrow rect on lifeline) during processing
  - alt fragment = mutually exclusive branches
  - Combined fragment with title bar, guard conditions
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _drawhelpers as H
from PIL import Image, ImageDraw

# ── Dimensions ────────────────────────────────────────────────────────────────
OX = 24                       # left margin inside frame
OY = 42                       # top offset (title + frame border)
W  = 960                      # logical width  (pixels before 2×)
Hh = 760                      # logical height
BG = "#FFFFFF"
BLACK = "#000000"
WHITE = "#FFFFFF"

SCALE = 2

# ── Lifeline positions (horizontal, logical px from left of frame) ───────────
LIVES = [
    ("User",                   60),
    ("Login Page (Login.tsx)", 190),
    ("AuthContext (signIn)",   350),
    ("AuthService (loginUser)",510),
    ("Supabase Auth",          670),
    ("doctor_profiles (DB)",   830),
]
LF_W = 130            # lifeline box width
LF_H = 28             # lifeline box height
LF_SP = 10            # gap between lifeline right edge and next x
# Computed x-centers:
CX = {name: x + LF_W // 2 for name, x in LIVES}
# Computed x-left edges for drawing:
XL = {name: x for name, x in LIVES}

# ── Message y-positions (logical, measured from top of frame body, below lives)
# Frame body starts at y = LF_H + 10 = 38 inside frame
STEP_Y = {
    # Opening
    "open":    50,   # User → Login : buka /login
    "show_form": 78, # Login → User : tampilkan formulir
    # Submit
    "submit":  110,  # User → Login : submit(email, password, selectedRole)
    "validate":138,  # Login self : validasi input (email & password)
    # Auth call
    "call_signin": 166,  # Login → AuthContext : signIn(email, password, selectedRole)
    "call_login":  194,  # AuthContext → AuthService : loginUser(email, password)
    "call_auth":   222,  # AuthService → Supabase Auth : signInWithPassword(email, password)
    # Auth response
    "auth_return": 260,  # Supabase Auth → AuthService : {user, session}
    "svc_return":  288,  # AuthService → AuthContext : {data: {...}, error: null}
    # Role resolution
    "resolve_role":316,  # AuthContext self : resolve role (app_metadata.role)
    "fetch_profile":354,  # AuthContext → doctor_profiles : SELECT role, account_status
    "profile_return":388,  # doctor_profiles → AuthContext : {role, accountStatus}
    # alt1: role mismatch
    "alt1_title": 430,   # [alt] kredensial valid
    "alt1_else":  484,   # [else] kredensial tidak valid
    # alt2: navigasi
    "alt2_title": 520,   # [alt] role cocok
    "nav_admin":  554,   # Login → User : /admin
    "nav_pending":588,   # Login → User : /login (pending)
    "nav_rejected":622,  # Login → User : /login (rejected)
    "nav_dashboard":656, # Login → User : /dashboard
    # Errors
    "err_creds":  690,   # AuthContext → Login : error
    "err_mismatch":720,  # AuthContext → Login : error role mismatch
    "err_nav":    750,   # Login → User : pesan error
}

# Frame bounds (logical)
FRAME_L = 10
FRAME_T = LF_H + 8
FRAME_R = W - 10
FRAME_B = Hh - 10

# Alt fragment bounds (logical, within frame)
ALT1_T = STEP_Y["alt1_title"] - 6
ALT1_B = STEP_Y["alt1_else"] + 48 + 10   # extends past else content
ALT2_T = STEP_Y["alt2_title"] - 6
ALT2_B = STEP_Y["nav_dashboard"] + 30 + 10


def f(size, bold=False, italic=False):
    return H._font(size, bold=bold, italic=italic)


def draw_rect(d, x, y, w, h, fill=None, outline=BLACK, lw=1.2):
    sx, sy, sw, sh = x * SCALE, y * SCALE, w * SCALE, h * SCALE
    kw = max(1, int(lw * SCALE))
    if fill:
        d.rectangle([sx, sy, sx + sw, sy + sh], fill=fill, outline=outline, width=kw)
    else:
        d.rectangle([sx, sy, sx + sw, sy + sh], outline=outline, width=kw)


def draw_arrow(d, x0, y0, x1, y1, dashed=False, head="closed", fill=BLACK):
    """Draw an arrow from (x0,y0) to (x1,y1). head: 'closed' or 'open'."""
    sx0, sy0 = x0 * SCALE, y0 * SCALE
    sx1, sy1 = x1 * SCALE, y1 * SCALE
    kw = max(1, int(1.2 * SCALE))
    dash_seg = int(4 * SCALE)
    if dashed:
        d.setdash([dash_seg, dash_seg])
    else:
        d.setdash(None)
    d.line([(sx0, sy0), (sx1, sy1)], fill=fill, width=kw)
    # Arrowhead
    dx, dy = sx1 - sx0, sy1 - sy0
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return
    nx, ny = dx / length, dy / length
    # Perpendicular
    px, py = -ny, nx
    hs = max(5, int(8 * SCALE))   # half-size of arrowhead base
    le = max(6, int(10 * SCALE))  # length of arrowhead
    tip_x = sx1
    tip_y = sy1
    base_x1 = sx1 - nx * le + px * hs
    base_y1 = sy1 - ny * le + py * hs
    base_x2 = sx1 - nx * le - px * hs
    base_y2 = sy1 - ny * le - py * hs
    if dashed:
        d.setdash(None)
    if head == "closed":
        d.polygon([(tip_x, tip_y), (base_x1, base_y1), (base_x2, base_y2)], fill=fill)
    else:
        d.line([(tip_x, tip_y), (base_x1, base_y1)], fill=fill, width=kw)
        d.line([(tip_x, tip_y), (base_x2, base_y2)], fill=fill, width=kw)
    d.setdash(None)


def centered_text(d, cx, cy, text, font, lh=14):
    """Center text around (cx, cy)."""
    tw = H.text_w(d, text, font)
    x = cx - tw // 2
    H.text(d, x, cy, text, font=font)


def text_below(d, cx, y, text, font, lh=14):
    H.text(d, cx - H.text_w(d, text, font) // 2, y, text, font=font)


# ── Build diagram ────────────────────────────────────────────────────────────
img, d = H.new_img(W, Hh)

# Background
img.paste(BG, (0, 0, img.width, img.height))
d = ImageDraw.Draw(img)

# Title
title_font = f(13, bold=True)
tw = H.text_w(d, "Sequence Diagram Sign In - PIXEL-T", title_font)
H.text(d, (W - tw) // 2, 8, "Sequence Diagram Sign In - PIXEL-T", font=title_font)

# Frame rectangle
frame_font = f(10, bold=True)
H.text(d, FRAME_L + 6, FRAME_T + 2, "Sign In", font=frame_font)
draw_rect(d, FRAME_L, FRAME_T, FRAME_R - FRAME_L, FRAME_B - FRAME_T, outline=BLACK, lw=1.2)

# ── Lifeline boxes + lines ───────────────────────────────────────────────────
for name, lx in XL:
    draw_rect(d, lx, FRAME_T, LF_W, LF_H, fill=WHITE, outline=BLACK, lw=1.2)
    centered_text(d, CX[name], FRAME_T + LF_H // 2, name, f(9, bold=True))
    # Lifeline (dashed vertical)
    line_x = CX[name] * SCALE
    d.line([line_x, (FRAME_T + LF_H) * SCALE,
            line_x, (FRAME_B - 4) * SCALE],
           fill=BLACK, width=max(1, int(1.0 * SCALE)))


def activation_bar(y_top, y_bot):
    """Draw activation bar on AuthContext lifeline (center x = CX['AuthContext (signIn)'])."""
    ax = CX["AuthContext (signIn)"]
    sx, sy = ax * SCALE, y_top * SCALE
    sw, sh = max(2, int(4 * SCALE)), max(2, int((y_bot - y_top) * SCALE))
    d.rectangle([sx, sy, sx + sw, sy + sh], fill=BLACK)


def msg(src, tgt, label, y, dashed=False, head="closed"):
    """Draw a message arrow between two lifelines."""
    src_cx = CX[src]
    tgt_cx = CX[tgt]
    draw_arrow(d, src_cx, y, tgt_cx, y, dashed=dashed, head=head)
    # Label above arrow (centered)
    lbl_font = f(8 if len(label) > 25 else 9)
    lbl_w = H.text_w(d, label, lbl_font)
    mid_x = (src_cx + tgt_cx) // 2
    H.text(d, mid_x - lbl_w // 2, y - 10, label, font=lbl_font)


def msg_offset(src, tgt, label, y, offset, dashed=False, head="closed"):
    """Draw a message with horizontal offset (to avoid overlap)."""
    src_cx = CX[src] + offset
    tgt_cx = CX[tgt] + offset
    draw_arrow(d, src_cx, y, tgt_cx, y, dashed=dashed, head=head)
    lbl_font = f(8 if len(label) > 25 else 9)
    lbl_w = H.text_w(d, label, lbl_font)
    mid_x = (src_cx + tgt_cx) // 2
    H.text(d, mid_x - lbl_w // 2, y - 10, label, font=lbl_font)


def self_msg(lifename, label, y, offset_x=15, dashed=False):
    """Draw a self-loop message on a lifeline."""
    cx = CX[lifename]
    ox = offset_x
    # Path: right, down, left, down, left (back to lifeline)
    x1, y1 = cx + ox, y
    x2, y2 = cx + ox + 30, y
    x3, y3 = cx + ox + 30, y + 18
    x4, y4 = cx + ox, y + 18
    x5, y5 = cx, y + 24
    draw_arrow(d, x1, y1, x2, y2, dashed=dashed)
    d.line([(x2 * SCALE, y2 * SCALE), (x3 * SCALE, y3 * SCALE)], fill=BLACK, width=max(1, int(1.0 * SCALE)))
    draw_arrow(d, x3, y3, x4, y4, dashed=dashed)
    d.line([(x4 * SCALE, y4 * SCALE), (x5 * SCALE, y5 * SCALE)], fill=BLACK, width=max(1, int(1.0 * SCALE)))
    # Label
    lbl_font = f(8)
    lbl_w = H.text_w(d, label, lbl_font)
    H.text(d, x2 + 4, y + 4, label, font=lbl_font)


# ── Draw messages ─────────────────────────────────────────────────────────────

# 1: User → Login : buka /login
msg("User", "Login Page (Login.tsx)", "buka /login", STEP_Y["open"])
# 2: Login → User : tampilkan formulir (dashed return)
msg("Login Page (Login.tsx)", "User", "tampilkan formulir", STEP_Y["show_form"], dashed=True)

# 3: User → Login : submit
msg("User", "Login Page (Login.tsx)", "submit(email, password, selectedRole)", STEP_Y["submit"])
# 4: Login self : validasi input
self_msg("Login Page (Login.tsx)", "validasi input", STEP_Y["validate"])

# 5: Login → AuthContext : signIn
msg("Login Page (Login.tsx)", "AuthContext (signIn)", "signIn(email, password, selectedRole)",
    STEP_Y["call_signin"])
# Activate AuthContext
activation_bar(STEP_Y["call_signin"] - 2, STEP_Y["fetch_profile"] + 30)

# 6: AuthContext → AuthService : loginUser
msg("AuthContext (signIn)", "AuthService (loginUser)", "loginUser(email, password)",
    STEP_Y["call_login"])
# Activate AuthService
asx = CX["AuthService (loginUser)"]
draw_rect(d, asx - 2, (STEP_Y["call_login"] - 2) * SCALE, 4 * SCALE,
          (STEP_Y["call_auth"] - STEP_Y["call_login"] + 6) * SCALE, fill=BLACK)

# 7: AuthService → Supabase Auth : signInWithPassword
msg("AuthService (loginUser)", "Supabase Auth", "signInWithPassword(email, password)",
    STEP_Y["call_auth"])
# Activate Supabase Auth
sa_x = CX["Supabase Auth"]
draw_rect(d, sa_x - 2, (STEP_Y["call_auth"] - 2) * SCALE, 4 * SCALE,
          (STEP_Y["auth_return"] - STEP_Y["call_auth"] + 6) * SCALE, fill=BLACK)

# 8: Supabase Auth → AuthService : {user, session}
msg("Supabase Auth", "AuthService (loginUser)", "{ user, session }",
    STEP_Y["auth_return"], dashed=True)
# 9: AuthService → AuthContext : {data: {...}, error: null}
msg("AuthService (loginUser)", "AuthContext (signIn)", "{ data, error: null }",
    STEP_Y["svc_return"], dashed=True)

# 10: AuthContext self : resolve role
self_msg("AuthContext (signIn)", "resolve role\n(app_metadata.role)",
         STEP_Y["resolve_role"])

# 11: AuthContext → doctor_profiles : SELECT role, account_status
msg("AuthContext (signIn)", "doctor_profiles (DB)",
    "SELECT role, account_status WHERE user_id",
    STEP_Y["fetch_profile"])
# Activate doctor_profiles
dp_x = CX["doctor_profiles (DB)"]
draw_rect(d, dp_x - 2, (STEP_Y["fetch_profile"] - 2) * SCALE, 4 * SCALE,
          (STEP_Y["profile_return"] - STEP_Y["fetch_profile"] + 6) * SCALE, fill=BLACK)

# 12: doctor_profiles → AuthContext : {role, accountStatus}
msg("doctor_profiles (DB)", "AuthContext (signIn)", "{ role, accountStatus }",
    STEP_Y["profile_return"], dashed=True)

# End activation for AuthContext
activation_bar_end = STEP_Y["profile_return"] + 20

# ── ALT1: kredensial valid / tidak valid ─────────────────────────────────────
# Frame
alt1_l = min(XL[name] for name, _ in LIVES)
alt1_r = max(XL[name] + LF_W for name, _ in LIVES)
draw_rect(d, alt1_l, ALT1_T, alt1_r - alt1_l, ALT1_B - ALT1_T, outline=BLACK, lw=1.2)
# Title bar
draw_rect(d, alt1_l, ALT1_T, alt1_r - alt1_l, 18, fill=WHITE, outline=BLACK, lw=1.2)
# Split line
split_y = ALT1_T + 18 + (ALT1_B - ALT1_T - 18) // 2
d.line([(alt1_l + 2) * SCALE, split_y * SCALE,
        (alt1_r - 2) * SCALE, split_y * SCALE],
       fill=BLACK, width=max(1, int(1.0 * SCALE)))
# Labels
lbl_font_a = f(9, bold=True)
lbl_font_b = f(9, bold=True)
H.text(d, alt1_l + 6, ALT1_T + 4, "[alt] kredensial valid", font=lbl_font_a)
H.text(d, alt1_l + 6, split_y + 4, "[else] kredensial tidak valid", font=lbl_font_b)

# Success path inside alt1 (role mismatch check after profile fetch)
# Role mismatch error message from AuthContext → Login
msg("AuthContext (signIn)", "Login Page (Login.tsx)",
    "error: \"Jenis akun tidak sesuai\"",
    STEP_Y["err_mismatch"], dashed=True)
# Error display by Login → User
msg("Login Page (Login.tsx)", "User", "tampilkan pesan error",
    STEP_Y["err_nav"], dashed=True)

# Else path (credentials invalid) - dashed return to Login
# Show a short label inside the else branch
H.text(d, CX["AuthContext (signIn)"], STEP_Y["alt1_else"] + 8,
       "kredensial salah / email belum dikonfirmasi", font=f(8, italic=True))

# Close alt1 activation end
# Draw a small tick mark at end of AuthContext activation
ax_cx = CX["AuthContext (signIn)"]
d.line([(ax_cx - 4) * SCALE, (ALT1_B + 2) * SCALE,
        (ax_cx + 4) * SCALE, (ALT1_B + 2) * SCALE],
       fill=BLACK, width=max(1, int(1.2 * SCALE)))

# ── ALT2: navigasi berdasarkan role & status ────────────────────────────────
draw_rect(d, alt1_l, ALT2_T, alt1_r - alt1_l, ALT2_B - ALT2_T, outline=BLACK, lw=1.2)
draw_rect(d, alt1_l, ALT2_T, alt1_r - alt1_l, 18, fill=WHITE, outline=BLACK, lw=1.2)
split_y2 = ALT2_T + 18 + (ALT2_B - ALT2_T - 18) // 2
d.line([(alt1_l + 2) * SCALE, split_y2 * SCALE,
        (alt1_r - 2) * SCALE, split_y2 * SCALE],
       fill=BLACK, width=max(1, int(1.0 * SCALE)))
H.text(d, alt1_l + 6, ALT2_T + 4, "[alt] role cocok, bukan admin", font=lbl_font_a)
H.text(d, alt1_l + 6, split_y2 + 4, "[else] role mismatch / admin langsung ke /admin", font=lbl_font_b)

# Admin path (from else branch label, drawn as a message above)
msg("Login Page (Login.tsx)", "User",
    "/admin", STEP_Y["nav_admin"], dashed=True)

# Doctor paths
msg("Login Page (Login.tsx)", "User",
    "/login (pending)", STEP_Y["nav_pending"], dashed=True)
msg("Login Page (Login.tsx)", "User",
    "/login (rejected)", STEP_Y["nav_rejected"], dashed=True)
msg("Login Page (Login.tsx)", "User",
    "/dashboard", STEP_Y["nav_dashboard"], dashed=True)

# ── Note box ─────────────────────────────────────────────────────────────────
note_x = alt1_l
note_y = ALT2_B + 16
note_w = alt1_r - alt1_l
note_h = 80
draw_rect(d, note_x, note_y, note_w, note_h, fill=WHITE, outline=BLACK, lw=1.0)
# Fold corner
corner = 14
d.polygon([(note_x * SCALE + (note_w - corner) * SCALE, note_y * SCALE),
           (note_x * SCALE + (note_w - corner) * SCALE,
            (note_y + corner) * SCALE),
           (note_x * SCALE + note_w * SCALE, (note_y + corner) * SCALE)],
          fill=WHITE, outline=BLACK)
d.line([(note_x * SCALE + (note_w - corner) * SCALE, (note_y + corner) * SCALE),
        (note_x * SCALE + (note_w - corner) * SCALE, note_y * SCALE)],
       fill=BLACK, width=max(1, int(1.0 * SCALE)))
note_font = f(8)
note_lines = [
    "Catatan:",
    "Login hanya memakai Supabase Auth (tidak ada endpoint Flask).",
    "Role Admin: app_metadata.role (server-write-only).",
    "Role Dokter: doctor_profiles.role (dari database).",
    'Fitur "Remember my email" hanya menyimpan alamat email di localStorage.',
    "Halaman Reset Password merupakan use case terpisah.",
]
ny = note_y + 8
for ln in note_lines:
    H.text(d, note_x + 8, ny, ln, font=note_font)
    ny += 12

# ── Save ─────────────────────────────────────────────────────────────────────
out_path = os.path.join(HERE, "SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_VERIFIED.png")
img.save(out_path, "PNG")
print(f"Saved: {out_path}  ({img.size[0]}×{img.size[1]} px)")
