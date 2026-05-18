import type { NextApiRequest, NextApiResponse } from 'next';
import {
	buildMetadataQualityReport,
	loadMetadataQualityFromMetrics,
} from '../../../helpers/metadataQualityEvaluator';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method !== 'GET') {
		res.setHeader('Allow', 'GET');
		return res.status(405).json({ error: 'Method not allowed' });
	}

	const live = req.query.live === '1' || req.query.live === 'true';

	try {
		if (!live) {
			const fromMetrics = await loadMetadataQualityFromMetrics();
			if (fromMetrics) {
				return res.status(200).json(fromMetrics);
			}
		}
		const report = await buildMetadataQualityReport();
		res.status(200).json(report);
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : 'Metadata quality evaluation failed';
		res.status(502).json({ error: message });
	}
}
