import os
import sys
import pandas as pd

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: pip install psycopg2-binary")
    sys.exit(1)

try:
    import joblib
except ImportError:
    print("ERROR: pip install joblib")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: environment variable DATABASE_URL belum di-set.")
    print("Jalankan: $env:DATABASE_URL = \"postgresql://postgres:admin123@localhost:5432/sentimen\"")
    sys.exit(1)

# Koneksi (auto detect local vs cloud)
is_local = "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL
conn_kwargs = {} if is_local else {"sslmode": "require"}
print(f"Menghubungkan ke {'LOCAL' if is_local else 'CLOUD'} PostgreSQL ...")
conn = psycopg2.connect(DATABASE_URL, **conn_kwargs)
conn.autocommit = False
print("Terhubung.\n")

APPS = [
    ("instagram", 1),
    ("tiktok", 2),
    ("x", 3),
]

# Model IDs di DB: 1 = Naive Bayes, 2 = SVM
NB_MODEL_ID = 1
SVM_MODEL_ID = 2

# Sentimen IDs di DB: 1 = Positif, 2 = Negatif, 3 = Netral
LABEL_TO_ID = {"Positif": 1, "Negatif": 2, "Netral": 3}


def hapus_data_lama(cur):
    """Hapus semua data (urutan sesuai FK)."""
    print("Menghapus data lama...")
    cur.execute("DELETE FROM fact_sentimen")
    cur.execute("DELETE FROM ulasan")
    cur.execute("DELETE FROM dim_waktu")
    print("  OK")


def isi_dim_waktu(cur, semua_tanggal):
    """Isi dim_waktu dari set tanggal unik (schema: id_waktu, tanggal, bulan, tahun)."""
    print(f"\nIsi dim_waktu ({len(semua_tanggal)} tanggal unik)...")
    tanggal_to_id = {}
    for i, tgl in enumerate(sorted(semua_tanggal), start=1):
        tanggal_to_id[tgl] = i
    rows = [(idx, tgl, tgl.month, tgl.year) for tgl, idx in tanggal_to_id.items()]
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO dim_waktu (id_waktu, tanggal, bulan, tahun) VALUES (%s, %s, %s, %s)",
        rows, page_size=500)
    print(f"  OK, {len(rows)} baris")
    return tanggal_to_id


def proses_aplikasi(app_name, app_id, tanggal_to_id, id_ulasan_mulai):
    """Baca CSV + predict dengan model. Return list ulasan + list fact."""
    print(f"\n=== {app_name.upper()} (id_aplikasi={app_id}) ===")
    berkas = f"{app_name}_7_pelabelan.csv"
    if not os.path.exists(berkas):
        print(f"  Lewati: {berkas} tidak ada")
        return [], [], id_ulasan_mulai, set()

    df = pd.read_csv(berkas, keep_default_na=False)
    df = df[df["clean_text"].astype(str).str.len() > 0].reset_index(drop=True)
    print(f"  Load {len(df):,} ulasan dari {berkas}".replace(",", "."))

    model_path = f"model_{app_name}.joblib"
    if not os.path.exists(model_path):
        print(f"  WARNING: {model_path} tidak ada, prediksi di-skip")
        nb_pred = ["Negatif"] * len(df)
        svm_pred = ["Negatif"] * len(df)
    else:
        paket = joblib.load(model_path)
        vec = paket["vectorizer"]
        X_vec = vec.transform(df["clean_text"].astype(str))
        nb_pred = paket["nb"].predict(X_vec)
        svm_pred = paket["svm"].predict(X_vec)
        print(f"  Prediksi NB & SVM selesai")

    ulasan_rows = []
    fact_rows = []
    tanggal_set = set()

    for i, row in df.iterrows():
        id_ulasan = id_ulasan_mulai + i
        content = str(row.get("content", ""))[:1000]
        try:
            score = int(row.get("score", 0))
        except Exception:
            score = 0
        at_str = str(row.get("at", ""))[:19]
        try:
            at_date = pd.to_datetime(at_str).date()
        except Exception:
            at_date = pd.Timestamp("2026-01-01").date()
        tanggal_set.add(at_date)
        clean_text = str(row.get("clean_text", ""))[:1000]

        id_waktu = tanggal_to_id.get(at_date, 1)

        ulasan_rows.append((id_ulasan, content, score, at_date, clean_text))

        actual_label = str(row.get("label", "Negatif"))
        actual_id = LABEL_TO_ID.get(actual_label, 2)

        nb_id = LABEL_TO_ID.get(nb_pred[i], 2)
        svm_id = LABEL_TO_ID.get(svm_pred[i], 2)

        # Fact NB: id_sentimen = actual, id_sentimen_prediksi = NB
        fact_rows.append((id_ulasan, app_id, id_waktu, NB_MODEL_ID,
                          actual_id, nb_id, actual_id == nb_id, False))
        # Fact SVM
        fact_rows.append((id_ulasan, app_id, id_waktu, SVM_MODEL_ID,
                          actual_id, svm_id, actual_id == svm_id, False))

    print(f"  {len(ulasan_rows):,} ulasan, {len(fact_rows):,} fact rows".replace(",", "."))
    return ulasan_rows, fact_rows, id_ulasan_mulai + len(df), tanggal_set


def main():
    cur = conn.cursor()

    # Phase 1: kumpulkan semua tanggal unik dulu (untuk dim_waktu)
    print("Phase 1: Scan tanggal unik di semua CSV...")
    semua_tanggal = set()
    for app_name, _ in APPS:
        berkas = f"{app_name}_7_pelabelan.csv"
        if not os.path.exists(berkas):
            continue
        df = pd.read_csv(berkas, keep_default_na=False, usecols=["at"])
        for at_str in df["at"].astype(str):
            try:
                tgl = pd.to_datetime(at_str[:19]).date()
                semua_tanggal.add(tgl)
            except Exception:
                pass
    print(f"  Ditemukan {len(semua_tanggal)} tanggal unik")

    # Phase 2: hapus data lama + isi dim_waktu
    hapus_data_lama(cur)
    tanggal_to_id = isi_dim_waktu(cur, semua_tanggal)

    # Phase 3: proses per aplikasi
    print("\nPhase 3: Proses per aplikasi...")
    all_ulasan = []
    all_fact = []
    id_ulasan_next = 1
    for app_name, app_id in APPS:
        ulasan_rows, fact_rows, id_ulasan_next, _ = proses_aplikasi(
            app_name, app_id, tanggal_to_id, id_ulasan_next
        )
        all_ulasan.extend(ulasan_rows)
        all_fact.extend(fact_rows)

    # Phase 4: insert ke DB
    print(f"\nPhase 4: Insert ke DB...")
    print(f"  Insert {len(all_ulasan):,} ulasan ...".replace(",", "."), end=" ", flush=True)
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO ulasan (id_ulasan, content, score, at_date, content_bersih) "
        "VALUES (%s, %s, %s, %s, %s)",
        all_ulasan, page_size=1000)
    print("OK")

    print(f"  Insert {len(all_fact):,} fact_sentimen ...".replace(",", "."), end=" ", flush=True)
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO fact_sentimen "
        "(id_ulasan, id_aplikasi, id_waktu, id_model, id_sentimen, id_sentimen_prediksi, prediksi_benar, data_uji) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        all_fact, page_size=1000)
    print("OK")

    # Reset sequence
    cur.execute("SELECT setval(pg_get_serial_sequence('ulasan','id_ulasan'), (SELECT MAX(id_ulasan) FROM ulasan))")
    cur.execute("SELECT setval(pg_get_serial_sequence('fact_sentimen','id_fact'), (SELECT MAX(id_fact) FROM fact_sentimen))")
    cur.execute("SELECT setval(pg_get_serial_sequence('dim_waktu','id_waktu'), (SELECT MAX(id_waktu) FROM dim_waktu))")

    conn.commit()
    print("\nCommit berhasil.")

    # Verifikasi
    print("\nVerifikasi:")
    for tabel in ["ulasan", "fact_sentimen", "dim_waktu", "dim_aplikasi", "dim_sentimen", "dim_model"]:
        cur.execute(f"SELECT COUNT(*) FROM {tabel}")
        n = cur.fetchone()[0]
        print(f"  {tabel:20s}: {n:>8,}".replace(",", "."))

    # Distribusi sentimen (Positif vs Negatif)
    cur.execute("""
        SELECT a.nama_aplikasi, s.label_sentimen, COUNT(*) AS jumlah
        FROM fact_sentimen f
        JOIN dim_aplikasi a ON a.id_aplikasi = f.id_aplikasi
        JOIN dim_sentimen s ON s.id_sentimen = f.id_sentimen
        JOIN dim_model m ON m.id_model = f.id_model
        WHERE m.nama_model LIKE '%Naive%'
        GROUP BY a.nama_aplikasi, s.label_sentimen
        ORDER BY a.nama_aplikasi, s.label_sentimen
    """)
    print("\nDistribusi Pelabelan Hybrid (actual) per aplikasi:")
    for row in cur.fetchall():
        print(f"  {row[0]:12s} {row[1]:10s} : {row[2]:>8,}".replace(",", "."))

    conn.close()
    print("\n✓ SELESAI. Dashboard otomatis sync dengan DB baru.")


if __name__ == "__main__":
    main()