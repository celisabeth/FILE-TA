/**
 * Metadata dashboard embed — URL aktual dari context / API (lihat dashboardEmbedConfig.ts).
 */

import { buildDashboardLinks, defaultEmbedConfig, DASHBOARD_HUB_KEYS } from './dashboardEmbedConfig';

export type DashboardPortalKey =
	| 'superset'
	| 'supersetAqeOff'
	| 'supersetAqeOn'
	| 'grafanaInsight'
	| 'grafanaAqe'
	| 'grafanaMlops'
	| 'prometheus';

export interface DashboardPortalLink {
	key: DashboardPortalKey;
	title: string;
	description: string;
	icon: string;
	color: 'primary' | 'secondary' | 'dark' | 'info' | 'success' | 'warning' | 'danger';
	embedUrl: string;
	externalUrl: string;
	embedHint?: string;
}

export {
	DASHBOARD_HUB_KEYS,
	DASHBOARD_KPI_KEYS,
	DASHBOARD_MONITORING_KEYS,
} from './dashboardEmbedConfig';

/** Default statis (env) — halaman klien sebaiknya pakai useDashboardEmbed(). */
const DEFAULT_LINKS = buildDashboardLinks(defaultEmbedConfig());

export const DASHBOARD_PORTAL_LINKS = DEFAULT_LINKS;

export const ANALITIK_LINK = DEFAULT_LINKS.superset;
export const INSIGHT_LINK = DEFAULT_LINKS.grafanaInsight;
export const MONITORING_AQE_LINK = DEFAULT_LINKS.grafanaAqe;
export const MONITORING_MLOPS_LINK = DEFAULT_LINKS.grafanaMlops;

export const DASHBOARD_HUB_CARDS: DashboardPortalLink[] = DASHBOARD_HUB_KEYS.map(
	(k) => DEFAULT_LINKS[k],
);

export function getDashboardLink(key: DashboardPortalKey): DashboardPortalLink {
	return DEFAULT_LINKS[key];
}

export { buildDashboardLinks, defaultEmbedConfig };
