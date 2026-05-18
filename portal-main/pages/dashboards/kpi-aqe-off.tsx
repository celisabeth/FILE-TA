import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const KpiAqeOffPage: NextPage = () => <DashboardEmbedLayout linkKey='supersetAqeOff' />;

export default KpiAqeOffPage;
export const getStaticProps = dashboardEmbedStaticProps;
