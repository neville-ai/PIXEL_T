"""Render the audited PIXEL-T Sign Up activity diagram to PNG (monochrome, minimal).

The layout below mirrors ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.drawio
node-by-node and edge-by-edge so the raster export and the editable source stay
in sync. UML standard: filled initial node, bullseye final node, rhombus
decision nodes, square-bracket guards, orthogonal control flow.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _drawhelpers as H
from PIL import Image, ImageDraw

OUT = HERE

# ---------------------------------------------------------------------------
# Layout (drawio coordinates + offset for the title bar)
# ---------------------------------------------------------------------------
OX, OY = 20, 40
W, Hh = 860, 1010


def f(size, bold=False, italic=False):
    return H._font(size, bold=bold, italic=italic)


def rect(d, x, y, w, h, dashed=False, lw=1.2):
    H.rect(d, x + OX, y + OY, w, h, lw=lw, dash=dashed)


def circle(cx, cy, r, fill="black", lw=1.2):
    x, y = cx + OX, cy + OY
    d.ellipse([(x - r) * H.SCALE, (y - r) * H.SCALE,
               (x + r) * H.SCALE, (y + r) * H.SCALE],
              fill=fill, outline="black", width=max(1, int(lw * H.SCALE)))


def diamond(cx, cy, w, h, lw=1.2):
    pts = [(cx + OX, cy + OY - h / 2),
           (cx + OX + w / 2, cy + OY),
           (cx + OX, cy + OY + h / 2),
           (cx + OX - w / 2, cy + OY)]
    d.polygon([(p[0] * H.SCALE, p[1] * H.SCALE) for p in pts],
              fill="white", outline="black")
    for i in range(4):
        p0, p1 = pts[i], pts[(i + 1) % 4]
        d.line([(p0[0] * H.SCALE, p0[1] * H.SCALE),
                (p1[0] * H.SCALE, p1[1] * H.SCALE)],
               fill="black", width=max(1, int(lw * H.SCALE)))


def centered_text(cx, cy, lines, font):
    lh = 14
    y = cy + OY - (len(lines) * lh) / 2 + 2
    for ln in lines:
        H.text(d, cx + OX, y, ln, font=font, center=True)
        y += lh


def left_text(x, y, lines, font, lh=12):
    yy = y + OY
    for ln in lines:
        H.text(d, x + OX, yy, ln, font=font)
        yy += lh


def arrow(x0, y0, x1, y1, lw=1.2):
    H.arrow(d, x0 + OX, y0 + OY, x1 + OX, y1 + OY, lw=lw, head="open")


# ---------------------------------------------------------------------------
def activity(x, y, w, h, lines, font_size=11):
    rect(d, x, y, w, h)
    centered_text(x + w / 2, y + h / 2, lines, f(font_size))


def decision(cx, cy, w, h, lines, font_size=10):
    diamond(cx, cy, w, h)
    centered_text(cx, cy, lines, f(font_size))


def note(x, y, w, h, title, lines):
    rect(d, x, y, w, h, dashed=True, lw=1.0)
    H.text(d, x + OX + 8, y + OY + 8, title, font=f(10, bold=True))
    left_text(x + 8, y + 28, lines, f(9), lh=12)


def build():
    global d
    img, d = H.new_img(W, Hh)

    # Title
    H.text(d, W / 2, 12, "Activity Diagram Sign Up - PIXEL-T",
           font=f(14, bold=True), center=True)

    # Initial node (filled) — drawio st at (290,40,20,20), center (300,50)
    circle(300, 50, 10, fill="black")

    # Final node (bullseye) — drawio en at (280,946,40,40), center (300,966)
    circle(300, 966, 20, fill="white", lw=1.2)
    circle(300, 966, 10, fill="black")

    # Main flow activities
    activity(170, 88, 260, 42, ["Membuka halaman /register"])
    activity(170, 146, 260, 64, [
        "Mengisi formulir pendaftaran",
        "(nama lengkap, email, kata sandi,",
        "konfirmasi kata sandi, rumah sakit,",
        "spesialisasi dokter)",
    ])
    activity(170, 226, 260, 56, [
        "Memvalidasi input",
        "(wajib, format email, kata sandi >= 6,",
        "konfirmasi cocok)",
    ])
    decision(300, 333, 160, 70, ["Input valid?"])
    activity(560, 430, 180, 40, [
        "Menampilkan pesan kesalahan",
        "(validasi / Supabase Auth)",
    ], font_size=9)
    activity(170, 384, 260, 48, ["Memanggil signUp() ->", "supabase.auth.signUp()"])
    decision(300, 476, 160, 64, ["Permintaan signUp berhasil?"])
    activity(170, 524, 260, 48, [
        "Supabase membuat auth.users",
        "(dengan user_metadata)",
    ])
    activity(140, 588, 320, 60, [
        "Trigger handle_new_doctor_signup",
        "INSERT doctor_profiles (role='doctor',",
        "account_status='pending')",
    ])
    decision(300, 698, 180, 68, ["Sesi dikembalikan?"])
    activity(160, 748, 280, 56, [
        "Memperbarui state autentikasi",
        "role=doctor, account_status=pending",
    ])
    activity(480, 748, 200, 56, [
        "Menampilkan instruksi",
        "konfirmasi email",
    ])
    activity(150, 820, 300, 48, [
        "Menampilkan pesan pendaftaran berhasil",
        "(menunggu persetujuan admin)",
    ])
    activity(170, 884, 260, 42, ["Mengakses halaman /login"])

    # Note
    note(560, 70, 250, 130, "Catatan", [
        "Rute /register dilindungi PublicOnlyRoute.",
        "Pendaftaran publik hanya untuk Dokter.",
        "Admin dibuat via Supabase Admin API",
        "(app_metadata.role='admin') dan tidak memiliki",
        "baris doctor_profiles. Kegagalan trigger dicatat",
        "sebagai WARNING dan tidak membatalkan pendaftaran.",
    ])

    # Edges
    arrow(300, 60, 300, 88)          # st -> a1
    arrow(300, 130, 300, 146)        # a1 -> a2
    arrow(300, 210, 300, 226)        # a2 -> a3
    arrow(300, 282, 300, 298)        # a3 -> d1
    arrow(300, 368, 300, 384)        # d1 -> a4  [Ya]
    # d1 -> aerr [Tidak]
    arrow(380, 333, 500, 333)
    arrow(500, 333, 500, 430)
    arrow(500, 430, 560, 430)
    # aerr -> a2 loop
    arrow(650, 470, 650, 368)
    arrow(650, 368, 490, 368)
    arrow(490, 368, 490, 178)
    arrow(490, 178, 430, 178)
    arrow(300, 432, 300, 444)        # a4 -> d3
    arrow(300, 508, 300, 524)        # d3 -> a5  [Ya]
    # d3 -> aerr [Tidak]
    arrow(380, 476, 650, 476)
    arrow(650, 476, 650, 470)
    arrow(300, 572, 300, 588)        # a5 -> a6
    arrow(300, 648, 300, 664)        # a6 -> d2
    arrow(300, 732, 300, 748)        # d2 -> a7  [Ya]
    # d2 -> a8 [Tidak]
    arrow(390, 698, 465, 698)
    arrow(465, 698, 465, 776)
    arrow(465, 776, 480, 776)
    arrow(300, 804, 300, 820)        # a7 -> a9
    # a8 -> a9 merge
    arrow(580, 804, 580, 844)
    arrow(580, 844, 450, 844)
    arrow(300, 868, 300, 884)        # a9 -> a10
    arrow(300, 926, 300, 946)        # a10 -> en

    # Guard labels
    H.text(d, 300 + OX + 10, 376 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 325 + OY, "[Tidak]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 516 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 468 + OY, "[Tidak]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 740 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 690 + OY, "[Tidak]", font=f(10, bold=True))

    H.save(img, os.path.join(OUT, "ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.png"))


if __name__ == "__main__":
    build()
    print("Saved ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.png")
