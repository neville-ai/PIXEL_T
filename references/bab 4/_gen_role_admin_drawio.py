"""Generate the six _ROLE_ADMIN_REVISED .drawio sources for PIXEL-T."""
from __future__ import annotations

OUT = r"C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mxfile(diagram_id: str, diagram_name: str, pw: str, ph: str, body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" agent="OpenCode" version="24.0.0" type="device">\n'
        f'  <diagram name="{diagram_name}" id="{diagram_id}">\n'
        "    <mxGraphModel dx=\"1200\" dy=\"900\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\""
        + pw + "\" pageHeight=\"" + ph + "\" math=\"0\" shadow=\"0\">\n"
        "      <root>\n"
        "        <mxCell id=\"0\"/>\n"
        "        <mxCell id=\"1\" parent=\"0\"/>\n"
        + body +
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )


def cell(cid: str, value: str, x: float, y: float, w: float, h: float,
         style: str) -> str:
    return (
        f'        <mxCell id="{cid}" value="{esc(value)}" style="{style}" vertex="1" parent="1">\n'
        f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>\n'
        "        </mxCell>\n"
    )


def edge(cid: str, style: str, src: str, tgt: str, pts) -> str:
    arr = "".join(f"<mxPoint x=\"{x}\" y=\"{y}\"/>" for x, y in pts)
    return (
        f'        <mxCell id="{cid}" style="{style}" edge="1" parent="1" source="{src}" target="{tgt}">\n'
        '          <mxGeometry relative="1" as="geometry"><Array as="points">' + arr + "</Array></mxGeometry>\n"
        "        </mxCell>\n"
    )


ACT_RECT = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;arcSize=20;"
DEC_RHOMBUS = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;"
ELLIPSE = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;"
DBLE = "ellipse;shape=doubleEllipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;"
ACT_ARROW = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;endFill=0;strokeColor=#000000;fontColor=#000000;fontSize=9;"
DASH_ARROW = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=open;endFill=0;strokeColor=#000000;fontColor=#000000;fontSize=9;"
ACTOR = ("shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
         "fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=11;")
USECASE = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=11;"
BND = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=11;"

def write(path: str, content: str):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

# =========================== ERD
body = ""
body += cell("users", "users (auth.users)<br>id : uuid (PK)<br>email : text<br>raw_user_meta_data : jsonb<br>raw_app_meta_data : jsonb<br>created_at : timestamptz", 40, 40, 300, 150,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;align=left;verticalAlign=top;spacingLeft=6;")
body += cell("dp", "doctor_profiles<br>id : uuid (PK)<br>user_id : uuid (FK, UNIQUE)<br>full_name : text<br>phone : text<br>primary_specialty : text<br>hospital : text<br>department : text<br>str_number : text<br>is_verified : boolean<br>role : text DEFAULT 'doctor'<br>account_status : text DEFAULT 'pending'<br>approved_by : uuid (FK)<br>approved_at : timestamptz<br>rejection_reason : text<br>avatar_url : text<br>created_at / updated_at : timestamptz", 470, 40, 360, 340,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;align=left;verticalAlign=top;spacingLeft=6;")
body += cell("an", "analyses<br>id : uuid (PK)<br>user_id : uuid (FK, NOT NULL)<br>status : varchar(20)<br>original_image_path : text<br>segmentation_status : varchar(20)<br>segmentation_overlay_path : text<br>gradcam_overlay_path : text<br>summary_text : text<br>current_step : varchar(64)<br>progress_percent : smallint<br>created_at / completed_at / updated_at : timestamptz", 40, 430, 790, 200,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;align=left;verticalAlign=top;spacingLeft=6;")
body += edge("e1", "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#000000;",
             "dp", "users", [(470, 160), (340, 110)])
body += edge("e2", "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#000000;",
             "an", "users", [(230, 430), (230, 200)])
body += cell("m1", "1", 478, 148, 30, 14, "text;html=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;")
body += cell("m2", "0..1", 292, 96, 40, 14, "text;html=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;")
body += cell("m3", "*", 218, 420, 30, 14, "text;html=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;")
body += cell("m4", "1", 248, 192, 30, 14, "text;html=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;")
body += cell("note", "Catatan Admin: tanpa tabel admins; admin = auth.users.raw_app_meta_data.role = ''admin'' (server-write-only), tanpa baris doctor_profiles.",
             640, 430, 360, 130,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontColor=#000000;fontSize=9;align=left;verticalAlign=top;spacingLeft=6;")
write(OUT + r"\ERD_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("erd-admin-rev", "ERD PIXEL-T Admin Doctor Revised", "1040", "660", body))

# =========================== USE CASE
body = ""
body += cell("bnd", "Sistem PIXEL-T", 280, 120, 700, 750, BND)
body += cell("acD", "Dokter", 90, 410, 80, 110, ACTOR)
body += cell("acC", "Calon Pengguna", 90, 600, 80, 110, ACTOR)
body += cell("acA", "Admin", 1040, 330, 80, 110, ACTOR)
ucs = [
    ("uc1", 500, 150, 170, 44, "Sign Up"),
    ("uc2", 500, 220, 170, 44, "Sign In"),
    ("uc3", 500, 290, 170, 44, "Sign Out"),
    ("uc4", 340, 400, 170, 44, "Reset Password"),
    ("uc5", 340, 470, 170, 44, "Upload Image"),
    ("uc6", 340, 540, 170, 44, "Segmentation"),
    ("uc7", 340, 610, 170, 44, "View History"),
    ("uc8", 340, 680, 170, 44, "Search History"),
    ("uc9", 340, 750, 170, 44, "View Doctor Profile"),
    ("uc10", 340, 820, 170, 44, "Edit Doctor Profile"),
    ("uc11", 800, 220, 170, 44, "Dashboard Admin"),
    ("uc12", 800, 300, 170, 44, "Daftar Dokter"),
    ("uc13", 800, 380, 170, 44, "Setujui Akun Dokter"),
    ("uc14", 800, 460, 170, 44, "Tolak Akun Dokter"),
]
for cid, x, y, wid, hei, label in ucs:
    body += cell(cid, label, x, y, wid, hei, USECASE)
assoc = [
    ("a1", "acD", "uc2", [(112, 395), (500, 242)]),
    ("a2", "acD", "uc3", [(112, 420), (500, 312)]),
    ("a3", "acC", "uc1", [(112, 610), (500, 172)]),
    ("a4", "acA", "uc2", [(1040, 330), (670, 242)]),
    ("a5", "acA", "uc3", [(1040, 345), (670, 312)]),
]
for cid, src, tgt, pts in assoc:
    body += edge(cid, ACT_ARROW, src, tgt, pts)
rels = [
    ("r1", "uc4", "uc2", [(500, 422), (560, 264)], "<<extend>>"),
    ("r2", "uc6", "uc5", [(425, 540), (425, 514)], "<<include>>"),
    ("r3", "uc8", "uc7", [(425, 680), (425, 654)], "<<extend>>"),
    ("r4", "uc10", "uc9", [(425, 820), (425, 794)], "<<extend>>"),
]
for cid, src, tgt, pts, lbl in rels:
    body += edge(cid, DASH_ARROW, src, tgt, pts)
write(OUT + r"\USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("uc-admin-rev", "Use Case PIXEL-T Admin Doctor Revised", "1120", "900", body))

# =========================== ACTIVITY SIGN UP
body = ""
body += cell("st", "Start", 170, 42, 60, 32, ELLIPSE)
body += cell("en", "End", 170, 968, 60, 32, DBLE)
body += cell("a1", "Membuka halaman /register", 170, 78, 260, 42, ACT_RECT)
body += cell("a2", "Mengisi formulir pendaftaran", 170, 148, 260, 42, ACT_RECT)
body += cell("a3", "Memvalidasi input (wajib, email, sandi >= 6)", 170, 218, 260, 42, ACT_RECT)
body += cell("d1", "Input valid?", 220, 288, 160, 70, DEC_RHOMBUS)
body += cell("a4", "Memanggil signUp() -> Supabase Auth signUp", 170, 388, 260, 48, ACT_RECT)
body += cell("a5", "Supabase membuat auth.users", 170, 464, 260, 42, ACT_RECT)
body += cell("a6", "Trigger handle_new_doctor_signup: INSERT doctor_profiles (role=doctor, status=pending)", 150, 534, 300, 60, ACT_RECT)
body += cell("d2", "Sesi dikembalikan?", 210, 622, 180, 68, DEC_RHOMBUS)
body += cell("a7", "Menyimpan sesi; role=doctor, account_status=pending", 160, 718, 280, 48, ACT_RECT)
body += cell("a8", "Menampilkan instruksi konfirmasi email", 480, 718, 200, 48, ACT_RECT)
body += cell("a9", "Menampilkan pesan pendaftaran berhasil (menunggu persetujuan)", 150, 796, 300, 42, ACT_RECT)
body += cell("a10", "Mengarahkan pengguna ke /login", 170, 866, 260, 42, ACT_RECT)
body += cell("aerr", "Menampilkan pesan kesalahan", 560, 286, 180, 38, ACT_RECT)
edges_su = [
    ("e1", "st", "a1", [(200, 74), (200, 99)]),
    ("e2", "a1", "a2", [(300, 119), (300, 149)]),
    ("e3", "a2", "a3", [(300, 169), (300, 199)]),
    ("e4", "a3", "d1", [(300, 239), (300, 296)]),
    ("e5", "d1", "a4", [(300, 356), (300, 382)]),
    ("e6", "a4", "a5", [(300, 414), (300, 441)]),
    ("e7", "a5", "a6", [(300, 486), (300, 531)]),
    ("e8", "a6", "d2", [(300, 594), (300, 618)]),
    ("e9", "d2", "a7", [(300, 688), (300, 742)]),
    ("e10", "a7", "a9", [(300, 766), (300, 795)]),
    ("e11", "a9", "a10", [(300, 838), (300, 867)]),
    ("e12", "a10", "en", [(300, 898), (300, 950)]),
    ("e13", "d1", "aerr", [(390, 323), (540, 323)]),
    ("e14", "aerr", "a2", [(650, 305), (650, 169)]),
]
for cid, src, tgt, pts in edges_su:
    body += edge(cid, ACT_ARROW, src, tgt, pts)
body += cell("note", "Pendaftaran publik hanya untuk Dokter. Admin dibuat via Supabase Admin API (app_metadata.role=admin) dan tidak memiliki baris doctor_profiles.",
             540, 80, 250, 130,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontColor=#000000;fontSize=9;align=left;verticalAlign=top;spacingLeft=6;")
write(OUT + r"\ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("act-signup-admin", "Activity Diagram Sign Up PIXEL-T Admin Doctor Revised", "820", "1040", body))

# =========================== ACTIVITY SIGN IN
body = ""
body += cell("st", "Start", 170, 42, 60, 32, ELLIPSE)
body += cell("en", "End", 170, 1120, 60, 32, DBLE)
body += cell("a1", "Membuka halaman /login", 170, 78, 300, 42, ACT_RECT)
body += cell("a2", "Mengisi email, kata sandi, memilih jenis akun", 170, 148, 300, 48, ACT_RECT)
body += cell("d1", "Input valid?", 220, 224, 180, 66, DEC_RHOMBUS)
body += cell("a3", "Memanggil signIn() -> supabase.auth.signInWithPassword", 170, 316, 340, 48, ACT_RECT)
body += cell("d2", "Kredensial valid?", 220, 392, 200, 66, DEC_RHOMBUS)
body += cell("a4", "Menyimpan sesi (AuthContext)", 170, 486, 280, 42, ACT_RECT)
body += cell("a5", "Membaca app_metadata.role (hanya server yang dapat menulis)", 170, 556, 300, 56, ACT_RECT)
body += cell("d3", "role = admin?", 220, 640, 160, 64, DEC_RHOMBUS)
body += cell("a6", "Membaca doctor_profiles (role, account_status)", 170, 742, 340, 56, ACT_RECT)
body += cell("d4", "Jenis akun dipilih sesuai role?", 220, 826, 200, 66, DEC_RHOMBUS)
body += cell("d5", "role = admin?", 220, 922, 160, 64, DEC_RHOMBUS)
body += cell("a7", "Mengarahkan ke /dashboard", 170, 1022, 280, 44, ACT_RECT)
body += cell("a8", "Mengarahkan ke /admin", 480, 922, 200, 44, ACT_RECT)
body += cell("a9", "Kembali ke /login (pending)", 480, 1000, 200, 40, ACT_RECT)
body += cell("a10", "Kembali ke /login (rejected)", 720, 1000, 200, 40, ACT_RECT)
body += cell("aerr", "Menampilkan pesan jenis akun tidak sesuai", 480, 826, 200, 48, ACT_RECT)
edges_si = [
    ("e1", "st", "a1", [(200, 74), (200, 99)]),
    ("e2", "a1", "a2", [(320, 119), (320, 172)]),
    ("e3", "a2", "d1", [(320, 194), (320, 257)]),
    ("e4", "d1", "a3", [(320, 290), (320, 340)]),
    ("e5", "a3", "d2", [(340, 362), (340, 425)]),
    ("e6", "d2", "a4", [(320, 458), (320, 505)]),
    ("e7", "a4", "a5", [(310, 527), (310, 587)]),
    ("e8", "a5", "d3", [(300, 612), (300, 636)]),
    ("e9", "d3", "d5", [(280, 672), (280, 890)]),
    ("e10", "a5", "d4", [(340, 613), (340, 838)]),
    ("e11", "d4", "aerr", [(420, 859), (460, 859)]),
    ("e12", "d4", "d5", [(320, 892), (320, 918)]),
    ("e13", "d5", "a7", [(300, 986), (300, 1018)]),
    ("e14", "d5", "a8", [(380, 954), (460, 944)]),
    ("e15", "d5", "a9", [(360, 970), (460, 1020)]),
    ("e16", "d5", "a10", [(380, 970), (700, 1020)]),
]
for cid, src, tgt, pts in edges_si:
    body += edge(cid, ACT_ARROW, src, tgt, pts)
write(OUT + r"\ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("act-signin-admin", "Activity Diagram Sign In PIXEL-T Admin Doctor Revised", "960", "1200", body))

# =========================== SEQUENCE HELPERS
LIFELINE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;"
            "recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=10;")
MSG = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=open;endFill=0;strokeColor=#000000;fontColor=#000000;fontSize=9;"
MSG_RET = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;endArrow=open;endFill=0;strokeColor=#000000;fontColor=#000000;fontSize=9;"
SELF = "edgeStyle=none;rounded=0;html=1;endArrow=open;endFill=0;strokeColor=#000000;fontColor=#000000;fontSize=9;"

def lifelines(names, xs, top=30, bottom=880, head_h=42):
    """Return dict name -> center x. Draw lifeline head + vertical line cells."""
    cells = []
    for name, x in zip(names, xs):
        cid = name.replace(" ", "_").replace("\n", "_").replace("/", "_")
        cells.append(cell(cid, name, x - 70, top, 140, head_h, LIFELINE))
        cells.append(cell(cid + "_line", "", x, top + head_h, 1, bottom - top - head_h,
                          "shape=line;verticalLabelPosition=middle;html=1;verticalAlign=top;"
                          "endArrow=none;startArrow=none;strokeColor=#000000;fontColor=#000000;fontSize=9;"))
    return "".join(cells), {name: name.replace(" ", "_").replace("\n", "_").replace("/", "_") for name, x in zip(names, xs)}


def msg(cid, src, tgt, y, label, dashed=False):
    return (edge(cid, MSG_RET if dashed else MSG, src, tgt, [(0, y), (0, y)]))


def msgl(cid, src, tgt, x1, x2, y, label, dashed=False):
    """Message edge with label; x1/x2 lifeline centers."""
    return edge(cid, MSG_RET if dashed else MSG, src, tgt, [(x1, y), (x2, y)])


def selfmsg(cid, src, x, y, label, w=120, h=26):
    """Simple self message using two line cells (avoid source==target)."""
    return (cell(cid + "_h", label, x + 4, y - 14, w + 80, 22,
                 "text;html=1;strokeColor=none;fillColor=none;fontColor=#000000;fontSize=8;")
            + cell(cid + "_s", "", x, y, w, h,
                   "shape=umlSelf;whiteSpace=wrap;html=1;strokeColor=#000000;fontColor=#000000;fontSize=8;")
            )

# =========================== SEQUENCE SIGN UP
body = ""
names = ["Pengguna", "Register Page\n(Register.tsx)", "AuthContext\n(signUp)", "AuthService\n(registerUser)",
         "Supabase Auth", "DB Trigger\n(doctor_profiles)"]
xs = [70, 290, 510, 730, 950, 1170]
lc, pos = lifelines(names, xs, top=30, bottom=880)
body += lc
y = 120
seq_su = [
    ("s1", "Pengguna", "Register Page\n(Register.tsx)", y, "1: buka /register", False),
]
body += msgl("s1", pos["Pengguna"], pos["Register Page\n(Register.tsx)"], 70, 220, y, "1: buka /register")
y += 42
body += msgl("s2", pos["Register Page\n(Register.tsx)"], pos["Pengguna"], 220, 70, y, "2: tampilkan formulir", True)
y += 42
body += msgl("s3", pos["Pengguna"], pos["Register Page\n(Register.tsx)"], 70, 220, y, "3: submit data pendaftaran")
y += 42
body += selfmsg("s4", pos["Register Page\n(Register.tsx)"], 220, y, "4: validasi input", w=120)
y += 50
body += msgl("s5", pos["Register Page\n(Register.tsx)"], pos["AuthContext\n(signUp)"], 220, 440, y, "5: signUp(...)")
y += 42
body += msgl("s6", pos["AuthContext\n(signUp)"], pos["AuthService\n(registerUser)"], 440, 660, y, "6: registerUser(...)")
y += 42
body += msgl("s7", pos["AuthService\n(registerUser)"], pos["Supabase Auth"], 660, 880, y, "7: auth.signUp({...})")
y += 42
body += selfmsg("s8", pos["Supabase Auth"], 880, y, "8: buat auth.users", w=120)
y += 50
body += msgl("s9", pos["Supabase Auth"], pos["DB Trigger\n(doctor_profiles)"], 880, 1100, y, "9: AFTER INSERT auth.users")
y += 42
body += selfmsg("s10", pos["DB Trigger\n(doctor_profiles)"], 1100, y, "10: INSERT doctor_profiles (role=doctor, status=pending)", w=180)
y += 62
body += msgl("s11", pos["Supabase Auth"], pos["AuthService\n(registerUser)"], 880, 660, y, "11: { user, session }", True)
y += 42
body += msgl("s12", pos["AuthService\n(registerUser)"], pos["AuthContext\n(signUp)"], 660, 440, y, "12: AuthResponse", True)
y += 42
body += selfmsg("s13", pos["AuthContext\n(signUp)"], 440, y, "13: set session (jika ada); role=doctor, status=pending", w=180)
y += 62
body += msgl("s14", pos["AuthContext\n(signUp)"], pos["Register Page\n(Register.tsx)"], 440, 220, y, "14: hasil", True)
y += 42
body += msgl("s15", pos["Register Page\n(Register.tsx)"], pos["Pengguna"], 220, 70, y, "15: pesan berhasil + menunggu persetujuan", True)
body += cell("note", "Jika session null -> requiresEmailConfirmation=true (konfirmasi email). Tidak ada pemanggilan Flask API. Akun Admin tidak dibuat di sini.",
             40, 700, 330, 130,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontColor=#000000;fontSize=9;align=left;verticalAlign=top;spacingLeft=6;")
write(OUT + r"\SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("seq-signup-admin", "Sequence Diagram Sign Up PIXEL-T Admin Doctor Revised", "1260", "920", body))

# =========================== SEQUENCE SIGN IN
body = ""
names = ["Pengguna", "Login Page\n(Login.tsx)", "AuthContext\n(signIn)", "AuthService\n(loginUser)",
         "Supabase Auth", "doctor_profiles\n(Supabase DB)", "Route Guard"]
xs = [70, 280, 500, 720, 940, 1150, 1320]
lc, pos = lifelines(names, xs, top=30, bottom=1000)
body += lc
y = 120
body += msgl("s1", pos["Pengguna"], pos["Login Page\n(Login.tsx)"], 70, 210, y, "1: buka /login")
y += 42
body += msgl("s2", pos["Login Page\n(Login.tsx)"], pos["Pengguna"], 210, 70, y, "2: tampilkan formulir", True)
y += 42
body += msgl("s3", pos["Pengguna"], pos["Login Page\n(Login.tsx)"], 70, 210, y, "3: submit email, password, selectedRole")
y += 42
body += msgl("s4", pos["Login Page\n(Login.tsx)"], pos["AuthContext\n(signIn)"], 210, 430, y, "4: signIn(...)")
y += 42
body += msgl("s5", pos["AuthContext\n(signIn)"], pos["AuthService\n(loginUser)"], 430, 650, y, "5: loginUser(...)")
y += 42
body += msgl("s6", pos["AuthService\n(loginUser)"], pos["Supabase Auth"], 650, 870, y, "6: signInWithPassword")
y += 42
body += msgl("s7", pos["Supabase Auth"], pos["AuthService\n(loginUser)"], 870, 650, y, "7: { user, session }", True)
y += 42
body += msgl("s8", pos["AuthService\n(loginUser)"], pos["AuthContext\n(signIn)"], 650, 430, y, "8: AuthResponse", True)
y += 42
body += selfmsg("s9", pos["AuthContext\n(signIn)"], 430, y, "9: getAdminRoleFromAppMetadata(user)", w=170)
y += 50
body += cell("alt1", "[alt] app_metadata.role = admin", 420, y - 22, 560, 44,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=8;verticalAlign=top;align=left;spacingLeft=6;")
y += 34
body += selfmsg("s10", pos["AuthContext\n(signIn)"], 430, y, "set role=admin, account_status=null", w=170)
y += 46
body += cell("alt2", "[else] role dari doctor_profiles", 420, y - 14, 560, 34,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;fontSize=8;verticalAlign=top;align=left;spacingLeft=6;")
y += 26
body += msgl("s11", pos["AuthContext\n(signIn)"], pos["doctor_profiles\n(Supabase DB)"], 430, 1080, y, "fetchUserProfileStatus(user)")
y += 42
body += msgl("s12", pos["doctor_profiles\n(Supabase DB)"], pos["AuthContext\n(signIn)"], 1080, 430, y, "{ role, account_status }", True)
y += 42
body += selfmsg("s13", pos["AuthContext\n(signIn)"], 430, y, "validasi kecocokan selectedRole", w=170)
y += 48
body += msgl("s14", pos["AuthContext\n(signIn)"], pos["Login Page\n(Login.tsx)"], 430, 210, y, "10: { error? }", True)
y += 42
body += msgl("s15", pos["Login Page\n(Login.tsx)"], pos["Route Guard"], 210, 1250, y, "11: navigasi (PublicOnly / Protected / Admin)")
y += 42
body += msgl("s16", pos["Route Guard"], pos["Pengguna"], 1250, 70, y, "12: /admin | /dashboard | /login (pending/rejected)", True)
body += cell("note", "Login hanya memakai Supabase Auth (tidak ada endpoint Flask). Role Admin: app_metadata.role. Status Dokter: doctor_profiles.account_status.",
             40, 930, 360, 110,
             "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;dashed=1;fontColor=#000000;fontSize=9;align=left;verticalAlign=top;spacingLeft=6;")
write(OUT + r"\SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.drawio",
      mxfile("seq-signin-admin", "Sequence Diagram Sign In PIXEL-T Admin Doctor Revised", "1400", "1080", body))
print("DRAWIO DONE")
