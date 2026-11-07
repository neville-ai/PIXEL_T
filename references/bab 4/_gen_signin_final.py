"""Render the PIXEL-T Sign In activity diagram to PNG (monochrome, minimal).

Layout mirrors ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.drawio node-by-node.
UML standard: filled initial node, bullseye final node, rhombus decision nodes,
square-bracket guards, orthogonal control flow.
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
W, Hh = 860, 1050


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


# ---------------------------------------------------------------------------
def build():
    global d
    img, d = H.new_img(W, Hh)

    # Title
    H.text(d, W / 2, 12, "Activity Diagram Sign In - PIXEL-T",
           font=f(14, bold=True), center=True)

    # Initial node (filled black circle)
    circle(300, 50, 10, fill="black")

    # Final node (bullseye)
    circle(300, 1030, 20, fill="white", lw=1.2)
    circle(300, 1030, 10, fill="black")

    # ── Main flow activities ──────────────────────────────────────
    activity(170, 88, 260, 42, ["Membuka halaman /login"])

    activity(170, 146, 260, 56, [
        "Mengisi email, kata sandi,",
        "dan memilih jenis akun",
    ])

    activity(170, 218, 260, 48, [
        "Memvalidasi input",
        "(email wajib, kata sandi wajib)",
    ])

    decision(300, 306, 160, 66, ["Input valid?"])

    # Error display (validation + auth failure)
    activity(560, 380, 180, 48, [
        "Menampilkan pesan kesalahan",
        "(validasi / autentikasi)",
    ])

    # Sign In call
    activity(170, 384, 260, 48, [
        "Memanggil signIn() ->",
        "supabase.auth.signInWithPassword()",
    ])

    # Credential check decision
    decision(300, 466, 160, 66, ["Kredensial valid?"])

    # Session update
    activity(170, 552, 280, 52, [
        "Memperbarui sesi & state autentikasi",
        "(user, session, role, account_status)",
    ])

    # Role match check
    decision(300, 638, 180, 66, ["Role cocok dengan akun?"])

    # Role mismatch error
    activity(560, 638, 200, 48, [
        "Menampilkan pesan jenis akun tidak sesuai",
    ])

    # Role decision
    decision(300, 734, 160, 66, ["Role = admin?"])

    # Admin redirect
    activity(170, 822, 200, 42, ["Mengarahkan ke /admin"])

    # Pending check
    decision(300, 822, 160, 66, ["Akun pending?"])

    # Pending redirect
    activity(560, 822, 220, 42, [
        "Kembali ke /login",
        "(menunggu persetujuan)",
    ])

    # Rejected check
    decision(300, 910, 160, 66, ["Akun ditolak?"])

    # Rejected redirect
    activity(560, 910, 220, 42, [
        "Kembali ke /login",
        "(pendaftaran ditolak)",
    ])

    # Dashboard redirect
    activity(170, 990, 260, 42, [
        "Mengakses halaman tujuan",
        "(dashboard atau halaman sebelumnya)",
    ])

    # Note
    note(560, 88, 250, 140, "Catatan", [
        "Halaman /login dilindungi PublicOnlyRoute.",
        "Role selector (Admin/Dokter) adalah konteks login,",
        "bukan sumber otorisasi. Role aktual ditentukan oleh:",
        "- app_metadata.role (admin, server-write-only)",
        "- doctor_profiles (dokter, dari database)",
        'Fitur "Remember my email" hanya menyimpan alamat',
        "email di localStorage, bukan sesi autentikasi.",
    ])

    # ── Edges (main flow) ────────────────────────────────────────
    arrow(300, 60, 300, 88)          # st -> a1
    arrow(300, 130, 300, 146)        # a1 -> a2
    arrow(300, 202, 300, 218)        # a2 -> a3
    arrow(300, 266, 300, 273)        # a3 -> d1 top

    # d1 -> a4 [Ya]
    arrow(300, 339, 300, 384)
    # d1 -> aerr [Tidak]
    arrow(380, 306, 500, 306)
    arrow(500, 306, 500, 380)
    arrow(500, 380, 560, 380)

    # aerr -> a2 (loop)
    arrow(650, 428, 650, 306)
    arrow(650, 306, 490, 306)
    arrow(490, 306, 490, 178)
    arrow(490, 178, 430, 178)
    arrow(300, 432, 300, 466)        # a4 -> d2

    # d2 -> a5 [Ya]
    arrow(300, 506, 300, 552)
    # d2 -> aerr [Tidak]
    arrow(380, 499, 650, 499)
    arrow(650, 499, 650, 428)

    # a5 -> d3
    arrow(300, 604, 300, 638)
    # d3 -> d4 [Ya]
    arrow(300, 701, 300, 734)
    # d3 -> a6 [Tidak]
    arrow(380, 671, 560, 671)
    arrow(560, 671, 560, 686)

    # a6 -> a2 (loop)
    arrow(660, 662, 660, 552)
    arrow(660, 552, 490, 552)
    arrow(490, 552, 490, 178)
    arrow(490, 178, 430, 178)

    # d4 -> a7 [Ya]
    arrow(300, 767, 300, 822)
    # d4 -> d5 [Tidak]
    arrow(300, 800, 300, 855)

    # d5 -> a8 [Ya]
    arrow(380, 855, 560, 855)
    arrow(560, 855, 560, 864)
    # d5 -> d6 [Tidak]
    arrow(300, 888, 300, 910)

    # d6 -> a9 [Ya]
    arrow(380, 943, 560, 943)
    arrow(560, 943, 560, 952)
    # d6 -> a10 [Tidak]
    arrow(300, 976, 300, 990)

    # a7 -> en
    arrow(270, 864, 270, 1010)
    arrow(270, 1010, 280, 1010)
    # a8 -> en
    arrow(670, 864, 670, 1010)
    arrow(670, 1010, 320, 1010)
    arrow(320, 1010, 320, 1030)
    # a9 -> en
    arrow(670, 952, 670, 1010)
    arrow(670, 1010, 320, 1010)
    # a10 -> en
    arrow(300, 1032, 300, 1050)

    # ── Guard labels ─────────────────────────────────────────────
    H.text(d, 300 + OX + 10, 348 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 298 + OY, "[Tidak]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 514 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 491 + OY, "[Tidak]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 712 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 400 + OX, 663 + OY, "[Tidak]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 808 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 868 + OY, "[Ya]", font=f(10, bold=True))
    H.text(d, 300 + OX + 10, 954 + OY, "[Ya]", font=f(10, bold=True))

    H.save(img, os.path.join(OUT, "ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.png"))


if __name__ == "__main__":
    build()
    print("Saved ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.png")
