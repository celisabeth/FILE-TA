import React from 'react';
import Badge from '../bootstrap/Badge';
import Icon from '../icon/Icon';
import { layerColor } from '../../helpers/atlasApi';
import {
	LINEAGE_METADATA_BY_LAYER,
	MEDALLION_DATA_LAYERS,
	MEDALLION_PIPELINE_EDGES,
	processMatchesEdge,
	type ParsedLineageNode,
} from '../../helpers/lineageDisplay';

const LAYER_ICONS: Record<string, string> = {
	staging: 'CloudUpload',
	bronze: 'Storage',
	silver: 'AutoFixHigh',
	gold: 'Star',
};

export interface MedallionLineageFlowProps {
	nodes: ParsedLineageNode[];
	highlightGuid?: string;
	showMetadataTypes?: boolean;
	maxDatasetsPerLayer?: number;
}

function datasetsForLayer(nodes: ParsedLineageNode[], layer: string, limit: number) {
	return nodes.filter((n) => !n.isProcess && n.layer === layer).slice(0, limit);
}

function processesForEdge(nodes: ParsedLineageNode[], edgeId: string) {
	const edge = MEDALLION_PIPELINE_EDGES.find((e) => e.id === edgeId);
	if (!edge) return [];
	return nodes.filter((n) => n.isProcess && processMatchesEdge(n.attributes || {}, edge));
}

function LayerColumn({
	layer,
	items,
	highlightGuid,
	showMetadataTypes,
}: {
	layer: string;
	items: ParsedLineageNode[];
	highlightGuid?: string;
	showMetadataTypes?: boolean;
}) {
	const color = layerColor(layer);
	const meta = LINEAGE_METADATA_BY_LAYER[layer] || [];

	return (
		<div className='text-center flex-shrink-0' style={{ minWidth: 140, maxWidth: 200 }}>
			<div
				className={`p-3 rounded-3 border border-${color} bg-l10-${color} mb-2`}
				style={{ minHeight: 72 }}>
				<Icon icon={LAYER_ICONS[layer] as any} size='2x' color={color as any} />
				<div className='fw-bold mt-2 text-capitalize'>{layer}</div>
			</div>
			{items.map((n) => (
				<div
					key={n.guid}
					className={`small mb-1 px-2 py-1 rounded ${
						highlightGuid === n.guid ? `bg-${color} text-white` : 'bg-light'
					}`}
					title={n.qualifiedName}>
					{n.displayName}
				</div>
			))}
			{items.length === 0 && <small className='text-muted d-block'>Belum ada entitas</small>}
			{showMetadataTypes && meta.length > 0 && (
				<div className='mt-2'>
					{meta.slice(0, 3).map((m) => (
						<Badge key={m} color={color as any} isLight className='me-1 mb-1'>
							{m}
						</Badge>
					))}
				</div>
			)}
		</div>
	);
}

function EdgeColumn({ edgeId, processes }: { edgeId: string; processes: ParsedLineageNode[] }) {
	const edge = MEDALLION_PIPELINE_EDGES.find((e) => e.id === edgeId);
	if (!edge) return null;

	return (
		<div
			className='d-flex flex-column align-items-center justify-content-center px-2 flex-shrink-0'
			style={{ minWidth: 100 }}>
			<Icon icon='ArrowForward' color='primary' />
			<div className='small fw-semibold text-primary mt-1'>{edge.stepLabel}</div>
			<Badge color='primary' isLight className='mt-1'>
				{edge.pipelineName}
			</Badge>
			{processes.map((p) => (
				<small key={p.guid} className='text-muted mt-1 text-center' title={p.qualifiedName}>
					{p.displayName}
				</small>
			))}
			<small className='text-muted mt-1 text-center' style={{ fontSize: '0.7rem' }}>
				{edge.lineageKind}
			</small>
		</div>
	);
}

const MedallionLineageFlow: React.FC<MedallionLineageFlowProps> = ({
	nodes,
	highlightGuid,
	showMetadataTypes = false,
	maxDatasetsPerLayer = 3,
}) => {
	const limit = Math.max(1, maxDatasetsPerLayer);

	return (
		<div className='overflow-auto py-2'>
			<div className='d-flex flex-row align-items-stretch justify-content-center flex-nowrap gap-1'>
				{MEDALLION_DATA_LAYERS.map((layer, idx) => (
					<React.Fragment key={layer}>
						<LayerColumn
							layer={layer}
							items={datasetsForLayer(nodes, layer, limit)}
							highlightGuid={highlightGuid}
							showMetadataTypes={showMetadataTypes}
						/>
						{idx < MEDALLION_DATA_LAYERS.length - 1 && (
							<EdgeColumn
								edgeId={MEDALLION_PIPELINE_EDGES[idx].id}
								processes={processesForEdge(nodes, MEDALLION_PIPELINE_EDGES[idx].id)}
							/>
						)}
					</React.Fragment>
				))}
			</div>
		</div>
	);
};

export default MedallionLineageFlow;
