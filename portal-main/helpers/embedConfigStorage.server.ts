import fs from 'fs/promises';
import path from 'path';
import {
	type DashboardEmbedConfig,
	defaultEmbedConfig,
	mergeEmbedConfig,
} from './dashboardEmbedConfig';

function configFilePath(): string {
	const envPath = process.env.EMBED_CONFIG_PATH;
	if (envPath) return envPath;
	return path.join(process.cwd(), 'data', 'embed-config.json');
}

export async function readEmbedConfigFile(): Promise<DashboardEmbedConfig | null> {
	const filePath = configFilePath();
	try {
		const text = await fs.readFile(filePath, 'utf-8');
		const raw = JSON.parse(text) as Partial<DashboardEmbedConfig>;
		return mergeEmbedConfig(raw);
	} catch {
		return null;
	}
}

export async function writeEmbedConfigFile(config: DashboardEmbedConfig): Promise<string> {
	const filePath = configFilePath();
	await fs.mkdir(path.dirname(filePath), { recursive: true });
	await fs.writeFile(filePath, JSON.stringify(config, null, 2), 'utf-8');
	return filePath;
}

export async function resolveEmbedConfig(): Promise<DashboardEmbedConfig> {
	const fromFile = await readEmbedConfigFile();
	return fromFile || defaultEmbedConfig();
}
