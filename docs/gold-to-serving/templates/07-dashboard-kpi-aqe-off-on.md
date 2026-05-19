# Template 07 — Dashboard KPI AQE OFF & ON

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)  
**Referensi chart:** salin dari [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md), ganti database & schema saja.

Speedup pipeline → **Grafana** (bukan template ini).

---

## Step 1 — DATABASE (dua koneksi)

| Display name | SQLAlchemy URI |
|--------------|----------------|
| `Lakehouse AQE OFF` | `trino://admin@trino:8080/lakehouse_aqe_off` |
| `Lakehouse AQE ON` | `trino://admin@trino:8080/lakehouse_aqe_on` |

**Settings** → **Database connections** → ulangi untuk masing-masing.

Prasyarat data: DAG `aqe_full_experiment` sukses.

```bash
docker exec lhmeta-trino trino --execute "SELECT COUNT(*) FROM lakehouse.gold_aqe_off.fact_rekap_iku_institusi"
docker exec lhmeta-trino trino --execute "SELECT COUNT(*) FROM lakehouse.gold_aqe_on.fact_rekap_iku_institusi"
```

---

## Step 2–4 — OFF (ulangi pola template 01)

### Dataset `v_rekap_iku_tahun_off`

| Item | Nilai |
|------|-------|
| SQL Lab → Database | **Lakehouse AQE OFF** |

```sql
SELECT w.tahun, r.iku_kode, r.iku_nama,
       r.nilai_capaian, r.nilai_target, r.satuan, r.status_capaian
FROM gold_aqe_off.fact_rekap_iku_institusi r
JOIN gold_aqe_off.dim_waktu w ON r.waktu_id = w.waktu_id
ORDER BY w.tahun, r.iku_kode;
```

Jika **0 baris** (belum re-run `aqe_full_experiment` setelah patch `build_dim_waktu`), pakai join alternatif — ganti schema `gold_aqe_off` / `gold_aqe_on` sesuai cabang:

```sql
JOIN gold_aqe_off.dim_waktu w
  ON w.tahun = CAST(r.waktu_id / 100 AS INTEGER)
 AND w.bulan = MOD(r.waktu_id, 100)
```

Save dataset → `v_rekap_iku_tahun_off`.

### Chart

| Field | Nilai |
|-------|-------|
| Dataset | `v_rekap_iku_tahun_off` |
| Type | Bar Chart |
| Dimension | `iku_kode` |
| Metric | AVG `nilai_capaian` |
| Save | `chart_executive_iku_off` |

### Dashboard

| Nama | `Executive IKU — AQE OFF` |
| Portal embed | `/dashboards/kpi-aqe-off` |

---

## Step 2–4 — ON (sama, ganti koneksi & schema)

| Item | OFF | ON |
|------|-----|-----|
| Database SQL Lab | Lakehouse AQE OFF | Lakehouse AQE ON |
| Schema di SQL | `gold_aqe_off` | `gold_aqe_on` |
| Dataset | `v_rekap_iku_tahun_off` | `v_rekap_iku_tahun_on` |
| Chart | `chart_executive_iku_off` | `chart_executive_iku_on` |
| Dashboard | Executive IKU — AQE OFF | Executive IKU — AQE ON |
| Portal | kpi-aqe-off | kpi-aqe-on |

---

## Verifikasi parity (SQL Lab)

```sql
SELECT 'OFF' AS ctx, COUNT(*) AS n FROM lakehouse.gold_aqe_off.fact_rekap_iku_institusi
UNION ALL
SELECT 'ON', COUNT(*) FROM lakehouse.gold_aqe_on.fact_rekap_iku_institusi;
```

---

## Checklist laporan BAB IV

| Bukti | Alat |
|-------|------|
| Screenshot dashboard OFF & ON | Superset |
| Speedup / durasi | Grafana + `metrics/aqe_comparison_*.json` |
