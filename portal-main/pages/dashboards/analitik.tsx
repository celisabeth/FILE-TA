import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout, {
	dashboardEmbedStaticProps,
} from '../../components/dashboard/DashboardEmbedLayout';
import { ANALITIK_LINK } from '../../helpers/dashboardPortal';

const DashboardAnalitikPage: NextPage = () => <DashboardEmbedLayout link={ANALITIK_LINK} />;

export default DashboardAnalitikPage;
export const getStaticProps = dashboardEmbedStaticProps;
