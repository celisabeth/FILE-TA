import React, { useState } from 'react';
import type { NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft, SubHeaderRight } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Card, { CardBody, CardHeader, CardLabel, CardTitle, CardSubTitle } from '../../components/bootstrap/Card';
import Button from '../../components/bootstrap/Button';
import Icon from '../../components/icon/Icon';
import Badge from '../../components/bootstrap/Badge';
import DashboardEmbedSettingsModal from '../../components/dashboard/DashboardEmbedSettingsModal';
import { useDashboardEmbed } from '../../context/dashboardEmbedContext';
import { DASHBOARD_HUB_KEYS } from '../../helpers/dashboardEmbedConfig';
import type { DashboardPortalKey } from '../../helpers/dashboardPortal';

const PATH_BY_KEY: Record<DashboardPortalKey, string> = {
	superset: '/dashboards/analitik',
	grafanaInsight: '/dashboards/insight',
	grafanaAqe: '/dashboards/monitoring-aqe',
	grafanaMlops: '/dashboards/monitoring-mlops',
	prometheus: '/dashboards',
};

const DashboardsHubPage: NextPage = () => {
	const { links, source, config } = useDashboardEmbed();
	const [settingsOpen, setSettingsOpen] = useState(false);

	return (
		<PageWrapper>
			<Head>
				<title>Dashboard & Monitoring — Insightera Portal</title>
			</Head>
			<SubHeader>
				<SubHeaderLeft>
					<Icon icon='Insights' className='me-2' size='2x' />
					<span className='h4 mb-0'>Dashboard & Monitoring</span>
				</SubHeaderLeft>
				<SubHeaderRight>
					<Button color='primary' isLight icon='Settings' onClick={() => setSettingsOpen(true)}>
						Atur URL Embed
					</Button>
				</SubHeaderRight>
			</SubHeader>
			<Page>
				<div className='row g-4 mb-4'>
					<div className='col-12'>
						<Card stretch>
							<CardBody>
								<p className='mb-2'>
									Satu portal untuk <strong>Data Catalog</strong> (Atlas),{' '}
									<strong>Dashboard Analitik</strong> (Superset), dan{' '}
									<strong>Monitoring</strong> (Grafana). URL embed dikonfigurasi dari
									portal — tidak perlu edit env di VM.
								</p>
								<Badge color='info' isLight className='me-2'>
									Sumber: {source}
								</Badge>
								<Badge color='light' isLight>
									Grafana: {config.grafanaBase}
								</Badge>
							</CardBody>
						</Card>
					</div>
				</div>
				<div className='row g-4'>
					{DASHBOARD_HUB_KEYS.map((key) => {
						const item = links[key];
						return (
							<div key={item.key} className='col-12 col-lg-6'>
								<Card stretch className={`border-${item.color} border-2`}>
									<CardHeader>
										<CardLabel icon={item.icon} iconColor={item.color}>
											<CardTitle>{item.title}</CardTitle>
											<CardSubTitle tag='div' className='text-muted'>
												{item.description}
											</CardSubTitle>
										</CardLabel>
									</CardHeader>
									<CardBody>
										<p className='small text-muted text-truncate mb-3' title={item.embedUrl}>
											{item.embedUrl}
										</p>
										<div className='d-flex flex-wrap gap-2'>
											<Link
												href={PATH_BY_KEY[item.key] || '/dashboards'}
												passHref
												legacyBehavior>
												<Button color={item.color} icon='Fullscreen'>
													Buka halaman embed
												</Button>
											</Link>
											<Button
												color='dark'
												isLight
												icon='Settings'
												onClick={() => setSettingsOpen(true)}>
												URL Embed
											</Button>
										</div>
									</CardBody>
								</Card>
							</div>
						);
					})}
				</div>
			</Page>
			<DashboardEmbedSettingsModal isOpen={settingsOpen} setIsOpen={setSettingsOpen} />
		</PageWrapper>
	);
};

export default DashboardsHubPage;

export const getStaticProps: GetStaticProps = async ({ locale }) => ({
	props: {
		// @ts-ignore
		...(await serverSideTranslations(locale || 'en', ['common', 'menu'])),
	},
});
