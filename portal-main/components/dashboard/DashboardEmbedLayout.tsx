import React, { useState } from 'react';
import Head from 'next/head';
import PageWrapper from '../../layout/PageWrapper/PageWrapper';
import SubHeader, { SubHeaderLeft, SubHeaderRight } from '../../layout/SubHeader/SubHeader';
import Page from '../../layout/Page/Page';
import Button from '../bootstrap/Button';
import Icon from '../icon/Icon';
import Spinner from '../bootstrap/Spinner';
import EmbeddedServiceFrame from './EmbeddedServiceFrame';
import DashboardEmbedSettingsModal from './DashboardEmbedSettingsModal';
import { useDashboardEmbed } from '../../context/dashboardEmbedContext';
import type { DashboardPortalKey } from '../../helpers/dashboardPortal';

interface DashboardEmbedLayoutProps {
	linkKey: DashboardPortalKey;
}

const DashboardEmbedLayout: React.FC<DashboardEmbedLayoutProps> = ({ linkKey }) => {
	const { getLink, loading } = useDashboardEmbed();
	const [settingsOpen, setSettingsOpen] = useState(false);
	const link = getLink(linkKey);

	return (
		<PageWrapper>
			<Head>
				<title>{link.title} — Insightera</title>
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
						color='light'
						isLight
						icon='Settings'
						onClick={() => setSettingsOpen(true)}>
						URL Embed
					</Button>
					<Button
						color={link.color}
						isLight
						className='ms-2'
						icon='OpenInNew'
						tag='a'
						href={link.embedUrl}
						target='_blank'
						rel='noopener noreferrer'>
						Buka di tab baru
					</Button>
				</SubHeaderRight>
			</SubHeader>
			<Page container='fluid'>
				{loading ? (
					<div className='text-center py-5'>
						<Spinner color='primary' size='3rem' />
					</div>
				) : (
					<EmbeddedServiceFrame link={link} />
				)}
			</Page>
			<DashboardEmbedSettingsModal
				isOpen={settingsOpen}
				setIsOpen={setSettingsOpen}
				highlightKey={linkKey}
			/>
		</PageWrapper>
	);
};

export default DashboardEmbedLayout;
