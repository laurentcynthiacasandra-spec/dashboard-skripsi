"""Force close semua koneksi ke DB sentimen, lalu TRUNCATE tabel."""
import psycopg2

# Step 1: Connect ke database 'postgres' (bukan 'sentimen') untuk bisa force close koneksi lain
print("Step 1: Force close koneksi ke DB sentimen...")
conn = psycopg2.connect("postgresql://postgres:admin123@localhost:5432/postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'sentimen' AND pid != pg_backend_pid()
""")
jumlah = cur.rowcount
print(f"  {jumlah} koneksi aktif di-close paksa")
conn.close()

# Step 2: Connect ke sentimen dan TRUNCATE
print("\nStep 2: TRUNCATE tabel...")
conn = psycopg2.connect("postgresql://postgres:admin123@localhost:5432/sentimen")
cur = conn.cursor()
cur.execute("TRUNCATE fact_sentimen, ulasan, dim_waktu RESTART IDENTITY CASCADE")
conn.commit()
print("  OK, 3 tabel sudah kosong")
conn.close()

print("\n✓ Database siap untuk di-populate ulang.")
print("Sekarang jalankan: python update_db_dari_pipeline.py")
