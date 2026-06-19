import type { NextApiRequest, NextApiResponse } from 'next';
import {
	type DashboardEmbedConfig,
	defaultEmbedConfig,
	mergeEmbedConfig,
} from '../../../helpers/dashboardEmbedConfig';
import { readEmbedConfigFile, writeEmbedConfigFile } from '../../../helpers/embedConfigStorage.server';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method === 'GET') {
		const fromFile = await readEmbedConfigFile();
		// Env (.env / docker-compose) sebagai dasar; file hanya menimpa field yang disimpan UI
		const config = fromFile ? mergeEmbedConfig(fromFile) : defaultEmbedConfig();
		return res.status(200).json({
			config,
			source: fromFile ? 'file+env' : 'env',
		});
	}

	if (req.method === 'POST' || req.method === 'PUT') {
		const body = req.body as Partial<DashboardEmbedConfig>;
		if (!body || typeof body !== 'object') {
			return res.status(400).json({ error: 'Invalid config body' });
		}

		const current = (await readEmbedConfigFile()) || defaultEmbedConfig();
		const merged = mergeEmbedConfig({
			grafanaBase: body.grafanaBase ?? current.grafanaBase,
			supersetBase: body.supersetBase ?? current.supersetBase,
			prometheusBase: body.prometheusBase ?? current.prometheusBase,
			links: { ...current.links, ...(body.links || {}) },
		});

		const filePath = await writeEmbedConfigFile(merged);
		return res.status(200).json({
			config: merged,
			source: 'file',
			path: filePath,
		});
	}

	res.setHeader('Allow', 'GET, POST, PUT');
	return res.status(405).json({ error: 'Method not allowed' });
}
