#!/usr/bin/env python3
"""
Bronze Data Generator — ITERA Data Lakehouse Insight
====================================================
Data sintetis domain perguruan tinggi (15 CSV staging) untuk:
  • Metode Metadata (Medallion + Atlas + portal)
  • Metode AQE (shuffle, skew join prodi SD)
  • Metode MLOps (Gold → feature → model)

Mode:
  --mode full    : overwrite semua CSV di data/staging/
  --mode append  : tambah batch baru (uji ulang setelah menambah baris)

Profil (--profile) — basis populasi ITERA real (~22.621 mhs, 705 dosen, 320 tendik):
  metadata / real : populasi kampus, tanpa skew
  insight / aqe   : populasi real + skew 75% ke SD (uji AQE pada skala operasional)
  aqe-stress      : ~3× mahasiswa (stress test opsional)
  aqe-large       : ~5× mahasiswa (alias stress test berat)

Panduan: docs/generate-data/README.md

Contoh:
  python3 scripts/generate_bronze_data.py --mode full --profile metadata
  python3 scripts/generate_bronze_data.py --mode append --batch-size 3000
  python3 scripts/generate_bronze_data.py --profile aqe --dry-run
  python3 scripts/generate_bronze_data.py --profile aqe --scale 1.5
"""

import argparse
import csv
import os
import random
import string
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Reference / Master Data  (ITERA — lihat scripts/itera_reference.py)
# ---------------------------------------------------------------------------

from itera_reference import (
    DEFAULT_SKEW_PRODI,
    FAKULTAS,
    FAKULTAS_IDS,
    ITERA_ORGANISASI,
    ITERA_POPULATION,
    PRODI_IDS,
    PRODI_MASTER,
    PRODI_S1_IDS,
    TENDIK_JABATAN,
    build_volume_profile,
    pick_unit_for_fakultas,
    pick_unit_for_tendik,
)

JURUSAN = FAKULTAS
JURUSAN_IDS = FAKULTAS_IDS


def _prodi_meta(prodi_id: str) -> dict:
    return next(p for p in PRODI_MASTER if p["prodi_id"] == prodi_id)
PROVINSI = [
    "Lampung", "DKI Jakarta", "Jawa Barat", "Jawa Tengah", "Jawa Timur",
    "Banten", "Sumatera Selatan", "Sumatera Utara", "Sumatera Barat",
    "Bengkulu", "Riau", "Jambi", "Aceh", "Bali", "NTB", "NTT",
    "Kalimantan Barat", "Kalimantan Timur", "Sulawesi Selatan", "Papua",
    "Yogyakarta", "Kalimantan Selatan", "Sulawesi Utara", "Kepulauan Riau",
    "Bangka Belitung", "Maluku",
]
JALUR_MASUK = ["SNBP", "SNBT", "Mandiri"]
STATUS_AKTIF = ["Aktif", "Aktif", "Aktif", "Aktif", "Cuti", "DO"]
JENIS_KELAMIN = ["L", "P"]

JABATAN_FUNGSIONAL = [
    "Tenaga Pengajar", "Asisten Ahli", "Lektor",
    "Lektor Kepala", "Guru Besar",
]
STATUS_ASN = ["PNS", "PPPK", "Non-ASN"]
PENDIDIKAN = ["S2", "S3"]

SKEMA_PENELITIAN = ["Mandiri", "Dana ITERA", "Hibah Dikti", "Industri"]
TOPIK_PENELITIAN = [
    "Sustainable Energy", "Innovative Industry",
    "Green Infrastructure", "Community Development",
]
STATUS_PUBLIKASI = ["Belum", "Jurnal Nasional", "Jurnal Internasional"]

JENIS_MBKM = [
    "Magang", "KKN Tematik", "Riset", "Pertukaran",
    "Wirausaha", "Proyek Kemanusiaan",
]
JENIS_KERJASAMA = ["MoU", "PKS"]
KATEGORI_MITRA = ["PT_DN", "PT_LN", "Industri", "Pemerintah", "Litbang"]
LINGKUP = ["Pendidikan", "Penelitian", "PkM", "MBKM", "Semua"]
LEMBAGA_AKREDITASI = ["BAN-PT", "LAM", "Internasional"]
PREDIKAT_AKREDITASI = ["Baik", "Baik Sekali", "Unggul", "A", "B", "Internasional"]
SUMBER_DANA = ["PNBP", "APBN", "SBSN", "Hibah"]
KOMPONEN_ANGGARAN = ["Gaji", "Operasional", "Penelitian", "Investasi", "PkM"]

BIDANG_PRESTASI = ["Riset", "Olahraga", "Seni", "Teknologi", "Debat", "Desain"]
TINGKAT_PRESTASI = ["Institusi", "Regional", "Nasional", "Internasional"]
PERINGKAT = ["Juara 1", "Juara 2", "Juara 3", "Finalis"]
STATUS_PASCA_LULUS = ["Bekerja", "Studi Lanjut", "Wirausaha", "Belum Bekerja"]

NAMA_DEPAN = [
    "Ahmad", "Budi", "Citra", "Dewi", "Eka", "Fajar", "Gita", "Hadi",
    "Indra", "Joni", "Kartika", "Lestari", "Muhammad", "Nadia", "Omar",
    "Putri", "Qori", "Rina", "Sari", "Taufik", "Umar", "Vina", "Wahyu",
    "Yusuf", "Zahra", "Andi", "Bayu", "Dian", "Fitri", "Galih",
    "Hendra", "Irma", "Joko", "Kiki", "Lia", "Mira", "Novi", "Okta",
    "Prima", "Rizki", "Sinta", "Tina", "Ulfa", "Wati", "Yani", "Zaki",
    "Arif", "Bella", "Cahya", "Dinda", "Elsa", "Fandi", "Gilang",
    "Hana", "Ilham", "Jihan", "Kevin", "Luna", "Maulana", "Nisa",
]
NAMA_BELAKANG = [
    "Pratama", "Saputra", "Wijaya", "Kusuma", "Hidayat", "Nugroho",
    "Permana", "Santoso", "Wibowo", "Ramadhani", "Setiawan", "Utami",
    "Purnama", "Suherman", "Gunawan", "Wulandari", "Handayani",
    "Susanti", "Fitriani", "Maharani", "Laksono", "Prasetyo", "Surya",
    "Mahendra", "Hakim", "Fauzi", "Ramadhan", "Aditya", "Putra",
    "Anggraini", "Safitri", "Damayanti", "Suryadi", "Firmansyah",
]

INSTITUSI_MITRA = [
    "Universitas Indonesia", "ITB", "UGM", "ITS", "Unila", "Unsri",
    "Universitas Lampung", "Politeknik Negeri Lampung", "IPB University",
    "Telkom University", "PT PLN", "PT Pertamina", "PT Bukit Asam",
    "PT Telkom Indonesia", "Bank Indonesia", "PT Astra International",
    "Huawei Indonesia", "Google Indonesia", "Toyota Motor Manufacturing",
    "BPS Lampung", "BMKG", "LIPI", "BRIN", "UNDP Indonesia",
    "World Bank Jakarta", "JICA Indonesia", "NUS Singapore",
    "Universiti Malaya", "Chulalongkorn University",
    "Kyushu University", "Osaka University", "TU Delft",
]

KOTA_LAMPUNG = [
    "Bandar Lampung", "Metro", "Pringsewu", "Pesawaran",
    "Lampung Selatan", "Lampung Tengah", "Lampung Utara",
    "Tanggamus", "Way Kanan", "Lampung Timur", "Tulang Bawang",
    "Mesuji", "Pesisir Barat", "Lampung Barat",
]

KOMPETISI = [
    "Gemastik", "KMIPN", "PKM Dikti", "LKTIN Nasional", "Pilmapres",
    "ONMIPA", "Smart City Competition", "IoT Hackathon", "Data Science Challenge",
    "Imagine Cup", "Shell Eco-Marathon", "ACM ICPC Regional",
    "Kontes Robot Indonesia", "Electric Vehicle Competition",
    "National Bridge Competition", "Geospatial Hackathon",
]

# Profil volume — basis populasi ITERA real (lihat itera_reference.ITERA_POPULATION).
# aqe / insight memakai ~22.621 mhs + skew 75% ke SD (~17k baris) — cukup untuk uji AQE shuffle/skew.
# aqe-stress: opsi stress test (3× mahasiswa) via --profile aqe-stress atau --scale pada aqe.
VOLUME_PROFILES: dict[str, dict[str, int | float]] = {
    "metadata": build_volume_profile(skew_fraction=0.0),
    "dev": build_volume_profile(skew_fraction=0.0),
    "real": build_volume_profile(skew_fraction=0.0),
    "insight": build_volume_profile(skew_fraction=0.75),
    "aqe": build_volume_profile(skew_fraction=0.75),
    "aqe-stress": build_volume_profile(scale=3.0, skew_fraction=0.80, derived_scale=2.0),
    # Alias lama: stress test ~5× populasi kampus
    "aqe-large": build_volume_profile(scale=5.0, skew_fraction=0.80, derived_scale=3.0),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rand_name() -> str:
    return f"{random.choice(NAMA_DEPAN)} {random.choice(NAMA_BELAKANG)}"


def _rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def _now_ts() -> str:
    return datetime.now(tz=None).astimezone().isoformat(timespec="seconds")


def _uid(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:8]
    return f"{prefix}{short}" if prefix else short


def _write_csv(filepath: Path, rows: list[dict], append: bool = False):
    """Write or append rows to a CSV file."""
    if not rows:
        return
    mode = "a" if append and filepath.exists() else "w"
    write_header = mode == "w" or not filepath.exists()
    with open(filepath, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(
        f"  {'Appended' if append else 'Wrote'} {len(rows):>9,} rows "
        f"({size_mb:>7.1f} MB) → {filepath.name}"
    )


def _pick_prodi(
    skew_prodi: str | None,
    skew_fraction: float,
) -> str:
    """Pilih prodi_id; injeksi skew untuk uji AQE skew join."""
    if skew_prodi and skew_fraction > 0 and random.random() < skew_fraction:
        return skew_prodi
    return random.choice(PRODI_S1_IDS)


def _resolve_volume(profile: str, scale: float) -> dict[str, float]:
    """Hitung target baris: profil dasar × --scale (kecuali skew_fraction)."""
    base = dict(VOLUME_PROFILES[profile])
    if scale == 1.0:
        return base
    out: dict[str, float] = {}
    for k, v in base.items():
        if k == "default_skew_fraction":
            out[k] = v
        elif k in ("kegiatan_avg", "penelitian_avg", "pengabdian_avg", "lulusan_pct", "mbkm_pct"):
            out[k] = v
        else:
            out[k] = int(v * scale) if isinstance(v, int) else float(v) * scale
    return out

# ---------------------------------------------------------------------------
# Generators (setiap fungsi mengembalikan list[dict])
# ---------------------------------------------------------------------------

def gen_fakultas() -> list[dict]:
    ts = _now_ts()
    return [
        {
            "fakultas_id": fid,
            "nama_fakultas": nama,
            "status": "Aktif",
            "ingested_at": ts,
        }
        for fid, nama in FAKULTAS.items()
    ]


def gen_organisasi_itera() -> list[dict]:
    ts = _now_ts()
    rows = []
    for o in ITERA_ORGANISASI:
        rows.append({
            "org_id": o["org_id"],
            "nama_organisasi": o["nama_organisasi"],
            "tipe": o["tipe"],
            "parent_org_id": o.get("parent_org_id", ""),
            "tingkat": o.get("tingkat", ""),
            "fakultas_id": o.get("fakultas_id", ""),
            "ingested_at": ts,
        })
    return rows


def gen_prodi(scale: float) -> list[dict]:
    ts = _now_ts()
    return [
        {**p, "status": "Aktif", "ingested_at": ts}
        for p in PRODI_MASTER
    ]


def gen_mahasiswa(
    n: int,
    angkatan_range: tuple[int, int],
    skew_prodi: str | None = None,
    skew_fraction: float = 0.0,
) -> list[dict]:
    ts = _now_ts()
    rows = []
    for i in range(n):
        angkatan = random.randint(*angkatan_range)
        prodi = _pick_prodi(skew_prodi, skew_fraction)
        meta = _prodi_meta(prodi)
        sks_total = random.randint(0, 144) if angkatan < 2024 else random.randint(0, 48)
        rows.append({
            "mahasiswa_id": f"{angkatan}{prodi}{i:05d}",
            "nama": _rand_name(),
            "prodi_id": prodi,
            "fakultas_id": meta["fakultas_id"],
            "jurusan_id": meta["jurusan_id"],
            "angkatan": angkatan,
            "jalur_masuk": random.choice(JALUR_MASUK),
            "jenis_kelamin": random.choice(JENIS_KELAMIN),
            "asal_provinsi": random.choices(PROVINSI, weights=[30]+[3]*(len(PROVINSI)-1), k=1)[0],
            "status_aktif": random.choice(STATUS_AKTIF),
            "ipk_terakhir": round(random.uniform(2.0, 4.0), 2),
            "total_sks": sks_total,
            "sks_luar_kampus": random.choices([0, 0, 0, 6, 12, 20, 22, 24], k=1)[0],
            "tanggal_masuk": f"{angkatan}-08-{random.randint(1,28):02d}",
            "ingested_at": ts,
        })
    return rows


def gen_lulusan(mahasiswa_rows: list[dict], pct: float = 0.35) -> list[dict]:
    ts = _now_ts()
    eligible = [m for m in mahasiswa_rows if m["angkatan"] <= 2023 and m["status_aktif"] == "Aktif"]
    sample = random.sample(eligible, k=min(int(len(eligible) * pct), len(eligible)))
    rows = []
    for m in sample:
        lama = random.randint(42, 72)
        rows.append({
            "lulusan_id": _uid("LLS"),
            "mahasiswa_id": m["mahasiswa_id"],
            "prodi_id": m["prodi_id"],
            "tanggal_lulus": str(_rand_date(date(m["angkatan"]+4, 1, 1), date(min(m["angkatan"]+6, 2025), 12, 28))),
            "ipk": round(random.uniform(2.75, 3.95), 2),
            "lama_studi_bulan": lama,
            "status_pasca_lulus": random.choices(STATUS_PASCA_LULUS, weights=[50, 15, 10, 25], k=1)[0],
            "nama_perusahaan": random.choice(INSTITUSI_MITRA) if random.random() > 0.3 else "",
            "bidang_kerja": random.choice(["Sesuai", "Tidak Sesuai"]),
            "masa_tunggu_bulan": random.randint(0, 18),
            "sumber_data": random.choice(["Tracer Study", "Laporan Wisuda"]),
            "ingested_at": ts,
        })
    return rows


def gen_tendik(n: int) -> list[dict]:
    """Tenaga kependidikan (non-dosen) — unit administrasi / UPA / biro."""
    ts = _now_ts()
    rows = []
    org_by_id = {o["org_id"]: o for o in ITERA_ORGANISASI}
    for i in range(n):
        unit_id = pick_unit_for_tendik()
        org = org_by_id.get(unit_id, {})
        rows.append({
            "tendik_id": f"T{random.randint(10000, 99999)}{i:04d}",
            "nama": _rand_name(),
            "unit_organisasi_id": unit_id,
            "fakultas_id": org.get("fakultas_id", ""),
            "jabatan": random.choice(TENDIK_JABATAN),
            "jenis_kelamin": random.choice(JENIS_KELAMIN),
            "status_kepegawaian": random.choices(
                ["PNS", "PPPK", "Kontrak", "Honorer"],
                weights=[35, 25, 30, 10],
                k=1,
            )[0],
            "tahun_bergabung": random.randint(2012, 2025),
            "ingested_at": ts,
        })
    return rows


def gen_dosen(
    n: int,
    skew_prodi: str | None = None,
    skew_fraction: float = 0.0,
) -> list[dict]:
    ts = _now_ts()
    rows = []
    for i in range(n):
        prodi = _pick_prodi(skew_prodi, skew_fraction * 0.6)
        meta = _prodi_meta(prodi)
        pend = random.choices(PENDIDIKAN, weights=[60, 40], k=1)[0]
        rows.append({
            "dosen_id": f"0{random.randint(100000, 999999)}{i:03d}",
            "nama": _rand_name(),
            "prodi_id": prodi,
            "fakultas_id": meta["fakultas_id"],
            "jurusan_id": meta["jurusan_id"],
            "unit_organisasi_id": pick_unit_for_fakultas(meta["fakultas_id"]),
            "jenis_kelamin": random.choice(JENIS_KELAMIN),
            "status_asn": random.choices(STATUS_ASN, weights=[40, 20, 40], k=1)[0],
            "pendidikan_terakhir": pend,
            "jabatan_fungsional": random.choice(JABATAN_FUNGSIONAL),
            "sedang_tugas_belajar": random.random() < 0.08,
            "sertifikat_dosen": random.random() < 0.55,
            "berasal_praktisi": random.random() < 0.15,
            "tahun_bergabung": random.randint(2014, 2025),
            "ingested_at": ts,
        })
    return rows


def gen_kegiatan_dosen(dosen_rows: list[dict], avg_per_dosen: float = 3.0) -> list[dict]:
    ts = _now_ts()
    jenis_list = ["Tridarma_PT_Lain", "Praktisi_Industri", "Pembina_Prestasi", "QS100"]
    rows = []
    for d in dosen_rows:
        k = max(0, int(random.gauss(avg_per_dosen, 1.5)))
        for _ in range(k):
            tahun = random.randint(2020, 2025)
            mulai = _rand_date(date(tahun, 1, 1), date(tahun, 6, 30))
            rows.append({
                "kegiatan_id": _uid("KGT"),
                "dosen_id": d["dosen_id"],
                "jenis_kegiatan": random.choice(jenis_list),
                "nama_institusi": random.choice(INSTITUSI_MITRA),
                "tanggal_mulai": str(mulai),
                "tanggal_selesai": str(mulai + timedelta(days=random.randint(30, 365))),
                "tahun": tahun,
                "ingested_at": ts,
            })
    return rows


def gen_penelitian(dosen_rows: list[dict], avg: float = 2.5) -> list[dict]:
    ts = _now_ts()
    rows = []
    for d in dosen_rows:
        k = max(0, int(random.gauss(avg, 1.2)))
        for _ in range(k):
            rows.append({
                "penelitian_id": _uid("PNL"),
                "judul": f"Penelitian {random.choice(TOPIK_PENELITIAN)} - {_uid()}",
                "dosen_id": d["dosen_id"],
                "jurusan_id": d["jurusan_id"],
                "tahun": random.randint(2020, 2025),
                "skema": random.choice(SKEMA_PENELITIAN),
                "dana": random.choice([5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000, 250_000_000]),
                "topik": random.choice(TOPIK_PENELITIAN),
                "status_publikasi": random.choices(STATUS_PUBLIKASI, weights=[30, 45, 25], k=1)[0],
                "rekognisi_internasional": random.random() < 0.12,
                "diterapkan_masyarakat": random.random() < 0.20,
                "ingested_at": ts,
            })
    return rows


def gen_pengabdian(dosen_rows: list[dict], avg: float = 1.5) -> list[dict]:
    ts = _now_ts()
    rows = []
    for d in dosen_rows:
        k = max(0, int(random.gauss(avg, 1.0)))
        for _ in range(k):
            rows.append({
                "pkm_id": _uid("PKM"),
                "judul": f"Pengabdian {random.choice(TOPIK_PENELITIAN)} - {_uid()}",
                "dosen_id": d["dosen_id"],
                "jurusan_id": d["jurusan_id"],
                "tahun": random.randint(2020, 2025),
                "dana": random.choice([3_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000]),
                "lokasi": random.choice(KOTA_LAMPUNG),
                "rekognisi_internasional": random.random() < 0.05,
                "diterapkan_masyarakat": random.random() < 0.45,
                "ingested_at": ts,
            })
    return rows


def gen_kerjasama(n: int) -> list[dict]:
    ts = _now_ts()
    rows = []
    for _ in range(n):
        tahun = random.randint(2019, 2025)
        mulai = _rand_date(date(tahun, 1, 1), date(tahun, 12, 28))
        berakhir = mulai + timedelta(days=random.choice([365, 730, 1095, 1825]))
        rows.append({
            "kerjasama_id": _uid("KJS"),
            "jenis": random.choice(JENIS_KERJASAMA),
            "mitra": random.choice(INSTITUSI_MITRA),
            "kategori_mitra": random.choice(KATEGORI_MITRA),
            "lingkup": random.choice(LINGKUP),
            "prodi_id": random.choice(PRODI_S1_IDS + [""]),
            "tanggal_mulai": str(mulai),
            "tanggal_berakhir": str(berakhir),
            "status": "Aktif" if berakhir >= date.today() else "Tidak Aktif",
            "tahun": tahun,
            "ingested_at": ts,
        })
    return rows


def gen_mbkm(mahasiswa_rows: list[dict], pct: float = 0.25) -> list[dict]:
    ts = _now_ts()
    eligible = [m for m in mahasiswa_rows if m["angkatan"] >= 2020 and m["angkatan"] < 2025]
    sample = random.sample(eligible, k=min(int(len(eligible) * pct), len(eligible)))
    rows = []
    for m in sample:
        tahun = random.randint(max(m["angkatan"] + 1, 2021), 2025)
        rows.append({
            "mbkm_id": _uid("MBKM"),
            "mahasiswa_id": m["mahasiswa_id"],
            "prodi_id": m["prodi_id"],
            "jenis_mbkm": random.choice(JENIS_MBKM),
            "institusi_mitra": random.choice(INSTITUSI_MITRA),
            "sks_diakui": random.choice([6, 12, 20, 20, 22, 24]),
            "tahun": tahun,
            "semester": random.choice(["Ganjil", "Genap"]),
            "prestasi_nasional": random.random() < 0.08,
            "ingested_at": ts,
        })
    return rows


def gen_akreditasi() -> list[dict]:
    ts = _now_ts()
    rows = []
    for p in PRODI_MASTER:
        n_akred = random.randint(1, 3)
        for i in range(n_akred):
            tahun = p["tahun_berdiri"] + 2 + i * 3
            if tahun > 2025:
                continue
            tgl_sk = _rand_date(date(tahun, 1, 1), date(tahun, 12, 28))
            rows.append({
                "akreditasi_id": _uid("AKR"),
                "prodi_id": p["prodi_id"],
                "lembaga": random.choices(LEMBAGA_AKREDITASI, weights=[70, 20, 10], k=1)[0],
                "nama_lembaga_detail": random.choice(["BAN-PT", "LAM-Teknik", "LAM-Sains", "ABET", "ASIIN"]),
                "predikat": random.choices(PREDIKAT_AKREDITASI, weights=[15, 25, 30, 10, 15, 5], k=1)[0],
                "tanggal_sk": str(tgl_sk),
                "tanggal_berakhir": str(tgl_sk + timedelta(days=1825)),
                "tahun": tahun,
                "ingested_at": ts,
            })
    return rows


def gen_keuangan(tahun_range: tuple[int, int]) -> list[dict]:
    ts = _now_ts()
    rows = []
    for tahun in range(tahun_range[0], tahun_range[1] + 1):
        for triwulan in range(1, 5):
            for sumber in SUMBER_DANA:
                for komponen in KOMPONEN_ANGGARAN:
                    pagu = random.randint(500_000_000, 50_000_000_000)
                    realisasi = int(pagu * random.uniform(0.4, 0.98))
                    rows.append({
                        "anggaran_id": _uid("ANG"),
                        "tahun": tahun,
                        "sumber_dana": sumber,
                        "komponen": komponen,
                        "pagu": pagu,
                        "realisasi": realisasi,
                        "triwulan": triwulan,
                        "ingested_at": ts,
                    })
    return rows


def gen_prestasi(mahasiswa_rows: list[dict], dosen_rows: list[dict], n: int) -> list[dict]:
    ts = _now_ts()
    dosen_ids = [d["dosen_id"] for d in dosen_rows]
    rows = []
    for _ in range(n):
        m = random.choice(mahasiswa_rows)
        rows.append({
            "prestasi_id": _uid("PRS"),
            "mahasiswa_id": m["mahasiswa_id"],
            "nama_kompetisi": random.choice(KOMPETISI),
            "bidang": random.choice(BIDANG_PRESTASI),
            "tingkat": random.choices(TINGKAT_PRESTASI, weights=[30, 25, 30, 15], k=1)[0],
            "peringkat": random.choice(PERINGKAT),
            "tahun": random.randint(2020, 2025),
            "dosen_pembina_id": random.choice(dosen_ids) if random.random() > 0.2 else "",
            "ingested_at": ts,
        })
    return rows

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    profile_names = ", ".join(VOLUME_PROFILES)
    parser = argparse.ArgumentParser(description="ITERA Bronze Data Generator (Insight)")
    parser.add_argument(
        "--mode", choices=["full", "append"], default="full",
        help="full = overwrite semua CSV; append = tambah batch baru",
    )
    parser.add_argument(
        "--profile", choices=list(VOLUME_PROFILES), default="real",
        help=f"Preset volume ({profile_names}); default: real (populasi ITERA)",
    )
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Pengali tambahan di atas --profile (mis. aqe + scale 2 ≈ 45k mahasiswa)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=5_000,
        help="Jumlah mahasiswa baru per batch (mode append)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Direktori output (default: data/staging/)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed untuk reprodusibilitas",
    )
    parser.add_argument(
        "--skew-prodi", type=str, default=DEFAULT_SKEW_PRODI,
        help="prodi_id yang dipakai sebagai hot key skew (default: SD / Sains Data)",
    )
    parser.add_argument(
        "--skew-fraction", type=float, default=None,
        metavar="P",
        help="Fraksi baris ke prodi skew (0–1). Default: dari profil (aqe=0.75)",
    )
    parser.add_argument(
        "--no-skew", action="store_true",
        help="Distribusi prodi merata (nonaktifkan skew join sintetis)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Tampilkan rencana volume tanpa menulis CSV",
    )
    args = parser.parse_args()

    random.seed(args.seed if args.mode == "full" else None)

    if args.output_dir:
        out = Path(args.output_dir)
    else:
        out = Path(__file__).resolve().parent.parent / "data" / "staging"
    out.mkdir(parents=True, exist_ok=True)

    append = args.mode == "append"
    vol = _resolve_volume(args.profile, args.scale)
    skew_fraction = 0.0 if args.no_skew else (
        args.skew_fraction if args.skew_fraction is not None else float(vol["default_skew_fraction"])
    )
    skew_prodi = None if args.no_skew else args.skew_prodi
    if skew_prodi and skew_prodi not in PRODI_IDS:
        parser.error(f"--skew-prodi '{skew_prodi}' tidak ada. Pilihan: {', '.join(PRODI_IDS)}")

    print(f"\n{'='*60}")
    print(f"  ITERA Bronze Data Generator (Insight)")
    print(f"  mode={args.mode}  profile={args.profile}  scale={args.scale}")
    print(f"  skew: prodi={skew_prodi or '-'}  fraction={skew_fraction:.2f}")
    print(f"  Output: {out}")
    print(f"{'='*60}\n")

    # --- master: fakultas, organisasi, prodi (selalu overwrite) ---
    fakultas_rows = gen_fakultas()
    organisasi_rows = gen_organisasi_itera()
    prodi_rows = gen_prodi(args.scale)

    if args.mode == "full":
        n_mhs = int(vol["mahasiswa"])
        n_dosen = int(vol["dosen"])
        n_tendik = int(vol.get("tendik", ITERA_POPULATION["tendik"]))
        n_kerjasama = int(vol["kerjasama"])
        n_prestasi = int(vol["prestasi"])
        kegiatan_avg = float(vol["kegiatan_avg"])
        penelitian_avg = float(vol["penelitian_avg"])
        pengabdian_avg = float(vol["pengabdian_avg"])
        lulusan_pct = float(vol["lulusan_pct"])
        mbkm_pct = float(vol["mbkm_pct"])
        angkatan = (2016, 2025)
        tahun_keuangan = (2018, 2025)
    else:
        n_mhs = args.batch_size
        n_dosen = max(50, args.batch_size // 32)
        n_tendik = max(10, args.batch_size // 71)
        n_kerjasama = max(10, args.batch_size // 80)
        n_prestasi = max(100, args.batch_size // 10)
        kegiatan_avg = 3.0
        penelitian_avg = 2.5
        pengabdian_avg = 1.5
        lulusan_pct = 0.35
        mbkm_pct = 0.25
        angkatan = (2024, 2025)
        tahun_keuangan = (2025, 2025)

    est_derived = int(n_dosen * kegiatan_avg) + int(n_dosen * penelitian_avg) + int(n_dosen * pengabdian_avg)
    est_total = (
        len(prodi_rows) + n_mhs + int(n_mhs * lulusan_pct * 0.5) + n_dosen + n_tendik + est_derived
        + n_kerjasama + int(n_mhs * mbkm_pct * 0.4) + n_prestasi + 500
    )
    print("  Rencana volume (perkiraan) — acuan ITERA real:")
    print(f"    populasi kampus   : {ITERA_POPULATION['mahasiswa']:,} mhs | "
          f"{ITERA_POPULATION['dosen']:,} dosen | {ITERA_POPULATION['tendik']:,} tendik")
    print(f"    raw_mahasiswa      : {n_mhs:>10,}")
    print(f"    raw_dosen          : {n_dosen:>10,}")
    print(f"    raw_tendik         : {n_tendik:>10,}")
    print(f"    raw_prestasi       : {n_prestasi:>10,}")
    print(f"    derived (dosen×avg): {est_derived:>10,}  (kegiatan+penelitian+pengabdian)")
    print(f"    total perkiraan    : {est_total:>10,} baris")
    if skew_fraction > 0:
        print(f"    hot key join       : ~{skew_fraction*100:.0f}% baris → prodi_id={skew_prodi}")
    print()

    if args.dry_run:
        print("  (--dry-run: tidak menulis file)\n")
        return

    _write_csv(out / "raw_fakultas.csv", fakultas_rows, append=False)
    _write_csv(out / "raw_organisasi_itera.csv", organisasi_rows, append=False)
    _write_csv(out / "raw_prodi.csv", prodi_rows, append=False)

    # --- raw_mahasiswa ---
    mhs = gen_mahasiswa(n_mhs, angkatan, skew_prodi=skew_prodi, skew_fraction=skew_fraction)
    _write_csv(out / "raw_mahasiswa.csv", mhs, append=append)

    # --- raw_lulusan ---
    lulusan = gen_lulusan(mhs, pct=lulusan_pct)
    _write_csv(out / "raw_lulusan.csv", lulusan, append=append)

    # --- raw_dosen ---
    dosen = gen_dosen(n_dosen, skew_prodi=skew_prodi, skew_fraction=skew_fraction)
    _write_csv(out / "raw_dosen.csv", dosen, append=append)

    # --- raw_tendik ---
    tendik = gen_tendik(n_tendik)
    _write_csv(out / "raw_tendik.csv", tendik, append=append)

    # --- raw_kegiatan_dosen ---
    kegiatan = gen_kegiatan_dosen(dosen, avg_per_dosen=kegiatan_avg)
    _write_csv(out / "raw_kegiatan_dosen.csv", kegiatan, append=append)

    # --- raw_penelitian ---
    penelitian = gen_penelitian(dosen, avg=penelitian_avg)
    _write_csv(out / "raw_penelitian.csv", penelitian, append=append)

    # --- raw_pengabdian ---
    pengabdian = gen_pengabdian(dosen, avg=pengabdian_avg)
    _write_csv(out / "raw_pengabdian.csv", pengabdian, append=append)

    # --- raw_kerjasama ---
    kerjasama = gen_kerjasama(n_kerjasama)
    _write_csv(out / "raw_kerjasama.csv", kerjasama, append=append)

    # --- raw_mbkm ---
    mbkm = gen_mbkm(mhs, pct=mbkm_pct)
    _write_csv(out / "raw_mbkm.csv", mbkm, append=append)

    # --- raw_akreditasi ---
    akreditasi = gen_akreditasi()
    _write_csv(out / "raw_akreditasi.csv", akreditasi, append=append)

    # --- raw_keuangan ---
    keuangan = gen_keuangan(tahun_keuangan)
    _write_csv(out / "raw_keuangan.csv", keuangan, append=append)

    # --- raw_prestasi_mahasiswa ---
    prestasi = gen_prestasi(mhs, dosen, n_prestasi)
    _write_csv(out / "raw_prestasi_mahasiswa.csv", prestasi, append=append)

    counts = {
        "raw_fakultas.csv": len(fakultas_rows),
        "raw_organisasi_itera.csv": len(organisasi_rows),
        "raw_prodi.csv": len(prodi_rows),
        "raw_mahasiswa.csv": len(mhs),
        "raw_lulusan.csv": len(lulusan),
        "raw_dosen.csv": len(dosen),
        "raw_tendik.csv": len(tendik),
        "raw_kegiatan_dosen.csv": len(kegiatan),
        "raw_penelitian.csv": len(penelitian),
        "raw_pengabdian.csv": len(pengabdian),
        "raw_kerjasama.csv": len(kerjasama),
        "raw_mbkm.csv": len(mbkm),
        "raw_akreditasi.csv": len(akreditasi),
        "raw_keuangan.csv": len(keuangan),
        "raw_prestasi_mahasiswa.csv": len(prestasi),
    }
    total = sum(counts.values())
    total_bytes = sum((out / name).stat().st_size for name in counts if (out / name).exists())

    print(f"\n{'='*60}")
    print(f"  ✅ Total baris: {total:,}  |  disk: {total_bytes / (1024**2):.1f} MB")
    print(f"  profile={args.profile}  scale={args.scale}  skew_fraction={skew_fraction}")
    for name, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {n:>10,}  {name}")
    print(f"\n  File CSV: {out}/")
    print(f"  Langkah berikutnya: staging→bronze→silver→gold | metadata_full_experiment | aqe_full_experiment | mlops_pipeline")
    print(f"  Panduan: docs/generate-data/README.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
