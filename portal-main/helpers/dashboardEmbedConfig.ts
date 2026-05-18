import type { DashboardPortalKey, DashboardPortalLink } from './dashboardPortal';

export interface DashboardEmbedConfig {
	grafanaBase: string;
	supersetBase: string;
	prometheusBase: string;
	/** Override URL penuh per dashboard (opsional). */
	links?: Partial<
		Record<DashboardPortalKey, { embedUrl?: string; externalUrl?: string; embedHint?: string }>
	>;
}

const GRAFANA_DASHBOARD_UIDS: Record<
	'grafanaInsight' | 'grafanaAqe' | 'grafanaMlops',
	string
> = {
	grafanaInsight: 'lakehouse-dashboard-insight',
	grafanaAqe: 'lakehouse-aqe-experiment',
	grafanaMlops: 'lakehouse-mlops-pipeline',
};

export function stripTrailingSlash(url: string): string {
	return url.replace(/\/+$/, '');
}

export function defaultEmbedConfig(): DashboardEmbedConfig {
	const grafanaBase = stripTrailingSlash(
		(typeof process !== 'undefined' && process.env.NEXT_PUBLIC_GRAFANA_URL) ||
			'http://localhost:13001',
	);
	const supersetBase = stripTrailingSlash(
		(typeof process !== 'undefined' && process.env.NEXT_PUBLIC_SUPERSET_URL) ||
			'http://localhost:18089',
	);
	const prometheusBase = stripTrailingSlash(
		(typeof process !== 'undefined' && process.env.NEXT_PUBLIC_PROMETHEUS_URL) ||
			'http://localhost:19090',
	);
	return { grafanaBase, supersetBase, prometheusBase, links: {} };
}

function grafanaDashboardUrl(base: string, uid: string, kiosk = true): string {
	const q = kiosk ? '?orgId=1&kiosk' : '?orgId=1';
	return `${stripTrailingSlash(base)}/d/${uid}${q}`;
}

export function mergeEmbedConfig(partial?: Partial<DashboardEmbedConfig> | null): DashboardEmbedConfig {
	const base = defaultEmbedConfig();
	if (!partial) return base;
	return {
		grafanaBase: partial.grafanaBase
			? stripTrailingSlash(partial.grafanaBase)
			: base.grafanaBase,
		supersetBase: partial.supersetBase
			? stripTrailingSlash(partial.supersetBase)
			: base.supersetBase,
		prometheusBase: partial.prometheusBase
			? stripTrailingSlash(partial.prometheusBase)
			: base.prometheusBase,
		links: { ...base.links, ...(partial.links || {}) },
	};
}

export function buildDashboardLinks(config: DashboardEmbedConfig): Record<
	DashboardPortalKey,
	DashboardPortalLink
> {
	const { grafanaBase, supersetBase, prometheusBase } = config;
	const override = config.links || {};

	const links: Record<DashboardPortalKey, DashboardPortalLink> = {
		superset: {
			key: 'superset',
			title: 'Dashboard Analitik KPI IKU',
			description:
				'Apache Superset — chart & dashboard OLAP dari Gold star schema (Trino). Executive IKU, per prodi, tata kelola.',
			icon: 'Analytics',
			color: 'primary',
			embedUrl: `${supersetBase}/superset/welcome/?standalone=1`,
			externalUrl: `${supersetBase}/`,
			embedHint: 'Login Superset: admin / admin. Buat dataset dari lakehouse.gold lalu chart.',
		},
		grafanaInsight: {
			key: 'grafanaInsight',
			title: 'Dashboard Insight',
			description:
				'Forecast, Risk Score, Opportunity, Anomalies — output pipeline MLOps (Prometheus).',
			icon: 'Insights',
			color: 'info',
			embedUrl: grafanaDashboardUrl(grafanaBase, GRAFANA_DASHBOARD_UIDS.grafanaInsight),
			externalUrl: grafanaDashboardUrl(
				grafanaBase,
				GRAFANA_DASHBOARD_UIDS.grafanaInsight,
				false,
			),
			embedHint:
				'Login Grafana: admin / admin. Jalankan mlops_pipeline atau demo metrics terlebih dahulu.',
		},
		grafanaAqe: {
			key: 'grafanaAqe',
			title: 'Monitoring AQE',
			description:
				'Performa pipeline Silver/Gold — speedup AQE ON vs OFF, durasi workload Spark & Trino.',
			icon: 'Speed',
			color: 'warning',
			embedUrl: grafanaDashboardUrl(grafanaBase, GRAFANA_DASHBOARD_UIDS.grafanaAqe),
			externalUrl: grafanaDashboardUrl(grafanaBase, GRAFANA_DASHBOARD_UIDS.grafanaAqe, false),
			embedHint: 'Isi metrics/ setelah aqe_full_experiment.',
		},
		grafanaMlops: {
			key: 'grafanaMlops',
			title: 'Monitoring MLOps Pipeline',
			description: 'Durasi task DAG mlops_pipeline, metrik training MLflow, ringkasan use case.',
			icon: 'PrecisionManufacturing',
			color: 'success',
			embedUrl: grafanaDashboardUrl(grafanaBase, GRAFANA_DASHBOARD_UIDS.grafanaMlops),
			externalUrl: grafanaDashboardUrl(
				grafanaBase,
				GRAFANA_DASHBOARD_UIDS.grafanaMlops,
				false,
			),
			embedHint: 'Task export_mlops_metrics menulis metrics/mlops_metrics_latest.json.',
		},
		prometheus: {
			key: 'prometheus',
			title: 'Prometheus',
			description: 'Explorer metrik mentah lakehouse_* (AQE, MLOps, Insight).',
			icon: 'QueryStats',
			color: 'danger',
			embedUrl: `${prometheusBase}/graph`,
			externalUrl: `${prometheusBase}/`,
			embedHint: 'Target scrape: metrics-exporter:9101',
		},
	};

	for (const key of Object.keys(override) as DashboardPortalKey[]) {
		const o = override[key];
		if (!o || !links[key]) continue;
		if (o.embedUrl) links[key].embedUrl = o.embedUrl.trim();
		if (o.externalUrl) links[key].externalUrl = o.externalUrl.trim();
		if (o.embedHint) links[key].embedHint = o.embedHint;
	}

	return links;
}

export const DASHBOARD_HUB_KEYS: DashboardPortalKey[] = [
	'superset',
	'grafanaInsight',
	'grafanaAqe',
	'grafanaMlops',
];
