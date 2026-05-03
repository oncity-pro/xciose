<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, ref, watch } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { Card, Descriptions, DescriptionsItem, Tag } from 'ant-design-vue';

import { getBucketDepositConfigApi } from '#/api/settings';
import { getDeliveryRecordListApi, updateDeliveryRecordApi } from '#/api/delivery-record';
import type { DeliveryRecord } from '#/api/delivery-record';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import type { VxeTableGridOptions } from '#/adapter/vxe-table';

const props = defineProps<{
  customerData?: Customer | null;
  brandName?: string;
}>();

const customer = computed(() => props.customerData);
const depositPerBucket = ref<number>(30);

// 送水记录
const deliveryRecords = ref<DeliveryRecord[]>([]);
const deliveryLoading = ref(false);

const emptyBucketDeposit = computed(() => {
  const owed = customer.value?.owed_empty_bucket ?? 0;
  return Number((owed * depositPerBucket.value).toFixed(2));
});

const deliveryGridOptions: VxeTableGridOptions<any> = {
  editConfig: {
    trigger: 'click',
    mode: 'cell',
    showStatus: true,
    activeMethod: (params: any) => {
      console.log('edit activeMethod', params.row?.id, params.column?.field);
      return !String(params.row?.id).startsWith('__empty__');
    },
  },
  columns: [
    {
      field: 'date',
      title: '日期',
      width: 120,
      editRender: { name: 'input' },
    },
    {
      field: 'water_delivered',
      title: '送水量',
      width: 100,
      editRender: { name: 'input' },
    },
    {
      field: 'buckets_returned',
      title: '回桶数',
      width: 100,
      editRender: { name: 'input' },
    },
    {
      field: 'owed_empty_buckets',
      title: '欠空桶',
      width: 100,
      editRender: { name: 'input' },
    },
    {
      field: 'storage_amount',
      title: '存水量',
      width: 100,
      editRender: { name: 'input' },
    },
    {
      field: 'remark',
      title: '备注',
      minWidth: 200,
      editRender: { name: 'input' },
    },
  ],
  pagerConfig: {},
  showOverflow: true,
  proxyConfig: {
    ajax: {
      query: async () => {
        return {
          items: displayDeliveryRecords.value,
          total: displayDeliveryRecords.value.length,
        };
      },
    },
  },
};

const [DeliveryGrid, deliveryGridApi] = useVbenVxeGrid({
  gridOptions: deliveryGridOptions,
});

const displayDeliveryRecords = computed(() => {
  const data = deliveryRecords.value.map((r) => ({ ...r }));
  while (data.length < 10) {
    data.push({
      id: `__empty__${data.length}`,
      customer: '',
      date: '',
      water_delivered: '',
      buckets_returned: '',
      owed_empty_buckets: '',
      storage_amount: '',
      remark: '',
    } as any);
  }
  return data;
});

async function loadDeliveryRecords() {
  if (!customer.value?.id) return;
  deliveryLoading.value = true;
  try {
    const data = await getDeliveryRecordListApi(customer.value.id);
    deliveryRecords.value = data;
    await deliveryGridApi.reload();
  } catch (error) {
    console.error('加载送水记录失败:', error);
  } finally {
    deliveryLoading.value = false;
  }
}

async function handleEditClosed({ row }: any) {
  if (String(row.id).startsWith('__empty__')) return;
  if (!row.id) return;

  try {
    await updateDeliveryRecordApi(row.id, {
      date: row.date,
      water_delivered: row.water_delivered,
      buckets_returned: row.buckets_returned,
      owed_empty_buckets: row.owed_empty_buckets,
      storage_amount: row.storage_amount,
      remark: row.remark,
    });
  } catch (error) {
    console.error('更新送水记录失败:', error);
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
      return '套餐客户';
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
        {{ /^\d+$/.test(customer.id) ? String(Number(customer.id)) : customer.id }}
      </DescriptionsItem>
      <DescriptionsItem label="姓名地址">
        {{ customer.name }}
      </DescriptionsItem>
      <DescriptionsItem label="客户类型">
        <Tag :color="getCustomerTypeColor(customer.customer_type)">
          {{ getCustomerTypeLabel(customer.customer_type) }}
        </Tag>
      </DescriptionsItem>
      <DescriptionsItem v-if="customer.customer_type === 'vip'" label="优惠方案">
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
    <div class="mt-5">
      <Card
        v-if="customer"
        title="送水记录"
        :loading="deliveryLoading"
        :body-style="{ padding: '12px' }"
      >
        <DeliveryGrid class="w-full" @edit-closed="handleEditClosed" />
      </Card>
    </div>
  </Modal>
</template>
