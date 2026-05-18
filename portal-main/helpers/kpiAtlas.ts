import type { AtlasEntity } from './atlasApi';
import { hydrateAtlasEntities, searchEntities } from './atlasApi';

export const LEADERSHIP_CONSUMERS = [
	{
		role: 'Rektor',
		desc: 'Ringkasan capaian seluruh IKU institusi',
		icon: 'Person',
	},
	{
		role: 'Wakil Rektor Bidang Akademik & Kemahasiswaan',
		desc: 'IKU-1, IKU-2, IKU-7 (lulusan, MBKM, metode pembelajaran)',
		icon: 'School',
	},
	{
		role: 'Wakil Rektor Bidang Keuangan & Umum',
		desc: 'SAKIP, anggaran, dan tata kelola institusi',
		icon: 'AccountBalance',
	},
	{
		role: 'Kepala Biro Akademik Perencanaan dan Umum',
		desc: 'Perencanaan strategis, rekap IKU, pelaporan Renstra',
		icon: 'Assignment',
	},
	{
		role: 'Kepala Bagian Umum dan Akademik',
		desc: 'Data operasional akademik dan dimensi prodi/mahasiswa',
		icon: 'MenuBook',
	},
	{
		role: 'Dekan Fakultas Sains',
		desc: 'Drill-down capaian IKU per prodi fakultas Sains',
		icon: 'Biotech',
	},
	{
		role: 'Wakil Rektor Bidang Teknologi Infrastruktur dan Kewilayahan',
		desc: 'Drill-down capaian IKU per prodi fakultas FTIK',
		icon: 'Engineering',
	},
	{
		role: 'Dekan Fakultas Teknologi Industri',
		desc: 'Drill-down capaian IKU per prodi fakultas FTI',
		icon: 'PrecisionManufacturing',
	},
] as const;

export const IKU_DEFINITIONS = [
	{
		code: 'IKU-1',
		name: 'Lulusan bekerja/studi/wirausaha',
		icon: 'School',
		color: 'primary',
		target2024: 78,
		fact: 'fact_iku1_lulusan',
	},
	{
		code: 'IKU-2',
		name: 'Mahasiswa MBKM / prestasi nasional',
		icon: 'EmojiEvents',
		color: 'primary',
		target2024: 35,
		fact: 'fact_iku2_mbkm',
	},
	{
		code: 'IKU-3',
		name: 'Dosen tridarma luar/praktisi',
		icon: 'Groups',
		color: 'primary',
		target2024: 25,
		fact: 'fact_iku3_dosen_tridarma',
	},
	{
		code: 'IKU-4',
		name: 'Dosen S3/sertifikat/praktisi',
		icon: 'WorkspacePremium',
		color: 'primary',
		target2024: 50,
		fact: 'fact_iku4_kualifikasi_dosen',
	},
	{
		code: 'IKU-5',
		name: 'Rasio output penelitian intl per dosen',
		icon: 'Science',
		color: 'primary',
		target2024: 0.25,
		fact: 'fact_iku5_penelitian_pkm',
	},
	{
		code: 'IKU-6',
		name: 'Prodi bekerjasama mitra',
		icon: 'Handshake',
		color: 'primary',
		target2024: 60,
		fact: 'fact_iku6_kerjasama_prodi',
	},
	{
		code: 'IKU-7',
		name: 'MK case method / team-based',
		icon: 'AutoStories',
		color: 'primary',
		target2024: 40,
		fact: 'fact_iku7_metode_pembelajaran',
	},
	{
		code: 'IKU-8',
		name: 'Prodi akreditasi internasional',
		icon: 'Public',
		color: 'primary',
		target2024: 3.0,
		fact: 'fact_iku8_akreditasi_internasional',
	},
] as const;

export type IkuDefinition = (typeof IKU_DEFINITIONS)[number];

export interface KpiCardView {
	code: string;
	name: string;
	icon: string;
	color: string;
	target2024: number;
	fact: string;
	registered: boolean;
	rowCount: number;
	capaian: number | null;
	target: number;
	status?: string;
	satuan: string;
	formula?: string;
	qualifiedName?: string;
	guid?: string;
}

export interface KpiDashboardPayload {
	generatedAt: string;
	goldCount: number;
	ikuRegistered: number;
	dimensionCount: number;
	factCount: number;
	cards: KpiCardView[];
}

export function parseProfiling(entity?: AtlasEntity): Record<string, any> {
	const raw = entity?.attributes?.profiling;
	if (!raw) return {};
	if (typeof raw === 'object') return raw as Record<string, any>;
	if (typeof raw !== 'string') return {};
	try {
		return JSON.parse(raw);
	} catch {
		return {};
	}
}

export function mergeAtlasEntities(...lists: AtlasEntity[][]): AtlasEntity[] {
	const byGuid = new Map<string, AtlasEntity>();
	for (const list of lists) {
		for (const e of list) {
			if (e?.guid) byGuid.set(e.guid, e);
		}
	}
	return [...byGuid.values()];
}

export function matchIkuEntity(
	entities: AtlasEntity[],
	iku: { code: string; fact: string },
): AtlasEntity | undefined {
	return entities.find((e) => {
		const name = (e.attributes?.name || '') as string;
		const qn = (e.attributes?.qualifiedName || '') as string;
		const layer = (e.attributes?.layer || '') as string;

		if (name === iku.fact) return true;
		if (qn === `gold.${iku.fact}@lakehouse` || qn.includes(iku.fact)) return true;
		if (layer === 'gold' && name.includes(iku.fact.replace('fact_', ''))) return true;

		const prof = parseProfiling(e);
		if (prof.kpi?.iku_code === iku.code) return true;

		return false;
	});
}

function isGoldEntity(e: AtlasEntity): boolean {
	const layer = e.attributes?.layer;
	const qn = String(e.attributes?.qualifiedName || '');
	return layer === 'gold' || qn.startsWith('gold.');
}

function tableType(entity?: AtlasEntity): string {
	const prof = parseProfiling(entity);
	return String(prof.star_schema?.table_type || '');
}

export function buildKpiCard(iku: IkuDefinition, matched?: AtlasEntity): KpiCardView {
	const profiling = parseProfiling(matched);
	const kpiMeta = profiling.kpi || {};
	const rowCount = Number(matched?.attributes?.row_count ?? 0);
	const capaianRaw = kpiMeta.nilai_capaian;
	const capaian =
		capaianRaw === null || capaianRaw === undefined || capaianRaw === ''
			? null
			: Number(capaianRaw);

	return {
		code: iku.code,
		name: iku.name,
		icon: iku.icon,
		color: iku.color,
		target2024: iku.target2024,
		fact: iku.fact,
		registered: Boolean(matched),
		rowCount: Number.isFinite(rowCount) ? rowCount : 0,
		capaian: capaian != null && !Number.isNaN(capaian) ? capaian : null,
		target: Number(kpiMeta.nilai_target ?? iku.target2024),
		status: kpiMeta.status_capaian as string | undefined,
		satuan: kpiMeta.satuan || (iku.code === 'IKU-5' ? 'Rasio' : '%'),
		formula: kpiMeta.formula as string | undefined,
		qualifiedName: matched?.attributes?.qualifiedName as string | undefined,
		guid: matched?.guid,
	};
}

export async function buildKpiDashboardFromAtlas(): Promise<KpiDashboardPayload> {
	const [kpiRes, goldRes, queryRes] = await Promise.all([
		searchEntities('lakehouse_dataset', undefined, 'KPI_Metric', 50, 0),
		searchEntities('lakehouse_dataset', undefined, 'Gold_Layer', 100, 0),
		searchEntities('lakehouse_dataset', 'gold.fact_iku', undefined, 50, 0),
	]);

	const stubs = mergeAtlasEntities(
		kpiRes.entities || [],
		goldRes.entities || [],
		queryRes.entities || [],
	).filter(isGoldEntity);

	const goldEntities = await hydrateAtlasEntities(stubs);

	const dimensionCount = goldEntities.filter((e) => tableType(e) === 'dimension').length;
	const factCount = goldEntities.filter((e) => tableType(e) === 'fact').length;

	const cards = IKU_DEFINITIONS.map((iku) =>
		buildKpiCard(iku, matchIkuEntity(goldEntities, iku)),
	);

	return {
		generatedAt: new Date().toISOString(),
		goldCount: goldRes.approximateCount || goldEntities.length,
		ikuRegistered: cards.filter((c) => c.registered).length,
		dimensionCount,
		factCount,
		cards,
	};
}

export function kpiStatusColor(status?: string): 'success' | 'warning' | 'danger' | 'info' {
	switch (status) {
		case 'Tercapai':
			return 'success';
		case 'On Track':
			return 'warning';
		case 'Tidak Tercapai':
			return 'danger';
		default:
			return 'info';
	}
}
