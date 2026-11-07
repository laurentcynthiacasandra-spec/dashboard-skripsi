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

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
stemmer = StemmerFactory().create_stemmer()
df = pd.read_csv(f"{APP}_5_stopword.csv", keep_default_na=False)
vocab = sorted({w for t in df["stopword"] for w in str(t).split()})
print(f"Kata unik yang di-stem: {len(vocab)}"); t0 = time.time(); peta = {}
for i, w in enumerate(vocab, 1):
    peta[w] = stemmer.stem(w)
    if i % 5000 == 0: print(f"   ...{i}/{len(vocab)} ({time.time()-t0:.0f} dtk)", flush=True)
df["clean_text"] = df["stopword"].map(lambda t: " ".join(peta[w] for w in str(t).split()))
df.to_csv(f"{APP}_6_stemming.csv", index=False)
contoh(df, "stopword", "clean_text")
print(f"\nSELESAI {APP} dalam {(time.time()-t0)/60:.1f} menit. Lanjut: python 04g_pelabelan.py {APP}")