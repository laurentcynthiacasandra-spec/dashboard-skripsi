import os
import sys
import pandas as pd

# ================================================================
#  Argumen
# ================================================================
_args = sys.argv[1:]
_n = [a for a in _args if a.isdigit()]
_app = [a.lower() for a in _args if not a.isdigit()]
APP = _app[0] if _app else "semua"
if APP == "twitter":
    APP = "x"
N_UJI = int(_n[0]) if _n else 50000

# Jalankan semua aplikasi via subprocess
if APP in ("semua", "all"):
    import subprocess
    for _a in ("instagram", "tiktok", "x"):
        print(f"\n=== {_a.upper()} ===", flush=True)
        if subprocess.run([sys.executable, os.path.abspath(__file__), _a, str(N_UJI)]).returncode:
            sys.exit(f"Berhenti: {_a} gagal")
    sys.exit(0)

if APP not in ("instagram", "tiktok", "x"):
    sys.exit(f"Cara pakai: python {os.path.basename(__file__)} [instagram|tiktok|x] [jumlah_uji]")


# ================================================================
#  Leksikon InSet + Fungsi Pelabelan Hybrid
# ================================================================
NEGASI = {"tidak", "bukan", "jangan", "belum", "tak", "nggak", "gak", "ga", "tdk", "jgn"}


def muat_leksikon():
    """Baca file InSet TSV jadi dict kata → bobot sentimen."""
    pos, neg = {}, {}
    for nama, dic in [("inset_positive.tsv", pos), ("inset_negative.tsv", neg)]:
        with open(nama, encoding="utf-8") as f:
            next(f, None)
            for ln in f:
                parts = ln.strip().split("\t")
                if len(parts) == 2:
                    try:
                        dic[parts[0].lower()] = int(parts[1])
                    except ValueError:
                        pass
    return pos, neg


def label_hybrid(teks_bersih, rating, pos_lex, neg_lex):
    """Terapkan aturan hybrid pada satu ulasan. Return (label, sumber)."""
    tokens = teks_bersih.split() if isinstance(teks_bersih, str) else []
    skor = 0
    ada_kata_leksikon = False
    i = 0
    while i < len(tokens):
        w = tokens[i]
        negasi = (w in NEGASI) and (i + 1 < len(tokens))
        target = tokens[i + 1] if negasi else w
        if target in pos_lex:
            skor += (-pos_lex[target]) if negasi else pos_lex[target]
            ada_kata_leksikon = True
        elif target in neg_lex:
            skor += (-neg_lex[target]) if negasi else neg_lex[target]
            ada_kata_leksikon = True
        i += 2 if negasi else 1

    try:
        rating = int(rating)
    except Exception:
        rating = 0

    # Redistribusi Netral: TIDAK ADA label Netral di output
    if ada_kata_leksikon:
        if skor > 0 and rating >= 3:
            return "Positif", "leksikon"
        if skor < 0 and rating <= 3:
            return "Negatif", "leksikon"
        if rating >= 4:
            return "Positif", "rating"
        if rating <= 2:
            return "Negatif", "rating"
        if skor > 0:
            return "Positif", "netral→dekat positif"
        if skor < 0:
            return "Negatif", "netral→dekat negatif"
        return "Negatif", "netral→majority class"
    if rating >= 4:
        return "Positif", "rating"
    if rating <= 2:
        return "Negatif", "rating"
    return "Negatif", "netral→majority class"


# ================================================================
#  Main Processing
# ================================================================
pos_lex, neg_lex = muat_leksikon()
print(f"Leksikon dimuat: {len(pos_lex)} positif, {len(neg_lex)} negatif")

file_in = f"{APP}_6_stemming.csv"
if not os.path.exists(file_in):
    sys.exit(f"Berhenti: file {file_in} tidak ditemukan.")

df = pd.read_csv(file_in, keep_default_na=False)
df = df.head(N_UJI)
print(f"Memproses {len(df)} ulasan {APP}...")

# Cari kolom teks bersih — bisa 'stemming', 'stem', atau nama lain
kol_teks = None
for kol in ["clean_text", "stemming", "stem", "content_bersih", "normalisasi", "stopword"]:
    if kol in df.columns:
        kol_teks = kol
        break
if kol_teks is None:
    sys.exit(f"Berhenti: kolom teks tidak ditemukan. Kolom: {df.columns.tolist()}")
print(f"Pakai kolom teks: '{kol_teks}', kolom rating: 'score'")

labels, sources = [], []
for teks, rating in zip(df[kol_teks], df["score"]):
    lbl, src = label_hybrid(teks, rating, pos_lex, neg_lex)
    labels.append(lbl)
    sources.append(src)

df["label"] = labels
df["sumber_label"] = sources

file_out = f"{APP}_7_pelabelan.csv"
df.to_csv(file_out, index=False)

# Statistik
print("\nDistribusi label:")
print(df["label"].value_counts())
print(f"\nSumber label:")
print(df["sumber_label"].value_counts())

print(f"\nSELESAI {APP}: {len(df)} ulasan -> {file_out}")
print(f"Lanjut: python 08_tfidf_training.py")
