<script lang="ts" setup>
import type { AnalysisOverviewItem } from '@vben/common-ui';
import type { TabOption } from '@vben/types';

import { computed, onMounted, ref } from 'vue';

import {
  AnalysisChartCard,
  AnalysisChartsTabs,
  AnalysisOverview,
  VbenCountToAnimator,
} from '@vben/common-ui';
import {
  SvgBellIcon,
  SvgCakeIcon,
  SvgDownloadIcon,
} from '@vben/icons';

import { getCustomerStatsApi } from '#/api/customer';
import { getDeliveryStatsApi } from '#/api/delivery-record';

import AnalyticsTrends from './analytics-trends.vue';
import AnalyticsVisitsData from './analytics-visits-data.vue';
import AnalyticsVisitsSales from './analytics-visits-sales.vue';
import AnalyticsVisitsSource from './analytics-visits-source.vue';
import AnalyticsVisits from './analytics-visits.vue';
import CustomerOverviewCard from './customer-overview-card.vue';

// 客户统计数据
const customerStats = ref({ 
  total: 0,
  newThisMonth: 0,
  closedThisMonth: 0
});

// 今日送水量
const todayWaterDelivered = ref(0);

// 加载客户统计数据
async function loadCustomerStats() {
  try {
    const data = await getCustomerStatsApi();
    customerStats.value = data;
  } catch (error) {
    console.error('加载客户统计数据失败:', error);
  }
}

// 加载今日送水量
async function loadTodayWaterDelivered() {
  try {
    const today = new Date().toISOString().split('T')[0] || '';
    const result = await getDeliveryStatsApi(today);
    todayWaterDelivered.value = result.total || 0;
  } catch (error) {
    console.error('加载今日送水量失败:', error);
  }
}

// 动态生成概览数据（不包含客户量，客户量使用自定义组件）
const overviewItems = computed<AnalysisOverviewItem[]>(() => [
  {
    icon: SvgCakeIcon,
    title: '今日送水量',
    totalTitle: '今日总送水量',
    totalValue: todayWaterDelivered.value,
    value: todayWaterDelivered.value,
  },
  {
    icon: SvgDownloadIcon,
    title: '下载量',
    totalTitle: '总下载量',
    totalValue: 120_000,
    value: 8000,
  },
  {
    icon: SvgBellIcon,
    title: '使用量',
    totalTitle: '总使用量',
    totalValue: 50_000,
    value: 5000,
  },
]);

onMounted(() => {
  loadCustomerStats();
  loadTodayWaterDelivered();
});

const chartTabs: TabOption[] = [
  {
    label: '本月数据',
    value: 'trends',
  },
  {
    label: '本年数据',
    value: 'visits',
  },
];
</script>

<template>
  <div class="p-5">
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <CustomerOverviewCard 
        :total="customerStats.total" 
        :new-this-month="customerStats.newThisMonth"
        :closed-this-month="customerStats.closedThisMonth"
      />
      <div v-for="item in overviewItems" :key="item.title" class="card-box w-full rounded-lg border border-border bg-card">
        <div class="flex flex-col space-y-1 px-6 pt-4 pb-0">
          <div class="text-lg font-semibold leading-none tracking-tight">{{ item.title }}</div>
        </div>
        <div class="flex items-center justify-between px-6 py-4">
          <VbenCountToAnimator :end-val="item.value" :start-val="1" class="text-lg font-bold" prefix="" />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="size-7 shrink-0"
          >
            <path v-if="item.title === '今日送水量'" d="M3 3v18h18" />
            <path v-else-if="item.title === '下载量'" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <path v-else d="M12 2v20M2 12h20" />
          </svg>
        </div>
        <!-- 分隔线 -->
        <div class="mx-6">
          <div class="border-t"></div>
        </div>
        
        <!-- CardFooter -->
        <div class="flex items-center justify-between px-6 py-4">
          <span class="text-xs">{{ item.totalTitle }}</span>
          <VbenCountToAnimator :end-val="item.totalValue" :start-val="1" class="text-base font-semibold" prefix="" />
        </div>
      </div>
    </div>
    <div class="mt-5 w-full md:flex">
      <div class="md:mr-4 md:w-2/3">
        <AnalysisChartsTabs :tabs="chartTabs">
          <template #trends>
            <AnalyticsTrends />
          </template>
          <template #visits>
            <AnalyticsVisits />
          </template>
        </AnalysisChartsTabs>
      </div>
      <AnalysisChartCard class="mt-5 md:mt-0 md:w-1/3" title="品牌占比">
        <AnalyticsVisitsSource />
      </AnalysisChartCard>
    </div>

    <div class="mt-5 w-full md:flex">
      <AnalysisChartCard class="mt-5 md:mt-0 md:mr-4 md:w-1/2" title="访问数量">
        <AnalyticsVisitsData />
      </AnalysisChartCard>
      <AnalysisChartCard class="mt-5 md:mt-0 md:w-1/2" title="访问来源">
        <AnalyticsVisitsSales />
      </AnalysisChartCard>
    </div>
  </div>
</template>
