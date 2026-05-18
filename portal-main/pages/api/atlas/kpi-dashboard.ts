import type { NextApiRequest, NextApiResponse } from 'next';
import { buildKpiDashboardFromAtlas } from '../../../helpers/kpiAtlas';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method !== 'GET') {
		res.setHeader('Allow', 'GET');
		return res.status(405).json({ error: 'Method not allowed' });
	}

	try {
		const payload = await buildKpiDashboardFromAtlas();
		res.status(200).json(payload);
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : 'KPI dashboard load failed';
		res.status(502).json({ error: message });
	}
}
