<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { getCustomerListApi } from '#/api/customer';
import { getWaterBrandListApi } from '#/api/water-brand';

const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

async function loadBrandDistribution() {
  try {
    // 并行获取品牌列表和客户列表
    const [brands, customers] = await Promise.all([
      getWaterBrandListApi(),
      getCustomerListApi(),
    ]);

    // 建立品牌ID到名称的映射
    const brandMap = new Map<number, string>();
    brands.forEach((brand) => {
      brandMap.set(brand.id, brand.name);
    });

    // 统计每个品牌的客户数量
    const brandCount = new Map<number, number>();
    let unsetCount = 0;

    customers.forEach((customer) => {
      const brandId = customer.brand;
      if (brandId && brandMap.has(brandId)) {
        brandCount.set(brandId, (brandCount.get(brandId) || 0) + 1);
      } else {
        unsetCount++;
      }
    });

    // 构建饼图数据
    const pieData: Array<{ name: string; value: number }> = [];

    // 添加有品牌的客户
    brandCount.forEach((count, brandId) => {
      pieData.push({
        name: brandMap.get(brandId) || `品牌${brandId}`,
        value: count,
      });
    });

    // 添加未设置品牌的客户
    if (unsetCount > 0) {
      pieData.push({
        name: '未设置品牌',
        value: unsetCount,
      });
    }

    // 如果没有数据，显示空状态
    if (pieData.length === 0) {
      pieData.push({ name: '暂无数据', value: 0 });
    }

    // 渲染图表
    renderEcharts({
      legend: {
        bottom: '2%',
        left: 'center',
      },
      series: [
        {
          animationDelay() {
            return Math.random() * 100;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          avoidLabelOverlap: false,
          color: ['#5ab1ef', '#b6a2de', '#67e0e3', '#2ec7c9', '#ffb980', '#d87a80', '#8d98b3'],
          data: pieData,
          emphasis: {
            label: {
              fontSize: '12',
              fontWeight: 'bold',
              show: true,
            },
          },
          itemStyle: {
            borderRadius: 10,
            borderWidth: 2,
          },
          label: {
            position: 'center',
            show: false,
          },
          labelLine: {
            show: false,
          },
          name: '品牌占比',
          radius: ['40%', '65%'],
          type: 'pie',
        },
      ],
      tooltip: {
        formatter: '{b}: {c}位 ({d}%)',
        trigger: 'item',
      },
    });
  } catch (error) {
    console.error('加载品牌占比数据失败:', error);
    // 显示错误状态的图表
    renderEcharts({
      legend: {
        bottom: '2%',
        left: 'center',
      },
      series: [
        {
          animationDelay() {
            return Math.random() * 100;
          },
          animationEasing: 'exponentialInOut',
          animationType: 'scale',
          avoidLabelOverlap: false,
          color: ['#ccc'],
          data: [{ name: '加载失败', value: 1 }],
          emphasis: {
            label: {
              fontSize: '12',
              fontWeight: 'bold',
              show: true,
            },
          },
          itemStyle: {
            borderRadius: 10,
            borderWidth: 2,
          },
          label: {
            position: 'center',
            show: false,
          },
          labelLine: {
            show: false,
          },
          name: '品牌占比',
          radius: ['40%', '65%'],
          type: 'pie',
        },
      ],
      tooltip: {
        trigger: 'item',
      },
    });
  }
}

onMounted(() => {
  loadBrandDistribution();
});
</script>

<template>
  <EchartsUI ref="chartRef" />
</template>
