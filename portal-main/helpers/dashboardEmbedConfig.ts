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

const SERVICE_PORTS = {
	grafana: 13001,
	superset: 18089,
	prometheus: 19090,
} as const;

function envOrDefault(name: string, fallback: string): string {
	if (typeof process !== 'undefined' && process.env[name]) {
		return String(process.env[name]);
	}
	return fallback;
}

/** Host publik untuk mengganti localhost (env atau hostname browser). */
export function resolvePublicHost(): string | null {
	const fromEnv =
		(typeof process !== 'undefined' &&
			(process.env.NEXT_PUBLIC_PORTAL_PUBLIC_HOST ||
				process.env.LHINSIGHT_PUBLIC_HOST)) ||
		null;
	if (fromEnv) {
		try {
			const withProto = fromEnv.includes('://') ? fromEnv : `http://${fromEnv}`;
			return new URL(withProto).hostname;
		} catch {
			return fromEnv.split(':')[0] || null;
		}
	}
	if (typeof window !== 'undefined' && window.location?.hostname) {
		const h = window.location.hostname;
		if (h !== 'localhost' && h !== '127.0.0.1') return h;
	}
	return null;
}

function isLoopbackHost(hostname: string): boolean {
	return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
}

/**
 * Jika URL memakai localhost tetapi portal dibuka lewat IP/domain (mis. 103.174.114.177),
 * ganti host agar tab baru & iframe bisa diakses dari mesin pengguna.
 */
export function resolvePublicServiceUrl(rawUrl: string, defaultPort: number): string {
	const fallback = `http://localhost:${defaultPort}`;
	const trimmed = stripTrailingSlash(rawUrl || fallback);
	try {
		const parsed = new URL(trimmed.includes('://') ? trimmed : `http://${trimmed}`);
		const port = parsed.port || String(defaultPort);
		const protocol = parsed.protocol || 'http:';
		const publicHost = resolvePublicHost();
		if (publicHost && isLoopbackHost(parsed.hostname)) {
			return stripTrailingSlash(`${protocol}//${publicHost}:${port}`);
		}
		return stripTrailingSlash(parsed.origin || trimmed);
	} catch {
		return trimmed;
	}
}

export function rewriteLocalhostInUrl(url: string): string {
	if (!url?.trim()) return url;
	const publicHost = resolvePublicHost();
	if (!publicHost) return url;
	try {
		const u = new URL(url);
		if (isLoopbackHost(u.hostname)) {
			u.hostname = publicHost;
			return u.toString();
		}
	} catch {
		/* ignore */
	}
	return url;
}

/** Normalisasi base URL + override link yang masih menunjuk ke localhost. */
export function normalizeEmbedConfigForClient(config: DashboardEmbedConfig): DashboardEmbedConfig {
	const normalized: DashboardEmbedConfig = {
		grafanaBase: resolvePublicServiceUrl(config.grafanaBase, SERVICE_PORTS.grafana),
		supersetBase: resolvePublicServiceUrl(config.supersetBase, SERVICE_PORTS.superset),
		prometheusBase: resolvePublicServiceUrl(config.prometheusBase, SERVICE_PORTS.prometheus),
		links: {},
	};

	for (const [key, val] of Object.entries(config.links || {})) {
		if (!val) continue;
		normalized.links![key as DashboardPortalKey] = {
			embedUrl: val.embedUrl ? rewriteLocalhostInUrl(val.embedUrl) : undefined,
			externalUrl: val.externalUrl ? rewriteLocalhostInUrl(val.externalUrl) : undefined,
			embedHint: val.embedHint,
		};
	}
	return normalized;
}

export function defaultEmbedConfig(): DashboardEmbedConfig {
	const raw: DashboardEmbedConfig = {
		grafanaBase: envOrDefault('NEXT_PUBLIC_GRAFANA_URL', `http://localhost:${SERVICE_PORTS.grafana}`),
		supersetBase: envOrDefault(
			'NEXT_PUBLIC_SUPERSET_URL',
			`http://localhost:${SERVICE_PORTS.superset}`,
		),
		prometheusBase: envOrDefault(
			'NEXT_PUBLIC_PROMETHEUS_URL',
			`http://localhost:${SERVICE_PORTS.prometheus}`,
		),
		links: {},
	};
	return normalizeEmbedConfigForClient(raw);
}

function grafanaDashboardUrl(base: string, uid: string, kiosk = true): string {
	const q = kiosk ? '?orgId=1&kiosk' : '?orgId=1';
	return `${stripTrailingSlash(base)}/d/${uid}${q}`;
}

export function mergeEmbedConfig(partial?: Partial<DashboardEmbedConfig> | null): DashboardEmbedConfig {
	const base = defaultEmbedConfig();
	if (!partial) return base;
	const merged: DashboardEmbedConfig = {
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
	return normalizeEmbedConfigForClient(merged);
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
			externalUrl: `${supersetBase}/superset/welcome/?standalone=1`,
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

	for (const key of Object.keys(links) as DashboardPortalKey[]) {
		if (!links[key].externalUrl?.trim()) {
			links[key].externalUrl = links[key].embedUrl;
		}
	}

	return links;
}

export const DASHBOARD_HUB_KEYS: DashboardPortalKey[] = [
	'superset',
	'grafanaInsight',
	'grafanaAqe',
	'grafanaMlops',
];
