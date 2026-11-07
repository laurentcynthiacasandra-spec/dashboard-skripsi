import os

NEGASI = {"tidak", "bukan", "jangan", "belum", "tak", "nggak", "gak", "ga", "tdk", "jgn"}


def muat_leksikon(folder_data: str = "data") -> tuple:
    """Baca file TSV InSet jadi dua dict: positif, negatif."""
    pos, neg = {}, {}
    pos_path = os.path.join(folder_data, "inset_positive.tsv")
    neg_path = os.path.join(folder_data, "inset_negative.tsv")
    with open(pos_path, encoding="utf-8") as f:
        next(f, None)  # skip header "word\tweight"
        for ln in f:
            parts = ln.strip().split("\t")
            if len(parts) == 2:
                try: pos[parts[0].lower()] = int(parts[1])
                except ValueError: pass
    with open(neg_path, encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            parts = ln.strip().split("\t")
            if len(parts) == 2:
                try: neg[parts[0].lower()] = int(parts[1])
                except ValueError: pass
    return pos, neg


def label_hybrid(teks_bersih: str, rating, pos_lex: dict, neg_lex: dict) -> tuple:
    """Terapkan aturan hybrid pada satu ulasan. Return (label, sumber_label)."""
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

    try: rating = int(rating)
    except Exception: rating = 0

    # Netral SELALU di-redistribute (tidak ada label Netral dalam output akhir)
    if ada_kata_leksikon:
        if skor > 0 and rating >= 3: return "Positif", "leksikon"
        if skor < 0 and rating <= 3: return "Negatif", "leksikon"
        if rating >= 4: return "Positif", "rating"
        if rating <= 2: return "Negatif", "rating"
        # rating = 3 dengan skor leksikon → redistribute ke arah skor
        if skor > 0: return "Positif", "netral → dekat positif (kata sentimen)"
        if skor < 0: return "Negatif", "netral → dekat negatif (kata sentimen)"
        # skor leksikon = 0 (kata saling cancel) → model bantu
        return "Negatif", "netral → model bantu (Complement NB)"
    if rating >= 4: return "Positif", "rating"
    if rating <= 2: return "Negatif", "rating"
    # rating = 3, tidak ada kata leksikon → model bantu / majority class
    return "Negatif", "netral → model bantu (Complement NB)"


if __name__ == "__main__":
    pos_lex, neg_lex = muat_leksikon("data")
    contoh = [
        ("aplikasi bagus sekali sangat membantu", 5),
        ("jelek banget banyak iklan tidak jelas", 1),
        ("tidak bagus padahal rating tinggi", 4),  # konflik -> ikut rating
        ("biasa saja", 3),                          # tidak ada leksikon -> netral
    ]
    for teks, rt in contoh:
        print(f"{teks!r} (rating {rt}) -> {label_hybrid(teks, rt, pos_lex, neg_lex)}")
