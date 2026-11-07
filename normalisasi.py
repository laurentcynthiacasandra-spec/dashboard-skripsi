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

import urllib.request
from collections import Counter
pos = pd.read_csv("inset_positive.tsv", sep="\t"); neg = pd.read_csv("inset_negative.tsv", sep="\t")
inset = set(pos["word"]) | set(neg["word"])
if not os.path.exists("kamus_alay.csv"):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/nasalsabila/kamus-alay/master/colloquial-indonesian-lexicon.csv", "kamus_alay.csv")
k = pd.read_csv("kamus_alay.csv"); k = k[(k.slang != k.formal) & (k.slang.str.len() > 1)]
kamus = {}
for s, f in zip(k.slang.str.lower(), k.formal.str.lower()):
    if s in DILINDUNGI or s in inset: continue
    kamus.setdefault(s, f)
# KAMUS TAMBAHAN (domain ulasan aplikasi) + KOREKSI entri kamus umum yang salah. Isinya menimpa kamus umum.
KAMUS_TAMBAHAN = {"apk": "aplikasi", "ig": "instagram", "tt": "tiktok", "ngapain": "mengapa", "klo": "kalau", "kalo": "kalau",
                  "kaga": "tidak", "kagak": "tidak", "si": "si", "benerin": "perbaiki", "perbaikin": "perbaiki",
                  "ngebug": "bug", "ngelag": "lag", "gbs": "enggak bisa", "gabs": "enggak bisa", "dpt": "dapat",
                  "sll": "selalu", "trus": "terus", "bs": "bisa", "bsa": "bisa", "gada": "enggak ada", "ngga": "enggak",
                  "terimakasih": "terima kasih", "makasih": "terima kasih", "mksh": "terima kasih",
                  "dgn": "dengan", "utk": "untuk", "tlg": "tolong", "tolongin": "tolong", "bagusss": "bagus"}
kamus.update(KAMUS_TAMBAHAN)
print(f"Kamus normalisasi aktif: {len(kamus)} entri (termasuk {len(KAMUS_TAMBAHAN)} entri tambahan domain)")
df = pd.read_csv(f"{APP}_3_tokenizing.csv", keep_default_na=False)
diubah = Counter(); n_ulasan_berubah = 0; hasil = []
for t in df["tokens"]:
    out = []; ada = False
    for w in str(t).split():
        b = kamus.get(w, w)
        if b != w: diubah[(w, b)] += 1; ada = True
        out.append(b)
    n_ulasan_berubah += ada; hasil.append(" ".join(out))
df["normalisasi"] = hasil
df.to_csv(f"{APP}_4_normalisasi.csv", index=False)
pd.DataFrame([(a, b, c) for (a, b), c in diubah.most_common(300)], columns=["kata_asli", "kata_baku", "jumlah"]).to_csv(f"normalisasi_{APP}_contoh.csv", index=False)
contoh(df, "tokens", "normalisasi")
print("\n15 perubahan terbanyak:", [(a, b, c) for (a, b), c in diubah.most_common(15)])
print(f"Ulasan yang berubah: {n_ulasan_berubah}/{len(df)} ({n_ulasan_berubah/len(df)*100:.1f}%)")
print(f"SELESAI {APP}. Lanjut: python 04e_stopword.py {APP}")