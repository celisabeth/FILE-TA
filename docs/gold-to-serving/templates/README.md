# Template Dashboard Analitik KPI IKU

> **Belum tahu mulai dari mana?** Baca panduan utama:  
> **[../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md)**  
> (langkah klik Superset untuk **lakehouse.gold**, **gold_aqe_off**, **gold_aqe_on** + embed portal)

Template di folder ini = **checklist isian** untuk laporan BAB IV dan daftar panel chart. **Tidak** di-upload otomatis ke Superset — Anda membuat chart/dashboard manual di UI, lalu mengisi tabel kosong di file `.md` ini.

---

## Peta template → koneksi Trino

| No | File | Dashboard | Koneksi Superset | Schema |
|----|------|-----------|------------------|--------|
| 01 | [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md) | Executive 8 IKU + SAKIP | `Lakehouse Gold (IKU)` | `gold` |
| 02 | [02-dashboard-iku-per-indikator.md](02-dashboard-iku-per-indikator.md) | Detail IKU-1 … 8 | Lakehouse Gold | `gold` |
| 03 | [03-dashboard-tata-kelola-sakip.md](03-dashboard-tata-kelola-sakip.md) | Tata kelola | Lakehouse Gold | `gold` |
| 04 | [04-dashboard-prodi-drilldown.md](04-dashboard-prodi-drilldown.md) | Per prodi | Lakehouse Gold | `gold` |
| 05 | [05-dashboard-mlops-prediktif.md](05-dashboard-mlops-prediktif.md) | Forecast, Risk, … | **Grafana** | metrik Prometheus |
| 06 | [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) | Query SQL Lab | Salin per koneksi | ganti prefix schema |
| 07 | [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md) | Duplikat Executive | AQE OFF + AQE ON | `gold_aqe_off` / `gold_aqe_on` |

---

## Urutan disarankan

1. [../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md) — Langkah A–E  
2. Isi [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md) sambil membuat dashboard utama  
3. (Penelitian AQE) [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md) + duplikat dashboard  
4. (Opsional) 02, 03, 04  
5. MLOps prediktif → [05-dashboard-mlops-prediktif.md](05-dashboard-mlops-prediktif.md) + Grafana

**Konsep star schema & OLAP:** [../README.md](../README.md)
