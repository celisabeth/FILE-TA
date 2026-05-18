const ATLAS_BASE = process.env.NEXT_PUBLIC_ATLAS_URL || 'http://localhost:21000';
const ATLAS_USER = process.env.ATLAS_USER || 'admin';
const ATLAS_PASS = process.env.ATLAS_PASS || 'admin';

function authHeader(): string {
	if (typeof window !== 'undefined') return '';
	return 'Basic ' + Buffer.from(`${ATLAS_USER}:${ATLAS_PASS}`).toString('base64');
}

export async function atlasRequest<T = any>(
	path: string,
	options: RequestInit = {},
): Promise<T> {
	const url = `${ATLAS_BASE}${path}`;
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		Accept: 'application/json',
		...((options.headers as Record<string, string>) || {}),
	};

	const auth = authHeader();
	if (auth) headers['Authorization'] = auth;

	const res = await fetch(url, { ...options, headers });

	if (!res.ok) {
		const text = await res.text().catch(() => '');
		throw new Error(`Atlas ${res.status}: ${text.slice(0, 300)}`);
	}

	return res.json();
}

export interface AtlasSearchResult {
	approximateCount: number;
	entities: AtlasEntity[];
}

export interface AtlasEntity {
	guid: string;
	typeName: string;
	attributes: Record<string, any>;
	classifications?: { typeName: string; attributes?: Record<string, any> }[];
	status: string;
}

export interface AtlasLineageResult {
	baseEntityGuid: string;
	lineageDirection: string;
	lineageDepth: number;
	guidEntityMap: Record<string, AtlasEntity>;
	relations: { fromEntityId: string; toEntityId: string; relationshipId: string }[];
}

export async function searchEntities(
	typeName: string,
	query?: string,
	classification?: string,
	limit = 50,
	offset = 0,
): Promise<AtlasSearchResult> {
	const body: any = { typeName, limit, offset };
	if (query) body.query = query;
	if (classification) body.classification = classification;

	return atlasRequest('/api/atlas/v2/search/basic', {
		method: 'POST',
		body: JSON.stringify(body),
	});
}

/** Samakan atribut dari search stub vs GET penuh (termasuk alias camelCase Atlas). */
export function normalizeDatasetAttributes(
	attrs: Record<string, any> | undefined,
): Record<string, any> {
	if (!attrs) return {};
	const out: Record<string, any> = { ...attrs };
	const aliases: Record<string, string[]> = {
		row_count: ['rowCount'],
		column_count: ['columnCount'],
		schema_def: ['schemaDef', 'schema'],
		pii_columns: ['piiColumns'],
		ingested_at: ['ingestedAt'],
		enriched_at: ['enrichedAt'],
	};
	for (const [canonical, alts] of Object.entries(aliases)) {
		if (out[canonical] == null) {
			for (const alt of alts) {
				if (out[alt] != null) {
					out[canonical] = out[alt];
					break;
				}
			}
		}
	}
	return out;
}

export async function getEntity(guid: string): Promise<{ entity: AtlasEntity }> {
	const full = await atlasRequest<{ entity: AtlasEntity }>(
		`/api/atlas/v2/entity/guid/${guid}?minExtInfo=false&ignoreRelationships=true`,
	);
	if (full.entity?.attributes) {
		full.entity.attributes = normalizeDatasetAttributes(full.entity.attributes);
	}
	return full;
}

/** Muat atribut lengkap (row_count, profiling.kpi, …) — search/basic tidak mengirimnya. */
export async function hydrateAtlasEntities(entities: AtlasEntity[]): Promise<AtlasEntity[]> {
	const hydrated: AtlasEntity[] = [];
	for (const stub of entities) {
		if (!stub.guid) {
			hydrated.push({
				...stub,
				attributes: normalizeDatasetAttributes(stub.attributes),
			});
			continue;
		}
		try {
			const full = await getEntity(stub.guid);
			const entity = full.entity ?? (full as unknown as AtlasEntity);
			if (!entity.classifications?.length && stub.classifications?.length) {
				entity.classifications = stub.classifications;
			}
			hydrated.push(entity);
		} catch {
			hydrated.push({
				...stub,
				attributes: normalizeDatasetAttributes(stub.attributes),
			});
		}
	}
	return hydrated;
}

export async function getEntityByQualifiedName(
	typeName: string,
	qualifiedName: string,
): Promise<{ entity: AtlasEntity }> {
	return atlasRequest(
		`/api/atlas/v2/entity/uniqueAttribute/type/${typeName}?attr:qualifiedName=${encodeURIComponent(qualifiedName)}`,
	);
}

export async function getLineage(
	guid: string,
	depth = 5,
	direction: 'BOTH' | 'INPUT' | 'OUTPUT' = 'BOTH',
): Promise<AtlasLineageResult> {
	return atlasRequest(
		`/api/atlas/v2/lineage/${guid}?depth=${depth}&direction=${direction}`,
	);
}

export async function getClassificationDefs(): Promise<any> {
	return atlasRequest('/api/atlas/v2/types/typedefs?type=classification');
}

export async function getMetrics(): Promise<any> {
	return atlasRequest('/api/atlas/v2/admin/metrics');
}

export function layerFromQualifiedName(qn: string): string {
	if (!qn) return 'unknown';
	if (qn.startsWith('staging.')) return 'staging';
	if (qn.startsWith('bronze.')) return 'bronze';
	if (qn.startsWith('silver.')) return 'silver';
	if (qn.startsWith('gold.')) return 'gold';
	// Proses ETL: etl.staging_to_bronze.* — bukan layer data; gunakan helpers/lineageDisplay.ts
	if (qn.startsWith('etl.')) return 'etl';
	return 'unknown';
}

/** Satu warna dominan (primary) untuk badge, ikon, dan border layer/classification. */
export function layerColor(_layer: string): string {
	return 'primary';
}

export function classificationColor(_cls: string): string {
	return 'primary';
}
