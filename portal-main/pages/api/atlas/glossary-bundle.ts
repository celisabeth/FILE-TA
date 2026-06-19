import type { NextApiRequest, NextApiResponse } from 'next';
import { atlasGlossaryToTerms, fetchAtlasGlossaries } from '../../../helpers/atlasGlossary';
import { buildGlossaryFromAtlas, mergeGlossaryTerms } from '../../../helpers/glossaryFromMetadata';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
	if (req.method !== 'GET') {
		res.setHeader('Allow', 'GET');
		return res.status(405).json({ error: 'Method not allowed' });
	}

	try {
		const limit = Math.min(Number(req.query.limit) || 500, 1000);

		let atlasConnected = false;
		let atlasTerms: { term: string; definition: string; category: string; guid?: string }[] = [];
		let glossaries: Awaited<ReturnType<typeof fetchAtlasGlossaries>> = [];

		try {
			glossaries = await fetchAtlasGlossaries();
			atlasTerms = atlasGlossaryToTerms(glossaries);
			atlasConnected = true;
		} catch {
			atlasConnected = false;
		}

		const meta = await buildGlossaryFromAtlas(limit);
		const fallback = meta.fallback.map((t) => ({ ...t, source: 'local' as const }));
		const terms = mergeGlossaryTerms(atlasTerms, meta.terms, fallback, meta.entities);

		res.status(200).json({
			generatedAt: meta.generatedAt,
			atlasConnected,
			silverEntityCount: meta.silverEntityCount,
			glossaries,
			terms,
		});
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : 'Glossary bundle failed';
		res.status(502).json({ error: message });
	}
}
