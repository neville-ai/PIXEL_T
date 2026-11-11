import os
import sys

from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# 1. LOAD ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    sys.exit("ERROR: SUPABASE_URL belum diisi pada Backend/.env")

if not SUPABASE_SERVICE_ROLE_KEY:
    sys.exit(
        "ERROR: SUPABASE_SERVICE_ROLE_KEY belum diisi pada Backend/.env"
    )


# ============================================================
# 2. INITIALIZE SUPABASE ADMIN CLIENT
# ============================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)


# ============================================================
# 3. SET ADMIN ROLE
# ============================================================

def set_admin_role(user_id: str):

    try:
        print("\nMengambil data akun dari Supabase...")

        response = supabase.auth.admin.get_user_by_id(user_id)
        user = response.user

        if user is None:
            raise RuntimeError("Akun tidak ditemukan.")

        print(f"Email ditemukan: {user.email}")

        # Pertahankan app_metadata yang sudah ada
        current_metadata = user.app_metadata or {}

        updated_metadata = {
            **current_metadata,
            "role": "admin"
        }

        print("Memperbarui app_metadata...")

        result = supabase.auth.admin.update_user_by_id(
            user_id,
            {
                "app_metadata": updated_metadata
            }
        )

        updated_user = result.user

        if updated_user is None:
            raise RuntimeError(
                "Supabase tidak mengembalikan data pengguna setelah update."
            )

        # Verifikasi role
        actual_role = (
            updated_user.app_metadata or {}
        ).get("role")

        if actual_role != "admin":
            raise RuntimeError(
                f"Verifikasi gagal. Role aktual: {actual_role}"
            )

        print("\n====================================")
        print("ROLE ADMIN BERHASIL DITETAPKAN")
        print("====================================")
        print(f"UID   : {updated_user.id}")
        print(f"Email : {updated_user.email}")
        print(f"Role  : {actual_role}")
        print("====================================")

    except Exception as error:
        print("\nGAGAL menetapkan role Admin.")
        print(f"Detail error: {error}")
        sys.exit(1)


# ============================================================
# 4. EXECUTION
# ============================================================

if __name__ == "__main__":

    print("PIXEL-T ADMIN ROLE CONFIGURATION")
    print("--------------------------------")

    user_id = input("Masukkan User UID akun Admin: ").strip()

    if not user_id:
        sys.exit("ERROR: User UID tidak boleh kosong.")

    confirmation = input(
        "\nApakah UID tersebut benar-benar akun Admin? (yes/no): "
    ).strip().lower()

    if confirmation == "yes":
        set_admin_role(user_id)
    else:
        print("Operasi dibatalkan.")