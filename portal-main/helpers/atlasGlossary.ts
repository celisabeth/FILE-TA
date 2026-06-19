import { atlasRequest } from './atlasApi';

export interface AtlasGlossaryWithTerms {
	guid: string;
	name: string;
	description?: string;
	terms?: Array<{
		guid?: string;
		termGuid?: string;
		displayText?: string;
		name?: string;
		shortDescription?: string;
		longDescription?: string;
	}>;
}

/** Ambil glossaries Atlas + terms per glossary (format respons bervariasi). */
export async function fetchAtlasGlossaries(): Promise<AtlasGlossaryWithTerms[]> {
	const result = await atlasRequest<unknown>('/api/atlas/v2/glossary');
	const list: AtlasGlossaryWithTerms[] = Array.isArray(result)
		? (result as AtlasGlossaryWithTerms[])
		: ((result as { glossaries?: AtlasGlossaryWithTerms[] })?.glossaries || []);

	const enriched: AtlasGlossaryWithTerms[] = [];
	for (const g of list) {
		if (g.terms?.length) {
			enriched.push(g);
			continue;
		}
		if (!g.guid) {
			enriched.push({ ...g, terms: [] });
			continue;
		}
		try {
			const termsRes = await atlasRequest<{ terms?: AtlasGlossaryWithTerms['terms'] }>(
				`/api/atlas/v2/glossary/${g.guid}/terms`,
			);
			enriched.push({
				...g,
				terms: termsRes?.terms || (termsRes as unknown as AtlasGlossaryWithTerms['terms']) || [],
			});
		} catch {
			enriched.push({ ...g, terms: [] });
		}
	}
	return enriched;
}

export function atlasGlossaryToTerms(
	glossaries: AtlasGlossaryWithTerms[],
): { term: string; definition: string; category: string; guid?: string }[] {
	const out: { term: string; definition: string; category: string; guid?: string }[] = [];
	for (const g of glossaries) {
		for (const t of g.terms || []) {
			const term = t.displayText || t.name;
			if (!term) continue;
			out.push({
				guid: t.termGuid || t.guid,
				term,
				definition: t.shortDescription || t.longDescription || '',
				category: g.name || 'Atlas',
			});
		}
	}
	return out;
}
