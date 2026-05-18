import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const KpiAqeOnPage: NextPage = () => <DashboardEmbedLayout linkKey='supersetAqeOn' />;

export default KpiAqeOnPage;
export const getStaticProps = dashboardEmbedStaticProps;
