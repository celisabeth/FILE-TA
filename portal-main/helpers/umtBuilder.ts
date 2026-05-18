import type { AtlasEntity } from './atlasApi';
import {
	hydrateAtlasEntities,
	layerFromQualifiedName,
	normalizeDatasetAttributes,
	searchEntities,
} from './atlasApi';
import { loadDatasetSummaryIndex } from './metricsReader';
import { enrichUmtRows } from './umtEnrichment';

export interface UmtRow {
	asset_qualified_name: string;
	guid: string;
	layer: string;
	technical_json: Record<string, unknown>;
	business_json: Record<string, unknown>;
	operational_json: Record<string, unknown>;
	last_enriched_at: string | null;
}

function parseJsonField(raw: unknown): Record<string, unknown> {
	if (!raw) return {};
	if (typeof raw === 'object') return raw as Record<string, unknown>;
	if (typeof raw !== 'string') return {};
	try {
		const parsed = JSON.parse(raw);
		return typeof parsed === 'object' && parsed !== null ? parsed : {};
	} catch {
		return {};
	}
}

function parseStringList(raw: unknown): string[] {
	const obj = parseJsonField(raw);
	if (Array.isArray(raw)) return raw as string[];
	if (Array.isArray(obj)) return obj as string[];
	return [];
}

function buildTechnicalJson(attrs: Record<string, any>): Record<string, unknown> {
	return {
		schema: parseJsonField(attrs.schema_def),
		format: attrs.format ?? null,
		location: attrs.location ?? null,
		row_count: attrs.row_count ?? null,
		column_count: attrs.column_count ?? null,
		pii_columns: parseStringList(attrs.pii_columns),
	};
}

function buildBusinessJson(attrs: Record<string, any>): Record<string, unknown> {
	const profiling = parseJsonField(attrs.profiling);
	const business = (profiling.business as Record<string, unknown>) || {};

	return {
		description: attrs.description ?? null,
		owner: business.owner ?? null,
		domain: business.domain ?? attrs.domain ?? null,
		glossary_terms: business.glossary_terms ?? [],
		iku_relevance: business.iku_relevance ?? [],
		update_frequency: business.update_frequency ?? null,
		kpi: profiling.kpi ?? null,
		consumption: profiling.consumption ?? null,
		ai_metadata: profiling.ai_metadata ?? null,
	};
}

function buildOperationalJson(
	attrs: Record<string, any>,
	classifications: { typeName: string }[],
): Record<string, unknown> {
	const profiling = parseJsonField(attrs.profiling);

	return {
		classifications: classifications.map((c) => c.typeName),
		quality: profiling.quality ?? null,
		compliance: profiling.compliance ?? null,
		star_schema: profiling.star_schema ?? null,
		transformations: profiling.transformations ?? null,
	};
}

function resolveLastEnrichedAt(attrs: Record<string, any>): string | null {
	if (attrs.enriched_at) return String(attrs.enriched_at);
	if (attrs.ingested_at) return String(attrs.ingested_at);
	const profiling = parseJsonField(attrs.profiling);
	if (profiling.profiled_at) return String(profiling.profiled_at);
	return null;
}

export function entityToUmtRow(entity: AtlasEntity): UmtRow {
	const attrs = normalizeDatasetAttributes(entity.attributes);
	const qn = String(attrs.qualifiedName || '');
	const layer = String(attrs.layer || layerFromQualifiedName(qn));
	const classifications = entity.classifications || [];

	return {
		asset_qualified_name: qn,
		guid: entity.guid,
		layer,
		technical_json: buildTechnicalJson(attrs),
		business_json: buildBusinessJson(attrs),
		operational_json: buildOperationalJson(attrs, classifications),
		last_enriched_at: resolveLastEnrichedAt(attrs),
	};
}

const LAYER_ORDER = ['staging', 'bronze', 'silver', 'gold', 'unknown'];

export function sortUmtRows(rows: UmtRow[]): UmtRow[] {
	return [...rows].sort((a, b) => {
		const la = LAYER_ORDER.indexOf(a.layer);
		const lb = LAYER_ORDER.indexOf(b.layer);
		if (la !== lb) return la - lb;
		return a.asset_qualified_name.localeCompare(b.asset_qualified_name);
	});
}

export async function buildUmtFromAtlas(limit = 500): Promise<{
	rows: UmtRow[];
	approximateCount: number;
	generatedAt: string;
}> {
	const result = await searchEntities('lakehouse_dataset', undefined, undefined, limit, 0);
	const entities = await hydrateAtlasEntities(result.entities || []);
	const datasetSummary = await loadDatasetSummaryIndex();
	const rows = sortUmtRows(
		enrichUmtRows(entities.map(entityToUmtRow), datasetSummary),
	);

	return {
		rows,
		approximateCount: result.approximateCount ?? rows.length,
		generatedAt: new Date().toISOString(),
	};
}
