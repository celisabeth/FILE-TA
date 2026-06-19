import type { AtlasEntity } from './atlasApi';
import { hydrateAtlasEntities, layerFromQualifiedName, searchEntities } from './atlasApi';
import { parseEntityProfiling, getBusinessMeta } from './entityProfiling';

export interface GlossaryTermFromMetadata {
	term: string;
	definition: string;
	category: string;
	source: 'silver_metadata' | 'gold_metadata' | 'local';
	related_assets?: string[];
}

/** Definisi untuk istilah yang muncul di BUSINESS_METADATA Silver */
const TERM_DEFINITIONS: Record<string, { definition: string; category: string }> = {
	'Mahasiswa Aktif': {
		definition: 'Mahasiswa dengan status akademik aktif pada semester berjalan',
		category: 'Academic',
	},
	MBKM: {
		definition: 'Merdeka Belajar Kampus Merdeka — program kredit di luar kampus (≥20 SKS)',
		category: 'Academic',
	},
	'SKS Luar Kampus': {
		definition: 'Satuan kredit semester yang diperoleh dari kegiatan di luar perguruan tinggi',
		category: 'Academic',
	},
	'Lulusan Terserap': {
		definition: 'Lulusan yang bekerja, melanjutkan studi, atau berwirausaha (tracer study)',
		category: 'Business',
	},
	'Tracer Study': {
		definition: 'Survei pelacakan alumni untuk mengukur penyerapan lulusan',
		category: 'Business',
	},
	'Masa Tunggu': {
		definition: 'Waktu antara lulus dan memperoleh pekerjaan pertama',
		category: 'Business',
	},
	'Dosen Tetap': {
		definition: 'Dosen dengan status kepegawaian tetap di perguruan tinggi',
		category: 'Academic',
	},
	Tridarma: {
		definition: 'Tri Dharma Perguruan Tinggi: pendidikan, penelitian, pengabdian masyarakat',
		category: 'Academic',
	},
	Serdos: {
		definition: 'Sertifikasi Dosen — sertifikat kompetensi mengajar',
		category: 'Academic',
	},
	'Jabatan Fungsional': {
		definition: 'Jenjang kepangkatan akademik dosen (Asisten Ahli, Lektor, dst.)',
		category: 'Academic',
	},
	'Rekognisi Internasional': {
		definition: 'Publikasi atau output penelitian terindeks internasional (Scopus/WoS)',
		category: 'Academic',
	},
	'Pengabdian Masyarakat': {
		definition: 'Kegiatan dosen untuk memecahkan masalah masyarakat (PkM)',
		category: 'Academic',
	},
	'Hibah Penelitian': {
		definition: 'Pendanaan eksternal untuk kegiatan penelitian',
		category: 'Academic',
	},
	MoU: {
		definition: 'Memorandum of Understanding — perjanjian kerjasama institusi',
		category: 'Governance',
	},
	PKS: {
		definition: 'Perjanjian Kerja Sama operasional antara ITERA dan mitra',
		category: 'Governance',
	},
	'Mitra Kerjasama': {
		definition: 'Organisasi/industri mitra dalam kerjasama pendidikan atau riset',
		category: 'Governance',
	},
	'BAN-PT': {
		definition: 'Badan Akreditasi Nasional Perguruan Tinggi',
		category: 'Governance',
	},
	LAM: {
		definition: 'Lembaga Akreditasi Mandiri untuk program studi',
		category: 'Governance',
	},
	'Akreditasi Internasional': {
		definition: 'Akreditasi prodi oleh lembaga internasional (AACSB, ABET, dll.)',
		category: 'Governance',
	},
	Unggul: {
		definition: 'Peringkat akreditasi tertinggi dalam sistem BAN-PT',
		category: 'Governance',
	},
	IKU: {
		definition: 'Indikator Kinerja Utama — metrik kinerja institusi dari Renstra',
		category: 'Business',
	},
	SAKIP: {
		definition: 'Sistem Akuntabilitas Kinerja Instansi Pemerintah',
		category: 'Governance',
	},
	PII: {
		definition: 'Personally Identifiable Information — data yang dapat mengidentifikasi individu',
		category: 'Security',
	},
};

const FALLBACK_TERMS: GlossaryTermFromMetadata[] = [
	{
		term: 'Medallion Architecture',
		definition:
			'Arsitektur lakehouse berlapis: Staging (CSV), Bronze (raw), Silver (clean), Gold (curated)',
		category: 'Technical',
		source: 'local',
	},
	{
		term: 'Star Schema',
		definition: 'Model data warehouse dengan tabel fakta dan dimensi untuk OLAP',
		category: 'Technical',
		source: 'local',
	},
	{
		term: 'Data Lineage',
		definition: 'Jejak transformasi data dari sumber hingga konsumsi',
		category: 'Governance',
		source: 'local',
	},
	{
		term: 'Apache Iceberg',
		definition: 'Format tabel open-source dengan ACID dan time travel di data lake',
		category: 'Technical',
		source: 'local',
	},
	{
		term: 'Apache Atlas',
		definition: 'Platform metadata dan data governance',
		category: 'Technical',
		source: 'local',
	},
	{
		term: 'Data Quality Score',
		definition: 'Skor kelengkapan data: PASS ≥80%, QUARANTINE 60–79%, REJECT <60%',
		category: 'Quality',
		source: 'local',
	},
	{
		term: 'Renstra',
		definition: 'Rencana Strategis ITERA 2020–2024 sebagai acuan target IKU',
		category: 'Business',
		source: 'local',
	},
];

function definitionForTerm(term: string): { definition: string; category: string } {
	if (TERM_DEFINITIONS[term]) return TERM_DEFINITIONS[term];
	return {
		definition: `Istilah bisnis terkait metadata lakehouse ITERA: ${term}`,
		category: 'Business',
	};
}

export function collectGlossaryTermsFromEntities(entities: AtlasEntity[]): GlossaryTermFromMetadata[] {
	const byTerm = new Map<string, GlossaryTermFromMetadata>();

	for (const entity of entities) {
		const attrs = entity.attributes || {};
		const qn = String(attrs.qualifiedName || '');
		const layer = String(attrs.layer || layerFromQualifiedName(qn));
		const profiling = parseEntityProfiling(attrs.profiling);
		const biz = getBusinessMeta(profiling);

		if (biz?.glossary_terms) {
			for (const term of biz.glossary_terms) {
				const def = definitionForTerm(term);
				const existing = byTerm.get(term);
				if (existing) {
					if (!existing.related_assets?.includes(qn)) {
						existing.related_assets = [...(existing.related_assets || []), qn];
					}
				} else {
					byTerm.set(term, {
						term,
						definition: def.definition,
						category: def.category,
						source: 'silver_metadata',
						related_assets: [qn],
					});
				}
			}
		}

		const kpi = profiling.kpi as Record<string, unknown> | undefined;
		if (layer === 'gold' && kpi?.iku_code) {
			const code = String(kpi.iku_code);
			const nama = String(kpi.iku_nama || code);
			byTerm.set(code, {
				term: code,
				definition: nama,
				category: 'Business',
				source: 'gold_metadata',
				related_assets: [qn],
			});
		}
	}

	return [...byTerm.values()].sort((a, b) => a.term.localeCompare(b.term));
}

export async function buildGlossaryFromAtlas(limit = 500): Promise<{
	terms: GlossaryTermFromMetadata[];
	fallback: GlossaryTermFromMetadata[];
	silverEntityCount: number;
	generatedAt: string;
	entities: AtlasEntity[];
}> {
	const [allRes, silverRes, goldRes] = await Promise.all([
		searchEntities('lakehouse_dataset', undefined, undefined, limit, 0),
		searchEntities('lakehouse_dataset', undefined, 'Silver_Layer', limit, 0),
		searchEntities('lakehouse_dataset', undefined, 'Gold_Layer', limit, 0),
	]);

	const stubs = mergeEntityLists(
		allRes.entities || [],
		silverRes.entities || [],
		goldRes.entities || [],
	);
	const entities = await hydrateAtlasEntities(stubs);

	const silverCount = entities.filter(
		(e) => (e.attributes?.layer || layerFromQualifiedName(e.attributes?.qualifiedName)) === 'silver',
	).length;

	return {
		terms: collectGlossaryTermsFromEntities(entities),
		fallback: FALLBACK_TERMS,
		silverEntityCount: silverCount,
		generatedAt: new Date().toISOString(),
		entities,
	};
}

/** Kata kunci untuk menghubungkan istilah lokal ke aset katalog (qualifiedName). */
const TERM_LINK_ALIASES: Record<string, string[]> = {
	iku: ['iku-', 'indikator kinerja', 'fact_iku', 'renstra'],
	renstra: ['renstra', 'iku', 'rencana strategis', 'fact_iku'],
	mbkm: ['mbkm', 'silver_mahasiswa', 'kerjasama'],
	tridarma: ['tridarma', 'kegiatan_dosen', 'silver_dosen'],
	serdos: ['serdos', 'sertifikasi', 'silver_dosen'],
	sakip: ['sakip', 'tata_kelola', 'fact_tata'],
	pii: ['pii', 'pii_columns', 'silver_mahasiswa', 'silver_dosen'],
	'medallion architecture': ['bronze.', 'silver.', 'gold.', 'staging.'],
	'star schema': ['dim_', 'fact_', 'gold.'],
	'data lineage': ['lineage', 'etl.', 'staging_to_bronze', 'bronze_to_silver'],
	'apache iceberg': ['iceberg', 'warehouse'],
	'apache atlas': ['lakehouse_dataset', 'atlas'],
	'data quality score': ['quality', 'quarantine', 'silver_'],
	prodi: ['dim_prodi', 'silver_prodi', 'raw_prodi'],
	nidn: ['dosen', 'nidn'],
	nim: ['mahasiswa', 'nim'],
};

function mergeEntityLists(...lists: AtlasEntity[][]): AtlasEntity[] {
	const byGuid = new Map<string, AtlasEntity>();
	for (const list of lists) {
		for (const e of list) {
			if (e?.guid) byGuid.set(e.guid, e);
		}
	}
	return [...byGuid.values()];
}

function entitySearchText(entity: AtlasEntity): string {
	const attrs = entity.attributes || {};
	const profiling = parseEntityProfiling(attrs.profiling);
	const biz = getBusinessMeta(profiling) || {};
	const kpi = (profiling.kpi as Record<string, unknown>) || {};
	const parts: string[] = [
		String(attrs.qualifiedName || ''),
		String(attrs.name || ''),
		String(attrs.description || ''),
		String(attrs.layer || ''),
		...(biz.glossary_terms || []),
		...(biz.iku_relevance || []),
		String(kpi.iku_code || ''),
		String(kpi.iku_nama || ''),
	];
	return parts.join(' ').toLowerCase();
}

export function linkRelatedAssets(
	terms: GlossaryTermFromMetadata[],
	entities: AtlasEntity[],
): GlossaryTermFromMetadata[] {
	const indexed = entities
		.map((e) => ({
			qn: String(e.attributes?.qualifiedName || ''),
			text: entitySearchText(e),
		}))
		.filter((x) => x.qn);

	return terms.map((term) => {
		if (term.related_assets && term.related_assets.length > 0) {
			return term;
		}
		const needle = term.term.toLowerCase();
		const aliases = TERM_LINK_ALIASES[needle] || [needle];
		const related: string[] = [];
		for (const { qn, text } of indexed) {
			if (aliases.some((a) => a.length > 2 && text.includes(a))) {
				if (!related.includes(qn)) related.push(qn);
			}
		}
		return { ...term, related_assets: related.slice(0, 6) };
	});
}

export function mergeGlossaryTerms(
	atlasTerms: { term: string; definition: string; category: string; guid?: string }[],
	metadataTerms: GlossaryTermFromMetadata[],
	fallbackTerms: GlossaryTermFromMetadata[],
	entities: AtlasEntity[] = [],
): Array<GlossaryTermFromMetadata & { source: string; guid?: string }> {
	const map = new Map<string, GlossaryTermFromMetadata & { source: string; guid?: string }>();

	for (const t of fallbackTerms) {
		map.set(t.term.toLowerCase(), { ...t, source: 'local' });
	}
	for (const t of metadataTerms) {
		const key = t.term.toLowerCase();
		const prev = map.get(key);
		map.set(key, {
			...prev,
			...t,
			source: t.source,
			related_assets: t.related_assets?.length ? t.related_assets : prev?.related_assets,
		});
	}
	for (const t of atlasTerms) {
		const key = t.term.toLowerCase();
		const prev = map.get(key);
		map.set(key, {
			term: t.term,
			definition: t.definition || prev?.definition || '',
			category: t.category || prev?.category || 'Atlas',
			source: 'atlas',
			guid: t.guid,
			related_assets: prev?.related_assets,
		});
	}

	const merged = [...map.values()].sort((a, b) => a.term.localeCompare(b.term));
	return linkRelatedAssets(merged, entities) as Array<
		GlossaryTermFromMetadata & { source: string; guid?: string }
	>;
}
