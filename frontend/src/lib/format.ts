import type { User } from '@supabase/supabase-js';

/**
 * Bulan pendek bahasa Indonesia, dipakai agar format tanggal pada kartu
 * dashboard sama persis dengan referensi desain (`2 Okt 2026, 14:20`).
 * `toLocaleString('id-ID')` tidak dipakai karena resultasinya memisahkan
 * jam dengan titik (`14.20`), bukan titik dua seperti pada referensi.
 */
const ID_MONTHS_SHORT = [
  'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
] as const;

function pad2(value: number): string {
  return value.toString().padStart(2, '0');
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/**
 * Format tanggal analisis mengikuti referensi dashboard:
 * - hari ini  -> `Hari ini, 09:15`
 * - lainnya   -> `2 Okt 2026, 14:20`
 *
 * Nilai tidak valid / kosong dikembalikan `-` (konsisten dengan History).
 * `now` hanya disuntikkan agar mudah diuji.
 */
export function formatAnalysisDate(value: string | null, now: Date = new Date()): string {
  if (!value) return '-';

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  const time = `${pad2(parsed.getHours())}:${pad2(parsed.getMinutes())}`;

  if (isSameDay(parsed, now)) {
    return `Hari ini, ${time}`;
  }

  const month = ID_MONTHS_SHORT[parsed.getMonth()] ?? '';
  return `${parsed.getDate()} ${month} ${parsed.getFullYear()}, ${time}`;
}

/**
 * Nama tampilan pengguna yang sepenuhnya diturunkan dari data autentikasi
 * Supabase yang nyata:
 * 1. `user_metadata.full_name` (diisi saat registrasi), bila ada dan tidak
 *    kosong;
 * 2. selain itu alamat email;
 * 3. selain itu string kosong (konsumen harus menangani fallback sendiri).
 *
 * Nama klinis tidak pernah di-hardcode di sini maupun di komponen mana pun.
 */
export function getDisplayName(user: Pick<User, 'user_metadata' | 'email'> | null): string {
  if (!user) return '';

  const fullName = user.user_metadata?.full_name;
  if (typeof fullName === 'string' && fullName.trim().length > 0) {
    return fullName.trim();
  }

  return typeof user.email === 'string' && user.email.length > 0 ? user.email : '';
}

/**
 * Inisial untuk avatar bulat pada header.
 * - dua kata atau lebih -> huruf pertama kata pertama + kata terakhir;
 * - satu kata          -> dua huruf pertama.
 */
export function getUserInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '';
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
}
