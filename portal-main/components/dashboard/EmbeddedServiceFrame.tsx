import React, { useState } from 'react';
import Alert from '../bootstrap/Alert';
import Button from '../bootstrap/Button';
import Icon from '../icon/Icon';
import type { DashboardPortalLink } from '../../helpers/dashboardPortal';

interface EmbeddedServiceFrameProps {
	link: DashboardPortalLink;
	height?: string;
}

const EmbeddedServiceFrame: React.FC<EmbeddedServiceFrameProps> = ({
	link,
	height = 'calc(100vh - 220px)',
}) => {
	const [loadError, setLoadError] = useState(false);

	return (
		<>
			{link.embedHint && (
				<Alert color='info' isLight className='mb-3'>
					<Icon icon='Info' className='me-2' />
					{link.embedHint}{' '}
					<Button
						color='info'
						isLink
						tag='a'
						href={link.embedUrl}
						target='_blank'
						rel='noopener noreferrer'
						className='ms-1'>
						Buka di tab baru
					</Button>
				</Alert>
			)}
			{loadError && (
				<Alert color='warning' className='mb-3'>
					Embed mungkin diblokir (X-Frame-Options / CORS). Gunakan tombol &quot;Buka di tab
					baru&quot; di header atau pastikan Grafana{' '}
					<code>GF_SECURITY_ALLOW_EMBEDDING=true</code>.
				</Alert>
			)}
			<div
				className='ratio ratio-16x9 rounded-3 overflow-hidden border bg-light'
				style={{ minHeight: height }}>
				<iframe
					title={link.title}
					src={link.embedUrl}
					className='w-100 h-100 border-0'
					style={{ minHeight: height }}
					allow='fullscreen'
					loading='lazy'
					referrerPolicy='no-referrer-when-downgrade'
					onError={() => setLoadError(true)}
				/>
			</div>
		</>
	);
};

export default EmbeddedServiceFrame;
