import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const MonitoringMlopsPage: NextPage = () => <DashboardEmbedLayout linkKey='grafanaMlops' />;

export default MonitoringMlopsPage;
export const getStaticProps = dashboardEmbedStaticProps;
