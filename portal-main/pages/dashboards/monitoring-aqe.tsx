import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout, {
	dashboardEmbedStaticProps,
} from '../../components/dashboard/DashboardEmbedLayout';
import { MONITORING_AQE_LINK } from '../../helpers/dashboardPortal';

const MonitoringAqePage: NextPage = () => <DashboardEmbedLayout link={MONITORING_AQE_LINK} />;

export default MonitoringAqePage;
export const getStaticProps = dashboardEmbedStaticProps;
