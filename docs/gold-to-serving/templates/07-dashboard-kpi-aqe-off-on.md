# Template — Dashboard KPI AQE OFF & AQE ON (Superset)

> **Panduan langkah demi langkah:** [../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md) (§ Langkah D & E)

Duplikasi **Dashboard Executive IKU** ([01-dashboard-executive-iku.md](01-dashboard-executive-iku.md)) untuk membandingkan **salinan Gold** hasil pipeline AQE, bukan untuk mengukur speedup (speedup → Grafana Monitoring AQE).

---

## Prasyarat

- Koneksi Superset: `Lakehouse AQE OFF` dan `Lakehouse AQE ON` — lihat [`../koneksi-trino-superset.md`](../koneksi-trino-superset.md)
- Dataset dari `gold_aqe_off.*` dan `gold_aqe_on.*` (struktur sama dengan `lakehouse.gold.*`)

---

## Dashboard OFF — `gold_aqe_off`

| Panel | Dataset | Catatan |
|-------|---------|---------|
| Bar 8 IKU | `fact_rekap_iku_institusi` (koneksi OFF) | Suffix judul chart: **「AQE OFF」** |
| Heatmap capaian | sama | |
| Filter tahun | `dim_waktu` | |

**Judul dashboard:** `Executive IKU — AQE OFF (gold_aqe_off)`

---

## Dashboard ON — `gold_aqe_on`

Identik dengan OFF, ganti:

- Koneksi: **Lakehouse AQE ON**
- Schema tabel: `gold_aqe_on`
- Suffix: **「AQE ON」**

**Judul dashboard:** `Executive IKU — AQE ON (gold_aqe_on)`

---

## Verifikasi parity (SQL Lab)

```sql
-- OFF
SELECT COUNT(*) AS n FROM gold_aqe_off.fact_rekap_iku_institusi;

-- ON
SELECT COUNT(*) AS n FROM gold_aqe_on.fact_rekap_iku_institusi;

-- Banding nilai (harus mendekati jika data sama)
SELECT 'OFF' AS ctx, iku_kode, nilai_capaian
FROM gold_aqe_off.fact_rekap_iku_institusi
UNION ALL
SELECT 'ON', iku_kode, nilai_capaian
FROM gold_aqe_on.fact_rekap_iku_institusi
ORDER BY iku_kode, ctx;
```

---

## Embed portal

| Dashboard | Path portal | URL embed (contoh) |
|-----------|-------------|-------------------|
| OFF | `/dashboards/kpi-aqe-off` | `http://<IP>:18089/superset/dashboard/<ID_OFF>/?standalone=1` |
| ON | `/dashboards/kpi-aqe-on` | `http://<IP>:18089/superset/dashboard/<ID_ON>/?standalone=1` |

Isi ID setelah dashboard disimpan — **Atur URL Embed** di header halaman.

---

## Laporan BAB IV

| Bukti | Alat | File / screenshot |
|-------|------|-------------------|
| KPI parity OFF vs ON | Superset (2 dashboard) | Screenshot kedua dashboard |
| Speedup / durasi pipeline | Grafana + metrics | `metrics/aqe_comparison_*.json` |
