# Template — Dataset (BAB III)

Panduan generate: [`../../generate-data/README.md`](../../generate-data/README.md)

## Ringkasan

| Item | Nilai | Sumber otomatis |
|------|-------|-----------------|
| Perintah generate | | |
| Profil (`--profile`) | metadata / insight / aqe | |
| Mode | full / append | |
| Batch append (jika ada) | | baris mahasiswa |
| Jumlah file CSV | 12 | `metrics/dataset_summary_*.json` |
| Total baris | | `summary.total_rows` |
| Total ukuran (MB) | | `summary.total_size_mb` |
| Skew prodi | SD / tidak | `--skew-fraction` |

## Tabel per file

| File CSV | Baris (sebelum) | Baris (sesudah append) | Ukuran (MB) |
|----------|-----------------|------------------------|-------------|
| raw_mahasiswa.csv | | | |
| raw_dosen.csv | | | |
| raw_lulusan.csv | | | |
| … | | | |

## Catatan domain data (ITERA / IKU)

-

## Uji ulang (append)

| Run | Batch append | Total baris setelah | Tanggal |
|-----|--------------|---------------------|---------|
| 1 | — (full) | | |
| 2 | 5000 | | |
