# Dashboard Analisis Sentimen Instagram, TikTok, dan X

Dashboard web untuk analisis sentimen ulasan pengguna aplikasi media sosial **Instagram, TikTok, dan X** di Google Play Store menggunakan algoritma **Naive Bayes (Complement)** dan **Support Vector Machine (kernel linear)**, dengan visualisasi interaktif berbasis web.

Dibangun untuk skripsi Program Studi Sistem Informasi, Fakultas Teknologi Informasi, Universitas Tarumanagara.

---

## Deskripsi

Aplikasi ini menyajikan hasil analisis sentimen terhadap 145.248 ulasan pengguna yang dikumpulkan dari Google Play Store. Dashboard berjalan di browser desktop maupun mobile tanpa perlu instalasi aplikasi.

### Fitur Utama

- **Ringkasan Insight Utama** — metrik total ulasan, rata-rata sentimen positif, model terbaik, dan rincian per aplikasi dalam kartu interaktif.
- **Perbandingan Sentimen** — proporsi sentimen positif dan negatif antar aplikasi dan selang waktu, dengan filter tahun, tanggal, dan algoritma.
- **Performa Algoritma** — evaluasi Naive Bayes dan SVM per aplikasi dalam bentuk tabel metrik, confusion matrix, dan grafik macro-F1.
- **Halaman Admin** — unggah data ulasan baru dengan pemrosesan pipeline otomatis (preprocessing, pelabelan hybrid, prediksi dua model), kelola pengguna (tambah, ubah peran, ganti password, hapus akun), dan riwayat unggahan.

---

## Pipeline Analisis

Alur pengolahan data dari ulasan mentah sampai siap divisualisasikan:

```
Scraping Google Play
      │
      ▼
Preprocessing  (case folding → cleaning → tokenizing → normalisasi → stopword removal → stemming)
      │
      ▼
Pelabelan Hybrid  (leksikon InSet + rating bintang + valence tuning untuk negasi)
      │
      ▼
Pembagian data latih dan uji  (80:20, stratified)
      │
      ▼
Vektorisasi TF-IDF  (unigram + bigram, 5.000 fitur, min_df = 2)
      │
      ▼
Pelatihan dua model paralel
   ├─ Complement Naive Bayes
   └─ Support Vector Machine (kernel linear, C = 1.0)
      │
      ▼
Evaluasi  (accuracy, precision, recall, F1, macro-F1, confusion matrix)
      │
      ▼
Data Warehouse Neon PostgreSQL  (skema bintang: dim_aplikasi, dim_waktu, dim_model, dim_sentimen, fact_sentimen)
      │
      ▼
Dashboard Streamlit
```

---

## Struktur Folder

```
dashboard-skripsi/
├── streamlit_app.py           Aplikasi utama Streamlit
├── requirements.txt           Daftar paket Python
├── README.md                  File ini
├── LICENSE                    Lisensi MIT
├── .gitignore                 Berkas yang tidak dimasukkan ke Git
├── data/                      Leksikon untuk pelabelan hybrid
│   ├── inset_positive.tsv     3.609 kata positif (InSet)
│   └── inset_negative.tsv     6.609 kata negatif (InSet)
└── pipeline/                  Modul pipeline sebagai dokumentasi metode
    ├── 01_case_folding.py
    ├── 02_cleaning.py
    ├── 03_tokenizing.py
    ├── 04_stopword_removal.py
    ├── 05_stemming.py
    ├── 06_pelabelan_hybrid.py
    └── 07_tfidf_training.py
```

Catatan: modul di `pipeline/` adalah dokumentasi proses tahap demi tahap. Versi terintegrasi dari semua tahap tersebut sudah berada di dalam `streamlit_app.py` dan otomatis dijalankan saat Admin mengunggah ulasan baru.

---

## Cara Menjalankan

### Online (Streamlit Cloud)

Aplikasi ini sudah di-deploy. Buka URL yang diberikan di laporan skripsi, lalu masuk dengan akun yang diberikan.

### Lokal

Prasyarat: Python 3.12, akses ke basis data PostgreSQL berisi data analisis.

```bash
# Clone repository
git clone https://github.com/laurentcynthiacasandra-spec/dashboard-skripsi.git
cd dashboard-skripsi

# Instalasi dependensi
pip install -r requirements.txt

# Siapkan secret DATABASE_URL (contoh Linux / Mac)
export DATABASE_URL="postgresql://user:pass@host.neon.tech/neondb?sslmode=require"

# Jalankan Streamlit
streamlit run streamlit_app.py
```

Dashboard akan terbuka di `http://localhost:8501`.

---

## Teknologi

| Lapisan | Pilihan |
|---|---|
| Frontend / Backend | Streamlit |
| Visualisasi | Plotly |
| Basis data | PostgreSQL (Neon) |
| Preprocessing | Sastrawi (stemmer dan stopword bahasa Indonesia) |
| Leksikon sentimen | InSet (Fajri91) |
| Vektorisasi | TF-IDF (scikit-learn) |
| Algoritma | Complement Naive Bayes, Linear SVM (scikit-learn) |
| Autentikasi | bcrypt |

---

## Peneliti

**Laurent Cynthia Casandra** · NPM 825230031  
Program Studi Sistem Informasi, Fakultas Teknologi Informasi  
Universitas Tarumanagara, 2026

---

## Lisensi

MIT License — lihat berkas `LICENSE`.

Leksikon InSet (Fajri91) digunakan sesuai lisensi aslinya; kutipan:
Koto, F., & Rahmaningtyas, G. Y. (2017). *Inset lexicon: Evaluation of a word list for Indonesian sentiment analysis in microblogs*. IALP.
