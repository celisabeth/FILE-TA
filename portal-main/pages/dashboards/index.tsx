import React from 'react';
import type { NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Card, { CardBody, CardHeader, CardLabel, CardTitle, CardSubTitle } from '../../components/bootstrap/Card';
import Button from '../../components/bootstrap/Button';
import Icon from '../../components/icon/Icon';
import Badge from '../../components/bootstrap/Badge';
import { DASHBOARD_HUB_CARDS } from '../../helpers/dashboardPortal';

const PATH_BY_KEY: Record<string, string> = {
	superset: '/dashboards/analitik',
	grafanaInsight: '/dashboards/insight',
	grafanaAqe: '/dashboards/monitoring-aqe',
	grafanaMlops: '/dashboards/monitoring-mlops',
};

const DashboardsHubPage: NextPage = () => {
	return (
		<PageWrapper>
			<Head>
				<title>Dashboard & Monitoring — InsightERA Portal</title>
			</Head>
			<SubHeader>
				<SubHeaderLeft>
					<Icon icon='Insights' className='me-2' size='2x' />
					<span className='h4 mb-0'>Dashboard & Monitoring</span>
				</SubHeaderLeft>
			</SubHeader>
			<Page>
				<div className='row g-4 mb-4'>
					<div className='col-12'>
						<Card stretch>
							<CardBody>
								<p className='mb-2'>
									Satu portal untuk <strong>Data Catalog</strong> (Atlas),{' '}
									<strong>Dashboard Analitik</strong> (Superset), dan{' '}
									<strong>Monitoring</strong> (Grafana: Insight, AQE, MLOps). URL embed
									dari <code>NEXT_PUBLIC_SUPERSET_URL</code> dan{' '}
									<code>NEXT_PUBLIC_GRAFANA_URL</code>.
								</p>
								<Badge color='info' isLight>
									portal-main · :13000
								</Badge>
							</CardBody>
						</Card>
					</div>
				</div>
				<div className='row g-4'>
					{DASHBOARD_HUB_CARDS.map((item) => (
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
									<div className='d-flex flex-wrap gap-2'>
										<Link href={PATH_BY_KEY[item.key] || '/dashboards'} passHref legacyBehavior>
											<Button color={item.color} icon='Fullscreen'>
												Buka embed
											</Button>
										</Link>
										<Button
											color='dark'
											isLight
											icon='OpenInNew'
											tag='a'
											href={item.externalUrl}
											target='_blank'
											rel='noopener noreferrer'>
											Tab baru
										</Button>
									</div>
								</CardBody>
							</Card>
						</div>
					))}
				</div>
			</Page>
		</PageWrapper>
	);
};

export default DashboardsHubPage;

export const getStaticProps: GetStaticProps = async ({ locale }) => ({
	props: {
		...(await serverSideTranslations(locale || 'en', ['common', 'menu'])),
	},
});
