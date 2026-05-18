import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout, {
	dashboardEmbedStaticProps,
} from '../../components/dashboard/DashboardEmbedLayout';
import { INSIGHT_LINK } from '../../helpers/dashboardPortal';

const DashboardInsightPage: NextPage = () => <DashboardEmbedLayout link={INSIGHT_LINK} />;

export default DashboardInsightPage;
export const getStaticProps = dashboardEmbedStaticProps;
