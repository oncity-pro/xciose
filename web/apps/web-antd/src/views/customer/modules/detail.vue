<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { Card, Descriptions, DescriptionsItem, Table, Tag } from 'ant-design-vue';

import { getBucketDepositConfigApi } from '#/api/settings';
import { getDeliveryRecordListApi } from '#/api/delivery-record';
import type { DeliveryRecord } from '#/api/delivery-record';

const props = defineProps<{
  customerData?: Customer | null;
  brandName?: string;
}>();

const customer = computed(() => props.customerData);
const depositPerBucket = ref<number>(30);

// 送水记录
const deliveryRecords = ref<DeliveryRecord[]>([]);
const deliveryLoading = ref(false);

const deliveryColumns = [
  { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
  { title: '送水量', dataIndex: 'water_delivered', key: 'water_delivered', width: 100, align: 'center' as const },
  { title: '回桶数', dataIndex: 'buckets_returned', key: 'buckets_returned', width: 100, align: 'center' as const },
  { title: '欠空桶', dataIndex: 'owed_empty_buckets', key: 'owed_empty_buckets', width: 100, align: 'center' as const },
  { title: '存水量', dataIndex: 'storage_amount', key: 'storage_amount', width: 100, align: 'center' as const },
  { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
];

const emptyBucketDeposit = computed(() => {
  const owed = customer.value?.owed_empty_bucket ?? 0;
  return Number((owed * depositPerBucket.value).toFixed(2));
});

async function loadDeliveryRecords() {
  if (!customer.value?.id) return;
  deliveryLoading.value = true;
  try {
    const data = await getDeliveryRecordListApi(customer.value.id);
    deliveryRecords.value = data;
  } catch (error) {
    console.error('加载送水记录失败:', error);
  } finally {
    deliveryLoading.value = false;
  }
}

const [Modal, modalApi] = useVbenModal({
  async onOpenChange(isOpen: boolean) {
    if (isOpen) {
      modalApi.setState({ title: '客户详情' });
      try {
        const config = await getBucketDepositConfigApi();
        depositPerBucket.value = config.amount_per_bucket;
      } catch (error) {
        console.error('加载空桶押金配置失败:', error);
      }
      await loadDeliveryRecords();
    }
  },
});

function getCustomerTypeColor(type?: string) {
  switch (type) {
    case 'vip':
      return 'gold';
    case 'normal':
      return 'blue';
    case 'pickup':
      return 'cyan';
    case 'closed':
      return 'default';
    case 'slow_pay':
      return 'orange';
    case 'blacklist':
      return 'red';
    default:
      return 'default';
  }
}

function getCustomerTypeLabel(type?: string) {
  switch (type) {
    case 'vip':
      return 'VIP客户';
    case 'normal':
      return '普通客户';
    case 'pickup':
      return '自提客户';
    case 'closed':
      return '已注销';
    case 'slow_pay':
      return '收款慢';
    case 'blacklist':
      return '黑名单';
    default:
      return type || '-';
  }
}
</script>

<template>
  <Modal :footer="false" class="w-[1080px]">
    <Descriptions
      v-if="customer"
      :column="3"
      bordered
      :label-style="{ width: '80px', whiteSpace: 'nowrap' }"
      :content-style="{ whiteSpace: 'nowrap' }"
    >
      <DescriptionsItem label="客户编号">
        {{ customer.id }}
      </DescriptionsItem>
      <DescriptionsItem label="姓名地址">
        {{ customer.name }}
      </DescriptionsItem>
      <DescriptionsItem label="客户类型">
        <Tag :color="getCustomerTypeColor(customer.customer_type)">
          {{ getCustomerTypeLabel(customer.customer_type) }}
        </Tag>
      </DescriptionsItem>
      <DescriptionsItem v-if="customer.customer_type === 'vip'" label="VIP优惠方案">
        {{ customer.vip_scheme ? customer.vip_scheme.replace('_', '送') : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="品牌">
        {{ brandName || customer.brand_name || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="联系电话">
        {{ customer.phone || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="开户日期">
        {{ customer.openDate || customer.open_date || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="最后送水日期">
        {{ customer.lastDeliveryDate || customer.last_delivery_date || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="存水量">
        {{ customer.storage_amount ?? '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="总用水量">
        {{ customer.total_water_usage ?? customer.totalWaterUsage ?? '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="空桶押金">
        {{ emptyBucketDeposit }} 元
      </DescriptionsItem>
      <DescriptionsItem label="欠空桶">
        {{ customer.owed_empty_bucket ?? '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="备注">
        {{ customer.remark || '-' }}
      </DescriptionsItem>
    </Descriptions>

    <!-- 送水记录 -->
    <Card
      v-if="customer"
      title="送水记录"
      :loading="deliveryLoading"
      class="mt-6"
      :body-style="{ padding: '12px' }"
    >
      <Table
        :columns="deliveryColumns"
        :data-source="deliveryRecords"
        :pagination="false"
        size="small"
        :locale="{ emptyText: '暂无送水记录' }"
      />
    </Card>
  </Modal>
</template>
