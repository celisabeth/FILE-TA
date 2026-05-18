import React from 'react';
import type { NextPage } from 'next';
import DashboardEmbedLayout from '../../components/dashboard/DashboardEmbedLayout';
import { dashboardEmbedStaticProps } from '../../helpers/dashboardEmbedStaticProps';

const DashboardAnalitikPage: NextPage = () => <DashboardEmbedLayout linkKey='superset' />;

export default DashboardAnalitikPage;
export const getStaticProps = dashboardEmbedStaticProps;
