import type { UmtRow } from './umtBuilder';
import type { DatasetSummaryTable } from './metricsReader.types';

const DEFAULT_DOMAIN = 'ITERA Data Lakehouse';

const LAYER_BUSINESS_DEFAULTS: Record<string, { owner?: string; update_frequency?: string }> = {
	staging: {
		owner: 'Tim Data Ingestion',
		update_frequency: 'batch (per upload CSV)',
	},
	bronze: { owner: 'data-platform', update_frequency: 'batch' },
	silver: { owner: 'data-governance', update_frequency: 'batch' },
	gold: { owner: 'Biro Akademik & Perencanaan', update_frequency: 'harian (OLAP refresh)' },
};

function tableNameFromQn(qualifiedName: string): string {
	const base = qualifiedName.split('@', 1)[0];
	const dot = base.indexOf('.');
	return dot >= 0 ? base.slice(dot + 1) : base;
}

function isEmpty(val: unknown): boolean {
	if (val === null || val === undefined) return true;
	if (typeof val === 'string' && !val.trim()) return true;
	if (Array.isArray(val) && val.length === 0) return true;
	if (typeof val === 'object' && !Array.isArray(val) && Object.keys(val as object).length === 0) {
		return true;
	}
	return false;
}

function mergeTechnical(target: Record<string, unknown>, source: Record<string, unknown>) {
	for (const key of ['schema', 'format', 'location', 'row_count', 'column_count', 'pii_columns']) {
		if (isEmpty(target[key]) && !isEmpty(source[key])) {
			target[key] = source[key];
		}
	}
}

function mergeBusiness(target: Record<string, unknown>, source: Record<string, unknown>) {
	for (const key of [
		'description',
		'owner',
		'domain',
		'glossary_terms',
		'iku_relevance',
		'update_frequency',
		'kpi',
		'consumption',
		'ai_metadata',
	]) {
		if (isEmpty(target[key]) && !isEmpty(source[key])) {
			target[key] = source[key];
		}
	}
}

export function enrichUmtRows(
	rows: UmtRow[],
	datasetSummary: Record<string, DatasetSummaryTable> = {},
): UmtRow[] {
	const byLayerTable = new Map<string, UmtRow>();
	for (const row of rows) {
		const table = tableNameFromQn(row.asset_qualified_name);
		if (table && row.layer) {
			byLayerTable.set(`${row.layer}:${table}`, row);
		}
	}

	for (const row of rows) {
		const table = tableNameFromQn(row.asset_qualified_name);
		const tech = row.technical_json;
		const biz = row.business_json;
		const ops = row.operational_json;

		if (row.layer === 'staging' && table) {
			const ds = datasetSummary[table];
			if (ds) {
				if (isEmpty(tech.row_count) && ds.row_count != null) {
					tech.row_count = ds.row_count;
				}
				if (isEmpty(tech.column_count) && ds.column_count != null) {
					tech.column_count = ds.column_count;
				}
				if (isEmpty(tech.location) && ds.file) {
					tech.location = `s3a://staging/${ds.file}`;
				}
				if (isEmpty(tech.format)) {
					tech.format = 'csv';
				}
			}

			const bronze = byLayerTable.get(`bronze:${table}`);
			if (bronze) {
				mergeTechnical(tech, bronze.technical_json);
				if (isEmpty(tech.column_count) && tech.schema && typeof tech.schema === 'object') {
					tech.column_count = Object.keys(tech.schema as object).length;
				}
			}
		}

		if (row.layer === 'silver' && table.startsWith('silver_')) {
			const bronzeGuess = table.replace(/^silver_/, 'raw_');
			const bronze = byLayerTable.get(`bronze:${bronzeGuess}`);
			if (bronze) {
				mergeTechnical(tech, bronze.technical_json);
			}
		}

		const defaults = LAYER_BUSINESS_DEFAULTS[row.layer] || {};
		if (isEmpty(biz.domain)) biz.domain = DEFAULT_DOMAIN;
		if (isEmpty(biz.owner) && defaults.owner) biz.owner = defaults.owner;
		if (isEmpty(biz.update_frequency) && defaults.update_frequency) {
			biz.update_frequency = defaults.update_frequency;
		}
		if (biz.glossary_terms == null) biz.glossary_terms = [];
		if (biz.iku_relevance == null) biz.iku_relevance = [];
		if (row.layer === 'gold') {
			if (biz.kpi == null) biz.kpi = {};
			if (biz.consumption == null) biz.consumption = {};
			if (biz.ai_metadata == null) biz.ai_metadata = {};
		}

		if (ops.classifications == null) ops.classifications = [];

		if (isEmpty(row.last_enriched_at)) {
			const fromProfiling = (biz as Record<string, unknown>).profiled_at;
			if (fromProfiling) row.last_enriched_at = String(fromProfiling);
		}
	}

	return rows;
}
