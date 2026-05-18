import React from 'react';
import Head from 'next/head';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft, SubHeaderRight } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Button from '../bootstrap/Button';
import Icon from '../icon/Icon';
import EmbeddedServiceFrame from './EmbeddedServiceFrame';
import type { DashboardPortalLink } from '../../helpers/dashboardPortal';

interface DashboardEmbedLayoutProps {
	link: DashboardPortalLink;
}

const DashboardEmbedLayout: React.FC<DashboardEmbedLayoutProps> = ({ link }) => {
	return (
		<PageWrapper>
			<Head>
				<title>{link.title} — InsightERA Portal</title>
			</Head>
			<SubHeader>
				<SubHeaderLeft>
					<Icon icon={link.icon as 'Analytics'} className='me-2' size='2x' />
					<div>
						<span className='h4 mb-0'>{link.title}</span>
						<div className='text-muted small'>{link.description}</div>
					</div>
				</SubHeaderLeft>
				<SubHeaderRight>
					<Button
						color={link.color}
						icon='OpenInNew'
						tag='a'
						href={link.externalUrl}
						target='_blank'
						rel='noopener noreferrer'>
						Buka layanan
					</Button>
				</SubHeaderRight>
			</SubHeader>
			<Page container='fluid'>
				<EmbeddedServiceFrame link={link} />
			</Page>
		</PageWrapper>
	);
};

export default DashboardEmbedLayout;

export const dashboardEmbedStaticProps: GetStaticProps = async ({ locale }) => ({
	props: {
		...(await serverSideTranslations(locale || 'en', ['common', 'menu'])),
	},
});
