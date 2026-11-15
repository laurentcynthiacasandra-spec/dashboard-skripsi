import os
import sys
import pandas as pd
import psycopg2
from sklearn.feature_extraction.text import CountVectorizer


def _get_db_url():
    try:
        import toml
        secrets = toml.load('.streamlit/secrets.toml')
        return secrets['DATABASE_URL']
    except Exception:
        url = os.environ.get('DATABASE_URL')
        if not url:
            print('ERROR: DATABASE_URL tidak ditemukan.')
            sys.exit(1)
        return url


KATA_NEGASI = {"tidak", "tdk", "enggak", "nggak", "ngga", "ga", "gak",
               "engga", "kagak", "belum", "jangan", "bukan", "tak",
               "dk", "kga", "kaga", "enggaa"}

NEGATIVE_INDICATORS = {"tidak", "jangan", "bukan", "belum", "susah", "sulit",
                       "tolong", "mohon", "perbaiki", "kenapa", "parah"}

BLACKLIST_SAMPLE_PUJIAN = {
    # Negasi
    "tidak", "tdk", "enggak", "nggak", "ngga", "ga", "gak", "engga", "kagak",
    "dk", "tak", "kga", "kaga", "enggaa", "enggaak", "gada", "gaada", "gpp",
    # Negatif adjektif
    "jelek", "jorok", "buruk", "parah", "sampah", "boong", "bohong",
    "ancur", "hancur", "kacau",
    "ngelek", "ngeleg", "ngelag", "ngbug", "lelet", "lemot", "lambat",
    "kurang", "minus", "sepi", "aneh",
    # Kata complaint
    "keluh", "bug", "bugs", "error", "lag", "susah", "sulit", "gagal",
    "masalah", "perbaiki", "mohon", "tolong", "kenapa", "mending",
    "blokir", "banned", "suspend", "tangguh", "sb", "hapus", "hilang",
    "benci", "males", "malas", "bosen", "bosan",
    "sering", "jarang", "lama", "kadang",
    "cuma", "tapi", "padahal", "sayang",
    "gajadi", "bom", "capek", "cape",
    # NSFW
    "bokep", "porno", "porn", "ngentot", "memek", "kontol", "jembut",
    "titit", "toket", "tete", "pepek",
    # Swear
    "anjing", "anjir", "bangsat", "kampret", "goblok", "tolol", "bajingan",
    "setan", "iblis", "pantek", "babi", "asu",
}

BLACKLIST_SAMPLE_UNIVERSAL = {
    "bokep", "porno", "porn", "ngentot", "memek", "kontol", "jembut",
    "titit", "toket", "tete", "pepek",
    "anjing", "anjir", "bangsat", "kampret", "goblok", "tolol", "bajingan",
    "setan", "iblis", "pantek", "babi", "asu",
    # Slang kasar / edgy (variant anj*)
    "anjay", "anjayy", "anjaay", "anjrit", "anjrot", "njir", "njay",
}

# Bahasa asing — sesuai batasan thesis (hanya Bahasa Indonesia)
# Kata ini akan menyebabkan bigram/sample di-reject
BLACKLIST_FOREIGN = {
    # English — artikel, pronoun, be-verb, preposition
    "the", "a", "an", "is", "are", "am", "was", "were", "be", "been", "being",
    "i", "you", "he", "she", "it", "we", "they",
    "my", "your", "his", "her", "its", "our", "their",
    "me", "us", "him", "them", "myself", "yourself",
    "this", "that", "these", "those",
    "and", "or", "but", "so", "if", "then", "when", "while", "because",
    "of", "to", "in", "on", "at", "by", "with", "from", "for",
    "about", "into", "through", "between", "after", "before",
    # English — verb umum
    "have", "has", "had", "do", "does", "did", "doing", "done",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "go", "goes", "going", "went", "come", "comes", "came",
    "get", "gets", "got", "make", "makes", "made",
    "know", "knows", "knew", "think", "thinks", "thought",
    "love", "loves", "loved", "like", "likes", "liked",
    "want", "wants", "wanted", "need", "needs", "needed",
    "give", "giving", "gave", "take", "takes", "took",
    "see", "sees", "saw", "look", "looks", "looked",
    "feel", "feels", "felt", "find", "finds", "found",
    "forget", "forgot", "remember",
    # English — adjektif umum
    "good", "great", "nice", "best", "better", "cool", "awesome", "amazing",
    "very", "really", "much", "many", "more", "most", "less", "few",
    "always", "never", "sometimes", "often", "usually",
    "please", "sorry", "thanks", "thank", "welcome",
    "yes", "no", "not", "yeah", "yep", "nope",
    # English — noun umum
    "world", "life", "day", "time", "year", "years", "hour", "month",
    "people", "person", "friend", "family",
    "thing", "things", "something", "anything", "everything", "nothing",
    "everyone", "anyone", "someone", "noone",
    # English — misc / internet lingo
    "don", "doesn", "won", "couldn", "wouldn", "shouldn", "isn", "aren",
    "zuck", "elon", "guys", "bro", "sis", "dude",
    # Japanese
    "arigatou", "gozaimasu", "sayonara", "konnichiwa", "ohayou",
    "sugoi", "kawaii", "senpai", "sensei", "chan", "kun", "san",
    "watashi", "anata", "boku", "ore",
    # Korean
    "annyeong", "saranghae", "oppa", "unnie", "noona", "hyung",
    "daebak", "aegyo", "fighting",
    # Spanish / French common
    "hola", "amigo", "amiga", "gracias",
    "bonjour", "merci", "oui",
}

STOPWORD_BIGRAM = {
    "saya tidak", "saya ga", "saya gak", "saya enggak",
    "tolong dong", "kak tolong", "mohon tolong",
    "aplikasi nya", "nya dong", "nya kak", "nya saja",
    "kenapa ya", "kenapa sih", "apa sih", "ini sih",
    "apakah bisa", "bagaimana cara", "cara menggunakan",
    "tapi kalo", "tapi ketika", "kalau sudah",
    "di atas", "ke bawah", "pada saat", "pada waktu",
    "aku mau", "saya mau", "ingin saya",
    "sama aja", "sama saja", "udah lama", "sudah lama",
}

STOPWORD_BIGRAM_PUJIAN = {
    "bisa buka", "bisa login", "bisa pakai", "bisa dibuka", "bisa dipakai",
    "akun tangguh", "kasih bintang", "kasih rating", "ada bug", "sering error",
    "aplikasi instagram", "aplikasi tiktok", "aplikasi twitter", "aplikasi facebook",
    "tik tok", "nya bagus", "nya bisa", "nya kurang",
    "bintang satu", "bintang lima", "bintang dua",
}


def normalize_negasi(teks: str) -> str:
    tokens = teks.split()
    hasil = []
    for t in tokens:
        if t.lower() in KATA_NEGASI:
            hasil.append("tidak")
        else:
            hasil.append(t.lower())
    return " ".join(hasil)


def tokens_bersih(teks: str):
    out = []
    for w in teks.lower().split():
        kata = ''.join(c for c in w if c.isalpha())
        if kata:
            out.append(kata)
    return out


def is_pujian_bigram_valid(frasa: str) -> bool:
    kata = frasa.split()
    for k in kata:
        if k in NEGATIVE_INDICATORS:
            return False
        if k in BLACKLIST_SAMPLE_PUJIAN:
            return False
        if k in BLACKLIST_FOREIGN:
            return False
    if frasa in STOPWORD_BIGRAM_PUJIAN:
        return False
    return True


def is_keluhan_bigram_valid(frasa: str) -> bool:
    """Bigram Keluhan tetap valid asal tidak full bahasa asing."""
    kata = frasa.split()
    foreign_count = sum(1 for k in kata if k in BLACKLIST_FOREIGN)
    # Kalau SEMUA kata dalam bigram adalah bhs asing → reject
    if foreign_count == len(kata):
        return False
    return True


def is_clean_pujian_sample(teks: str) -> bool:
    for k in tokens_bersih(teks):
        if k in BLACKLIST_SAMPLE_PUJIAN:
            return False
        if k in BLACKLIST_FOREIGN:
            return False
    return True


def is_safe_universal(teks: str) -> bool:
    """Untuk Keluhan: reject NSFW/swear, dan reject kalau >40% kata bhs asing."""
    kata_list = tokens_bersih(teks)
    for k in kata_list:
        if k in BLACKLIST_SAMPLE_UNIVERSAL:
            return False
    if kata_list:
        foreign_count = sum(1 for k in kata_list if k in BLACKLIST_FOREIGN)
        if foreign_count / len(kata_list) > 0.4:
            return False
    return True


def get_columns(conn, table_name):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """, (table_name,)
    )
    rows = cur.fetchall()
    cur.close()
    return [r[0] for r in rows]


def generate_bigram(df_sub, label, cap=20):
    """Generate daftar bigram (sampai `cap` buah) utk satu (app, label)."""
    teks_norm = df_sub["teks"].astype(str).str.lower().apply(normalize_negasi).tolist()
    teks_asli = df_sub["teks"].astype(str).tolist()

    vec = CountVectorizer(
        ngram_range=(2, 2),
        min_df=5,
        max_features=3000,
        token_pattern=r"[A-Za-z]{3,}",
    )
    X = vec.fit_transform(teks_norm)
    import numpy as np
    counts = np.asarray(X.sum(axis=0)).flatten()
    names = vec.get_feature_names_out()

    valid_idx = []
    for i, nm in enumerate(names):
        if nm in STOPWORD_BIGRAM:
            continue
        if label == "Pujian" and not is_pujian_bigram_valid(nm):
            continue
        if label == "Keluhan" and not is_keluhan_bigram_valid(nm):
            continue
        valid_idx.append(i)

    sorted_idx = sorted(valid_idx, key=lambda i: -counts[i])

    hasil = []
    for i in sorted_idx:
        if len(hasil) >= cap:
            break
        frasa = names[i]
        jumlah = int(counts[i])

        kandidat = [j for j, t in enumerate(teks_norm) if frasa in t]
        if label == "Pujian":
            kandidat_bersih = [j for j in kandidat if is_clean_pujian_sample(teks_asli[j])]
        else:
            kandidat_bersih = [j for j in kandidat if is_safe_universal(teks_asli[j])]

        if len(kandidat_bersih) < 3:
            continue

        kandidat_bersih.sort(key=lambda j: abs(len(teks_asli[j]) - 70))
        sampel_asli = []
        for j in kandidat_bersih[:3]:
            t = str(teks_asli[j])
            if len(t) > 150:
                t = t[:150] + "..."
            sampel_asli.append(t)

        hasil.append({
            "frasa": frasa,
            "jumlah": jumlah,
            "sampel": " || ".join(sampel_asli),
        })
    return hasil


def main():
    db_url = _get_db_url()
    print(f'[1/5] Connecting to database...')
    conn = psycopg2.connect(db_url, sslmode="require")

    print('[2/5] Cek struktur tabel...')
    try:
        kol_ulasan = get_columns(conn, "ulasan")
        kol_fact = get_columns(conn, "fact_sentimen")
        print(f'    Tabel ulasan: {kol_ulasan}')
        print(f'    Tabel fact_sentimen: {kol_fact}')
    except Exception as e:
        print(f'    WARNING: {e}')
        kol_ulasan = []
        kol_fact = []

    kol_teks = None
    for k in ["content_bersih", "content", "teks_bersih", "teks", "text", "review", "ulasan"]:
        if k in kol_ulasan:
            kol_teks = k
            break
    print(f'    → Pakai kolom teks: {kol_teks}')

    kol_rating = None
    rating_table = None
    for k in ["score", "skor_rating", "rating", "nilai_rating"]:
        if k in kol_fact:
            kol_rating = k
            rating_table = "f"
            break
    if not kol_rating:
        for k in ["score", "skor_rating", "rating", "nilai_rating"]:
            if k in kol_ulasan:
                kol_rating = k
                rating_table = "u"
                break
    print(f'    → Pakai kolom rating: {kol_rating} (tabel: {rating_table})')

    if not kol_teks or not kol_rating:
        print('ERROR: Kolom tidak lengkap')
        sys.exit(1)

    print('[3/5] Query data...')
    rating_ref = f"{rating_table}.{kol_rating}"
    query = f"""
        SELECT u.{kol_teks} AS teks,
               a.nama_aplikasi AS aplikasi,
               {rating_ref} AS rating
        FROM ulasan u
        JOIN fact_sentimen f ON f.id_ulasan = u.id_ulasan
        JOIN dim_aplikasi a ON a.id_aplikasi = f.id_aplikasi
        WHERE u.{kol_teks} IS NOT NULL
          AND LENGTH(u.{kol_teks}) > 5
          AND {rating_ref} IN (1, 2, 4, 5)
        GROUP BY u.{kol_teks}, a.nama_aplikasi, {rating_ref}
    """
    try:
        df_all = pd.read_sql(query, conn)
    except Exception as e:
        print(f'ERROR QUERY: {e}')
        sys.exit(1)

    df_all["label"] = df_all["rating"].apply(
        lambda r: "Pujian" if int(r) >= 4 else "Keluhan"
    )
    print(f'    Total: {len(df_all):,} | Keluhan: {(df_all["label"] == "Keluhan").sum():,} | Pujian: {(df_all["label"] == "Pujian").sum():,}')

    # === Generate + Dedupe + Rank ===
    print('[4/5] Generate bigram per aplikasi (dengan dedupe)...')
    hasil = []
    aplikasi_list = sorted(df_all["aplikasi"].unique())

    for app in aplikasi_list:
        print(f'\n  🔹 {app}:')
        dfK = df_all[(df_all["aplikasi"] == app) & (df_all["label"] == "Keluhan")]
        dfP = df_all[(df_all["aplikasi"] == app) & (df_all["label"] == "Pujian")]

        # Generate top 20 per kategori (lebih banyak dari 10 utk cadangan setelah dedupe)
        try:
            pool_keluhan = generate_bigram(dfK, "Keluhan", cap=20) if not dfK.empty else []
            print(f'      Keluhan generate: {len(pool_keluhan)} bigram')
        except Exception as e:
            pool_keluhan = []
            print(f'      ✗ Keluhan: {e}')

        try:
            pool_pujian = generate_bigram(dfP, "Pujian", cap=20) if not dfP.empty else []
            print(f'      Pujian generate:  {len(pool_pujian)} bigram')
        except Exception as e:
            pool_pujian = []
            print(f'      ✗ Pujian: {e}')

        # === DEDUPE: cari bigram yg muncul di kedua kategori ===
        map_keluhan = {h["frasa"]: h for h in pool_keluhan}
        map_pujian = {h["frasa"]: h for h in pool_pujian}
        duplikat = set(map_keluhan.keys()) & set(map_pujian.keys())

        if duplikat:
            print(f'      Duplikat terdeteksi: {len(duplikat)} bigram → simpan di kategori dgn count tertinggi')
            for frasa in duplikat:
                cnt_k = map_keluhan[frasa]["jumlah"]
                cnt_p = map_pujian[frasa]["jumlah"]
                if cnt_k >= cnt_p:
                    # Keluhan menang → hapus dari Pujian
                    pool_pujian = [h for h in pool_pujian if h["frasa"] != frasa]
                    print(f'        • "{frasa}": Keluhan={cnt_k} vs Pujian={cnt_p} → simpan di Keluhan')
                else:
                    pool_keluhan = [h for h in pool_keluhan if h["frasa"] != frasa]
                    print(f'        • "{frasa}": Keluhan={cnt_k} vs Pujian={cnt_p} → simpan di Pujian')

        # === Ambil top 10, re-rank ===
        pool_keluhan.sort(key=lambda h: -h["jumlah"])
        pool_pujian.sort(key=lambda h: -h["jumlah"])

        for rank, h in enumerate(pool_keluhan[:10], 1):
            hasil.append({
                "aplikasi": app, "label": "Negatif", "rank": rank,
                "frasa": h["frasa"], "jumlah": h["jumlah"], "sampel": h["sampel"],
            })
        for rank, h in enumerate(pool_pujian[:10], 1):
            hasil.append({
                "aplikasi": app, "label": "Positif", "rank": rank,
                "frasa": h["frasa"], "jumlah": h["jumlah"], "sampel": h["sampel"],
            })
        print(f'      ✓ Final: Keluhan={min(10, len(pool_keluhan))}, Pujian={min(10, len(pool_pujian))}')

    print('\n[5/5] Menyimpan hasil...')
    df_hasil = pd.DataFrame(hasil)
    output_path = 'pipeline/keluhan_pujian.csv'
    df_hasil.to_csv(output_path, index=False)
    print(f'\n✓ Hasil disimpan: {output_path}')
    print(f'  Total {len(df_hasil)} baris\n')

    print(f'  Preview Top 5 per aplikasi:')
    for app in aplikasi_list:
        for label_db in ["Positif", "Negatif"]:
            label_tampil = "Pujian" if label_db == "Positif" else "Keluhan"
            sub = df_hasil[(df_hasil["aplikasi"] == app) & (df_hasil["label"] == label_db)].head(5)
            if not sub.empty:
                print(f'  • {app} {label_tampil}: {", ".join(sub["frasa"].tolist())}')

    conn.close()


if __name__ == '__main__':
    main()