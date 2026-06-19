export interface LayerDefinition {
	id: string;
	label: string;
	icon: string;
	color: string;
	classification: string;
	description: string;
	metadata: string[];
	pipeline: string;
}

export const MEDALLION_LAYERS: LayerDefinition[] = [
	{
		id: 'staging',
		label: 'Staging',
		icon: 'CloudUpload',
		color: 'primary',
		classification: 'Staging_Layer',
		description: 'Raw source data landing zone. CSV files uploaded from source systems.',
		metadata: ['Source files', 'CSV format', 'No transformation'],
		pipeline: 'Upload from data sources → MinIO staging bucket',
	},
	{
		id: 'bronze',
		label: 'Bronze',
		icon: 'Storage',
		color: 'primary',
		classification: 'Bronze_Layer',
		description: 'Raw Iceberg tables with schema inference and initial profiling.',
		metadata: [
			'Raw Technical Metadata',
			'Raw Lineage',
			'Raw Data Profiling',
			'Raw Classification (PII)',
		],
		pipeline: 'staging_to_bronze.py: CSV → Iceberg via PySpark',
	},
	{
		id: 'silver',
		label: 'Silver',
		icon: 'AutoFixHigh',
		color: 'primary',
		classification: 'Silver_Layer',
		description: 'Cleaned, enriched, and quality-checked data with business context.',
		metadata: [
			'Clean Metadata',
			'Quality Metadata',
			'Transformation Lineage',
			'Business Metadata',
			'Compliance Metadata',
		],
		pipeline: 'bronze_to_silver.py: Quality checks + enrichment + joins',
	},
	{
		id: 'gold',
		label: 'Gold',
		icon: 'Star',
		color: 'primary',
		classification: 'Gold_Layer',
		description: 'Star schema (5 dimensions + 10 facts) for OLAP Dashboard Pimpinan.',
		metadata: [
			'Business Metadata',
			'KPI Metadata',
			'AI Metadata',
			'Consumption Metadata',
			'Advanced Lineage',
		],
		pipeline: 'silver_to_gold.py: Star schema aggregation + IKU computation',
	},
];

/** Layer yang punya halaman dedicated `/layers/{id}`. */
export const LAYER_PAGE_IDS = ['bronze', 'silver', 'gold'] as const;
export type LayerPageId = (typeof LAYER_PAGE_IDS)[number];

export function getLayerById(id: string): LayerDefinition | undefined {
	return MEDALLION_LAYERS.find((l) => l.id === id);
}

export function isLayerPageId(id: string): id is LayerPageId {
	return (LAYER_PAGE_IDS as readonly string[]).includes(id);
}
