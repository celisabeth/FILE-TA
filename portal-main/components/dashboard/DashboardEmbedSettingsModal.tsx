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
	superset: 'Dashboard Analitik — lakehouse.gold (Superset)',
	supersetAqeOff: 'KPI IKU AQE OFF — gold_aqe_off (Superset)',
	supersetAqeOn: 'KPI IKU AQE ON — gold_aqe_on (Superset)',
	grafanaInsight: 'Dashboard Insight (Grafana)',
	grafanaAqe: 'Monitoring AQE — metrik pipeline (Grafana)',
	grafanaMlops: 'Monitoring MLOps (Grafana)',
	prometheus: 'Prometheus',
};

interface Props {
	isOpen: boolean;
	setIsOpen: (open: boolean) => void;
	/** Sorot satu dashboard saat dibuka dari halaman embed tertentu. */
	highlightKey?: DashboardPortalKey;
}

const DashboardEmbedSettingsModal: React.FC<Props> = ({ isOpen, setIsOpen, highlightKey }) => {
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
			setSuccess(
				'Konfigurasi disimpan di server (data/embed-config.json). Semua pengguna portal memakai URL embed ini.',
			);
		} catch (e: unknown) {
			setError(e instanceof Error ? e.message : 'Gagal menyimpan');
		} finally {
			setSaving(false);
		}
	};

	const handlePreview = () => {
		updateBases({ grafanaBase, supersetBase, prometheusBase });
		setSuccess(
			'Pratinjau diterapkan di browser ini. Klik Simpan ke server agar permanen untuk semua user.',
		);
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
					Atur URL yang dimuat di iframe portal (bukan halaman utama Grafana/Superset).
					Jika masih memakai <code>localhost</code>, host diganti ke alamat browser Anda
					(mis. <code>103.174.114.177</code>).
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

				<h6 className='mb-3'>Base URL layanan</h6>
				<FormGroup>
					<Label>Grafana base URL</Label>
					<Input
						value={grafanaBase}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
							setGrafanaBase(e.target.value)
						}
						placeholder={`http://${typeof window !== 'undefined' ? window.location.hostname : '103.174.114.177'}:13001`}
					/>
					<small className='text-muted'>
						Dipakai untuk menghitung URL embed Grafana jika field per-dashboard dikosongkan.
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

				<h6 className='mb-3 mt-4'>URL embed per dashboard (iframe)</h6>
				{DASHBOARD_HUB_KEYS.map((key) => {
					const override = config.links?.[key];
					const built = links[key];
					const isHighlight = highlightKey === key;
					return (
						<CardEmbedOverride
							key={key}
							label={LINK_LABELS[key]}
							embedUrl={override?.embedUrl ?? built.embedUrl}
							onEmbedChange={(v) =>
								updateLinkOverride(key, { embedUrl: v, externalUrl: v })
							}
							onClear={() => clearLinkOverride(key)}
							hasOverride={Boolean(override?.embedUrl)}
							highlight={isHighlight}
						/>
					);
				})}

				<Button
					color='link'
					className='px-0 mb-3'
					onClick={() => setAdvanced(!advanced)}
					icon={advanced ? 'ExpandLess' : 'ExpandMore'}>
					Prometheus (opsional)
				</Button>

				{advanced && (
					<CardEmbedOverride
						label={LINK_LABELS.prometheus}
						embedUrl={config.links?.prometheus?.embedUrl ?? links.prometheus.embedUrl}
						onEmbedChange={(v) =>
							updateLinkOverride('prometheus', { embedUrl: v, externalUrl: v })
						}
						onClear={() => clearLinkOverride('prometheus')}
						hasOverride={Boolean(config.links?.prometheus?.embedUrl)}
					/>
				)}
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
	onEmbedChange,
	onClear,
	hasOverride,
	highlight,
}: {
	label: string;
	embedUrl: string;
	onEmbedChange: (v: string) => void;
	onClear: () => void;
	hasOverride: boolean;
	highlight?: boolean;
}) {
	return (
		<div
			className={`border rounded p-3 mb-3${highlight ? ' border-primary border-2' : ''}`}>
			<div className='d-flex justify-content-between align-items-center mb-2'>
				<strong className='small'>{label}</strong>
				{hasOverride && (
					<Button color='light' size='sm' onClick={onClear}>
						Hapus override
					</Button>
				)}
			</div>
			<FormGroup className='mb-0'>
				<Label className='small'>URL embed (iframe)</Label>
				<Input
					value={embedUrl}
					onChange={(e: React.ChangeEvent<HTMLInputElement>) => onEmbedChange(e.target.value)}
					placeholder='http://103.174.114.177:13001/d/...?orgId=1&kiosk'
				/>
			</FormGroup>
		</div>
	);
}

export default DashboardEmbedSettingsModal;
