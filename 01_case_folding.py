import sys, os, re, time
import pandas as pd
_args = sys.argv[1:]
_n = [a for a in _args if a.isdigit()]                       # angka = jumlah ulasan uji kecil (opsional)
_app = [a.lower() for a in _args if not a.isdigit()]
APP = _app[0] if _app else "semua"                           # tanpa nama aplikasi = ketiganya
if APP == "twitter": APP = "x"          # nama aplikasi sekarang "X" (data dikumpulkan setelah rebranding)
N_UJI = int(_n[0]) if _n else None      # contoh: 500 = uji kecil; kosong = data penuh
if APP in ("semua", "all"):
    import subprocess
    for _a in ("instagram", "tiktok", "x"):
        print("\n=== %s ===" % _a.upper(), flush=True)
        if subprocess.run([sys.executable, os.path.abspath(__file__), _a] + _n).returncode:
            sys.exit("Berhenti: %s gagal" % _a)
    sys.exit(0)
if APP not in ("instagram", "tiktok", "x"):
    sys.exit("Cara pakai: python %s [instagram|tiktok|x] [jumlah_uji]   (tanpa nama aplikasi = ketiganya)" % os.path.basename(__file__))
NEGASI = {"tidak", "tak", "bukan", "belum", "jangan", "tanpa", "kurang", "enggak", "nggak",
          "gak", "ga", "tdk", "blm", "engga", "ngga"}      # kata negasi: JANGAN dihapus
DILINDUNGI = {"x", "tiktok", "instagram", "ig", "tt", "twitter",          # nama aplikasi
              "in", "it", "to", "is", "on", "at", "an", "no", "so", "of", "me", "my", "we", "he", "be",
              "do", "up", "if", "or", "as", "by", "us", "go", "ok", "app", "the", "and", "for", "you"}   # kata Inggris umum: jangan dianggap slang
def contoh(df, kol_awal, kol_akhir, n=4):
    print("\nCONTOH (sebelum -> sesudah):")
    for a, b in list(zip(df[kol_awal], df[kol_akhir]))[:n]:
        print("  -", str(a)[:80], "\n    =>", str(b)[:80])

cands = [f"{APP}_reviews_50000.xlsx"] + (["twitter_reviews_50000.xlsx"] if APP == "x" else [])
fin = next((c for c in cands if os.path.exists(c)), None)
if not fin: sys.exit("File Excel tidak ditemukan: " + " / ".join(cands))
df = pd.read_excel(fin, nrows=N_UJI)
df.insert(0, "review_id", range(1, len(df) + 1))
df = df[["review_id", "at", "content", "score"]].copy()
df["text_case_folding"] = df["content"].map(lambda t: str(t).lower())     # case folding
df.to_csv(f"{APP}_1_case_folding.csv", index=False)
contoh(df, "content", "text_case_folding")
print(f"\nSELESAI {APP}: {len(df)} ulasan -> {APP}_1_case_folding.csv. Lanjut: python 04b_cleaning.py {APP}")