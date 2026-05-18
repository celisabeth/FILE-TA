import fsSync from 'fs';
import fs from 'fs/promises';
import path from 'path';

/** Root folder metrik (selaras INSIGHT_METRICS_DIR / docker mount /metrics). */
export function metricsRoot(): string {
	const env =
		process.env.INSIGHT_METRICS_DIR ||
		process.env.META_METRICS_DIR ||
		process.env.AQE_METRICS_DIR;
	if (env) return env;
	if (process.env.METRICS_DIR) return process.env.METRICS_DIR;
	if (fsSync.existsSync('/metrics')) return '/metrics';
	const sibling = path.join(process.cwd(), '..', 'metrics');
	if (fsSync.existsSync(sibling)) return sibling;
	return path.join(process.cwd(), 'metrics');
}

async function fileExists(p: string): Promise<boolean> {
	try {
		await fs.access(p);
		return true;
	} catch {
		return false;
	}
}

async function newestMatching(dir: string, pattern: RegExp): Promise<string | null> {
	let entries: string[];
	try {
		entries = await fs.readdir(dir);
	} catch {
		return null;
	}
	const matches = entries.filter((n) => pattern.test(n));
	if (matches.length === 0) return null;

	let best: { file: string; mtime: number } | null = null;
	for (const name of matches) {
		const full = path.join(dir, name);
		const st = await fs.stat(full);
		if (!st.isFile()) continue;
		if (!best || st.mtimeMs > best.mtime) {
			best = { file: full, mtime: st.mtimeMs };
		}
	}
	return best?.file ?? null;
}

async function runDirFromPointer(root: string, track: string): Promise<string | null> {
	const ptrFile = path.join(root, 'latest', `${track}.json`);
	if (!(await fileExists(ptrFile))) return null;
	try {
		const raw = JSON.parse(await fs.readFile(ptrFile, 'utf-8')) as { dir?: string };
		if (!raw.dir) return null;
		const runDir = path.join(root, raw.dir);
		return (await fileExists(runDir)) ? runDir : null;
	} catch {
		return null;
	}
}

async function runDirFromIndex(root: string, track: string): Promise<string | null> {
	const idxFile = path.join(root, 'index.json');
	if (!(await fileExists(idxFile))) return null;
	try {
		const idx = JSON.parse(await fs.readFile(idxFile, 'utf-8')) as {
			latest?: Record<string, string>;
		};
		const runId = idx.latest?.[track];
		if (!runId) return null;
		const runDir = path.join(root, 'runs', runId);
		return (await fileExists(runDir)) ? runDir : null;
	} catch {
		return null;
	}
}

/**
 * Lokasi file metadata quality (skema audit baru + fallback legacy).
 * Urutan: latest/metadata/metadata_quality.json → run terakhir → root legacy.
 */
export async function resolveMetadataQualityPath(): Promise<string | null> {
	const root = metricsRoot();

	const ordered = [
		path.join(root, 'latest', 'metadata', 'metadata_quality.json'),
		path.join(root, 'metadata_quality_latest.json'),
	];

	for (const p of ordered) {
		if (await fileExists(p)) return p;
	}

	const runDirs: string[] = [];
	const fromPtr = await runDirFromPointer(root, 'metadata');
	if (fromPtr) runDirs.push(fromPtr);
	const fromIdx = await runDirFromIndex(root, 'metadata');
	if (fromIdx && !runDirs.includes(fromIdx)) runDirs.push(fromIdx);

	for (const runDir of runDirs) {
		const inRun =
			(await newestMatching(runDir, /^metadata_quality_\d{8}_\d{6}\.json$/)) ||
			(await newestMatching(runDir, /^metadata_quality_.*\.json$/));
		if (inRun) return inRun;
	}

	const runsRoot = path.join(root, 'runs');
	if (await fileExists(runsRoot)) {
		let entries: string[];
		try {
			entries = await fs.readdir(runsRoot);
		} catch {
			return null;
		}
		let best: { file: string; mtime: number } | null = null;
		for (const runId of entries) {
			if (!runId.startsWith('metadata_')) continue;
			const runDir = path.join(runsRoot, runId);
			const st = await fs.stat(runDir).catch(() => null);
			if (!st?.isDirectory()) continue;
			const hit = await newestMatching(runDir, /^metadata_quality_.*\.json$/);
			if (!hit) continue;
			const fst = await fs.stat(hit);
			if (!best || fst.mtimeMs > best.mtime) {
				best = { file: hit, mtime: fst.mtimeMs };
			}
		}
		if (best) return best.file;
	}

	return (await newestMatching(root, /^metadata_quality_\d{8}_\d{6}\.json$/)) || null;
}

export async function readJsonFile<T = Record<string, unknown>>(filePath: string): Promise<T> {
	const text = await fs.readFile(filePath, 'utf-8');
	return JSON.parse(text) as T;
}

/** Ringkasan CSV staging terbaru (dataset_summary_*.json). */
export async function resolveDatasetSummaryPath(): Promise<string | null> {
	const root = metricsRoot();
	const ordered = [path.join(root, 'dataset_summary_latest.json')];
	for (const p of ordered) {
		if (await fileExists(p)) return p;
	}

	const runDirs: string[] = [];
	const fromPtr = await runDirFromPointer(root, 'metadata');
	if (fromPtr) runDirs.push(fromPtr);
	const fromIdx = await runDirFromIndex(root, 'metadata');
	if (fromIdx && !runDirs.includes(fromIdx)) runDirs.push(fromIdx);

	for (const runDir of runDirs) {
		const hit = await newestMatching(runDir, /^dataset_summary_.*\.json$/);
		if (hit) return hit;
	}

	return (await newestMatching(root, /^dataset_summary_.*\.json$/)) || null;
}

export interface DatasetSummaryTable {
	table_name: string;
	row_count?: number;
	column_count?: number;
	file?: string;
}

export async function loadDatasetSummaryIndex(): Promise<
	Record<string, DatasetSummaryTable>
> {
	const filePath = await resolveDatasetSummaryPath();
	if (!filePath) return {};

	try {
		const raw = await readJsonFile<{ tables?: DatasetSummaryTable[] }>(filePath);
		const index: Record<string, DatasetSummaryTable> = {};
		for (const row of raw.tables || []) {
			if (row.table_name) index[row.table_name] = row;
		}
		return index;
	} catch {
		return {};
	}
}
