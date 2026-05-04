<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, nextTick, ref, watch } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { Button, Card, Descriptions, DescriptionsItem, Modal, Tag } from 'ant-design-vue';

import { getBucketDepositConfigApi } from '#/api/settings';
import {
  createDeliveryRecordApi,
  deleteDeliveryRecordApi,
  getDeliveryRecordListApi,
  updateDeliveryRecordApi,
} from '#/api/delivery-record';
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

// 控制是否自动填充第一行空行的默认值（只在初始加载时填充，保存后不再填充）
const shouldFillEmptyRowDefaults = ref(true);

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
  stripe: true,
  keepSource: true,
  editConfig: {
    trigger: 'click',
    mode: 'cell',
    showStatus: true,
    beforeEditMethod: ({ row, column, $table }: any) => {
      if (editableRowIds.value.has(row.id)) {
        return true;
      }
      // 空行点击送水日期单元格时，只有上一行有数据才允许进入编辑状态
      if (String(row.id).startsWith('__empty__') && column.field === 'date') {
        const data = $table.getData() || [];
        const rowIndex = data.findIndex((r: any) => r.id === row.id);
        const prevRow = data[rowIndex - 1];
        const nextRow = data[rowIndex + 1];
        if (prevRow && prevRow.date) {
          editableRowIds.value.add(row.id);
          // 只有上下行并非同时有数据时，才默认填充当天日期（使用本地时间避免UTC偏移）
          if (!row.date && !(nextRow && nextRow.date)) {
            const today = new Date();
            const y = today.getFullYear();
            const m = String(today.getMonth() + 1).padStart(2, '0');
            const d = String(today.getDate()).padStart(2, '0');
            row.date = `${y}-${m}-${d}`;
          }
          return true;
        }
      }
      return false;
    },
  },
  columns: [
    {
      field: 'date',
      title: '送水日期',
      width: 120,
      editRender: { name: 'input', attrs: { type: 'date' } },
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
      formatter: ({ cellValue, row }: any) => (row.date ? cellValue : ''),
    },
    {
      field: 'storage_amount',
      title: '存水量',
      width: 100,
      editRender: { name: 'input' },
      formatter: ({ cellValue, row }: any) => (row.date ? cellValue : ''),
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
      width: 120,
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
    const idx = data.length;
    const prevRow = data[idx - 1];
    if (idx === deliveryRecords.value.length && customer.value && shouldFillEmptyRowDefaults.value) {
      // 第一个空行：基于客户信息填充默认值（只在初始加载时）
      const openDate = customer.value.open_date || customer.value.openDate || '';
      const owedBuckets = customer.value.owed_empty_bucket ?? 0;
      const storage = customer.value.storage_amount ?? 0;
      const isVip = customer.value.customer_type === 'vip';
      data.push({
        id: `__empty__${idx}`,
        customer: '',
        date: openDate,
        water_delivered: owedBuckets,
        buckets_returned: 0,
        owed_empty_buckets: 0,
        storage_amount: isVip ? storage - owedBuckets : 0,
        remark: '',
      } as any);
    } else if (prevRow) {
      // 第二个及后续空行：欠空桶基于上一行计算，存水量不参与计算
      const prevWater = Number(prevRow.water_delivered) || 0;
      const prevReturned = Number(prevRow.buckets_returned) || 0;
      data.push({
        id: `__empty__${idx}`,
        customer: '',
        date: '',
        water_delivered: '',
        buckets_returned: '',
        owed_empty_buckets: prevWater - prevReturned,
        storage_amount: '',
        remark: '',
      } as any);
    } else {
      data.push({
        id: `__empty__${idx}`,
        customer: '',
        date: '',
        water_delivered: '',
        buckets_returned: '',
        owed_empty_buckets: '',
        storage_amount: '',
        remark: '',
      } as any);
    }
  }
  return data;
});

async function loadDeliveryRecords() {
  if (!customer.value?.id) return;
  editableRowIds.value.clear();
  shouldFillEmptyRowDefaults.value = true;
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

const [VbenModal, modalApi] = useVbenModal({
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
  const isEmptyRow = String(row.id).startsWith('__empty__');

  try {
    if (isEmptyRow) {
      // 空行：创建新记录
      const newRecord = await createDeliveryRecordApi({
        customer: String(customer.value!.id),
        date: row.date,
        water_delivered: Number(row.water_delivered) || 0,
        buckets_returned: Number(row.buckets_returned) || 0,
        owed_empty_buckets: Number(row.owed_empty_buckets) || 0,
        storage_amount: Number(row.storage_amount) || 0,
        remark: row.remark,
      });
      // 添加到源数据头部，表格会自动刷新
      deliveryRecords.value.unshift(newRecord);
      // 保存后不再自动填充空行默认值
      shouldFillEmptyRowDefaults.value = false;
      await deliveryGridApi.setGridOptions({
        data: displayDeliveryRecords.value,
      });
      // 更新可编辑状态：移除旧空行ID，添加新记录ID
      editableRowIds.value.delete(row.id);
      editableRowIds.value.add(newRecord.id);
    } else {
      // 真实数据行：更新记录
      await updateDeliveryRecordApi(row.id, {
        date: row.date,
        water_delivered: row.water_delivered,
        buckets_returned: row.buckets_returned,
        owed_empty_buckets: row.owed_empty_buckets,
        storage_amount: row.storage_amount,
        remark: row.remark,
      });
      editableRowIds.value.delete(row.id);
    }
  } catch (error) {
    console.error('保存送水记录失败:', error);
  }
}

function handleDeleteRow(row: any) {
  // 空行清除数据并移除编辑状态，无需调用后端
  if (String(row.id).startsWith('__empty__')) {
    editableRowIds.value.delete(row.id);
    row.date = '';
    row.water_delivered = '';
    row.buckets_returned = '';
    row.owed_empty_buckets = '';
    row.storage_amount = '';
    row.remark = '';
    return;
  }

  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这条送水记录吗？删除后将同步回滚客户的累计数据。',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await deleteDeliveryRecordApi(row.id);
        // 从本地数据中移除
        deliveryRecords.value = deliveryRecords.value.filter((r) => r.id !== row.id);
        editableRowIds.value.delete(row.id);
        // 清理所有空行的编辑状态（避免空行id重新计算后残留）
        for (const id of [...editableRowIds.value]) {
          if (String(id).startsWith('__empty__')) {
            editableRowIds.value.delete(id);
          }
        }
        await deliveryGridApi.setGridOptions({
          data: displayDeliveryRecords.value,
        });
      } catch (error) {
        console.error('删除送水记录失败:', error);
      }
    },
  });
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
  <VbenModal :footer="false" class="w-[1080px] detail-modal-no-scroll">
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
      <DescriptionsItem label="客户编号：">
        {{ /^\d+$/.test(customer.id) ? String(Number(customer.id)) : customer.id }}
      </DescriptionsItem>
      <DescriptionsItem label="姓名地址：">
        {{ customer.name }}
      </DescriptionsItem>
      <DescriptionsItem label="客户类型：">
        <Tag :color="getCustomerTypeColor(customer.customer_type)">
          {{ getCustomerTypeLabel(customer.customer_type) }}
        </Tag>
      </DescriptionsItem>
      <DescriptionsItem v-if="customer.customer_type === 'vip'" label="优惠方案：">
        {{ customer.vip_scheme ? customer.vip_scheme.replace('_', '送') : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="品牌：">
        {{ brandName || customer.brand_name || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="联系电话：">
        {{ customer.phone || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="开户日期：">
        {{ customer.openDate || customer.open_date || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="最后送水日期：">
        {{ customer.lastDeliveryDate || customer.last_delivery_date || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="存水量：">
        {{ customer.storage_amount != null ? `${customer.storage_amount} 桶` : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="总用水量：">
        {{ (customer.total_water_usage ?? customer.totalWaterUsage) != null ? `${customer.total_water_usage ?? customer.totalWaterUsage} 桶` : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="押桶数：">
        {{ customer.owed_empty_bucket != null ? `押${customer.owed_empty_bucket}个桶共${emptyBucketDeposit}元` : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="客户来源：">
        {{ customer.source === 'wechat' ? '微信' : customer.source === 'internet' ? '互联网' : customer.source === 'phone' ? '电话' : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="楼层：">
        {{ customer.floor_type === 'default' ? '默认' : customer.floor_type === 'elevator' ? '电梯' : customer.floor_type === 'stair' ? '步梯' : customer.floor_type === 'residential' ? '住宅' : '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="备注：">
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
          <template #action="{ row, $rowIndex }">
            <div class="flex items-center gap-1">
              <template v-if="!String(row.id).startsWith('__empty__')">
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
                  编辑
                </Button>
                <Button
                  v-if="$rowIndex !== 0"
                  type="link"
                  danger
                  size="small"
                  @click="handleDeleteRow(row)"
                >
                  删除
                </Button>
              </template>
              <template v-else-if="$rowIndex === deliveryRecords.length">
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
                  编辑
                </Button>
              </template>
              <template v-else>
                <Button
                  v-if="editableRowIds.has(row.id)"
                  type="link"
                  size="small"
                  @click="handleSaveRow(row)"
                >
                  保存
                </Button>
                <Button
                  v-if="!editableRowIds.has(row.id) && row.date"
                  type="link"
                  size="small"
                  @click="handleAddRow(row)"
                >
                  编辑
                </Button>
                <Button
                  v-if="editableRowIds.has(row.id) || row.date"
                  type="link"
                  danger
                  size="small"
                  @click="handleDeleteRow(row)"
                >
                  删除
                </Button>
              </template>
            </div>
          </template>
        </DeliveryGrid>
      </Card>
    </div>
  </VbenModal>
</template>

<style>
.detail-modal-no-scroll .ant-modal-body {
  max-height: none !important;
  overflow: visible !important;
  padding-bottom: 16px;
}
</style>
