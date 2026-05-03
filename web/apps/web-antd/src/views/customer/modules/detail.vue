<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, nextTick, ref, watch } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { Button, Card, Descriptions, DescriptionsItem, Tag } from 'ant-design-vue';

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

// 记录已点击"新增"、允许编辑的行ID
const editableRowIds = ref<Set<string | number>>(new Set());

// 送水记录
const deliveryRecords = ref<DeliveryRecord[]>([]);
const deliveryLoading = ref(false);

const emptyBucketDeposit = computed(() => {
  const owed = customer.value?.owed_empty_bucket ?? 0;
  return Number((owed * depositPerBucket.value).toFixed(2));
});

const deliveryGridOptions: VxeTableGridOptions<any> = {
  cellConfig: {
    height: 32,
  },
  headerRowStyle: {
    height: '32px',
  },
  keepSource: true,
  editConfig: {
    trigger: 'click',
    mode: 'cell',
    showStatus: true,
    beforeEditMethod: ({ row }: any) => {
      return editableRowIds.value.has(row.id);
    },
  },
  columns: [
    {
      field: 'date',
      title: '送水日期',
      width: 120,
      editRender: { name: 'date' },
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
    {
      field: 'action',
      title: '操作',
      width: 80,
      fixed: 'right',
      slots: { default: 'action' },
    },
  ],
  pagerConfig: {},
  showOverflow: true,
  data: [],
};

const [DeliveryGrid, deliveryGridApi] = useVbenVxeGrid({
  gridOptions: deliveryGridOptions,
});

const displayDeliveryRecords = computed(() => {
  const data = deliveryRecords.value.map((r) => ({ ...r }));
  while (data.length < 9) {
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
  editableRowIds.value.clear();
  deliveryLoading.value = true;
  try {
    const data = await getDeliveryRecordListApi(customer.value.id);
    deliveryRecords.value = data;
    await deliveryGridApi.setGridOptions({
      data: displayDeliveryRecords.value,
    });
  } catch (error) {
    console.error('加载送水记录失败:', error);
  } finally {
    deliveryLoading.value = false;
  }
}

async function handleEditClosed({ row, column }: any) {
  const field = column?.field || column?.property;
  console.log('edit-closed triggered', { field, rowId: row?.id, row, column });

  // 先把当前编辑行的数据同步回源数据，防止后续刷新覆盖用户输入
  const record = deliveryRecords.value.find((r) => r.id === row.id);
  if (record) {
    record.date = row.date;
    record.water_delivered = row.water_delivered;
    record.buckets_returned = row.buckets_returned;
    record.owed_empty_buckets = row.owed_empty_buckets;
    record.storage_amount = row.storage_amount;
    record.remark = row.remark;
  }

  // 如果编辑的是送水量列，自动根据客户总存水量扣减
  if (field === 'water_delivered') {
    const delivered = Number(row.water_delivered) || 0;
    const totalStorage = customer.value?.storage_amount ?? 0;
    const newStorage = totalStorage - delivered;
    row.storage_amount = newStorage;
    if (record) {
      record.storage_amount = newStorage;
    }
    console.log('自动计算存水量:', { delivered, totalStorage, result: newStorage });
  }

  // 空行不刷新表格（避免覆盖用户输入），真实数据行刷新以确保显示正确
  if (!String(row.id).startsWith('__empty__')) {
    deliveryGridApi.setGridOptions({ data: displayDeliveryRecords.value });
  }

  // 空行不保存到后端
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

// 把 edit-closed 事件绑定到 gridEvents 上，确保 VxeGrid 能正确接收
deliveryGridApi.setState({
  gridEvents: {
    editClosed: handleEditClosed,
  },
});

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

function handleAddRow(row: any) {
  editableRowIds.value.add(row.id);
  // 尝试自动进入第一列的编辑状态
  nextTick(() => {
    const grid = deliveryGridApi.grid;
    if (grid) {
      const table = (grid as any).$table || grid;
      table.setEditCell?.(row, 'date');
    }
  });
}

async function handleSaveRow(row: any) {
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
    editableRowIds.value.delete(row.id);
  } catch (error) {
    console.error('保存送水记录失败:', error);
  }
}

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
  <Modal :footer="false" class="w-[1080px] detail-modal-no-scroll">
    <div v-if="customer" class="mb-2 text-center font-semibold text-base">
      客户信息
    </div>
    <Descriptions
      v-if="customer"
      :column="3"
      bordered
      :label-style="{ width: '80px', whiteSpace: 'nowrap', padding: '4px 8px' }"
      :content-style="{ whiteSpace: 'nowrap', padding: '4px 8px' }"
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
    <div class="mt-3">
      <Card
        v-if="customer"
        title="送水记录"
        :loading="deliveryLoading"
        :head-style="{ padding: '6px 12px', minHeight: 'auto', textAlign: 'center' }"
        :body-style="{ padding: '8px' }"
      >
        <DeliveryGrid class="w-full">
          <template #action="{ row }">
            <Button
              v-if="editableRowIds.has(row.id)"
              type="link"
              size="small"
              @click="handleSaveRow(row)"
            >
              保存
            </Button>
            <Button
              v-else
              type="link"
              size="small"
              @click="handleAddRow(row)"
            >
              新增
            </Button>
          </template>
        </DeliveryGrid>
      </Card>
    </div>
  </Modal>
</template>

<style>
.detail-modal-no-scroll .ant-modal-body {
  max-height: none !important;
  overflow: visible !important;
  padding-bottom: 16px;
}
</style>
