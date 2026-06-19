import React from 'react';
import { useRouter } from 'next/router';
import type { NextPage } from 'next';
import { GetStaticProps } from 'next';
import Head from 'next/head';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Card, { CardBody } from '../../components/bootstrap/Card';
import Icon from '../../components/icon/Icon';
import Badge from '../../components/bootstrap/Badge';
import Button from '../../components/bootstrap/Button';
import { isLayerPageId, MEDALLION_LAYERS } from '../../helpers/layerConfig';

const LayersPage: NextPage = () => {
	const router = useRouter();

	return (
		<PageWrapper>
			<Head>
				<title>Medallion Layers — Insightera</title>
			</Head>
			<SubHeader>
				<SubHeaderLeft>
					<Icon icon='Layers' size='2x' color='primary' />
					<span className='h4 mb-0 ms-2 fw-bold'>Medallion Architecture</span>
				</SubHeaderLeft>
			</SubHeader>
			<Page>
				{MEDALLION_LAYERS.map((layer, i) => (
					<div key={layer.id} className='row mb-4'>
						<div className='col-12'>
							<Card shadow='sm' borderSize={1} borderColor={layer.color as any}>
								<CardBody>
									<div className='row align-items-center'>
										<div className='col-md-1 text-center'>
											<Icon
												icon={layer.icon as any}
												size='3x'
												color={layer.color as any}
											/>
											{i < MEDALLION_LAYERS.length - 1 && (
												<div className='mt-2'>
													<Icon icon='ArrowDownward' color='primary' />
												</div>
											)}
										</div>
										<div className='col-md-7'>
											<h4>
												<Badge color={layer.color as any} className='me-2'>
													{layer.label}
												</Badge>
											</h4>
											<p className='mb-2'>{layer.description}</p>
											<small className='text-muted'>
												<strong>Pipeline:</strong> {layer.pipeline}
											</small>
										</div>
										<div className='col-md-3'>
											<h6 className='mb-2'>Metadata Types</h6>
											{layer.metadata.map((m) => (
												<Badge key={m} color='light' className='me-1 mb-1'>
													{m}
												</Badge>
											))}
										</div>
										<div className='col-md-1 text-end'>
											<Button
												color={layer.color as any}
												isLight
												icon='ArrowForward'
												onClick={() =>
													router.push(
														isLayerPageId(layer.id)
															? `/layers/${layer.id}`
															: `/catalog?classification=${layer.classification}`,
													)
												}>
												Browse
											</Button>
										</div>
									</div>
								</CardBody>
							</Card>
						</div>
					</div>
				))}
			</Page>
		</PageWrapper>
	);
};

export const getStaticProps: GetStaticProps = async ({ locale }) => ({
	props: {
		// @ts-ignore
		...(await serverSideTranslations(locale, ['common', 'menu'])),
	},
});

export default LayersPage;
