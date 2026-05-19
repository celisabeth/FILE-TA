"""
Referensi master ITERA — fakultas, program studi, organisasi.

Dipakai oleh: generate_bronze_data.py, bronze_to_silver*, silver_to_gold*, benchmark demo.
Kolom `jurusan_id` di CSV legacy = kode fakultas (FS, FTI, FTIK).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fakultas (3)
# ---------------------------------------------------------------------------

FAKULTAS: dict[str, str] = {
    "FS": "Fakultas Sains",
    "FTI": "Fakultas Teknologi Industri",
    "FTIK": "Fakultas Teknologi Infrastruktur dan Kewilayahan",
}

# Alias untuk pipeline Spark yang masih memakai nama JURUSAN_MAP
JURUSAN_MAP: dict[str, str] = FAKULTAS
FAKULTAS_MAP: dict[str, str] = FAKULTAS

FAKULTAS_IDS = list(FAKULTAS.keys())

# ---------------------------------------------------------------------------
# Program studi per fakultas: (prodi_id, nama_prodi, jenjang)
# ---------------------------------------------------------------------------

_PRODI_BY_FAKULTAS: dict[str, list[tuple[str, str, str]]] = {
    "FS": [
        ("FI", "Fisika", "S1"),
        ("MFI", "Magister Fisika", "S2"),
        ("MA", "Matematika", "S1"),
        ("KI", "Kimia", "S1"),
        ("BI", "Biologi", "S1"),
        ("AT", "Sains Aktuaria", "S1"),
        ("SLL", "Sains Lingkungan Kelautan", "S1"),
        ("SD", "Sains Data", "S1"),
        ("SAP", "Sains Atmosfir Keplanetan", "S1"),
        ("FA", "Farmasi", "S1"),
    ],
    "FTI": [
        ("EL", "Teknik Elektro", "S1"),
        ("GF", "Teknik Geofisika", "S1"),
        ("GL", "Teknik Geologi", "S1"),
        ("IF", "Teknik Informatika", "S1"),
        ("MS", "Teknik Mesin", "S1"),
        ("MT", "Teknik Material", "S1"),
        ("TBS", "Teknik Biosistem", "S1"),
        ("TI", "Teknik Industri", "S1"),
        ("TF", "Teknik Fisika", "S1"),
        ("TK", "Teknik Kimia", "S1"),
        ("TP", "Teknologi Pangan", "S1"),
        ("TIP", "Teknologi Industri Pertanian", "S1"),
        ("TSE", "Teknik Sistem Energi", "S1"),
        ("TA", "Teknik Pertambangan", "S1"),
        ("TT", "Teknik Telekomunikasi", "S1"),
        ("IA", "Rekayasa Instrumentasi dan Automasi", "S1"),
        ("KOS", "Rekayasa Kosmetik", "S1"),
        ("BM", "Teknik Biomedis", "S1"),
        ("RH", "Rekayasa Kehutanan", "S1"),
        ("RMG", "Rekayasa Minyak dan Gas", "S1"),
        ("RO", "Rekayasa Keolahragaan", "S1"),
    ],
    "FTIK": [
        ("AR", "Arsitektur", "S1"),
        ("ARL", "Arsitektur Lanskap", "S1"),
        ("SI", "Teknik Sipil", "S1"),
        ("KA", "Teknik Perkeretaapian", "S1"),
        ("DKV", "Desain Komunikasi Visual", "S1"),
        ("PWK", "Perencanaan Wilayah dan Kota", "S1"),
        ("GT", "Teknik Geomatika", "S1"),
        ("TL", "Teknik Lingkungan", "S1"),
        ("KL", "Teknik Kelautan", "S1"),
        ("TKA", "Rekayasa Tata Kelola Air Terpadu", "S1"),
        ("PAR", "Pariwisata", "S1"),
    ],
}

# Tahun berdiri perkiraan (S2 sedikit lebih baru)
_TAHUN_BERDIRI: dict[str, int] = {
    "MFI": 2019,
    "SD": 2020,
    "SAP": 2021,
    "AT": 2018,
    "SLL": 2017,
    "KOS": 2020,
    "BM": 2019,
    "TKA": 2021,
    "PAR": 2018,
}


def _build_prodi_master() -> list[dict]:
    rows: list[dict] = []
    for fakultas_id, prodis in _PRODI_BY_FAKULTAS.items():
        nama_fakultas = FAKULTAS[fakultas_id]
        for prodi_id, nama_prodi, jenjang in prodis:
            rows.append({
                "prodi_id": prodi_id,
                "nama_prodi": nama_prodi,
                "jenjang": jenjang,
                "fakultas_id": fakultas_id,
                "jurusan_id": fakultas_id,
                "nama_fakultas": nama_fakultas,
                "tahun_berdiri": _TAHUN_BERDIRI.get(prodi_id, 2015 if jenjang == "S1" else 2020),
            })
    return rows


PRODI_MASTER: list[dict] = _build_prodi_master()
PRODI_IDS = [p["prodi_id"] for p in PRODI_MASTER]
PRODI_S1_IDS = [p["prodi_id"] for p in PRODI_MASTER if p["jenjang"] == "S1"]

DEFAULT_SKEW_PRODI = "SD"

# Populasi kampus (referensi operasional ITERA, ~2024/2025)
ITERA_POPULATION = {
    "mahasiswa": 22_621,
    "dosen": 705,
    "tendik": 320,
}

# Rasio turunan dari populasi real (kerjasama/prestasi mengikuti skala mahasiswa)
_DERIVED_AT_REAL_SCALE = {
    "kerjasama": 380,
    "prestasi": 2_300,
    "kegiatan_avg": 2.8,
    "penelitian_avg": 2.2,
    "pengabdian_avg": 1.3,
    "lulusan_pct": 0.35,
    "mbkm_pct": 0.24,
}

# Unit kerja tendik (bukan home-base prodi)
TENDIK_UNIT_IDS = [
    "REKTOR",
    "WR_AKADEMIK",
    "WR_KEUANGAN",
    "SPI",
    "BAPU",
    "BAG_UM_AKAD",
    "LPPM",
    "LP3M",
    "UPA_PERPUSTAKAAN",
    "UPA_TIK",
    "UPA_BAHASA",
    "UPA_LABTERPADU",
]

TENDIK_JABATAN = [
    "Staf Administrasi",
    "Staf Akademik",
    "Pranata Komputer",
    "Staf Keuangan",
    "Staf Humas",
    "Laboran",
    "Staf Perpustakaan",
    "Staf Kemahasiswaan",
]


def build_volume_profile(
    *,
    mahasiswa: int | None = None,
    dosen: int | None = None,
    tendik: int | None = None,
    scale: float = 1.0,
    skew_fraction: float = 0.0,
    derived_scale: float | None = None,
) -> dict[str, int | float]:
    """
    Hitung target baris profil dari populasi ITERA × scale.

    derived_scale: pengali kerjasama/prestasi (default = scale). Untuk stress test
    bisa set scale=3 pada mahasiswa saja lewat profil aqe-stress.
    """
    m = int((mahasiswa if mahasiswa is not None else ITERA_POPULATION["mahasiswa"]) * scale)
    d = int((dosen if dosen is not None else ITERA_POPULATION["dosen"]) * scale)
    t = int((tendik if tendik is not None else ITERA_POPULATION["tendik"]) * scale)
    ds = derived_scale if derived_scale is not None else scale
    base_m = ITERA_POPULATION["mahasiswa"]
    ratio = max(0.25, m / base_m)

    return {
        "mahasiswa": m,
        "dosen": d,
        "tendik": t,
        "kerjasama": max(80, int(_DERIVED_AT_REAL_SCALE["kerjasama"] * ratio * ds / max(scale, 0.01))),
        "prestasi": max(400, int(_DERIVED_AT_REAL_SCALE["prestasi"] * ratio * ds / max(scale, 0.01))),
        "kegiatan_avg": _DERIVED_AT_REAL_SCALE["kegiatan_avg"],
        "penelitian_avg": _DERIVED_AT_REAL_SCALE["penelitian_avg"],
        "pengabdian_avg": _DERIVED_AT_REAL_SCALE["pengabdian_avg"],
        "lulusan_pct": _DERIVED_AT_REAL_SCALE["lulusan_pct"],
        "mbkm_pct": _DERIVED_AT_REAL_SCALE["mbkm_pct"],
        "default_skew_fraction": skew_fraction,
    }


def pick_unit_for_tendik() -> str:
    import random

    return random.choice(TENDIK_UNIT_IDS)

# ---------------------------------------------------------------------------
# Organisasi ITERA (metadata / stewardship / unit kerja)
# ---------------------------------------------------------------------------

ITERA_ORGANISASI: list[dict] = [
    {"org_id": "REKTOR", "nama_organisasi": "Rektor", "tipe": "Pimpinan", "parent_org_id": "", "tingkat": 1},
    {"org_id": "WR_AKADEMIK", "nama_organisasi": "Wakil Rektor Bidang Akademik dan Kemahasiswaan", "tipe": "Pimpinan", "parent_org_id": "REKTOR", "tingkat": 2},
    {"org_id": "WR_KEUANGAN", "nama_organisasi": "Wakil Rektor Bidang Keuangan dan Umum", "tipe": "Pimpinan", "parent_org_id": "REKTOR", "tingkat": 2},
    {"org_id": "SPI", "nama_organisasi": "Satuan Pengawas Internal (SPI)", "tipe": "Satuan", "parent_org_id": "REKTOR", "tingkat": 2},
    {"org_id": "BAPU", "nama_organisasi": "Kepala Biro Akademik dan Perencanaan dan Umum", "tipe": "Biro", "parent_org_id": "WR_KEUANGAN", "tingkat": 3},
    {"org_id": "BAG_UM_AKAD", "nama_organisasi": "Kepala Bagian Umum dan Akademik", "tipe": "Bagian", "parent_org_id": "BAPU", "tingkat": 4},
    {"org_id": "DEKAN_FS", "nama_organisasi": "Dekan Fakultas Sains", "tipe": "Fakultas", "parent_org_id": "WR_AKADEMIK", "tingkat": 3, "fakultas_id": "FS"},
    {"org_id": "DEKAN_FTI", "nama_organisasi": "Dekan Fakultas Teknologi Industri", "tipe": "Fakultas", "parent_org_id": "WR_AKADEMIK", "tingkat": 3, "fakultas_id": "FTI"},
    {"org_id": "DEKAN_FTIK", "nama_organisasi": "Dekan Fakultas Teknologi Infrastruktur dan Kewilayahan", "tipe": "Fakultas", "parent_org_id": "WR_AKADEMIK", "tingkat": 3, "fakultas_id": "FTIK"},
    {"org_id": "SENAT", "nama_organisasi": "Senat", "tipe": "Senat", "parent_org_id": "REKTOR", "tingkat": 2},
    {"org_id": "LPPM", "nama_organisasi": "Kepala Lembaga Penelitian dan Pengabdian kepada Masyarakat", "tipe": "Lembaga", "parent_org_id": "WR_AKADEMIK", "tingkat": 3},
    {"org_id": "LP3M", "nama_organisasi": "Kepala Lembaga Penjaminan Mutu dan Pengembangan Pembelajaran", "tipe": "Lembaga", "parent_org_id": "WR_AKADEMIK", "tingkat": 3},
    {"org_id": "UPA_PERPUSTAKAAN", "nama_organisasi": "UPA Perpustakaan", "tipe": "UPA", "parent_org_id": "WR_AKADEMIK", "tingkat": 3},
    {"org_id": "UPA_TIK", "nama_organisasi": "UPA Teknologi Informasi dan Komunikasi (TIK)", "tipe": "UPA", "parent_org_id": "WR_KEUANGAN", "tingkat": 3},
    {"org_id": "UPA_BAHASA", "nama_organisasi": "UPA Bahasa", "tipe": "UPA", "parent_org_id": "WR_AKADEMIK", "tingkat": 3},
    {"org_id": "UPA_KFS", "nama_organisasi": "UPA Konservasi Flora Sumatera", "tipe": "UPA", "parent_org_id": "DEKAN_FS", "tingkat": 4, "fakultas_id": "FS"},
    {"org_id": "UPA_LABTERPADU", "nama_organisasi": "UPA Laboratorium Terpadu", "tipe": "UPA", "parent_org_id": "WR_AKADEMIK", "tingkat": 3},
]

ORG_IDS = [o["org_id"] for o in ITERA_ORGANISASI]

DEKAN_BY_FAKULTAS: dict[str, str] = {
    "FS": "DEKAN_FS",
    "FTI": "DEKAN_FTI",
    "FTIK": "DEKAN_FTIK",
}


def fakultas_for_prodi(prodi_id: str) -> str:
    for p in PRODI_MASTER:
        if p["prodi_id"] == prodi_id:
            return p["fakultas_id"]
    raise KeyError(prodi_id)


def pick_unit_for_fakultas(fakultas_id: str) -> str:
    """Unit organisasi yang masuk akal untuk dosen di fakultas tertentu."""
    import random

    pool = [DEKAN_BY_FAKULTAS[fakultas_id], "LPPM", "LP3M", "UPA_LABTERPADU"]
    if fakultas_id == "FS":
        pool.append("UPA_KFS")
    if fakultas_id == "FTI":
        pool.append("UPA_TIK")
    pool.extend(["BAG_UM_AKAD", "UPA_PERPUSTAKAAN"])
    return random.choice(pool)
