/**
 * Generator: BAB 4 - PIXEL-T.docx
 * Menghasilkan dokumen Bab IV Skripsi PIXEL-T lengkap dengan gambar dan format akademik.
 */

const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, Table, TableRow, TableCell, WidthType, BorderStyle,
  TableLayoutType, VerticalAlign, ShadingType, convertInchesToTwip,
  LevelFormat, PageBreak, PageOrientation, Header, Footer, PageNumber,
  NumberFormat, SectionType
} = require('docx');
const fs = require('fs');
const path = require('path');

// ─── PATHS ────────────────────────────────────────────────────────────────────
const BASE = path.join(__dirname, '..', '..', '..', 'references', 'bab 4');
const OUT  = path.join(BASE, 'BAB 4 - PIXEL-T.docx');

// ─── IMAGE HELPER ─────────────────────────────────────────────────────────────
function img(filename, widthCm = 14, heightCm = null) {
  let imgPath = path.join(BASE, filename);
  if (!fs.existsSync(imgPath)) {
    // try subfolder
    const parts = filename.split('/');
    imgPath = path.join(BASE, ...parts);
  }
  if (!fs.existsSync(imgPath)) return null;
  const data = fs.readFileSync(imgPath);
  const pxPerCm = 37.8;
  const w = Math.round(widthCm * pxPerCm);
  const h = heightCm ? Math.round(heightCm * pxPerCm) : Math.round(w * 0.65);
  return new ImageRun({
    data,
    transformation: { width: w, height: h },
    type: 'png'
  });
}

// ─── STYLE HELPERS ────────────────────────────────────────────────────────────
const FONT = 'Times New Roman';
const SZ   = 24; // 12pt = 24 half-points
const SZ_SM = 22; // 11pt

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({
      text,
      font: FONT,
      size: SZ,
      bold: opts.bold || false,
      italics: opts.italic || false,
    })],
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.spacingAfter !== undefined ? opts.spacingAfter : 240, line: 480, lineRule: 'auto' },
    indent: opts.indent !== false ? { firstLine: convertInchesToTwip(0.5) } : {},
    ...opts.paraOpts
  });
}

function paraRuns(runs, opts = {}) {
  return new Paragraph({
    children: runs.map(r => new TextRun({
      text: r.text,
      font: FONT,
      size: SZ,
      bold: r.bold || false,
      italics: r.italic || false,
    })),
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.spacingAfter !== undefined ? opts.spacingAfter : 240, line: 480, lineRule: 'auto' },
    indent: opts.indent !== false ? { firstLine: convertInchesToTwip(0.5) } : {},
  });
}

function heading1(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 28, bold: true })],
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 240 },
  });
}

function heading2(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ, bold: true })],
    heading: HeadingLevel.HEADING_2,
    alignment: AlignmentType.LEFT,
    spacing: { before: 360, after: 120 },
    indent: {},
  });
}

function heading3(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ, bold: true })],
    heading: HeadingLevel.HEADING_3,
    alignment: AlignmentType.LEFT,
    spacing: { before: 240, after: 120 },
    indent: {},
  });
}

function imgCaption(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ, bold: false })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 240 },
    indent: {},
  });
}

function paraImg(imageRun) {
  if (!imageRun) return null;
  return new Paragraph({
    children: [imageRun],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    indent: {},
  });
}

function bulletPara(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: SZ })],
    bullet: { level },
    spacing: { after: 120, line: 480, lineRule: 'auto' },
    indent: { left: convertInchesToTwip(0.5 + level * 0.25), hanging: convertInchesToTwip(0.25) },
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function emptyLine() {
  return new Paragraph({ children: [new TextRun({ text: '' })], spacing: { after: 0 } });
}

// ─── USE CASE TABLE HELPER ────────────────────────────────────────────────────
function tableCell(text, opts = {}) {
  return new TableCell({
    children: [new Paragraph({
      children: [new TextRun({ text, font: FONT, size: SZ_SM, bold: opts.bold || false })],
      alignment: AlignmentType.LEFT,
      spacing: { after: 60, line: 360, lineRule: 'auto' },
    })],
    verticalAlign: VerticalAlign.TOP,
    width: opts.width ? { size: opts.width, type: WidthType.PERCENTAGE } : undefined,
    shading: opts.shaded ? { type: ShadingType.CLEAR, fill: 'D9D9D9' } : undefined,
  });
}

function useCaseTable(caption, rows) {
  const tableRows = rows.map(([label, value]) =>
    new TableRow({
      children: [
        tableCell(label, { bold: true, shaded: true, width: 20 }),
        tableCell(value, { width: 80 }),
      ]
    })
  );
  return [
    new Paragraph({
      children: [new TextRun({ text: caption, font: FONT, size: SZ, bold: true })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 240, after: 120 },
      indent: {},
    }),
    new Table({
      rows: tableRows,
      width: { size: 100, type: WidthType.PERCENTAGE },
      layout: TableLayoutType.FIXED,
      borders: {
        top: { style: BorderStyle.SINGLE, size: 1 },
        bottom: { style: BorderStyle.SINGLE, size: 1 },
        left: { style: BorderStyle.SINGLE, size: 1 },
        right: { style: BorderStyle.SINGLE, size: 1 },
        insideH: { style: BorderStyle.SINGLE, size: 1 },
        insideV: { style: BorderStyle.SINGLE, size: 1 },
      },
    }),
    new Paragraph({ children: [new TextRun({ text: '' })], spacing: { after: 120 } }),
  ];
}

// ─── DOCUMENT BUILDER ─────────────────────────────────────────────────────────
function buildDoc() {
  const children = [];
  const addImg = (filename, widthCm, heightCm) => {
    const ir = img(filename, widthCm, heightCm);
    if (ir) children.push(paraImg(ir));
  };

  // ══════════════════════════════════════════════════════════════════════
  // JUDUL BAB
  // ══════════════════════════════════════════════════════════════════════
  children.push(heading1('BAB IV'));
  children.push(heading1('ANALISIS DAN PERANCANGAN SISTEM'));
  children.push(emptyLine());

  children.push(para(
    'Bab ini membahas hasil analisis kebutuhan dan perancangan sistem PIXEL-T, ' +
    'meliputi pemodelan fungsionalitas melalui Use Case Diagram beserta spesifikasinya, ' +
    'pemodelan alur aktivitas menggunakan Activity Diagram, pemodelan interaksi antarkomponen ' +
    'menggunakan Sequence Diagram, pemodelan struktur perangkat lunak melalui Class Diagram, ' +
    'serta pemodelan basis data menggunakan Entity Relationship Diagram (ERD). ' +
    'Seluruh perancangan didasarkan pada implementasi aktual web PIXEL-T dan bertujuan ' +
    'untuk menggambarkan mekanisme kerja sistem secara terstruktur dan konsisten.'
  ));

  // ══════════════════════════════════════════════════════════════════════
  // 4.1 USE CASE DIAGRAM
  // ══════════════════════════════════════════════════════════════════════
  children.push(heading2('4.1 Use Case Diagram'));
  children.push(para(
    'Sebagai langkah awal dalam pemodelan fungsional sistem, digunakan Use Case Diagram ' +
    'untuk memvisualisasikan ruang lingkup sistem dan interaksi yang terjadi antara aktor ' +
    'dengan fitur-fitur yang tersedia. Gambar 4.1 menunjukkan Use Case Diagram sistem PIXEL-T.'
  ));

  addImg('use_case_diagram.png', 13, 11);
  children.push(imgCaption('Gambar 4.1 Use Case Diagram Sistem PIXEL-T'));

  children.push(para(
    'Berdasarkan Gambar 4.1, sistem PIXEL-T memiliki satu aktor tunggal, yaitu pengguna ' +
    '(dokter atau tenaga medis), yang memiliki akses terhadap tujuh fitur utama: ' +
    'Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, dan Sign Out. ' +
    'Aktor harus menyelesaikan proses Sign In terlebih dahulu sebelum dapat mengakses ' +
    'fitur-fitur inti sistem.'
  ));

  // ── Spesifikasi Use Case ──────────────────────────────────────────────
  children.push(heading3('4.1.1 Spesifikasi Use Case'));
  children.push(para(
    'Setiap use case yang terdapat pada Gambar 4.1 dijelaskan secara terinci melalui ' +
    'tabel spesifikasi berikut.'
  ));

  // UC Sign Up
  children.push(...useCaseTable('Tabel 4.1 Spesifikasi Use Case Sign Up', [
    ['Aktor', 'Pengguna (Belum Terdaftar)'],
    ['Trigger & Tipe', 'Pengguna mengakses halaman /register dan mengisi formulir pendaftaran. Tipe: User-initiated, Synchronous.'],
    ['Pre-Conditions', '1. Pengguna belum memiliki akun PIXEL-T.\n2. Pengguna belum berada dalam sesi autentikasi yang aktif.'],
    ['Normal Course',
      '1. Pengguna membuka halaman Sign Up (/register) melalui tautan di halaman Sign In.\n' +
      '2. Sistem menampilkan formulir pendaftaran dengan enam kolom: Full Name, Email Address, Hospital Name, Doctor Specialty, Password, dan Confirm Password.\n' +
      '3. Pengguna mengisi seluruh kolom dan menekan tombol Create Account.\n' +
      '4. Sistem melakukan validasi sisi klien: kolom tidak boleh kosong, format email valid, kata sandi minimal 6 karakter, dan konfirmasi kata sandi harus cocok.\n' +
      '5. Sistem memanggil supabase.auth.signUp() beserta metadata pengguna.\n' +
      '6. Supabase Auth membuat rekaman akun baru pada auth.users.\n' +
      '7. Sistem menampilkan notifikasi keberhasilan dan mengarahkan pengguna ke halaman Sign In.'
    ],
    ['Post Condition', 'Rekaman akun baru berhasil dibuat pada auth.users. Pengguna berada di halaman Sign In.'],
  ]));
  children.push(para('Tabel 4.1 menjelaskan tahapan proses yang dilakukan oleh pengguna dalam melakukan pendaftaran akun (sign up) pada sistem PIXEL-T.'));

  // UC Sign In
  children.push(...useCaseTable('Tabel 4.2 Spesifikasi Use Case Sign In', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Pengguna mengakses halaman /login dan memasukkan kredensial. Tipe: User-initiated, Synchronous.'],
    ['Pre-Conditions', '1. Pengguna telah memiliki akun PIXEL-T yang terdaftar.\n2. Pengguna belum berada dalam sesi autentikasi yang aktif.'],
    ['Normal Course',
      '1. Pengguna membuka halaman Sign In (/login).\n' +
      '2. Pengguna mengisi alamat email dan kata sandi, kemudian menekan tombol Sign In.\n' +
      '3. Sistem melakukan validasi sisi klien untuk memastikan kolom tidak kosong.\n' +
      '4. Jika opsi Remember Me diaktifkan, alamat email disimpan ke localStorage.\n' +
      '5. Sistem memanggil supabase.auth.signInWithPassword() melalui AuthContext.\n' +
      '6. Supabase Auth mengembalikan token JWT dan objek sesi.\n' +
      '7. Sistem mengarahkan pengguna ke halaman Dashboard.'
    ],
    ['Post Condition', 'Sesi autentikasi aktif tersimpan. Pengguna berada di halaman Dashboard dan dapat mengakses seluruh fitur yang dilindungi.'],
  ]));
  children.push(para('Tabel 4.2 menjelaskan tahapan proses yang dilakukan oleh pengguna untuk masuk (sign in) ke dalam sistem PIXEL-T.'));

  // UC Upload Image
  children.push(...useCaseTable('Tabel 4.3 Spesifikasi Use Case Upload Image', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Pengguna mengakses halaman New Analysis dan mengunggah citra kolonoskopi. Tipe: User-initiated, Asynchronous.'],
    ['Pre-Conditions', '1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).\n2. Pengguna berada pada halaman New Analysis (/analysis/new).\n3. Pengguna memiliki berkas citra kolonoskopi yang akan diunggah.'],
    ['Normal Course',
      '1. Pengguna membuka halaman New Analysis melalui menu navigasi.\n' +
      '2. Sistem menampilkan antarmuka unggah berkas yang mendukung drag-and-drop maupun pemilihan berkas melalui dialog.\n' +
      '3. Pengguna memilih atau menyeret berkas citra ke area unggah.\n' +
      '4. Sistem melakukan validasi berkas sisi klien: ekstensi (.jpg, .jpeg, .png), tipe MIME, dan batas ukuran maksimal 10 MB.\n' +
      '5. Apabila validasi lolos, sistem menampilkan pratinjau citra.\n' +
      '6. Pengguna menekan tombol Start Analysis.\n' +
      '7. Sistem mengirimkan permintaan HTTP POST ke /api/analysis.\n' +
      '8. Backend menyimpan berkas ke Supabase Storage, membuat rekaman analyses berstatus processing, dan mengembalikan HTTP 202 beserta analysis_id.\n' +
      '9. Sistem mengarahkan pengguna ke halaman pemantauan hasil (/analysis/:id).'
    ],
    ['Post Condition', 'Berkas citra tersimpan di Supabase Storage. Rekaman analisis dibuat pada tabel analyses dengan status = processing.'],
  ]));
  children.push(para('Tabel 4.3 menjelaskan tahapan proses yang dilakukan oleh pengguna dalam mengunggah citra kolonoskopi ke dalam sistem PIXEL-T.'));

  // UC Segmentation
  children.push(...useCaseTable('Tabel 4.4 Spesifikasi Use Case Segmentation', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Proses segmentasi dipicu secara otomatis setelah citra berhasil diunggah. Tipe: System-initiated, Asynchronous.'],
    ['Pre-Conditions', '1. Pengguna telah berhasil mengunggah citra kolonoskopi.\n2. Rekaman analisis dengan status = processing tersedia pada tabel analyses.\n3. Berkas citra tersimpan di Supabase Storage.'],
    ['Normal Course',
      '1. Background worker mengambil tugas dari JobQueue dan memuat citra dari Supabase Storage.\n' +
      '2. Sistem memvalidasi integritas citra menggunakan pustaka Pillow.\n' +
      '3. Sistem menjalankan pra-pemrosesan: normalisasi dan penyesuaian ukuran ke 512x512 piksel.\n' +
      '4. Sistem menjalankan inferensi segmentasi menggunakan model U-Net dengan encoder ResNet50, menghasilkan masker biner.\n' +
      '5. Sistem menerapkan pasca-pemrosesan morfologi untuk menyempurnakan kontur masker.\n' +
      '6. Sistem menghasilkan visualisasi Grad-CAM pada lapisan konvolusi target.\n' +
      '7. Sistem menghasilkan empat artefak: binary_mask.png, segmentation_overlay.png, gradcam_heatmap.png, dan gradcam_overlay.png.\n' +
      '8. Keempat artefak disimpan ke Supabase Storage dan status diperbarui menjadi completed.'
    ],
    ['Post Condition', 'Keempat artefak tersimpan di Supabase Storage. Rekaman analyses diperbarui dengan status = completed dan metrik klinis.'],
  ]));
  children.push(para('Tabel 4.4 menjelaskan tahapan proses segmentasi citra kolonoskopi yang berjalan secara asinkron di latar belakang pada sistem PIXEL-T.'));

  // UC History
  children.push(...useCaseTable('Tabel 4.5 Spesifikasi Use Case View History', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Pengguna mengakses halaman Analysis History. Tipe: User-initiated, Synchronous.'],
    ['Pre-Conditions', '1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).\n2. Sistem dapat terhubung ke layanan backend untuk mengambil data riwayat.'],
    ['Normal Course',
      '1. Pengguna mengakses halaman Analysis History (/history) melalui menu navigasi.\n' +
      '2. Sistem memanggil listHistory() untuk mengambil seluruh rekaman analisis milik pengguna aktif.\n' +
      '3. Sistem menampilkan daftar riwayat dalam format tabel berisi nama berkas, tanggal analisis, dan status (COMPLETED, PROCESSING, atau FAILED).\n' +
      '4. Sistem menampilkan 4 rekaman per halaman dengan kontrol paginasi.\n' +
      '5. Pengguna dapat memfilter daftar berdasarkan teks nama berkas, dropdown status, atau tanggal — seluruhnya berjalan di sisi klien menggunakan useMemo.\n' +
      '6. Pengguna dapat menekan tautan View untuk mengakses halaman detail analisis (/analysis/:id).\n' +
      '7. Pengguna dapat menghapus rekaman melalui modal konfirmasi yang memanggil deleteAnalysis().'
    ],
    ['Post Condition', 'Daftar riwayat analisis berhasil ditampilkan. Pengguna dapat menelusuri, memfilter, melihat detail, atau menghapus rekaman.'],
  ]));
  children.push(para('Tabel 4.5 menjelaskan tahapan proses yang dilakukan oleh pengguna dalam menelusuri riwayat analisis pada sistem PIXEL-T.'));

  // UC Doctor Profile
  children.push(...useCaseTable('Tabel 4.6 Spesifikasi Use Case View Doctor Profile', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Pengguna mengakses halaman Doctor Profile. Tipe: User-initiated, Synchronous.'],
    ['Pre-Conditions', '1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).\n2. Sistem dapat terhubung ke Supabase untuk mengambil data profil.'],
    ['Normal Course',
      '1. Pengguna mengakses halaman Doctor Profile (/profile) melalui menu navigasi.\n' +
      '2. Sistem memanggil fetchDoctorProfile() dari profile.ts untuk mengambil data dari tabel doctor_profiles.\n' +
      '3. Sistem secara bersamaan mengambil riwayat analisis untuk menghitung statistik aktivitas (total analisis dan jumlah completed).\n' +
      '4. Sistem menampilkan informasi personal, data profesional, dan kartu statistik aktivitas.\n' +
      '5. Pengguna dapat menekan tombol Edit Profile untuk membuka modal pengeditan.\n' +
      '6. Sistem menjalankan validateProfileData() sebelum menyimpan perubahan.\n' +
      '7. Sistem mengeksekusi operasi upsert ke tabel doctor_profiles dan memperbarui nama pada supabase.auth.updateUser().'
    ],
    ['Post Condition', 'Profil dokter berhasil ditampilkan. Apabila pengguna melakukan pengeditan, rekaman doctor_profiles diperbarui.'],
  ]));
  children.push(para('Tabel 4.6 menjelaskan tahapan proses yang dilakukan oleh pengguna dalam mengelola profil klinis pada sistem PIXEL-T.'));

  // UC Sign Out
  children.push(...useCaseTable('Tabel 4.7 Spesifikasi Use Case Sign Out', [
    ['Aktor', 'Pengguna Terdaftar (Dokter / Tenaga Medis)'],
    ['Trigger & Tipe', 'Pengguna memilih opsi keluar melalui menu navigasi. Tipe: User-initiated, Synchronous.'],
    ['Pre-Conditions', '1. Pengguna sedang berada dalam sesi autentikasi yang aktif.\n2. Menu navigasi tersedia dan dapat diakses.'],
    ['Normal Course',
      '1. Pengguna membuka menu navigasi dan menekan opsi Sign Out.\n' +
      '2. Sistem menampilkan modal konfirmasi keluar.\n' +
      '3. Pengguna mengonfirmasi dengan menekan tombol Yes, Sign Out.\n' +
      '4. Sistem memanggil supabase.auth.signOut() melalui AuthContext.\n' +
      '5. Supabase Auth mengakhiri sesi aktif dan menghapus token JWT.\n' +
      '6. AuthContext memperbarui status autentikasi menjadi tidak aktif.\n' +
      '7. Sistem mengarahkan pengguna ke halaman Sign In (/login).'
    ],
    ['Post Condition', 'Sesi autentikasi diakhiri sepenuhnya. Token JWT dihapus. Pengguna berada di halaman Sign In.'],
  ]));
  children.push(para('Tabel 4.7 menjelaskan tahapan proses yang dilakukan oleh pengguna untuk keluar (sign out) dari sistem PIXEL-T.'));

  // ══════════════════════════════════════════════════════════════════════
  // 4.2 ACTIVITY DIAGRAM
  // ══════════════════════════════════════════════════════════════════════
  children.push(pageBreak());
  children.push(heading2('4.2 Activity Diagram'));
  children.push(para(
    'Setelah mendefinisikan fungsionalitas sistem melalui Use Case Diagram, tahap selanjutnya ' +
    'adalah menyusun Activity Diagram. Activity Diagram digunakan untuk memodelkan alur kerja ' +
    '(workflow) sistem secara terstruktur dengan menggambarkan urutan aktivitas yang terjadi ' +
    'dari awal hingga akhir proses, termasuk simpul keputusan, cabang alternatif, dan kondisi ' +
    'penggabungan alur pada setiap fitur utama sistem PIXEL-T.'
  ));

  // ── 4.2.1 Sign Up ──────────────────────────────────────────────────────
  children.push(heading3('4.2.1 Activity Diagram Sign Up'));
  children.push(para(
    'Gambar 4.2 menunjukkan Activity Diagram Sign Up yang menggambarkan alur pendaftaran ' +
    'akun baru bagi dokter atau tenaga medis ke dalam sistem PIXEL-T.'
  ));
  addImg('activity_diagrams/Activity Diagram - Sign Up.drawio.png', 12, 14);
  children.push(imgCaption('Gambar 4.2 Activity Diagram Sign Up'));
  children.push(para(
    'Alur pendaftaran dimulai ketika calon pengguna membuka antarmuka pendaftaran. ' +
    'Pengguna melengkapi enam kolom isian: nama lengkap, alamat email, nama rumah sakit, ' +
    'bidang keahlian, kata sandi, dan konfirmasi kata sandi. Setelah pengguna mengirimkan ' +
    'formulir, sistem melakukan validasi masukan sisi klien: memastikan seluruh kolom terisi, ' +
    'format email valid, kata sandi minimal 6 karakter, dan konfirmasi kata sandi cocok. ' +
    'Apabila validasi tidak lolos, sistem menampilkan pesan kesalahan dan alur kembali ke ' +
    'langkah pengisian. Apabila validasi lolos, sistem memanggil Supabase Auth untuk membuat ' +
    'akun baru pada auth.users, menampilkan notifikasi keberhasilan, dan mengarahkan ' +
    'pengguna ke halaman Sign In.'
  ));

  // ── 4.2.2 Sign In ──────────────────────────────────────────────────────
  children.push(heading3('4.2.2 Activity Diagram Sign In'));
  children.push(para(
    'Gambar 4.3 menunjukkan Activity Diagram Sign In yang memodelkan alur verifikasi identitas ' +
    'dan pembentukan sesi autentikasi pengguna pada sistem PIXEL-T.'
  ));
  addImg('activity_diagrams/Activity Diagram - Sign In.drawio.png', 12, 14);
  children.push(imgCaption('Gambar 4.3 Activity Diagram Sign In'));
  children.push(para(
    'Proses masuk sistem dimulai saat pengguna mengakses antarmuka Sign In. Pengguna ' +
    'memasukkan alamat email dan kata sandi, kemudian mengirimkan formulir. Sistem melakukan ' +
    'validasi awal untuk memastikan kolom tidak kosong, lalu meneruskan permintaan autentikasi ' +
    'ke Supabase Auth melalui fungsi signInWithPassword. Apabila kredensial keliru, sistem ' +
    'menampilkan pesan kesalahan dan alur kembali ke langkah pengisian. Apabila kredensial sah, ' +
    'Supabase Auth menerbitkan token JWT, sesi disimpan pada AuthContext, dan sistem ' +
    'mengarahkan pengguna ke halaman Dashboard.'
  ));

  // ── 4.2.3 Upload Image ─────────────────────────────────────────────────
  children.push(heading3('4.2.3 Activity Diagram Upload Image'));
  children.push(para(
    'Gambar 4.4 menunjukkan Activity Diagram Upload Image yang memodelkan alur penerimaan, ' +
    'validasi berkas, dan pengiriman citra kolonoskopi ke server PIXEL-T.'
  ));
  addImg('activity_diagrams/Activity Diagram - Upload Image.drawio.png', 12, 14);
  children.push(imgCaption('Gambar 4.4 Activity Diagram Upload Image'));
  children.push(para(
    'Aktivitas pengunggahan dimulai ketika dokter mengakses halaman New Analysis. ' +
    'Pengguna memilih berkas citra melalui dialog pemilihan berkas atau mekanisme seret-dan-lepas. ' +
    'Sistem segera menjalankan validasi berkas sisi klien: apabila ekstensi di luar format yang ' +
    'diizinkan (.jpg, .jpeg, .png), tipe MIME tidak sesuai, atau ukuran berkas melebihi 10 MB, ' +
    'sistem menampilkan pesan kesalahan. Apabila berkas valid, sistem menampilkan pratinjau citra. ' +
    'Pengguna menekan tombol Start Analysis, sistem mengirimkan berkas melalui HTTP POST ke ' +
    '/api/analysis. Backend menyimpan citra asli ke Supabase Storage, mendaftarkan rekaman ' +
    'analisis berstatus processing, dan mengembalikan HTTP 202 beserta analysis_id. ' +
    'Sistem kemudian mengarahkan pengguna ke halaman pemantauan hasil.'
  ));

  // ── 4.2.4 Segmentation ─────────────────────────────────────────────────
  children.push(heading3('4.2.4 Activity Diagram Segmentation'));
  children.push(para(
    'Gambar 4.5 menunjukkan Activity Diagram Segmentation yang menggambarkan tahapan ' +
    'pemrosesan inferensi AI dan visualisasi Explainable AI pada citra kolonoskopi.'
  ));
  addImg('activity_diagrams/Activity Diagram - Segmentation.drawio.png', 12, 15);
  children.push(imgCaption('Gambar 4.5 Activity Diagram Segmentation'));
  children.push(para(
    'Alur segmentasi diawali ketika background worker mengeksekusi tugas dari antrean ' +
    'inferensi. Sistem backend memuat citra dari Supabase Storage dan melakukan pra-pemrosesan ' +
    '(normalisasi dan penyesuaian ukuran ke 512x512 piksel). Apabila terjadi kegagalan ' +
    'komputasi, sistem memperbarui status rekaman menjadi failed dan antarmuka menampilkan ' +
    'notifikasi bahwa analisis tidak dapat diselesaikan. Apabila berhasil, sistem mengeksekusi ' +
    'tahapan inferensi secara sekuensial: segmentasi biner menggunakan model U-Net dengan ' +
    'encoder ResNet50, pasca-pemrosesan morfologi, perhitungan metrik luas area polip, ' +
    'pembangkitan visualisasi Grad-CAM, dan penyusunan empat artefak keluaran. Seluruh artefak ' +
    'diunggah ke Supabase Storage dan status rekaman diperbarui menjadi completed. Frontend ' +
    'yang melakukan polling mendeteksi perubahan status dan menampilkan hasil kepada dokter.'
  ));

  // ── 4.2.5 History ──────────────────────────────────────────────────────
  children.push(heading3('4.2.5 Activity Diagram History'));
  children.push(para(
    'Gambar 4.6 menunjukkan Activity Diagram History yang memodelkan alur penelusuran ' +
    'riwayat pemeriksaan, penyaringan data, peninjauan detail, dan penghapusan rekaman.'
  ));
  addImg('activity_diagrams/Activity Diagram - History.drawio.png', 12, 14);
  children.push(imgCaption('Gambar 4.6 Activity Diagram History'));
  children.push(para(
    'Aktivitas penelusuran dimulai saat dokter membuka halaman History. Sistem memanggil ' +
    'listHistory untuk mengambil seluruh rekaman analisis berdasarkan user_id. Apabila belum ' +
    'ada rekaman, sistem menampilkan antarmuka empty state. Apabila data tersedia, sistem ' +
    'menyajikan daftar riwayat dalam tabel interaktif dengan paginasi 4 rekaman per halaman. ' +
    'Pengguna dapat mempersempit daftar menggunakan filter pencarian teks, dropdown status, ' +
    'atau filter tanggal — seluruhnya berjalan di sisi klien. Pengguna kemudian memilih ' +
    'tindakan: melihat detail analisis atau menghapus rekaman. Penghapusan memerlukan ' +
    'konfirmasi melalui modal sebelum sistem menghapus rekaman pada basis data dan ' +
    'seluruh berkas artefak di Supabase Storage.'
  ));

  // ── 4.2.6 Doctor Profile ───────────────────────────────────────────────
  children.push(heading3('4.2.6 Activity Diagram Doctor Profile'));
  children.push(para(
    'Gambar 4.7 menunjukkan Activity Diagram Doctor Profile yang memodelkan alur ' +
    'peninjauan profil klinis dokter dan pembaruan data profil melalui formulir modal.'
  ));
  addImg('activity_diagrams/Activity Diagram - Doctor Profile.drawio.png', 12, 14);
  children.push(imgCaption('Gambar 4.7 Activity Diagram Doctor Profile'));
  children.push(para(
    'Proses diawali ketika dokter mengakses halaman profil. Sistem mengambil data profil ' +
    'dari tabel doctor_profiles dan menghitung ringkasan statistik aktivitas dari riwayat ' +
    'analisis. Sistem menampilkan halaman profil yang memuat informasi personal, data ' +
    'profesional, dan kartu statistik. Apabila pengguna hanya ingin meninjau, alur langsung ' +
    'berakhir. Apabila pengguna ingin mengubah profil, sistem membuka modal formulir yang ' +
    'berisi kolom-kolom yang dapat disunting. Pengguna dapat membatalkan tindakan atau ' +
    'menyimpan perubahan. Sistem menjalankan validateProfileData() untuk memverifikasi data ' +
    'sebelum mengeksekusi operasi upsert ke tabel doctor_profiles dan menyinkronkan nama ' +
    'pada metadata Supabase Auth. Sistem menampilkan notifikasi keberhasilan dan memperbarui ' +
    'tampilan profil.'
  ));

  // ── 4.2.7 Sign Out ─────────────────────────────────────────────────────
  children.push(heading3('4.2.7 Activity Diagram Sign Out'));
  children.push(para(
    'Gambar 4.8 menunjukkan Activity Diagram Sign Out yang memodelkan alur pengakhiran ' +
    'sesi autentikasi pengguna secara aman dari sistem PIXEL-T.'
  ));
  addImg('activity_diagrams/Activity Diagram - Sign Out.drawio.png', 12, 10);
  children.push(imgCaption('Gambar 4.8 Activity Diagram Sign Out'));
  children.push(para(
    'Alur dimulai saat pengguna menekan tombol Sign Out pada menu navigasi. Sistem ' +
    'menampilkan modal konfirmasi untuk mencegah tindakan yang tidak disengaja. Apabila ' +
    'pengguna membatalkan, modal ditutup dan sesi tetap aktif. Apabila pengguna mengonfirmasi, ' +
    'sistem memanggil signOut() ke Supabase Auth untuk mengakhiri token akses JWT. AuthContext ' +
    'membersihkan data sesi, dan sistem mengarahkan pengguna ke halaman Sign In (/login). ' +
    'Seluruh rute privat kembali terlindungi dari akses tanpa autentikasi.'
  ));

  // ══════════════════════════════════════════════════════════════════════
  // 4.3 SEQUENCE DIAGRAM
  // ══════════════════════════════════════════════════════════════════════
  children.push(pageBreak());
  children.push(heading2('4.3 Sequence Diagram'));
  children.push(para(
    'Setelah memodelkan alur kerja sistem menggunakan Activity Diagram, tahap selanjutnya ' +
    'adalah menjabarkan interaksi antarkomponen secara lebih terinci menggunakan Sequence ' +
    'Diagram. Berbeda dengan Activity Diagram yang berfokus pada aliran aktivitas, ' +
    'Sequence Diagram berfokus pada urutan pesan dan komunikasi antarobjek berdasarkan ' +
    'garis waktu. Komponen yang terlibat meliputi pengguna (User), antarmuka React (Frontend), ' +
    'lapisan manajemen status (AuthContext), lapisan layanan (Service Layer), server Flask ' +
    '(Backend), mesin inferensi AI (Pipeline AI), serta layanan Supabase.'
  ));

  const seqImages = [
    ['sequence_diagram/sequence_diagram_sign_up.png',            'Sign Up'],
    ['sequence_diagram/sequence_diagram_sign_in.png',            'Sign In'],
    ['sequence_diagram/sequence_diagram_upload_image.png',       'Upload Image'],
    ['sequence_diagram/sequence_diagram_segmentation.png',       'Segmentation'],
    ['sequence_diagram/sequence_diagram_history.png',            'History'],
    ['sequence_diagram/sequence_diagram_doctor_profile.png',     'Doctor Profile'],
    ['sequence_diagram/sequence_diagram_sign_out.png',           'Sign Out'],
  ];

  const seqNumbers = ['4.9','4.10','4.11','4.12','4.13','4.14','4.15'];
  const seqSubNums = ['4.3.1','4.3.2','4.3.3','4.3.4','4.3.5','4.3.6','4.3.7'];

  const seqTexts = [
    // Sign Up
    'Proses pendaftaran dimulai saat pengguna membuka halaman registrasi. ' +
    'Komponen Register.tsx menampilkan formulir dan pengguna mengisi enam kolom pendaftaran, ' +
    'kemudian menekan tombol pendaftaran. Komponen menjalankan validasi formulir sisi klien: ' +
    'memastikan seluruh kolom terisi, format email valid, kata sandi minimal 6 karakter, ' +
    'dan konfirmasi kata sandi cocok. Apabila validasi gagal, antarmuka menampilkan pesan ' +
    'kesalahan tanpa melanjutkan permintaan. Apabila validasi lolos, komponen memanggil ' +
    'signUp pada AuthContext yang meneruskan ke auth.ts untuk mengeksekusi ' +
    'supabase.auth.signUp beserta metadata pengguna. Apabila pendaftaran berhasil, ' +
    'sistem mengevaluasi keberadaan sesi: apabila sesi langsung aktif, AuthContext ' +
    'memperbarui status pengguna; apabila belum aktif karena konfirmasi email diperlukan, ' +
    'antarmuka menampilkan notifikasi agar pengguna memeriksa kotak masuk email.',

    // Sign In
    'Alur masuk sistem dimulai ketika pengguna membuka halaman Sign In. Pengguna ' +
    'memasukkan email dan kata sandi, kemudian menekan tombol masuk. Komponen Login.tsx ' +
    'melakukan validasi masukan lokal untuk memastikan kedua kolom tidak kosong. Antarmuka ' +
    'memanggil signIn pada AuthContext yang meneruskan ke auth.ts untuk mengeksekusi ' +
    'supabase.auth.signInWithPassword. Apabila autentikasi ditolak, layanan menyaring ' +
    'kesalahan melalui formatAuthError() dan antarmuka menampilkan notifikasi galat. ' +
    'Apabila kredensial sah, Supabase Auth menerbitkan token JWT dan objek sesi. ' +
    'AuthContext memperbarui status pengguna secara global dan antarmuka mengarahkan ' +
    'pengguna ke halaman Dashboard.',

    // Upload Image
    'Proses pengunggahan dimulai saat pengguna memilih berkas citra pada halaman New Analysis. ' +
    'Frontend segera melakukan validasi berkas sisi klien mencakup pemeriksaan ekstensi, ' +
    'tipe MIME, dan batas ukuran 10 MB. Apabila berkas tidak memenuhi syarat, antarmuka ' +
    'menampilkan pesan kesalahan. Apabila valid, antarmuka menampilkan pratinjau citra. ' +
    'Pengguna menekan tombol untuk memulai analisis. Antarmuka mengambil sesi autentikasi ' +
    'aktif, menyusun berkas ke dalam FormData, dan mengirimkannya bersama token JWT ke ' +
    'backend melalui POST /api/analysis. Backend memverifikasi token, memvalidasi citra ' +
    'di sisi server, menyimpan berkas ke Supabase Storage, dan membuat rekaman analyses ' +
    'berstatus processing. Apabila antrean penuh, backend mengembalikan HTTP 429. ' +
    'Apabila berhasil, backend mengembalikan HTTP 202 beserta analysis_id.',

    // Segmentation
    'Alur segmentasi berkesinambungan dengan proses pengunggahan. Setelah backend ' +
    'membuat rekaman analyses berstatus processing dan mengembalikan HTTP 202 ke frontend, ' +
    'background worker secara asinkron memulai pipeline inferensi. Pipeline menjalankan ' +
    'serangkaian tahapan secara sekuensial: pra-pemrosesan citra, inferensi segmentasi ' +
    'menggunakan U-Net dengan encoder ResNet50, pasca-pemrosesan morfologi, kalkulasi ' +
    'Grad-CAM pada lapisan konvolusi target, dan penyusunan empat artefak keluaran. ' +
    'Apabila berhasil, backend mengunggah artefak ke Supabase Storage dan memperbarui ' +
    'status menjadi completed. Apabila gagal, status diperbarui menjadi failed. ' +
    'Sementara itu, frontend melakukan polling berkala dengan GET /api/analysis/{id}. ' +
    'Backend membaca status terkini dan mengembalikannya beserta Signed URL artefak. ' +
    'Antarmuka menampilkan hasil segmentasi, citra overlay, dan peta Grad-CAM kepada dokter.',

    // History
    'Penelusuran riwayat dimulai saat pengguna membuka halaman riwayat. Komponen ' +
    'History.tsx mengirimkan permintaan ke Backend (Flask API) melalui GET /api/history. ' +
    'Backend mengambil data riwayat milik pengguna aktif dari basis data, membuat Signed URL ' +
    'untuk gambar pratinjau, dan mengembalikan daftar riwayat. Apabila koneksi gagal, ' +
    'antarmuka menampilkan error state; apabila daftar kosong, antarmuka menampilkan ' +
    'pesan bahwa belum ada riwayat. Pengguna dapat melakukan pencarian dan filter lokal — ' +
    'berdasarkan nama berkas, status, atau tanggal — serta paginasi di sisi klien. ' +
    'Pengguna dapat memilih rekaman untuk melihat detail: frontend mengirimkan ' +
    'GET /api/analysis/{id} dan backend mengembalikan detail beserta Signed URL artefak. ' +
    'Untuk penghapusan, frontend menampilkan dialog konfirmasi; apabila dikonfirmasi, ' +
    'frontend mengirimkan DELETE /api/history/{id} dan backend menghapus rekaman serta ' +
    'berkas artefak dari Supabase Storage.',

    // Doctor Profile
    'Alur dimulai saat pengguna mengakses halaman profil. Komponen DoctorProfile.tsx ' +
    'memanggil fetchDoctorProfile() dari Profile Service (profile.ts) yang mengeksekusi ' +
    'kueri ke tabel doctor_profiles berdasarkan user_id. Apabila profil belum tersedia, ' +
    'layanan menggunakan data cadangan dari metadata Supabase Auth. Secara bersamaan, ' +
    'frontend memanggil GET /api/history untuk mengambil riwayat analisis guna ' +
    'menghitung metrik statistik aktivitas. Pengguna disajikan halaman profil yang ' +
    'memadukan informasi identitas, data profesional, dan kartu statistik. Apabila ' +
    'pengguna menekan Edit Profile, frontend menampilkan modal formulir. Pengguna dapat ' +
    'membatalkan atau menyimpan perubahan. Apabila menyimpan, Profile Service menjalankan ' +
    'validateProfileData(), kemudian mengeksekusi operasi upsert ke tabel doctor_profiles ' +
    'dan memperbarui nama pada supabase.auth.updateUser(). Antarmuka menampilkan notifikasi ' +
    'keberhasilan dan data profil yang diperbarui.',

    // Sign Out
    'Proses keluar dimulai ketika pengguna menekan tombol Sign Out pada antarmuka navigasi ' +
    '(AppShell). Sistem menampilkan modal konfirmasi untuk mencegah tindakan yang tidak ' +
    'disengaja. Pengguna mengonfirmasi dengan menekan tombol Yes. AppShell memanggil ' +
    'signOut() pada AuthContext yang meneruskan ke logoutUser() pada Auth Service. ' +
    'Layanan mengeksekusi supabase.auth.signOut() untuk mengakhiri sesi aktif. ' +
    'AuthContext menerima respons dan membersihkan variabel status pengguna dan sesi ' +
    'menjadi null, terlepas dari hasil respons Supabase. AppShell mengarahkan navigasi ' +
    'ke halaman masuk (/login). Listener onAuthStateChange pada AuthContext menerima ' +
    'notifikasi dari Supabase sebagai lapisan sinkronisasi kedua. Seluruh rute privat ' +
    'kembali terlindungi dari akses tanpa autentikasi.',
  ];

  const seqTitles = [
    'Sequence Diagram Sign Up', 'Sequence Diagram Sign In',
    'Sequence Diagram Upload Image', 'Sequence Diagram Segmentation',
    'Sequence Diagram History', 'Sequence Diagram Doctor Profile',
    'Sequence Diagram Sign Out',
  ];

  for (let i = 0; i < 7; i++) {
    children.push(heading3(`${seqSubNums[i]} ${seqTitles[i]}`));
    children.push(para(
      `Gambar ${seqNumbers[i]} menunjukkan ${seqTitles[i]} yang menggambarkan rangkaian ` +
      `interaksi antarkomponen dalam proses ${seqTitles[i].replace('Sequence Diagram ', '')} ` +
      `pada sistem PIXEL-T.`
    ));
    addImg(seqImages[i][0], 15, 9);
    children.push(imgCaption(`Gambar ${seqNumbers[i]} ${seqTitles[i]}`));
    children.push(para(seqTexts[i]));
  }

  // ══════════════════════════════════════════════════════════════════════
  // 4.4 CLASS DIAGRAM
  // ══════════════════════════════════════════════════════════════════════
  children.push(pageBreak());
  children.push(heading2('4.4 Perancangan Struktur Perangkat Lunak (Class Diagram)'));
  children.push(para(
    'Setelah memodelkan interaksi antarkomponen melalui Sequence Diagram, tahap berikutnya ' +
    'adalah mendefinisikan struktur statis perangkat lunak menggunakan Class Diagram. ' +
    'Class Diagram berfungsi untuk memetakan komponen-komponen perangkat lunak, mendefinisikan ' +
    'atribut dan operasi setiap kelas atau modul, serta menggambarkan relasi ketergantungan ' +
    'dan asosiasi antarkomponen dalam sistem PIXEL-T.'
  ));
  children.push(para(
    'Antarmuka pengguna (frontend) dibangun menggunakan React 18 dengan TypeScript yang ' +
    'menerapkan paradigma komponen fungsional. Class Diagram sistem PIXEL-T difokuskan pada ' +
    'arsitektur berorientasi objek di sisi peladen (backend), mesin inferensi kecerdasan buatan, ' +
    'dan entitas persistensi basis data relasional. Gambar 4.16 menunjukkan Class Diagram ' +
    'sistem PIXEL-T.'
  ));
  addImg('class_diagram.png', 15, 11);
  children.push(imgCaption('Gambar 4.16 Class Diagram Sistem PIXEL-T'));
  children.push(para(
    'Berdasarkan Gambar 4.16, komponen perangkat lunak sistem PIXEL-T terbagi ke dalam ' +
    'tiga lapisan tanggung jawab utama: Lapisan Layanan Bisnis dan Infrastruktur, ' +
    'Lapisan Mesin Kecerdasan Buatan, serta Lapisan Persistensi Basis Data.'
  ));

  children.push(heading3('4.4.1 Lapisan Layanan Bisnis dan Infrastruktur'));
  children.push(para(
    'Kelas AnalysisService (analysis_service.py) merupakan orkestrator utama yang ' +
    'mengendalikan seluruh siklus hidup analisis citra polip, mulai dari validasi masukan, ' +
    'pengunggahan berkas, penjadwalan inferensi latar belakang, hingga pembersihan data. ' +
    'Kelas ini bergantung pada AnalysisRepository untuk operasi basis data dan pada ' +
    'StorageService untuk pengelolaan berkas di Supabase Storage bucket analysis-assets.'
  ));
  children.push(para(
    'Kelas StorageService (storage_service.py) mengabstraksi komunikasi dengan Supabase ' +
    'Storage, menyediakan operasi pengunggahan, penerbitan Signed URL berkedaluarsa, ' +
    'dan penghapusan berkas. Kelas AnalysisRepository (analysis_repository.py) menerapkan ' +
    'Repository Pattern untuk mengisolasi logika akses data dari logika bisnis, menyediakan ' +
    'operasi CRUD pada tabel analyses.'
  ));

  children.push(heading3('4.4.2 Lapisan Mesin Kecerdasan Buatan'));
  children.push(para(
    'Modul AI inference functions (pipeline.py, segmentation.py, postprocessing.py, gradcam.py) ' +
    'merepresentasikan fungsi-fungsi komputasi inferensi AI dengan stereotipe module. ' +
    'Fungsi orkestrasi run_pipeline menjalankan seluruh tahapan secara sekuensial: ' +
    'pra-pemrosesan, segmentasi, pasca-pemrosesan, Grad-CAM, dan penyusunan artefak.'
  ));
  children.push(para(
    'Kelas ModelService (model_service.py) bertindak sebagai pengelola siklus hidup model ' +
    'PyTorch tunggal (Singleton) agar bobot model tidak dimuat ulang pada setiap permintaan ' +
    'inferensi. Kelas ini menyimpan konfigurasi model (arsitektur UNet, encoder ResNet50, ' +
    'ukuran input, ambang batas binerisasi) dan perangkat keras komputasi (GPU atau CPU). ' +
    'Fungsi predict dan generate_gradcam bergantung pada ModelService untuk menjalankan ' +
    'forward pass dan kalkulasi gradien.'
  ));

  children.push(heading3('4.4.3 Lapisan Persistensi Basis Data'));
  children.push(para(
    'Entitas auth.users (stereotipe external) merepresentasikan tabel autentikasi yang ' +
    'dikelola oleh Supabase Auth dengan atribut utama id (UUID) sebagai kunci induk. ' +
    'Entitas doctor_profiles (stereotipe entity) menyimpan informasi profil profesional ' +
    'dokter dengan foreign key user_id yang diikat melalui kendala UNIQUE. ' +
    'Entitas analyses (stereotipe entity) merekam seluruh siklus hidup pemrosesan citra ' +
    'dengan foreign key user_id yang memiliki aturan ON DELETE CASCADE.'
  ));

  children.push(heading3('4.4.4 Relasi Antarkomponen'));
  children.push(para(
    'Seluruh relasi pada Gambar 4.16 mengikuti standar UML 2.5. Relasi asosiasi basis data ' +
    '(garis solid) menghubungkan auth.users dengan doctor_profiles (kardinalitas 1:0..1) ' +
    'dan auth.users dengan analyses (kardinalitas 1:N). Relasi dependensi (garis putus-putus ' +
    'dengan panah terbuka) menunjukkan ketergantungan penggunaan antarkomponen: ' +
    'AnalysisService bergantung pada AnalysisRepository (persistensi), StorageService ' +
    '(upload/assets), dan AI inference functions (background pipeline); AnalysisRepository ' +
    'bergantung pada entitas analyses (CRUD); serta AI inference functions bergantung pada ' +
    'ModelService (inference/Grad-CAM).'
  ));

  // ══════════════════════════════════════════════════════════════════════
  // 4.5 ERD
  // ══════════════════════════════════════════════════════════════════════
  children.push(pageBreak());
  children.push(heading2('4.5 Perancangan Basis Data (Entity Relationship Diagram)'));
  children.push(para(
    'Setelah mendefinisikan struktur perangkat lunak melalui Class Diagram, tahap perancangan ' +
    'berikutnya adalah memodelkan struktur basis data menggunakan Entity Relationship Diagram ' +
    '(ERD). ERD bertujuan untuk mendefinisikan entitas yang digunakan, atribut-atributnya, ' +
    'serta relasi dan batasan integritas referensial antartabel dalam sistem PIXEL-T.'
  ));
  children.push(para(
    'Sistem PIXEL-T memanfaatkan basis data relasional PostgreSQL yang dikelola melalui ' +
    'platform Supabase Backend-as-a-Service (BaaS). Struktur relasi basis data sistem ' +
    'PIXEL-T disajikan pada Gambar 4.17.'
  ));
  addImg('ERD_PIXELT_FINAL.png', 14, 10);
  children.push(imgCaption('Gambar 4.17 Entity Relationship Diagram (ERD) Sistem PIXEL-T'));
  children.push(para(
    'Berdasarkan Gambar 4.17, basis data PIXEL-T terdiri dari tiga entitas relasional: ' +
    'users (auth.users), doctor_profiles, dan analyses. Masing-masing entitas memiliki ' +
    'fungsi, spesifikasi atribut, dan aturan integritas yang diuraikan berikut ini.'
  ));

  children.push(heading3('4.5.1 Entitas users (auth.users)'));
  children.push(para(
    'Entitas users merupakan entitas autentikasi yang dikelola oleh skema internal Supabase ' +
    'Auth (auth.users). Pemisahan skema ini memastikan manajemen kredensial pengguna ' +
    'terisolasi dari data aplikasi. Atribut utamanya meliputi id (UUID) sebagai Primary Key ' +
    'yang dibuat otomatis saat registrasi, email sebagai identitas autentikasi, created_at ' +
    'sebagai stempel waktu pembuatan akun, dan user_metadata (JSONB) yang menyimpan ' +
    'metadata tambahan pengguna.'
  ));

  children.push(heading3('4.5.2 Entitas doctor_profiles'));
  children.push(para(
    'Entitas doctor_profiles menyimpan informasi profil profesional dokter pengguna sistem ' +
    'PIXEL-T. Atribut utamanya mencakup id (UUID) sebagai Primary Key, user_id (UUID) ' +
    'sebagai Foreign Key yang merujuk pada users.id dengan kendala UNIQUE, full_name, ' +
    'primary_specialty, hospital, phone, birth_date, city, department, str_number, ' +
    'is_verified (BOOLEAN), bio, education (JSONB), experience (JSONB), serta stempel waktu ' +
    'created_at dan updated_at.'
  ));

  children.push(heading3('4.5.3 Entitas analyses'));
  children.push(para(
    'Entitas analyses adalah entitas transaksional utama yang merekam seluruh siklus hidup ' +
    'pemrosesan citra kolonoskopi. Atribut utamanya meliputi id (UUID) sebagai Primary Key, ' +
    'user_id (UUID) sebagai Foreign Key dengan aturan ON DELETE CASCADE, status dengan nilai ' +
    'terkendala (processing, completed, atau failed), jalur berkas artefak pada Supabase ' +
    'Storage (original_image_path, binary_mask_path, segmentation_overlay_path, ' +
    'gradcam_heatmap_path, gradcam_overlay_path), metrik klinis (area_pixels, area_ratio, ' +
    'segmentation_status), metadata model (model_architecture, model_version), serta ' +
    'indikator progres (current_step, progress_percent) dan stempel waktu (created_at, ' +
    'completed_at).'
  ));

  children.push(heading3('4.5.4 Relasi Antartabel'));
  children.push(para(
    'Relasi antartabel dihubungkan menggunakan mekanisme Foreign Key dengan notasi ' +
    'kardinalitas Crow\'s Foot. Pertama, relasi antara users dan doctor_profiles ' +
    '(kardinalitas 1:0..1) diklasifikasikan sebagai One-to-Optional-One: setiap akun ' +
    'dapat memiliki paling banyak satu profil klinis, diikat melalui doctor_profiles.user_id ' +
    'dengan kendala UNIQUE yang mencegah profil duplikat. Kedua, relasi antara users dan ' +
    'analyses (kardinalitas 1:N) diklasifikasikan sebagai One-to-Many: satu dokter dapat ' +
    'memiliki banyak rekaman analisis, diwujudkan melalui analyses.user_id dengan kendala ' +
    'NOT NULL dan ON DELETE CASCADE sehingga penghapusan akun otomatis menghapus ' +
    'seluruh riwayat analisis terkait.'
  ));

  children.push(heading3('4.5.5 Arsitektur Penyimpanan dan Keamanan Data'));
  children.push(para(
    'Berkas citra medis disimpan secara fisik pada wadah penyimpanan objek cloud ' +
    '(Supabase Storage) bernama analysis-assets, bukan di dalam tabel relasional. ' +
    'Tabel analyses hanya menyimpan jalur relatif berkas. Saat pengguna mengakses ' +
    'antarmuka hasil, backend mengonversi jalur relatif menjadi Signed URL bertanda tangan ' +
    'aman dengan masa berlaku terbatas. Keamanan data ditegakkan pada tingkat mesin basis ' +
    'data menggunakan Row Level Security (RLS) dengan kebijakan USING (auth.uid() = user_id) ' +
    'yang memastikan setiap dokter hanya dapat mengakses data miliknya sendiri.'
  ));

  // ══════════════════════════════════════════════════════════════════════
  // SELESAI
  // ══════════════════════════════════════════════════════════════════════
  return children.filter(c => c !== null);
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log('Membangun konten Bab IV...');
  const allChildren = buildDoc();
  console.log(`Total elemen dokumen: ${allChildren.length}`);

  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: 'Times New Roman', size: 24 },
        },
      },
    },
    sections: [{
      properties: {
        page: {
          margin: {
            top:    convertInchesToTwip(1),
            right:  convertInchesToTwip(1),
            bottom: convertInchesToTwip(1),
            left:   convertInchesToTwip(1.5),
          },
        },
      },
      children: allChildren,
    }],
  });

  console.log('Menghasilkan file .docx...');
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT, buffer);
  const stat = fs.statSync(OUT);
  console.log(`\n✅ BERHASIL: ${OUT}`);
  console.log(`   Ukuran file: ${(stat.size / 1024).toFixed(1)} KB`);
  console.log(`   Total elemen: ${allChildren.length}`);
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});

