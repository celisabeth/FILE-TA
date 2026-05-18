import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout, {
	dashboardEmbedStaticProps,
} from '../../components/dashboard/DashboardEmbedLayout';
import { MONITORING_MLOPS_LINK } from '../../helpers/dashboardPortal';

const MonitoringMlopsPage: NextPage = () => (
	<DashboardEmbedLayout link={MONITORING_MLOPS_LINK} />
);

export default MonitoringMlopsPage;
export const getStaticProps = dashboardEmbedStaticProps;
