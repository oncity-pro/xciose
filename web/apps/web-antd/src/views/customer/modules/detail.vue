<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, onBeforeUnmount, ref } from 'vue';

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

// 押金配置加载标记（避免重复请求）
const depositConfigLoaded = ref(false);

// 记录已点击"新增"、允许编辑的行ID
const editableRowIds = ref<Set<string | number>>(new Set());

// 防止重复保存的锁
const savingRowIds = ref<Set<string | number>>(new Set());

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
      // 初始行禁止编辑
      if (row.isInitRow) {
        return false;
      }
      if (editableRowIds.value.has(row.id)) {
        return true;
      }
      // 真实数据行：点击日期单元格允许整行编辑
      if (!String(row.id).startsWith('__empty__') && column.field === 'date') {
        editableRowIds.value.clear();
        editableRowIds.value.add(row.id);
        return true;
      }
      // 空行点击送水日期单元格时，允许进入编辑状态
      if (String(row.id).startsWith('__empty__') && column.field === 'date') {
        const data = $table.getData() || [];
        const rowIndex = data.findIndex((r: any) => r.id === row.id);
        const prevRow = data[rowIndex - 1];
        const nextRow = data[rowIndex + 1];
        // 后续空行：只有上一行有数据才允许进入编辑状态
        if (prevRow && prevRow.date) {
          editableRowIds.value.clear();
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
      type: 'seq',
      title: '序号',
      width: 60,
    },
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
      formatter: ({ cellValue, row }: any) => (row.date ? cellValue : ''),
    },
    {
      field: 'storage_amount',
      title: '存水量',
      width: 100,
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
  const data: any[] = [];

  // 序号1：始终是初始行（isInitRow），固定在表格第一行，作为数据参考，不可编辑
  if (customer.value) {
    const openDate = customer.value.open_date || customer.value.openDate || '';
    const storage = customer.value.storage_amount ?? 0;
    data.push({
      id: '__empty__0',
      isInitRow: true,
      customer: '',
      date: openDate,
      water_delivered: 0,
      buckets_returned: 0,
      owed_empty_buckets: 0,
      storage_amount: storage,
      remark: '',
    } as any);
  }

  // 序号2开始：追加真实送水记录（排除初始行）
  const realRecords = deliveryRecords.value.filter((r: any) => !r.isInitRow);
  data.push(...realRecords.map((r) => ({ ...r })));

  // 最后补充普通空行到9行
  while (data.length < 9) {
    const idx = data.length;
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

function calcOwedAndStorage(
  delivered: number,
  returned: number,
  prevRow: any | null,
  isInitRow: boolean,
  customerType: string | undefined,
  totalStorage: number,
): { owed: number; storage: number } {
  let owed: number;
  if (isInitRow) {
    owed = delivered - returned;
  } else if (prevRow) {
    const prevOwed = Number(prevRow.owed_empty_buckets) || 0;
    owed = delivered + prevOwed - returned;
  } else {
    owed = delivered - returned;
  }

  let storage = 0;
  if (customerType === 'vip') {
    if (isInitRow) {
      storage = totalStorage - delivered;
    } else if (prevRow) {
      const prevStorage = Number(prevRow.storage_amount) || 0;
      storage = prevStorage - delivered;
    }
  }

  return { owed, storage };
}

async function handleEditClosed({ row, column, $table }: any) {
  // 只对空行做实时预览计算，真实数据行避免污染原始数据
  if (!String(row.id).startsWith('__empty__')) return;

  const field = column?.field || column?.property;
  const tableData = $table ? $table.getData() : [];
  const rowIndex = tableData.findIndex((r: any) => r.id === row.id);
  const prevRow = rowIndex > 0 ? tableData[rowIndex - 1] : null;
  const isFirstEmptyRow = row.isInitRow;

  // 如果编辑的是送水量或回桶数列，自动计算欠桶数和存水量
  if (field === 'water_delivered' || field === 'buckets_returned') {
    const delivered = Number(row.water_delivered) || 0;
    const returned = Number(row.buckets_returned) || 0;
    const { owed, storage } = calcOwedAndStorage(
      delivered,
      returned,
      prevRow,
      isFirstEmptyRow,
      customer.value?.customer_type,
      customer.value?.storage_amount ?? 0,
    );
    row.owed_empty_buckets = owed;
    row.storage_amount = storage;
  }
}

async function handleSaveRow(row: any) {
  // 防止重复提交
  if (savingRowIds.value.has(row.id)) return;
  savingRowIds.value.add(row.id);

  try {
    // 先关闭当前编辑单元格，确保数据已提交到 row
    const grid = deliveryGridApi.grid;
    const table = (grid as any).$table || grid;
    if (table && typeof table.clearEdit === 'function') {
      table.clearEdit();
    }

    const tableData = table && typeof table.getData === 'function' ? table.getData() : [];
    const rowIndex = tableData.findIndex((r: any) => r.id === row.id);
    const prevRow = rowIndex > 0 ? tableData[rowIndex - 1] : null;
    const isFirstEmptyRow = row.isInitRow;
    const isEmptyRow = String(row.id).startsWith('__empty__');

    if (isEmptyRow) {
      if (!row.date) {
        editableRowIds.value.delete(row.id);
        return;
      }
      const delivered = Number(row.water_delivered) || 0;
      const returned = Number(row.buckets_returned) || 0;
      const { owed, storage } = calcOwedAndStorage(
        delivered,
        returned,
        prevRow,
        isFirstEmptyRow,
        customer.value?.customer_type,
        customer.value?.storage_amount ?? 0,
      );

      try {
        const newRecord = await createDeliveryRecordApi({
          customer: String(customer.value!.id),
          date: row.date,
          water_delivered: delivered,
          buckets_returned: returned,
          owed_empty_buckets: owed,
          storage_amount: storage,
          remark: row.remark,
        });
        deliveryRecords.value.push(newRecord);
        // 使用 displayDeliveryRecords 重新渲染表格，确保 isInitRow 空行始终固定在序号1
        await deliveryGridApi.setGridOptions({ data: displayDeliveryRecords.value });
        editableRowIds.value.delete(row.id);
        await loadDeliveryRecords();
      } catch (error) {
        console.error('保存送水记录失败:', error);
      }
      return;
    }

    // 真实数据行
    if (row.id === undefined || row.id === null || row.id === '') return;

    try {
      await updateDeliveryRecordApi(row.id, {
        date: row.date,
        water_delivered: row.water_delivered,
        buckets_returned: row.buckets_returned,
        owed_empty_buckets: row.owed_empty_buckets,
        storage_amount: row.storage_amount,
        remark: row.remark,
      });
      const record = deliveryRecords.value.find((r) => r.id === row.id);
      if (record) {
        record.date = row.date;
        record.water_delivered = row.water_delivered;
        record.buckets_returned = row.buckets_returned;
        record.owed_empty_buckets = row.owed_empty_buckets;
        record.storage_amount = row.storage_amount;
        record.remark = row.remark;
      }
      editableRowIds.value.delete(row.id);
      await loadDeliveryRecords();
    } catch (error) {
      console.error('更新送水记录失败:', error);
    }
  } finally {
    savingRowIds.value.delete(row.id);
  }
}

function isEditingRow(row: any) {
  return editableRowIds.value.has(row.id);
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
      if (!depositConfigLoaded.value) {
        try {
          const config = await getBucketDepositConfigApi();
          depositPerBucket.value = config.amount_per_bucket;
          depositConfigLoaded.value = true;
        } catch (error) {
          console.error('加载空桶押金配置失败:', error);
        }
      }
      await loadDeliveryRecords();
    }
  },
});

function handleDeleteRow(row: any) {
  // 初始行禁止删除
  if (row.isInitRow) {
    return;
  }

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
        editableRowIds.value = new Set(
          [...editableRowIds.value].filter((id) => !String(id).startsWith('__empty__')),
        );
        await loadDeliveryRecords();
      } catch (error) {
        console.error('删除送水记录失败:', error);
      }
    },
  });
}

onBeforeUnmount(() => {
  editableRowIds.value.clear();
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
        {{ /^\d+$/.test(customer.id) ? String(Number(customer.id)).padStart(3, '0') : customer.id }}
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
          <template #action="{ row }">
            <div class="flex items-center gap-1">
              <!-- 初始行不显示操作按钮 -->
              <template v-if="!row.isInitRow && isEditingRow(row)">
                <Button
                  type="link"
                  size="small"
                  @click="handleSaveRow(row)"
                >
                  保存
                </Button>
                <Button
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
