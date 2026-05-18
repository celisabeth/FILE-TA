import React, { useEffect, useState } from 'react';
import Modal, { ModalBody, ModalFooter, ModalHeader, ModalTitle } from '../bootstrap/Modal';
import Button from '../bootstrap/Button';
import Input from '../bootstrap/forms/Input';
import FormGroup from '../bootstrap/forms/FormGroup';
import Label from '../bootstrap/forms/Label';
import Alert from '../bootstrap/Alert';
import Icon from '../icon/Icon';
import { useDashboardEmbed } from '../../context/dashboardEmbedContext';
import type { DashboardPortalKey } from '../../helpers/dashboardPortal';
import { DASHBOARD_HUB_KEYS, mergeEmbedConfig } from '../../helpers/dashboardEmbedConfig';

const LINK_LABELS: Record<DashboardPortalKey, string> = {
	superset: 'Dashboard Analitik (Superset)',
	grafanaInsight: 'Dashboard Insight (Grafana)',
	grafanaAqe: 'Monitoring AQE (Grafana)',
	grafanaMlops: 'Monitoring MLOps (Grafana)',
	prometheus: 'Prometheus',
};

interface Props {
	isOpen: boolean;
	setIsOpen: (open: boolean) => void;
}

const DashboardEmbedSettingsModal: React.FC<Props> = ({ isOpen, setIsOpen }) => {
	const {
		config,
		links,
		source,
		updateBases,
		updateLinkOverride,
		clearLinkOverride,
		saveConfig,
		resetToDefaults,
	} = useDashboardEmbed();

	const [grafanaBase, setGrafanaBase] = useState(config.grafanaBase);
	const [supersetBase, setSupersetBase] = useState(config.supersetBase);
	const [prometheusBase, setPrometheusBase] = useState(config.prometheusBase);
	const [advanced, setAdvanced] = useState(false);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [success, setSuccess] = useState<string | null>(null);

	useEffect(() => {
		if (!isOpen) return;
		setGrafanaBase(config.grafanaBase);
		setSupersetBase(config.supersetBase);
		setPrometheusBase(config.prometheusBase);
		setError(null);
		setSuccess(null);
	}, [isOpen, config]);

	const handleSave = async () => {
		setSaving(true);
		setError(null);
		setSuccess(null);
		const toSave = mergeEmbedConfig({
			...config,
			grafanaBase,
			supersetBase,
			prometheusBase,
		});
		try {
			await saveConfig(toSave);
			setSuccess('Konfigurasi disimpan di server (data/embed-config.json). Semua pengguna portal memakai URL ini.');
		} catch (e: unknown) {
			setError(e instanceof Error ? e.message : 'Gagal menyimpan');
		} finally {
			setSaving(false);
		}
	};

	const handlePreview = () => {
		updateBases({ grafanaBase, supersetBase, prometheusBase });
		setSuccess('Pratinjau diterapkan di browser ini. Klik Simpan ke server agar permanen untuk semua user.');
	};

	return (
		<Modal isOpen={isOpen} setIsOpen={setIsOpen} size='lg' titleId='embed-settings'>
			<ModalHeader setIsOpen={setIsOpen}>
				<ModalTitle id='embed-settings'>
					<Icon icon='Settings' className='me-2' />
					Pengaturan URL Embed Dashboard
				</ModalTitle>
			</ModalHeader>
			<ModalBody>
				<p className='text-muted small'>
					Atur base URL Grafana, Superset, dan Prometheus tanpa mengubah variabel lingkungan di
					VM. URL embed dihitung otomatis dari base URL; bagian lanjutan memungkinkan override
					per dashboard.
				</p>
				<Alert color='info' isLight>
					Sumber aktif: <strong>{source}</strong>
					{source === 'env' && ' (default dari NEXT_PUBLIC_* — belum disimpan ke file)'}
				</Alert>

				{error && (
					<Alert color='danger' isLight>
						{error}
					</Alert>
				)}
				{success && (
					<Alert color='success' isLight>
						{success}
					</Alert>
				)}

				<FormGroup>
					<Label>Grafana base URL</Label>
					<Input
						value={grafanaBase}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
							setGrafanaBase(e.target.value)
						}
						placeholder='http://103.174.114.177:13001'
					/>
					<small className='text-muted'>
						Contoh embed Insight: {links.grafanaInsight.embedUrl}
					</small>
				</FormGroup>

				<FormGroup>
					<Label>Superset base URL</Label>
					<Input
						value={supersetBase}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
							setSupersetBase(e.target.value)
						}
						placeholder='http://103.174.114.177:18089'
					/>
				</FormGroup>

				<FormGroup>
					<Label>Prometheus base URL</Label>
					<Input
						value={prometheusBase}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
							setPrometheusBase(e.target.value)
						}
						placeholder='http://103.174.114.177:19090'
					/>
				</FormGroup>

				<Button
					color='link'
					className='px-0 mb-3'
					onClick={() => setAdvanced(!advanced)}
					icon={advanced ? 'ExpandLess' : 'ExpandMore'}>
					URL embed per dashboard (lanjutan)
				</Button>

				{advanced &&
					DASHBOARD_HUB_KEYS.concat(['prometheus'] as DashboardPortalKey[]).map((key) => {
						const override = config.links?.[key];
						const built = links[key];
						return (
							<CardEmbedOverride
								key={key}
								label={LINK_LABELS[key]}
								embedUrl={override?.embedUrl ?? built.embedUrl}
								externalUrl={override?.externalUrl ?? built.externalUrl}
								onEmbedChange={(v) => updateLinkOverride(key, { embedUrl: v })}
								onExternalChange={(v) => updateLinkOverride(key, { externalUrl: v })}
								onClear={() => clearLinkOverride(key)}
								hasOverride={Boolean(override?.embedUrl || override?.externalUrl)}
							/>
						);
					})}
			</ModalBody>
			<ModalFooter>
				<Button color='light' onClick={() => resetToDefaults()}>
					Reset default
				</Button>
				<Button color='info' isLight onClick={handlePreview}>
					Pratinjau
				</Button>
				<Button color='primary' onClick={handleSave} isDisable={saving}>
					{saving ? 'Menyimpan…' : 'Simpan ke server'}
				</Button>
			</ModalFooter>
		</Modal>
	);
};

function CardEmbedOverride({
	label,
	embedUrl,
	externalUrl,
	onEmbedChange,
	onExternalChange,
	onClear,
	hasOverride,
}: {
	label: string;
	embedUrl: string;
	externalUrl: string;
	onEmbedChange: (v: string) => void;
	onExternalChange: (v: string) => void;
	onClear: () => void;
	hasOverride: boolean;
}) {
	return (
		<div className='border rounded p-3 mb-3'>
			<div className='d-flex justify-content-between align-items-center mb-2'>
				<strong className='small'>{label}</strong>
				{hasOverride && (
					<Button color='light' size='sm' onClick={onClear}>
						Hapus override
					</Button>
				)}
			</div>
			<FormGroup>
				<Label className='small'>Embed URL (iframe)</Label>
				<Input
					value={embedUrl}
					onChange={(e: React.ChangeEvent<HTMLInputElement>) => onEmbedChange(e.target.value)}
				/>
			</FormGroup>
			<FormGroup className='mb-0'>
				<Label className='small'>External URL (tab baru)</Label>
				<Input
					value={externalUrl}
					onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
						onExternalChange(e.target.value)
					}
				/>
			</FormGroup>
		</div>
	);
}

export default DashboardEmbedSettingsModal;
