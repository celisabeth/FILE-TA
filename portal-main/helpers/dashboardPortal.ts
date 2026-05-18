/**
 * URL portal dashboard & monitoring — dibaca di browser (NEXT_PUBLIC_*).
 * Saat build production, set env sebelum `yarn build`.
 */

export type DashboardPortalKey =
	| 'superset'
	| 'grafanaInsight'
	| 'grafanaAqe'
	| 'grafanaMlops'
	| 'prometheus';

export interface DashboardPortalLink {
	key: DashboardPortalKey;
	title: string;
	description: string;
	icon: string;
	color: 'primary' | 'info' | 'success' | 'warning' | 'danger';
	embedUrl: string;
	externalUrl: string;
	embedHint?: string;
}

const grafanaBase = () =>
	(process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:13001').replace(/\/$/, '');

const supersetBase = () =>
	(process.env.NEXT_PUBLIC_SUPERSET_URL || 'http://localhost:18089').replace(/\/$/, '');

const prometheusBase = () =>
	(process.env.NEXT_PUBLIC_PROMETHEUS_URL || 'http://localhost:19090').replace(/\/$/, '');

const grafanaDashboardPath = (uid: string, kiosk = true) => {
	const q = kiosk ? '?orgId=1&kiosk' : '?orgId=1';
	return `${grafanaBase()}/d/${uid}${q}`;
};

export const DASHBOARD_PORTAL_LINKS: Record<DashboardPortalKey, DashboardPortalLink> = {
	superset: {
		key: 'superset',
		title: 'Dashboard Analitik KPI IKU',
		description:
			'Apache Superset — chart & dashboard OLAP dari Gold star schema (Trino). Executive IKU, per prodi, tata kelola.',
		icon: 'Analytics',
		color: 'primary',
		embedUrl: `${supersetBase()}/superset/welcome/?standalone=1`,
		externalUrl: `${supersetBase()}/`,
		embedHint: 'Login Superset: admin / admin. Buat dataset dari lakehouse.gold lalu chart.',
	},
	grafanaInsight: {
		key: 'grafanaInsight',
		title: 'Dashboard Insight',
		description:
			'Forecast, Risk Score, Opportunity, Anomalies — output pipeline MLOps (Prometheus).',
		icon: 'Insights',
		color: 'info',
		embedUrl: grafanaDashboardPath('lakehouse-dashboard-insight'),
		externalUrl: grafanaDashboardPath('lakehouse-dashboard-insight', false),
		embedHint: 'Login Grafana: admin / admin. Jalankan mlops_pipeline atau demo metrics terlebih dahulu.',
	},
	grafanaAqe: {
		key: 'grafanaAqe',
		title: 'Monitoring AQE',
		description:
			'Performa pipeline Silver/Gold — speedup AQE ON vs OFF, durasi workload Spark & Trino.',
		icon: 'Speed',
		color: 'warning',
		embedUrl: grafanaDashboardPath('lakehouse-aqe-experiment'),
		externalUrl: grafanaDashboardPath('lakehouse-aqe-experiment', false),
		embedHint: 'Isi metrics/ setelah aqe_full_experiment.',
	},
	grafanaMlops: {
		key: 'grafanaMlops',
		title: 'Monitoring MLOps Pipeline',
		description: 'Durasi task DAG mlops_pipeline, metrik training MLflow, ringkasan use case.',
		icon: 'PrecisionManufacturing',
		color: 'success',
		embedUrl: grafanaDashboardPath('lakehouse-mlops-pipeline'),
		externalUrl: grafanaDashboardPath('lakehouse-mlops-pipeline', false),
		embedHint: 'Task export_mlops_metrics menulis metrics/mlops_metrics_latest.json.',
	},
	prometheus: {
		key: 'prometheus',
		title: 'Prometheus',
		description: 'Explorer metrik mentah lakehouse_* (AQE, MLOps, Insight).',
		icon: 'QueryStats',
		color: 'danger',
		embedUrl: `${prometheusBase()}/graph`,
		externalUrl: `${prometheusBase()}/`,
		embedHint: 'Target scrape: metrics-exporter:9101',
	},
};

export const ANALITIK_LINK = DASHBOARD_PORTAL_LINKS.superset;
export const INSIGHT_LINK = DASHBOARD_PORTAL_LINKS.grafanaInsight;
export const MONITORING_AQE_LINK = DASHBOARD_PORTAL_LINKS.grafanaAqe;
export const MONITORING_MLOPS_LINK = DASHBOARD_PORTAL_LINKS.grafanaMlops;

export const DASHBOARD_HUB_CARDS: DashboardPortalLink[] = [
	DASHBOARD_PORTAL_LINKS.superset,
	DASHBOARD_PORTAL_LINKS.grafanaInsight,
	DASHBOARD_PORTAL_LINKS.grafanaAqe,
	DASHBOARD_PORTAL_LINKS.grafanaMlops,
];

export function getDashboardLink(key: DashboardPortalKey): DashboardPortalLink {
	return DASHBOARD_PORTAL_LINKS[key];
}
