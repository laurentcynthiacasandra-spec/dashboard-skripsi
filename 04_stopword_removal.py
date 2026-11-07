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

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
DIPERTAHANKAN = NEGASI | {"bisa"}      # "bisa" penting: "tidak bisa login" (keluhan) vs "bisa login"
stop = set(StopWordRemoverFactory().get_stop_words()) - DIPERTAHANKAN
print(f"Stopword aktif: {len(stop)} kata (negasi dan 'bisa' dipertahankan)")
df = pd.read_csv(f"{APP}_4_normalisasi.csv", keep_default_na=False)
df["stopword"] = df["normalisasi"].map(lambda t: " ".join(w for w in str(t).split() if w not in stop))
df.to_csv(f"{APP}_5_stopword.csv", index=False)
contoh(df, "normalisasi", "stopword")
print(f"\nRata-rata token: {df.normalisasi.str.split().str.len().mean():.1f} -> {df.stopword.str.split().str.len().mean():.1f}")
print(f"SELESAI {APP}. Lanjut: python 04f_stemming.py {APP}")