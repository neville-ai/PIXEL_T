"""Render the audited PIXEL-T use-case revision to PNG (monochrome, minimal).

Layout is intentionally identical to USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.drawio
so the raster export and the editable source stay in sync.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _drawhelpers as H
from PIL import Image, ImageDraw

OUT = HERE


def f(size, bold=False, italic=False):
    return H._font(size, bold=bold, italic=italic)


def use_case(d, x, y, label, w=170, h=44):
    d.ellipse([x * H.SCALE, y * H.SCALE, (x + w) * H.SCALE, (y + h) * H.SCALE],
              fill="white", outline="black", width=max(1, int(1.2 * H.SCALE)))
    lines = label.split("\n")
    yy = y + h / 2 - (len(lines) * 11) / 2 + 1
    for ln in lines:
        H.text(d, x + w / 2, yy, ln, font=f(9), center=True)
        yy += 11


def polyline(d, pts, dashed=False):
    for i in range(len(pts) - 1):
        H.arrow(d, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                dashed=dashed, head="none")


def open_arrow(d, x0, y0, x1, y1, dashed=False):
    """Final segment carrying an open arrowhead at (x1, y1)."""
    H.arrow(d, x0, y0, x1, y1, dashed=dashed, head="open")


def render():
    W, Hh = 1200, 980
    img, d = H.new_img(W, Hh)

    # --- System boundary ---
    H.rect(d, 290, 120, 700, 780, lw=1.2)
    H.text(d, 302, 128, "Sistem PIXEL-T", font=f(12, bold=True))

    # --- Actors ---
    H.actor(d, 130, 700, "Calon Pengguna")
    H.actor(d, 130, 450, "Dokter")
    H.actor(d, 1100, 510, "Admin")

    # --- Shared use cases ---
    use_case(d, 520, 150, "Sign Up")
    use_case(d, 520, 220, "Sign In")
    use_case(d, 520, 290, "Sign Out")

    # --- Doctor use cases ---
    use_case(d, 350, 400, "Reset Password")
    use_case(d, 350, 470, "Upload Image")
    use_case(d, 350, 540, "Segmentation")
    use_case(d, 350, 610, "View History")
    use_case(d, 350, 680, "Search / Filter History")
    use_case(d, 350, 750, "View Doctor\nProfile")
    use_case(d, 350, 820, "Edit Doctor\nProfile")

    # --- Admin use cases ---
    use_case(d, 810, 350, "View Admin\nDashboard")
    use_case(d, 810, 430, "View Doctor\nRegistrations")
    use_case(d, 810, 510, "Approve Doctor\nAccount")
    use_case(d, 810, 590, "Reject Doctor\nAccount")

    # ================= ASSOCIATIONS (solid) =================
    # Calon Pengguna -> Sign Up, Sign In
    polyline(d, [(150, 720), (150, 172), (520, 172)])
    polyline(d, [(150, 725), (150, 232), (520, 232)])

    # Dokter -> Sign In, Sign Out, Upload, Segmentation, View History, View Profile
    polyline(d, [(165, 470), (210, 470), (210, 252), (520, 252)])
    polyline(d, [(165, 478), (220, 478), (220, 312), (520, 312)])
    polyline(d, [(165, 486), (230, 486), (230, 492), (350, 492)])
    polyline(d, [(165, 494), (240, 494), (240, 562), (350, 562)])
    polyline(d, [(165, 502), (250, 502), (250, 632), (350, 632)])
    polyline(d, [(165, 510), (260, 510), (260, 772), (350, 772)])

    # Admin -> Sign In, Sign Out, admin use cases
    polyline(d, [(1080, 540), (1035, 540), (1035, 242), (690, 242)])
    polyline(d, [(1080, 548), (1025, 548), (1025, 322), (690, 322)])
    polyline(d, [(1080, 556), (1015, 556), (1015, 372), (980, 372)])
    polyline(d, [(1080, 564), (1005, 564), (1005, 452), (980, 452)])
    polyline(d, [(1080, 572), (995, 572), (995, 532), (980, 532)])
    polyline(d, [(1080, 580), (985, 580), (985, 612), (980, 612)])

    # ================= STEREOTYPE RELATIONS (dashed) =================
    # <<include>> Segmentation -> Upload Image
    open_arrow(d, 435, 540, 435, 514, dashed=True)
    H.text(d, 443, 520, "<<include>>", font=f(8))

    # <<extend>> Reset Password -> Sign In
    polyline(d, [(520, 422), (585, 422), (585, 270)], dashed=True)
    open_arrow(d, 585, 270, 585, 264, dashed=True)
    H.text(d, 593, 400, "<<extend>>", font=f(8))

    # <<extend>> Search / Filter History -> View History
    open_arrow(d, 435, 680, 435, 654, dashed=True)
    H.text(d, 443, 660, "<<extend>>", font=f(8))

    # <<extend>> Edit Doctor Profile -> View Doctor Profile
    open_arrow(d, 435, 820, 435, 794, dashed=True)
    H.text(d, 443, 800, "<<extend>>", font=f(8))

    # --- Title ---
    H.text(d, 290, 88, "Use Case Diagram PIXEL-T (Revisi Audit)",
           font=f(13, bold=True))

    out = os.path.join(OUT, "USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.png")
    H.save(img, out)
    return out


if __name__ == "__main__":
    path = render()
    # Integrity check: the file must reopen and decode as a valid image.
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        print(f"OK {path} {im.size[0]}x{im.size[1]} {im.format}")
