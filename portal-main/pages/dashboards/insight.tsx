import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const DashboardInsightPage: NextPage = () => (
	<DashboardEmbedLayout linkKey='grafanaInsight' />
);

export default DashboardInsightPage;
export const getStaticProps = dashboardEmbedStaticProps;
