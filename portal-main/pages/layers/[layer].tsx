import React, { useCallback, useEffect, useState } from 'react';
import type { NextPage } from 'next';
import { GetStaticPaths, GetStaticProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft, SubHeaderRight } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Card, {
	CardBody,
	CardHeader,
	CardLabel,
	CardTitle,
	CardActions,
} from '../../components/bootstrap/Card';
import Icon from '../../components/icon/Icon';
import Badge from '../../components/bootstrap/Badge';
import Button from '../../components/bootstrap/Button';
import Spinner from '../../components/bootstrap/Spinner';
import {
	getLayerById,
	isLayerPageId,
	LAYER_PAGE_IDS,
	type LayerPageId,
} from '../../helpers/layerConfig';
import { classificationColor } from '../../helpers/atlasApi';

interface DatasetItem {
	guid: string;
	typeName: string;
	attributes: Record<string, any>;
	classifications?: { typeName: string }[];
	status: string;
}

interface LayerDetailPageProps {
	layerId: LayerPageId;
}

const LayerDetailPage: NextPage<LayerDetailPageProps> = ({ layerId }) => {
	const router = useRouter();
	const layer = getLayerById(layerId)!;

	const [entities, setEntities] = useState<DatasetItem[]>([]);
	const [totalCount, setTotalCount] = useState(0);
	const [loading, setLoading] = useState(true);

	const fetchData = useCallback(async () => {
		setLoading(true);
		try {
			const params = new URLSearchParams({
				typeName: 'lakehouse_dataset',
				limit: '200',
				classification: layer.classification,
			});
			const res = await fetch(`/api/atlas/search?${params}`);
			const data = await res.json();
			const items: DatasetItem[] = data.entities || [];
			const filtered = items.filter((e) => {
				const qn = String(e.attributes?.qualifiedName || '');
				return qn.startsWith(`${layerId}.`);
			});
			setEntities(filtered.length > 0 ? filtered : items);
			setTotalCount(data.approximateCount ?? filtered.length ?? items.length);
		} catch {
			setEntities([]);
			setTotalCount(0);
		} finally {
			setLoading(false);
		}
	}, [layer.classification, layerId]);

	useEffect(() => {
		fetchData();
	}, [fetchData]);

	return (
		<PageWrapper>
			<Head>
				<title>
					{layer.label} Layer — Insightera
				</title>
			</Head>
			<SubHeader>
				<SubHeaderLeft>
					<Icon icon={layer.icon as any} size='2x' color={layer.color as any} />
					<span className='h4 mb-0 ms-2 fw-bold'>{layer.label} Layer</span>
					<Badge color={layer.color as any} isLight className='ms-3'>
						{totalCount} entitas
					</Badge>
				</SubHeaderLeft>
				<SubHeaderRight>
					<Button
						color='light'
						isLight
						icon='Layers'
						onClick={() => router.push('/layers')}>
						Semua Layer
					</Button>
					<Button
						color='primary'
						isLight
						className='ms-2'
						icon='Storage'
						onClick={() =>
							router.push(`/catalog?classification=${layer.classification}`)
						}>
						Browse Catalog
					</Button>
				</SubHeaderRight>
			</SubHeader>
			<Page>
				<div className='row mb-4'>
					<div className='col-12'>
						<Card shadow='sm' borderSize={1} borderColor={layer.color as any}>
							<CardBody>
								<p className='mb-2'>{layer.description}</p>
								<small className='text-muted d-block mb-3'>
									<strong>Pipeline:</strong> {layer.pipeline}
								</small>
								<h6 className='mb-2'>Metadata Types</h6>
								<div className='d-flex flex-wrap gap-1'>
									{layer.metadata.map((m) => (
										<Badge key={m} color='light'>
											{m}
										</Badge>
									))}
								</div>
							</CardBody>
						</Card>
					</div>
				</div>

				{loading ? (
					<div className='text-center py-5'>
						<Spinner color='primary' size='3rem' />
						<p className='mt-3 text-muted'>Memuat entitas dari Atlas…</p>
					</div>
				) : entities.length === 0 ? (
					<Card shadow='sm'>
						<CardBody className='text-center py-5'>
							<Icon icon='Inventory2' size='4x' color='primary' />
							<h4 className='mt-3'>Belum ada dataset di layer {layer.label}</h4>
							<p className='text-muted mb-4'>
								Jalankan pipeline metadata (<code>metadata_full_experiment</code>) agar
								entitas terdaftar di Atlas.
							</p>
							<Button
								color='primary'
								icon='PlayArrow'
								onClick={() =>
									router.push(`/catalog?classification=${layer.classification}`)
								}>
								Lihat di Catalog
							</Button>
						</CardBody>
					</Card>
				) : (
					<div className='row'>
						{entities.map((entity) => {
							const qn = entity.attributes?.qualifiedName || '';
							const name = entity.attributes?.name || qn;
							const desc = entity.attributes?.description || '';
							const rowCount = entity.attributes?.row_count;
							const colCount = entity.attributes?.column_count;
							const format = entity.attributes?.format;
							const location = entity.attributes?.location;
							const classifications = entity.classifications || [];

							return (
								<div key={entity.guid} className='col-md-6 col-lg-4 mb-3'>
									<Card
										shadow='sm'
										className='h-100 cursor-pointer border-start border-3'
										borderColor={layer.color as any}
										onClick={() =>
											router.push(`/catalog/${encodeURIComponent(qn)}`)
										}>
										<CardHeader className='pb-0'>
											<CardLabel
												icon='TableChart'
												iconColor={layer.color as any}>
												<CardTitle tag='h6' className='mb-0'>
													{name}
												</CardTitle>
											</CardLabel>
											<CardActions>
												<Badge color={layer.color as any} isLight>
													{layer.label}
												</Badge>
											</CardActions>
										</CardHeader>
										<CardBody className='pt-2'>
											{desc && (
												<p className='text-muted small mb-2'>
													{desc.length > 100
														? `${desc.slice(0, 100)}…`
														: desc}
												</p>
											)}
											<div className='d-flex flex-wrap gap-3 mb-2'>
												{format && (
													<small>
														<Icon icon='Description' className='me-1' />
														{format}
													</small>
												)}
												{rowCount != null && (
													<small>
														<Icon icon='TableRows' className='me-1' />
														{Number(rowCount).toLocaleString()} rows
													</small>
												)}
												{colCount != null && (
													<small>
														<Icon icon='ViewColumn' className='me-1' />
														{colCount} cols
													</small>
												)}
											</div>
											{location && (
												<small className='text-muted d-block mb-2 text-truncate'>
													<Icon icon='Folder' className='me-1' />
													{location}
												</small>
											)}
											<div className='d-flex flex-wrap gap-1'>
												{classifications.map((c) => (
													<Badge
														key={c.typeName}
														color={
															classificationColor(
																c.typeName,
															) as any
														}
														isLight
														className='small'>
														{c.typeName.replace(/_/g, ' ')}
													</Badge>
												))}
											</div>
										</CardBody>
									</Card>
								</div>
							);
						})}
					</div>
				)}

				<div className='mt-3'>
					<Link href='/lineage' className='text-primary'>
						<Icon icon='AccountTree' className='me-1' />
						Lihat data lineage
					</Link>
				</div>
			</Page>
		</PageWrapper>
	);
};

export const getStaticPaths: GetStaticPaths = async () => ({
	paths: LAYER_PAGE_IDS.map((layer) => ({ params: { layer } })),
	fallback: false,
});

export const getStaticProps: GetStaticProps<LayerDetailPageProps> = async ({ locale, params }) => {
	const layerParam = String(params?.layer || '');
	if (!isLayerPageId(layerParam)) {
		return { notFound: true };
	}

	return {
		props: {
			layerId: layerParam,
			// @ts-ignore
			...(await serverSideTranslations(locale, ['common', 'menu'])),
		},
	};
};

export default LayerDetailPage;
