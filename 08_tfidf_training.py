import os
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


def muat_data(berkas: str, kolom_teks: str = "normalisasi", kolom_label: str = "label") -> pd.DataFrame:
    """Baca file hasil pelabelan dan buang baris Netral (fokus ke klasifikasi biner)."""
    if berkas.lower().endswith(".csv"):
        df = pd.read_csv(berkas, keep_default_na=False)
    else:
        df = pd.read_excel(berkas)
    df = df[df[kolom_label].astype(str).str.strip().str.title().isin(["Positif", "Negatif"])]
    df = df[df[kolom_teks].astype(str).str.len() > 0].reset_index(drop=True)
    return df[[kolom_teks, kolom_label]].rename(columns={kolom_teks: "teks", kolom_label: "label"})


def latih_dan_evaluasi(df: pd.DataFrame, nama_aplikasi: str = "model") -> dict:
    """Latih TF-IDF + NB + SVM lalu cetak metrik. Return dict berisi model dan vectorizer."""
    X = df["teks"].astype(str).tolist()
    y = df["label"].astype(str).str.strip().str.title().tolist()

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
        print(f"       pos    neg")
        print(f"  pos {cm[0][0]:6d} {cm[0][1]:6d}")
        print(f"  neg {cm[1][0]:6d} {cm[1][1]:6d}")

        hasil[nama] = {"model": model, "waktu_latih": waktu_latih, "accuracy": acc,
                       "precision": prec, "recall": rec, "f1": f1, "macro_f1": macro,
                       "confusion_matrix": cm}
    return hasil


def simpan_model(hasil: dict, folder_keluar: str = ".") -> None:
    """Simpan vectorizer + kedua model ke satu file .joblib."""
    nama = hasil["nama_aplikasi"].lower().replace(" ", "_")
    paket = {
        "vectorizer": hasil["vectorizer"],
        "nb": hasil["Complement Naive Bayes"]["model"],
        "svm": hasil["SVM (kernel linear)"]["model"],
    }
    path = os.path.join(folder_keluar, f"model_{nama}.joblib")
    joblib.dump(paket, path)
    print(f"Model disimpan ke: {path}")


def cari_kolom_teks(berkas: str) -> str:
    """Cari kolom teks yang tersedia di file CSV."""
    df_cek = pd.read_csv(berkas, nrows=1)
    for k in ["clean_text", "stemming", "normalisasi", "stopword", "content_bersih", "content_final"]:
        if k in df_cek.columns:
            return k
    return None


if __name__ == "__main__":
    aplikasi = ["instagram", "tiktok", "x"]
    semua_hasil = {}

    # Train tiap aplikasi dari file hasil pelabelan tahap 7
    for app in aplikasi:
        berkas = f"{app}_7_pelabelan.csv"
        if not os.path.exists(berkas):
            print(f"Lewati {app}: file {berkas} tidak ada")
            continue

        kolom_teks = cari_kolom_teks(berkas)
        if kolom_teks is None:
            print(f"Lewati {app}: tidak ada kolom teks yang cocok.")
            continue

        print(f"\n{'='*60}")
        print(f"APLIKASI: {app.upper()}  (pakai kolom teks: '{kolom_teks}')")
        print(f"{'='*60}")

        df = muat_data(berkas, kolom_teks=kolom_teks, kolom_label="label")
        hasil = latih_dan_evaluasi(df, nama_aplikasi=app.capitalize())
        simpan_model(hasil, folder_keluar=".")
        semua_hasil[app] = hasil

    # Train juga model GABUNGAN semua aplikasi
    print(f"\n{'='*60}")
    print(f"APLIKASI: SEMUA (gabungan)")
    print(f"{'='*60}")

    df_semua = []
    for app in aplikasi:
        berkas = f"{app}_7_pelabelan.csv"
        if os.path.exists(berkas):
            kt = cari_kolom_teks(berkas)
            if kt:
                df_semua.append(muat_data(berkas, kolom_teks=kt, kolom_label="label"))

    if df_semua:
        df_all = pd.concat(df_semua, ignore_index=True)
        hasil_all = latih_dan_evaluasi(df_all, nama_aplikasi="Semua")
        simpan_model(hasil_all, folder_keluar=".")
        semua_hasil["semua"] = hasil_all

    # Ringkasan akurasi
    print(f"\n{'='*60}")
    print("RINGKASAN AKURASI")
    print(f"{'='*60}")
    print(f"{'Aplikasi':15s} {'NB Accuracy':>14s} {'SVM Accuracy':>14s}")
    print("-" * 45)
    for app, h in semua_hasil.items():
        nb_acc = h["Complement Naive Bayes"]["accuracy"]
        svm_acc = h["SVM (kernel linear)"]["accuracy"]
        print(f"{app:15s} {nb_acc:>14.4f} {svm_acc:>14.4f}")

    print(f"\nSELESAI. Model tersimpan di folder pipeline.")
