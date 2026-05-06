<script setup lang="ts">
import { ref, computed } from 'vue';
import { Card, DatePicker, Table, Statistic, Spin, Empty } from 'ant-design-vue';
import { getDeliveryStatsApi, type DeliveryBrandStat } from '#/api/delivery-record';
import dayjs from 'dayjs';

const selectedDate = ref(dayjs().format('YYYY-MM-DD'));
const loading = ref(false);
const stats = ref<DeliveryBrandStat[]>([]);
const total = ref(0);
const errorMsg = ref('');

const columns = [
  {
    title: '品牌名称',
    dataIndex: 'brand_name',
    key: 'brand_name',
  },
  {
    title: '送水量（桶）',
    dataIndex: 'total_delivered',
    key: 'total_delivered',
    align: 'right' as const,
  },
];

const tableData = computed(() => {
  const data = [...stats.value];
  if (total.value > 0) {
    data.push({
      brand_id: -1,
      brand_name: '合计',
      total_delivered: total.value,
    });
  }
  return data;
});

const rowClassName = (record: DeliveryBrandStat) => {
  return record.brand_id === -1 ? 'font-bold bg-gray-50' : '';
};

async function loadStats() {
  if (!selectedDate.value) return;
  loading.value = true;
  errorMsg.value = '';
  try {
    const result = await getDeliveryStatsApi(selectedDate.value);
    stats.value = result.brands || [];
    total.value = result.total || 0;
  } catch (error: any) {
    console.error('加载统计数据失败:', error);
    errorMsg.value = error?.message || '加载失败';
    stats.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function handleDateChange(_date: any, dateString: string) {
  selectedDate.value = dateString;
  loadStats();
}

// 初始加载
loadStats();
</script>

<template>
  <div class="p-4">
    <Card title="送水量统计" :bordered="false">
      <div class="mb-4 flex items-center gap-4">
        <span class="text-sm font-medium">选择日期：</span>
        <DatePicker
          v-model:value="selectedDate"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 180px"
          @change="handleDateChange"
        />
      </div>

      <Spin :spinning="loading">
        <div v-if="errorMsg" class="mb-4 rounded bg-red-50 p-3 text-red-600">
          {{ errorMsg }}
        </div>

        <div v-if="!loading && stats.length === 0 && !errorMsg" class="py-8">
          <Empty description="该日期暂无送水记录" />
        </div>

        <div v-if="stats.length > 0">
          <div class="mb-4 grid grid-cols-2 gap-4 md:grid-cols-4">
            <Card :bordered="true" size="small">
              <Statistic
                title="当日总送水量"
                :value="total"
                suffix="桶"
              />
            </Card>
            <Card :bordered="true" size="small">
              <Statistic
                title="涉及品牌数"
                :value="stats.length"
                suffix="个"
              />
            </Card>
          </div>

          <Table
            :columns="columns"
            :data-source="tableData"
            :pagination="false"
            size="middle"
            :row-class-name="rowClassName"
          />
        </div>
      </Spin>
    </Card>
  </div>
</template>
