"""Tahap 7 — Vektorisasi TF-IDF dan Pelatihan Model.

Mengubah teks menjadi fitur numerik dengan TF-IDF (unigram + bigram, 5.000
fitur, min_df = 2), kemudian melatih dua model klasifikasi paralel:

- Complement Naive Bayes
- Support Vector Machine (kernel linear, C = 1.0)

Model dievaluasi dengan accuracy, precision, recall, F1, dan macro-F1 pada
data uji (hold-out 20% stratified). Confusion matrix dicetak untuk setiap
model. Model yang sudah dilatih disimpan ke file .joblib untuk digunakan
kembali tanpa harus melatih ulang.
"""
import time

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC


def muat_data(berkas: str, kolom_teks: str = "content_final", kolom_label: str = "label") -> pd.DataFrame:
    """Baca file hasil pelabelan dan buang baris Netral (fokus ke klasifikasi biner)."""
    if berkas.lower().endswith(".csv"):
        df = pd.read_csv(berkas)
    else:
        df = pd.read_excel(berkas)
    df = df[df[kolom_label].str.strip().str.title().isin(["Positif", "Negatif"])]
    df = df[df[kolom_teks].astype(str).str.len() > 0].reset_index(drop=True)
    return df[[kolom_teks, kolom_label]].rename(columns={kolom_teks: "teks", kolom_label: "label"})


def latih_dan_evaluasi(df: pd.DataFrame, nama_aplikasi: str = "model") -> dict:
    """Latih TF-IDF + NB + SVM lalu cetak metrik. Return dict berisi model dan vectorizer."""
    X = df["teks"].astype(str).tolist()
    y = df["label"].str.strip().str.title().tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    print(f"\n=== {nama_aplikasi} ===")
    print(f"Jumlah data: {len(df)} (latih: {len(X_train)}, uji: {len(X_test)})")

    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, lowercase=True)
    Xv_train = vec.fit_transform(X_train)
    Xv_test = vec.transform(X_test)

    hasil = {"vectorizer": vec, "nama_aplikasi": nama_aplikasi}
    for nama, model in [("Complement Naive Bayes", ComplementNB()),
                        ("SVM (kernel linear)", LinearSVC(C=1.0, max_iter=2000))]:
        t0 = time.time()
        model.fit(Xv_train, y_train)
        waktu_latih = round(time.time() - t0, 2)
        y_pred = model.predict(Xv_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, pos_label="Positif")
        rec = recall_score(y_test, y_pred, pos_label="Positif")
        f1 = f1_score(y_test, y_pred, pos_label="Positif")
        macro = f1_score(y_test, y_pred, average="macro")
        cm = confusion_matrix(y_test, y_pred, labels=["Positif", "Negatif"])

        print(f"\n[{nama}]  waktu latih: {waktu_latih} dtk")
        print(f"  accuracy  = {acc:.4f}")
        print(f"  precision = {prec:.4f}  recall = {rec:.4f}  F1 = {f1:.4f}")
        print(f"  macro-F1  = {macro:.4f}")
        print(f"  confusion matrix (baris=aktual, kolom=prediksi):")
        print(f"     pos  neg")
        print(f"  pos {cm[0][0]:4d} {cm[0][1]:4d}")
        print(f"  neg {cm[1][0]:4d} {cm[1][1]:4d}")

        hasil[nama] = {"model": model, "waktu_latih": waktu_latih, "accuracy": acc,
                       "precision": prec, "recall": rec, "f1": f1, "macro_f1": macro,
                       "confusion_matrix": cm}
    return hasil


def simpan_model(hasil: dict, folder_keluar: str = ".") -> None:
    """Simpan vectorizer + kedua model ke satu file .joblib."""
    import os
    nama = hasil["nama_aplikasi"].lower().replace(" ", "_")
    paket = {
        "vectorizer": hasil["vectorizer"],
        "nb": hasil["Complement Naive Bayes"]["model"],
        "svm": hasil["SVM (kernel linear)"]["model"],
    }
    path = os.path.join(folder_keluar, f"model_{nama}.joblib")
    joblib.dump(paket, path)
    print(f"Model disimpan ke: {path}")


if __name__ == "__main__":
    # Contoh pemakaian per aplikasi:
    # df_ig = muat_data("hasil_6_pelabelan_instagram.xlsx")
    # hasil = latih_dan_evaluasi(df_ig, "Instagram")
    # simpan_model(hasil, folder_keluar=".")
    pass
