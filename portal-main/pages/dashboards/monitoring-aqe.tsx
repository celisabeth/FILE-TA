import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const MonitoringAqePage: NextPage = () => <DashboardEmbedLayout linkKey='grafanaAqe' />;

export default MonitoringAqePage;
export const getStaticProps = dashboardEmbedStaticProps;
