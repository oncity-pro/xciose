<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// 获取当前月份的天数
function getDaysInMonth(year: number, month: number) {
  return new Date(year, month, 0).getDate();
}

// 生成本月日期数组（1日, 2日, ...）
function generateMonthDates() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1; // getMonth() 返回 0-11
  const days = getDaysInMonth(year, month);
  return Array.from({ length: days }).map((_item, index) => `${index + 1}日`);
}

// 生成随机数据
function generateRandomData(count: number, min: number, max: number) {
  return Array.from({ length: count }).map(() =>
    Math.floor(Math.random() * (max - min + 1)) + min,
  );
}

onMounted(() => {
  const dates = generateMonthDates();
  const daysCount = dates.length;

  const data1 = generateRandomData(daysCount, 5000, 50_000);
  const data2 = generateRandomData(daysCount, 2000, 30_000);

  // 计算本月销量的最高值（取两条线数据的最大值）
  const maxValue = Math.max(...data1, ...data2);
  // 向上取整到合适的刻度，并留出顶部空间
  const yAxisMax = Math.ceil(maxValue / 5000) * 5000;

  renderEcharts({
    grid: {
      bottom: 0,
      containLabel: true,
      left: '1%',
      right: '2%',
      top: '2 %',
    },
    series: [
      {
        areaStyle: {},
        data: data1,
        itemStyle: {
          color: '#5ab1ef',
        },
        smooth: true,
        type: 'line',
      },
      {
        areaStyle: {},
        data: data2,
        itemStyle: {
          color: '#019680',
        },
        smooth: true,
        type: 'line',
      },
    ],
    tooltip: {
      axisPointer: {
        lineStyle: {
          color: '#019680',
          width: 1,
        },
      },
      trigger: 'axis',
    },
    xAxis: {
      axisTick: {
        show: false,
      },
      boundaryGap: false,
      data: dates,
      splitLine: {
        lineStyle: {
          type: 'solid',
          width: 1,
        },
        show: true,
      },
      type: 'category',
    },
    yAxis: [
      {
        axisTick: {
          show: false,
        },
        max: yAxisMax,
        splitArea: {
          show: true,
        },
        splitNumber: 4,
        type: 'value',
      },
    ],
  });
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
