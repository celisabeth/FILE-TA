import React, {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
} from 'react';
import type { DashboardPortalKey, DashboardPortalLink } from '../helpers/dashboardPortal';
import {
	type DashboardEmbedConfig,
	buildDashboardLinks,
	defaultEmbedConfig,
	mergeEmbedConfig,
} from '../helpers/dashboardEmbedConfig';

interface DashboardEmbedContextValue {
	config: DashboardEmbedConfig;
	links: Record<DashboardPortalKey, DashboardPortalLink>;
	loading: boolean;
	source: 'env' | 'file' | 'local';
	getLink: (key: DashboardPortalKey) => DashboardPortalLink;
	updateBases: (bases: Partial<Pick<DashboardEmbedConfig, 'grafanaBase' | 'supersetBase' | 'prometheusBase'>>) => void;
	updateLinkOverride: (
		key: DashboardPortalKey,
		override: { embedUrl?: string; externalUrl?: string },
	) => void;
	clearLinkOverride: (key: DashboardPortalKey) => void;
	saveConfig: (next?: DashboardEmbedConfig) => Promise<void>;
	resetToDefaults: () => void;
}

const STORAGE_KEY = 'insightera_embed_config_v1';

const DashboardEmbedContext = createContext<DashboardEmbedContextValue | undefined>(undefined);

function loadLocalConfig(): DashboardEmbedConfig | null {
	if (typeof window === 'undefined') return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		return mergeEmbedConfig(JSON.parse(raw) as Partial<DashboardEmbedConfig>);
	} catch {
		return null;
	}
}

function saveLocalConfig(config: DashboardEmbedConfig) {
	if (typeof window === 'undefined') return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

export function DashboardEmbedProvider({ children }: { children: React.ReactNode }) {
	const [config, setConfig] = useState<DashboardEmbedConfig>(defaultEmbedConfig());
	const [loading, setLoading] = useState(true);
	const [source, setSource] = useState<'env' | 'file' | 'local'>('env');

	useEffect(() => {
		let cancelled = false;
		(async () => {
			setLoading(true);
			try {
				const res = await fetch('/api/portal/embed-config');
				const data = await res.json();
				if (!cancelled && res.ok && data.config) {
					setConfig(mergeEmbedConfig(data.config));
					setSource(data.source === 'file' ? 'file' : 'env');
					return;
				}
			} catch {
				/* fallback below */
			}
			if (!cancelled) {
				const local = loadLocalConfig();
				setConfig(local || defaultEmbedConfig());
				setSource(local ? 'local' : 'env');
			}
		})().finally(() => {
			if (!cancelled) setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, []);

	const links = useMemo(() => buildDashboardLinks(config), [config]);

	const getLink = useCallback((key: DashboardPortalKey) => links[key], [links]);

	const updateBases = useCallback(
		(bases: Partial<Pick<DashboardEmbedConfig, 'grafanaBase' | 'supersetBase' | 'prometheusBase'>>) => {
			setConfig((prev) => mergeEmbedConfig({ ...prev, ...bases }));
			setSource('local');
		},
		[],
	);

	const updateLinkOverride = useCallback(
		(key: DashboardPortalKey, override: { embedUrl?: string; externalUrl?: string }) => {
			setConfig((prev) =>
				mergeEmbedConfig({
					...prev,
					links: {
						...prev.links,
						[key]: { ...prev.links?.[key], ...override },
					},
				}),
			);
			setSource('local');
		},
		[],
	);

	const clearLinkOverride = useCallback((key: DashboardPortalKey) => {
		setConfig((prev) => {
			const nextLinks = { ...prev.links };
			delete nextLinks[key];
			return mergeEmbedConfig({ ...prev, links: nextLinks });
		});
		setSource('local');
	}, []);

	const saveConfig = useCallback(async (next?: DashboardEmbedConfig) => {
		const toSave = next || config;
		const res = await fetch('/api/portal/embed-config', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(toSave),
		});
		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			throw new Error(err.error || 'Gagal menyimpan konfigurasi');
		}
		const data = await res.json();
		const merged = mergeEmbedConfig(data.config);
		setConfig(merged);
		saveLocalConfig(merged);
		setSource('file');
	}, [config]);

	const resetToDefaults = useCallback(() => {
		const defaults = defaultEmbedConfig();
		setConfig(defaults);
		if (typeof window !== 'undefined') {
			localStorage.removeItem(STORAGE_KEY);
		}
		setSource('env');
	}, []);

	const value = useMemo(
		() => ({
			config,
			links,
			loading,
			source,
			getLink,
			updateBases,
			updateLinkOverride,
			clearLinkOverride,
			saveConfig,
			resetToDefaults,
		}),
		[
			config,
			links,
			loading,
			source,
			getLink,
			updateBases,
			updateLinkOverride,
			clearLinkOverride,
			saveConfig,
			resetToDefaults,
		],
	);

	return (
		<DashboardEmbedContext.Provider value={value}>{children}</DashboardEmbedContext.Provider>
	);
}

export function useDashboardEmbed(): DashboardEmbedContextValue {
	const ctx = useContext(DashboardEmbedContext);
	if (!ctx) {
		throw new Error('useDashboardEmbed must be used within DashboardEmbedProvider');
	}
	return ctx;
}
