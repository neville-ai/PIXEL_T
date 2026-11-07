"""Render the six role-admin-revised diagrams to PNG (monochrome, minimal)."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _drawhelpers as H
from PIL import ImageDraw

OUT = HERE


def f(size, bold=False, italic=False):
    return H._font(size, bold=bold, italic=italic)


# ---------------------------------------------------------------------------
# ERD
# ---------------------------------------------------------------------------
def erd():
    W, Hh = 1040, 660
    img, d = H.new_img(W, Hh)

    H.box(d, 40, 40, 300, 170, "auth.users (Supabase Auth)", [
        "id : uuid (PK)",
        "email : text",
        "raw_user_meta_data : jsonb",
        "raw_app_meta_data : jsonb",
        "created_at : timestamptz",
    ], title_font=f(10, bold=True), line_font=f(9))

    H.box(d, 470, 40, 360, 350, "doctor_profiles", [
        "id : uuid (PK)",
        "user_id : uuid (FK, UNIQUE)",
        "full_name : text (NOT NULL)",
        "phone : text",
        "primary_specialty : text",
        "hospital : text",
        "department : text",
        "str_number : text",
        "is_verified : boolean",
        "role : text DEFAULT 'doctor'",
        "account_status : text DEFAULT 'pending'",
        "approved_by : uuid (FK)",
        "approved_at : timestamptz",
        "rejection_reason : text",
        "avatar_url : text",
        "created_at / updated_at : timestamptz",
    ], title_font=f(10, bold=True), line_font=f(9))

    H.box(d, 40, 430, 790, 200, "analyses", [
        "id : uuid (PK)",
        "user_id : uuid (FK, NOT NULL)",
        "status : varchar(20)  processing|completed|failed",
        "original_image_path : text (NOT NULL)",
        "segmentation_status : varchar(20)",
        "segmentation_overlay_path : text",
        "gradcam_overlay_path : text",
        "summary_text : text",
        "current_step : varchar(64)",
        "progress_percent : smallint",
        "created_at / completed_at / updated_at : timestamptz",
    ], title_font=f(10, bold=True), line_font=f(9))

    # relationship: doctor_profiles (0..1) --- (1) auth.users
    H.arrow(d, 470, 150, 340, 120, head="none")
    H.text(d, 352, 108, "0..1", font=f(10, bold=True))
    H.text(d, 452, 130, "1", font=f(10, bold=True))

    # relationship: analyses (*) --- (1) auth.users
    H.arrow(d, 230, 430, 230, 210, head="none")
    H.text(d, 240, 385, "*", font=f(11, bold=True))
    H.text(d, 240, 218, "1", font=f(10, bold=True))

    # annotation about Admin
    H.rect(d, 640, 430, 360, 150, dash=True)
    H.text(d, 650, 438, "Catatan Admin", font=f(9, bold=True))
    for i, ln in enumerate([
        "Admin TIDAK memiliki tabel tersendiri dan",
        "TIDAK memiliki baris doctor_profiles.",
        "Admin direpresentasikan oleh",
        "auth.users.raw_app_meta_data.role = 'admin'",
        "(hanya dapat ditulis server / service role).",
    ]):
        H.text(d, 650, 458 + i * 15, ln, font=f(8))

    H.text(d, 470, 610, "ERD PIXEL-T (Admin + Dokter) - monokrom", font=f(10, bold=True), center=False)
    H.save(img, os.path.join(OUT, "ERD_PIXELT_ROLE_ADMIN_REVISED.png"))


# ---------------------------------------------------------------------------
# Use Case
# ---------------------------------------------------------------------------
def use_case():
    W, Hh = 1120, 900
    img, d = H.new_img(W, Hh)

    # system boundary
    H.rect(d, 280, 120, 700, 750, lw=1.2)
    H.text(d, 292, 128, "Sistem PIXEL-T", font=f(11, bold=True))

    # actors
    H.actor(d, 90, 410, "Dokter")
    H.actor(d, 90, 600, "Calon Pengguna")
    H.actor(d, 1040, 330, "Admin")

    def uc(x, y, label, w=170, h=44):
        d.ellipse([x * H.SCALE, y * H.SCALE, (x + w) * H.SCALE, (y + h) * H.SCALE],
                  fill="white", outline="black", width=max(1, int(1.2 * H.SCALE)))
        lines = label.split("\n")
        yy = y + h / 2 - (len(lines) * 11) / 2
        for ln in lines:
            H.text(d, x + w / 2, yy, ln, font=f(9), center=True)
            yy += 11

    # shared (center top)
    uc(500, 150, "Sign Up")
    uc(500, 220, "Sign In")
    uc(500, 290, "Sign Out")

    # doctor (left stack)
    uc(340, 400, "Reset Password")
    uc(340, 470, "Upload Image")
    uc(340, 540, "Segmentation")
    uc(340, 610, "View History")
    uc(340, 680, "Search History")
    uc(340, 750, "View Doctor\nProfile")
    uc(340, 820, "Edit Doctor\nProfile")

    # admin (right stack)
    uc(800, 220, "Dashboard Admin")
    uc(800, 300, "Daftar Dokter")
    uc(800, 380, "Setujui Akun\nDokter")
    uc(800, 460, "Tolak Akun\nDokter")

    # associations
    H.arrow(d, 112, 400, 500, 172, head="none")            # Dokter - Sign Up? no; remove below
    # doctor to shared
    H.arrow(d, 112, 395, 500, 242, head="none")            # Dokter - Sign In
    H.arrow(d, 112, 420, 500, 312, head="none")            # Dokter - Sign Out
    # doctor to left stack
    for y in [422, 492, 562, 632, 702, 772, 842]:
        H.arrow(d, 112, 440, 340, y, head="none")
    # calon to signup
    H.arrow(d, 112, 610, 500, 172, head="none")
    # admin to shared
    H.arrow(d, 1018, 330, 670, 242, head="none")           # Admin - Sign In
    H.arrow(d, 1018, 345, 670, 312, head="none")           # Admin - Sign Out
    # admin stack
    for y in [242, 322, 402, 482]:
        H.arrow(d, 1018, 330, 970, y, head="none")

    # boundaries of the left stack are 340..510; lines from actor reach x=340 fine.
    # <<extend>> Reset Password -> Sign In
    H.arrow(d, 500, 422, 560, 264, dashed=True, head="open")
    H.text(d, 520, 330, "<<extend>>", font=f(8))
    # <<include>> Segmentation -> Upload Image
    H.arrow(d, 425, 540, 425, 514, dashed=True, head="open")
    H.text(d, 432, 520, "<<include>>", font=f(8))
    # <<extend>> Search History -> View History
    H.arrow(d, 425, 680, 425, 654, dashed=True, head="open")
    H.text(d, 432, 660, "<<extend>>", font=f(8))
    # <<extend>> Edit -> View Doctor Profile
    H.arrow(d, 425, 820, 425, 794, dashed=True, head="open")
    H.text(d, 432, 800, "<<extend>>", font=f(8))

    H.text(d, 300, 40, "Use Case Diagram PIXEL-T - Admin + Dokter", font=f(11, bold=True))
    H.save(img, os.path.join(OUT, "USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.png"))


# ---------------------------------------------------------------------------
# Activity helpers
# ---------------------------------------------------------------------------
def act_node(d, x, y, w, h, label, font_size=9):
    H.rect(d, x, y, w, h, lw=1.2)
    lines = label.split("\n")
    yy = y + h / 2 - (len(lines) * 11) / 2
    for ln in lines:
        H.text(d, x + w / 2, yy, ln, font=f(font_size), center=True)
        yy += 11


def diamond(d, x, y, w, h, label):
    cx, cy = x + w / 2, y + h / 2
    d.polygon([(cx * H.SCALE, y * H.SCALE),
               ((x + w) * H.SCALE, cy * H.SCALE),
               (cx * H.SCALE, (y + h) * H.SCALE),
               (x * H.SCALE, cy * H.SCALE)],
              fill="white", outline="black")
    lines = label.split("\n")
    yy = cy - (len(lines) * 10) / 2
    for ln in lines:
        H.text(d, cx, yy, ln, font=f(8), center=True)
        yy += 10


def start(d, cx, cy, r=14):
    d.ellipse([(cx - r) * H.SCALE, (cy - r) * H.SCALE, (cx + r) * H.SCALE, (cy + r) * H.SCALE],
              fill="black", outline="black")


def end(d, cx, cy, r=16):
    d.ellipse([(cx - r) * H.SCALE, (cy - r) * H.SCALE, (cx + r) * H.SCALE, (cy + r) * H.SCALE],
              outline="black", width=max(1, int(1.5 * H.SCALE)))
    d.ellipse([(cx - r / 2) * H.SCALE, (cy - r / 2) * H.SCALE,
               (cx + r / 2) * H.SCALE, (cy + r / 2) * H.SCALE],
              fill="black", outline="black")


# ---------------------------------------------------------------------------
# Activity Sign Up
# ---------------------------------------------------------------------------
def act_signup():
    W, Hh = 820, 1040
    img, d = H.new_img(W, Hh)
    cx = 300

    start(d, cx, 42)
    act_node(d, cx - 130, 78, 260, 42, "Membuka halaman /register")
    act_node(d, cx - 130, 148, 260, 42, "Mengisi formulir pendaftaran")
    act_node(d, cx - 130, 218, 260, 42, "Memvalidasi input\n(wajib, email, sandi >= 6)")
    diamond(d, cx - 80, 288, 160, 70, "Input valid?")

    act_node(d, cx - 130, 388, 260, 48, "Memanggil signUp()\n-> Supabase Auth signUp")
    act_node(d, cx - 130, 464, 260, 42, "Supabase membuat auth.users")
    act_node(d, cx - 150, 534, 300, 60,
             "Trigger handle_new_doctor_signup:\nINSERT doctor_profiles\n(role='doctor', account_status='pending')")
    diamond(d, cx - 90, 622, 180, 68, "Sesi dikembalikan?")

    act_node(d, cx - 140, 718, 280, 48, "Menyimpan sesi;\nrole=doctor, account_status=pending")
    act_node(d, cx + 180, 718, 210, 48, "Menampilkan instruksi\nkonfirmasi email", font_size=8)
    act_node(d, cx - 150, 796, 300, 42, "Menampilkan pesan pendaftaran berhasil\n(menunggu persetujuan)")
    act_node(d, cx - 130, 866, 260, 42, "Mengarahkan pengguna ke /login")
    end(d, cx, 968)

    # arrows
    H.arrow(d, cx, 56, cx, 78, head="fill")
    H.arrow(d, cx, 120, cx, 148, head="fill")
    H.arrow(d, cx, 190, cx, 218, head="fill")
    H.arrow(d, cx, 260, cx, 288, head="fill")
    # yes
    H.arrow(d, cx, 358, cx, 388, head="fill")
    H.text(d, cx + 8, 362, "Ya", font=f(8, bold=True))
    # no -> error -> back up
    H.arrow(d, cx + 80, 323, 560, 323, head="fill")
    H.text(d, 640, 300, "Tidak", font=f(8, bold=True))
    act_node(d, 560, 286, 180, 38, "Menampilkan pesan\nkesalahan", font_size=8)
    H.arrow(d, 740, 305, 760, 305, head="none")
    H.arrow(d, 760, 305, 760, 169, head="none")
    H.arrow(d, 760, 169, cx + 130, 169, head="fill")

    H.arrow(d, cx, 436, cx, 464, head="fill")
    H.arrow(d, cx, 506, cx, 534, head="fill")
    H.arrow(d, cx, 594, cx, 622, head="fill")
    # session yes / no
    H.arrow(d, cx, 690, cx, 718, head="fill")
    H.text(d, cx + 8, 694, "Ya", font=f(8, bold=True))
    H.arrow(d, cx + 90, 656, 690, 656, head="fill")
    H.text(d, 620, 634, "Tidak", font=f(8, bold=True))
    H.arrow(d, 690, 656, 690, 742, head="none")
    H.arrow(d, 690, 742, cx + 140, 742, head="fill")
    H.arrow(d, cx, 766, cx, 796, head="fill")
    H.arrow(d, cx, 838, cx, 866, head="fill")
    H.arrow(d, cx, 908, cx, 952, head="fill")

    # note about admin provisioning
    H.rect(d, 540, 80, 250, 150, dash=True)
    H.text(d, 550, 88, "Catatan", font=f(9, bold=True))
    for i, ln in enumerate([
        "Pendaftaran publik hanya untuk Dokter.",
        "Admin tidak mendaftar di sini.",
        "Admin dibuat via Supabase Admin API",
        "dengan app_metadata.role='admin'.",
        "Admin tidak memiliki baris",
        "doctor_profiles.",
    ]):
        H.text(d, 550, 108 + i * 15, ln, font=f(8))

    H.text(d, 300, 12, "Activity Diagram Sign Up - PIXEL-T", font=f(11, bold=True))
    H.save(img, os.path.join(OUT, "ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.png"))


# ---------------------------------------------------------------------------
# Activity Sign In
# ---------------------------------------------------------------------------
def act_signin():
    W, Hh = 900, 1200
    img, d = H.new_img(W, Hh)
    cx = 300

    start(d, cx, 42)
    act_node(d, cx - 150, 78, 300, 42, "Membuka halaman /login")
    act_node(d, cx - 150, 148, 300, 48, "Mengisi email, kata sandi,\nmemilih jenis akun")
    diamond(d, cx - 90, 224, 180, 66, "Input valid?")
    act_node(d, cx + 190, 224, 190, 40, "Menampilkan pesan\nkesalahan", font_size=8)

    act_node(d, cx - 170, 316, 340, 48, "Memanggil signIn()\n-> supabase.auth.signInWithPassword")
    diamond(d, cx - 100, 392, 200, 66, "Kredensial valid?")
    act_node(d, cx + 190, 392, 190, 40, "Menampilkan pesan\ngagal masuk", font_size=8)

    act_node(d, cx - 140, 486, 280, 42, "Menyimpan sesi (AuthContext)")
    act_node(d, cx - 150, 556, 300, 56, "Membaca app_metadata.role\n(hanya server yang dapat menulis)")
    diamond(d, cx - 80, 640, 160, 64, "role = 'admin'?")
    act_node(d, cx + 170, 640, 200, 48, "set role='admin'\naccount_status=null", font_size=8)

    act_node(d, cx - 170, 742, 340, 56, "Membaca doctor_profiles\n(role, account_status)")
    diamond(d, cx - 100, 826, 200, 66, "Jenis akun dipilih\nsesuai role?")
    act_node(d, cx + 190, 826, 190, 48, "Menampilkan pesan\njenis akun tidak sesuai", font_size=8)
    diamond(d, cx - 80, 922, 160, 64, "role = 'admin'?")

    act_node(d, cx - 140, 1022, 280, 44, "Mengarahkan ke /dashboard")
    act_node(d, cx + 170, 1000, 200, 44, "account_status?", font_size=8)
    act_node(d, cx + 170, 1070, 200, 40, "Ke /login (pending)", font_size=8)
    act_node(d, 660, 1000, 190, 40, "Mengarahkan ke /admin", font_size=8)
    act_node(d, 660, 1070, 190, 40, "Ke /login (rejected)", font_size=8)
    end(d, cx, 1120)

    # arrows
    H.arrow(d, cx, 56, cx, 78, head="fill")
    H.arrow(d, cx, 120, cx, 148, head="fill")
    H.arrow(d, cx, 196, cx, 224, head="fill")
    H.arrow(d, cx + 90, 257, 490, 246, head="fill")
    H.text(d, cx + 100, 232, "Tidak", font=f(8, bold=True))
    H.text(d, cx + 12, 262, "Ya", font=f(8, bold=True))
    H.arrow(d, cx, 290, cx, 316, head="fill")
    H.arrow(d, cx, 364, cx, 392, head="fill")
    H.arrow(d, cx + 100, 425, 490, 412, head="fill")
    H.text(d, cx + 110, 400, "Tidak", font=f(8, bold=True))
    H.text(d, cx + 12, 430, "Ya", font=f(8, bold=True))
    H.arrow(d, cx, 458, cx, 486, head="fill")
    H.arrow(d, cx, 528, cx, 556, head="fill")
    H.arrow(d, cx, 612, cx, 640, head="fill")
    H.arrow(d, cx + 80, 672, 470, 664, head="fill")
    H.text(d, cx + 92, 654, "Ya", font=f(8, bold=True))
    H.text(d, cx + 12, 690, "Tidak", font=f(8, bold=True))
    H.arrow(d, cx, 704, cx, 742, head="fill")
    H.arrow(d, cx, 798, cx, 826, head="fill")
    H.arrow(d, cx + 100, 859, 490, 850, head="fill")
    H.text(d, cx + 112, 838, "Tidak", font=f(8, bold=True))
    H.text(d, cx + 12, 866, "Ya", font=f(8, bold=True))
    H.arrow(d, cx, 892, cx, 922, head="fill")
    H.arrow(d, cx + 80, 954, 660, 1022, head="fill")
    H.text(d, cx + 100, 966, "Ya", font=f(8, bold=True))
    H.text(d, cx + 12, 972, "Tidak", font=f(8, bold=True))
    H.arrow(d, cx, 986, cx, 1022, head="fill")
    # branch labels
    H.arrow(d, cx + 140, 1044, 470, 1022, head="fill")
    H.text(d, 480, 1004, "approved", font=f(8, bold=True))
    H.arrow(d, cx + 140, 1044, 470, 1090, head="fill")
    H.text(d, 480, 1072, "pending / rejected", font=f(8, bold=True))
    H.arrow(d, cx, 1066, cx, 1104, head="fill")
    H.text(d, cx + 6, 1078, "approved", font=f(8, bold=True))

    H.text(d, 300, 12, "Activity Diagram Sign In - PIXEL-T", font=f(11, bold=True))
    H.save(img, os.path.join(OUT, "ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.png"))


# ---------------------------------------------------------------------------
# Sequence helpers
# ---------------------------------------------------------------------------
def lifelines(d, names, xs, top=40, bottom=880, head_h=42):
    for name, x in zip(names, xs):
        H.rect(d, x - 70, top, 140, head_h, lw=1.2)
        lines = name.split("\n")
        yy = top + head_h / 2 - (len(lines) * 10) / 2
        for ln in lines:
            H.text(d, x, yy, ln, font=f(8, bold=True), center=True)
            yy += 10
        d.line([(x * H.SCALE, (top + head_h) * H.SCALE), (x * H.SCALE, bottom * H.SCALE)],
               fill="black", width=max(1, int(1.0 * H.SCALE)))
    return {name: x for name, x in zip(names, xs)}


def msg(d, x1, x2, y, label, dashed=False, font_size=8):
    H.arrow(d, x1, y, x2, y, dashed=dashed, head="fill")
    mid = (x1 + x2) / 2
    H.text(d, mid, y - 12, label, font=f(font_size), center=True)


def self_msg(d, x, y, label, w=120, h=26):
    d.line([(x * H.SCALE, y * H.SCALE), ((x + w) * H.SCALE, y * H.SCALE)], fill="black")
    d.line([((x + w) * H.SCALE, y * H.SCALE), ((x + w) * H.SCALE, (y + h) * H.SCALE)], fill="black")
    H.arrow(d, x + w, y + h, x, y + h, head="fill")
    H.text(d, x + 6, y - 12, label, font=f(7))


# ---------------------------------------------------------------------------
# Sequence Sign Up
# ---------------------------------------------------------------------------
def seq_signup():
    W, Hh = 1260, 920
    img, d = H.new_img(W, Hh)
    names = ["Pengguna", "Register Page\n(Register.tsx)", "AuthContext\n(signUp)", "AuthService\n(registerUser)", "Supabase Auth", "DB Trigger\n(doctor_profiles)"]
    xs = [70, 290, 510, 730, 950, 1170]
    pos = lifelines(d, names, xs, top=30, bottom=880)

    y = 120
    msg(d, pos["Pengguna"], pos["Register Page\n(Register.tsx)"], y, "1: buka /register")
    y += 42
    msg(d, pos["Register Page\n(Register.tsx)"], pos["Pengguna"], y, "2: tampilkan formulir", dashed=True)
    y += 42
    msg(d, pos["Pengguna"], pos["Register Page\n(Register.tsx)"], y, "3: submit data pendaftaran")
    y += 42
    self_msg(d, pos["Register Page\n(Register.tsx)"], y, "4: validasi input")
    y += 50
    msg(d, pos["Register Page\n(Register.tsx)"], pos["AuthContext\n(signUp)"], y,
        "5: signUp(email, password, fullName, hospital, specialty)")
    y += 42
    msg(d, pos["AuthContext\n(signUp)"], pos["AuthService\n(registerUser)"], y, "6: registerUser(...)")
    y += 42
    msg(d, pos["AuthService\n(registerUser)"], pos["Supabase Auth"], y,
        "7: auth.signUp({ email, password, options.data })")
    y += 42
    self_msg(d, pos["Supabase Auth"], y, "8: buat auth.users", w=110)
    y += 50
    msg(d, pos["Supabase Auth"], pos["DB Trigger\n(doctor_profiles)"], y, "9: AFTER INSERT auth.users")
    y += 42
    self_msg(d, pos["DB Trigger\n(doctor_profiles)"], y,
             "10: INSERT doctor_profiles\n(role='doctor', status='pending')", w=150, h=34)
    y += 62
    msg(d, pos["Supabase Auth"], pos["AuthService\n(registerUser)"], y, "11: { user, session }", dashed=True)
    y += 42
    msg(d, pos["AuthService\n(registerUser)"], pos["AuthContext\n(signUp)"], y, "12: AuthResponse", dashed=True)
    y += 42
    self_msg(d, pos["AuthContext\n(signUp)"], y, "13: set session (jika ada)\nrole=doctor, status=pending", w=150, h=34)
    y += 62
    msg(d, pos["AuthContext\n(signUp)"], pos["Register Page\n(Register.tsx)"], y, "14: hasil", dashed=True)
    y += 42
    msg(d, pos["Register Page\n(Register.tsx)"], pos["Pengguna"], y,
        "15: pesan berhasil + menunggu persetujuan", dashed=True)

    # note
    H.rect(d, 40, 700, 330, 130, dash=True)
    H.text(d, 50, 708, "Catatan", font=f(9, bold=True))
    for i, ln in enumerate([
        "Jika session null -> requiresEmailConfirmation",
        "= true (pengguna harus konfirmasi email).",
        "Tidak ada pemanggilan Flask API pada Sign Up.",
        "Akun Admin tidak dibuat melalui alur ini.",
    ]):
        H.text(d, 50, 728 + i * 15, ln, font=f(8))

    H.text(d, 430, 10, "Sequence Diagram Sign Up - PIXEL-T", font=f(11, bold=True))
    H.save(img, os.path.join(OUT, "SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.png"))


# ---------------------------------------------------------------------------
# Sequence Sign In
# ---------------------------------------------------------------------------
def seq_signin():
    W, Hh = 1400, 1080
    img, d = H.new_img(W, Hh)
    names = ["Pengguna", "Login Page\n(Login.tsx)", "AuthContext\n(signIn)", "AuthService\n(loginUser)",
             "Supabase Auth", "doctor_profiles\n(Supabase DB)", "Route Guard"]
    xs = [70, 280, 500, 720, 940, 1150, 1320]
    pos = lifelines(d, names, xs, top=30, bottom=1000)

    y = 120
    msg(d, pos["Pengguna"], pos["Login Page\n(Login.tsx)"], y, "1: buka /login")
    y += 42
    msg(d, pos["Login Page\n(Login.tsx)"], pos["Pengguna"], y, "2: tampilkan formulir", dashed=True)
    y += 42
    msg(d, pos["Pengguna"], pos["Login Page\n(Login.tsx)"], y,
        "3: submit email, password, selectedRole")
    y += 42
    msg(d, pos["Login Page\n(Login.tsx)"], pos["AuthContext\n(signIn)"], y, "4: signIn(...)")
    y += 42
    msg(d, pos["AuthContext\n(signIn)"], pos["AuthService\n(loginUser)"], y, "5: loginUser(...)")
    y += 42
    msg(d, pos["AuthService\n(loginUser)"], pos["Supabase Auth"], y, "6: signInWithPassword")
    y += 42
    msg(d, pos["Supabase Auth"], pos["AuthService\n(loginUser)"], y, "7: { user, session }", dashed=True)
    y += 42
    msg(d, pos["AuthService\n(loginUser)"], pos["AuthContext\n(signIn)"], y, "8: AuthResponse", dashed=True)
    y += 42
    self_msg(d, pos["AuthContext\n(signIn)"], y, "9: getAdminRoleFromAppMetadata(user)", w=150)
    y += 50

    # alt fragment
    alt_top = y - 8
    msg(d, pos["AuthContext\n(signIn)"], pos["AuthContext\n(signIn)"], y, "[alt app_metadata.role = 'admin']", dashed=False)
    # draw the actual alt label box instead of a self message
    d.rectangle([480 * H.SCALE, alt_top * H.SCALE, 1180 * H.SCALE, (alt_top + 12) * H.SCALE],
                fill="white", outline="black")
    H.text(d, 486, alt_top + 2, "[alt] app_metadata.role = 'admin'", font=f(8, bold=True))
    y += 34
    self_msg(d, pos["AuthContext\n(signIn)"], y, "set role='admin', account_status=null", w=140)
    y += 46
    H.text(d, 486, y - 2, "[else] role dari doctor_profiles", font=f(8, bold=True))
    y += 24
    msg(d, pos["AuthContext\n(signIn)"], pos["doctor_profiles\n(Supabase DB)"], y,
        "fetchUserProfileStatus(user)")
    y += 42
    msg(d, pos["doctor_profiles\n(Supabase DB)"], pos["AuthContext\n(signIn)"], y,
        "{ role, account_status }", dashed=True)
    y += 42
    self_msg(d, pos["AuthContext\n(signIn)"], y, "validasi kecocokan selectedRole", w=140)
    y += 48
    msg(d, pos["AuthContext\n(signIn)"], pos["Login Page\n(Login.tsx)"], y, "10: { error? }", dashed=True)
    y += 42
    msg(d, pos["Login Page\n(Login.tsx)"], pos["Route Guard"], y,
        "11: navigasi (PublicOnly / Protected / Admin)")
    y += 42
    msg(d, pos["Route Guard"], pos["Pengguna"], y,
        "12: /admin | /dashboard | /login(pending/rejected)", dashed=True)

    # note
    H.rect(d, 40, 930, 360, 110, dash=True)
    H.text(d, 50, 938, "Catatan", font=f(9, bold=True))
    for i, ln in enumerate([
        "Login hanya memakai Supabase Auth; tidak ada",
        "endpoint Flask pada proses ini.",
        "Role Admin: app_metadata.role (server-write-only).",
        "Status Dokter: doctor_profiles.account_status.",
    ]):
        H.text(d, 50, 958 + i * 15, ln, font=f(8))

    H.text(d, 470, 10, "Sequence Diagram Sign In - PIXEL-T", font=f(11, bold=True))
    H.save(img, os.path.join(OUT, "SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.png"))


if __name__ == "__main__":
    erd()
    use_case()
    act_signup()
    act_signin()
    seq_signup()
    seq_signin()
    print("PNG DONE")
