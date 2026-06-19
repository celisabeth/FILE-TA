# Template — Perbandingan Format Data (BAB IV §4.1.5)

Sumber: `metrics/aqe_measurement_format_comparison_*.json`  
Sampel: subset `silver_mahasiswa` (default 50.000 baris)

## Identitas

| Item | Nilai |
|------|-------|
| Tanggal | |
| Jumlah baris sampel | |
| Catatan produksi | Iceberg + Parquet di MinIO |

## Tabel perbandingan

| Format | Ukuran (MB) | Write (s) | Read (s) | Throughput read (baris/s) |
|--------|-------------|-----------|----------|---------------------------|
| Parquet | | | | |
| ORC | | | | |
| JSON | | | | |

## Kesimpulan

- Format terkecil: …
- Read tercepat: …
- Rekomendasi layer Silver/Gold: Iceberg (Parquet) karena …
