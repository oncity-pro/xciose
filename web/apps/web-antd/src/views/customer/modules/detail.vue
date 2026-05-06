<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, onBeforeUnmount, ref, watch } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import {
  Button,
  Card,
  DatePicker,
  Descriptions,
  DescriptionsItem,
  Form,
  FormItem,
  InputNumber,
  message,
  Modal,
  Select,
  Tag,
} from 'ant-design-vue';

import dayjs from 'dayjs';

import { getBucketDepositConfigApi } from '#/api/settings';
import { getCustomerDetailApi, updateCustomerApi } from '#/api/customer';
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

const customer = ref<Customer | null>(props.customerData ? { ...props.customerData } : null);

// 监听 props.customerData 变化，确保弹窗打开时数据及时同步
watch(
  () => props.customerData,
  (newVal) => {
    if (newVal) {
      customer.value = { ...newVal };
      // 客户数据就绪后再加载送水记录
      loadDeliveryRecords();
    }
  },
  { immediate: true },
);
const depositPerBucket = ref<number>(30);

// 押金配置加载标记（避免重复请求）
const depositConfigLoaded = ref(false);

// 记录已点击"新增"、允许编辑的行ID
const editableRowIds = ref<Set<string | number>>(new Set());

// 防止重复保存的锁
const savingRowIds = ref<Set<string | number>>(new Set());

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
      formatter: ({ cellValue, row }: any) => {
        if (!row.date) return '';
        if (isRenewalRow(row)) return '0';
        return cellValue;
      },
    },
    {
      field: 'buckets_returned',
      title: '回桶数',
      width: 100,
      editRender: { name: 'input' },
      formatter: ({ cellValue, row }: any) => {
        if (!row.date) return '';
        if (isRenewalRow(row)) return '0';
        return cellValue;
      },
    },
    {
      field: 'owed_empty_buckets',
      title: '欠空桶',
      width: 100,
      formatter: ({ cellValue, row }: any) => {
        if (!row.date) return '';
        if (isRenewalRow(row)) {
          // 获取上一行的欠空桶数据
          const tableData = deliveryGridApi.grid?.getData() || [];
          const rowIndex = tableData.findIndex((r: any) => r.id === row.id);
          const prevRow = rowIndex > 0 ? tableData[rowIndex - 1] : null;
          return prevRow ? (prevRow.owed_empty_buckets ?? 0) : 0;
        }
        return cellValue;
      },
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
    // 根据优惠方案生成初始行备注
    let initRemark = '';
    const vipScheme = customer.value.vip_scheme;
    if (vipScheme) {
      const match = vipScheme.match(/(\d+)[_\-](\d+)/);
      if (match) {
        const buy = Number(match[1]);
        const give = Number(match[2]);
        initRemark = `订${buy}桶赠送${give}桶，共${buy + give}桶`;
      }
    }
    data.push({
      id: '__empty__0',
      isInitRow: true,
      customer: '',
      date: openDate,
      water_delivered: 0,
      buckets_returned: 0,
      owed_empty_buckets: 0,
      storage_amount: storage,
      remark: initRemark,
    } as any);
  }

  // 序号2开始：追加真实送水记录（排除初始行），按创建时间排序确保顺序固定
  const realRecords = deliveryRecords.value.filter((r: any) => !r.isInitRow);
  // 按创建时间升序排序，先创建的在前面
  realRecords.sort((a, b) => {
    const timeA = a.created_at || '';
    const timeB = b.created_at || '';
    return String(timeA).localeCompare(String(timeB));
  });
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
    // 按创建时间升序排序，确保顺序固定（不受送水日期修改影响）
    deliveryRecords.value = data.sort((a, b) => {
      const timeA = a.created_at || '';
      const timeB = b.created_at || '';
      return String(timeA).localeCompare(String(timeB));
    });
    await deliveryGridApi.setGridOptions({
      data: displayDeliveryRecords.value,
    });
  } catch (error) {
    console.error('加载送水记录失败:', error);
  } finally {
    deliveryLoading.value = false;
  }
}

// 刷新客户数据（用于保存/删除送水记录后更新客户信息）
async function refreshCustomerData() {
  if (!customer.value?.id) return;
  try {
    const updatedCustomer = await getCustomerDetailApi(customer.value.id);
    customer.value = updatedCustomer;
  } catch (error) {
    console.error('刷新客户数据失败:', error);
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
  // 只对包含日期的行做实时预览计算（排除初始行）
  if (row.isInitRow || !row.date) return;

  const field = column?.field || column?.property;
  const tableData = $table ? $table.getData() : [];
  const rowIndex = tableData.findIndex((r: any) => r.id === row.id);
  
  // 如果编辑的是送水量或回桶数列，自动计算当前行及后续所有行的欠桶数和存水量
  if (field === 'water_delivered' || field === 'buckets_returned') {
    // 从当前行开始，逐行向下计算
    for (let i = rowIndex; i < tableData.length; i++) {
      const currentRow = tableData[i];
      // 跳过没有日期的行（空行）
      if (!currentRow.date) break;
      
      // 如果是续存行，跳过计算，但需要更新其欠空桶为上一行的值
      if (isRenewalRow(currentRow)) {
        const prevRow = i > 0 ? tableData[i - 1] : null;
        if (prevRow && prevRow.date) {
          currentRow.owed_empty_buckets = prevRow.owed_empty_buckets ?? 0;
          // 续存行的存水量保持原值不变
        }
        continue;
      }
      
      const prevRow = i > 0 ? tableData[i - 1] : null;
      const isFirstDataRow = i === 0 || (prevRow && !prevRow.date);
      
      const delivered = Number(currentRow.water_delivered) || 0;
      const returned = Number(currentRow.buckets_returned) || 0;
      const { owed, storage } = calcOwedAndStorage(
        delivered,
        returned,
        prevRow,
        isFirstDataRow,
        customer.value?.customer_type,
        customer.value?.storage_amount ?? 0,
      );
      
      currentRow.owed_empty_buckets = owed;
      currentRow.storage_amount = storage;
    }
    
    // 刷新表格显示
    if ($table && typeof $table.updateData === 'function') {
      $table.updateData();
    }
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
        // 保持按创建时间排序
        deliveryRecords.value.sort((a, b) => {
          const timeA = a.created_at || '';
          const timeB = b.created_at || '';
          return String(timeA).localeCompare(String(timeB));
        });
        editableRowIds.value.delete(row.id);
        await refreshCustomerData();
        await deliveryGridApi.setGridOptions({
          data: displayDeliveryRecords.value,
        });
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
      await refreshCustomerData();
      await deliveryGridApi.setGridOptions({
        data: displayDeliveryRecords.value,
      });
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

function isRenewalRow(row: any) {
  const remark = String(row.remark || '');
  return remark.includes('续存') || /^订\d+赠\d+桶，共\d+桶/.test(remark);
}

// 把 edit-closed 事件绑定到 gridEvents 上，确保 VxeGrid 能正确接收
deliveryGridApi.setState({
  gridEvents: {
    editClosed: handleEditClosed,
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
        await refreshCustomerData();
        await deliveryGridApi.setGridOptions({
          data: displayDeliveryRecords.value,
        });
      } catch (error) {
        console.error('删除送水记录失败:', error);
      }
    },
  });
}

onBeforeUnmount(() => {
  editableRowIds.value.clear();
});

// ============ 续存弹窗 ============
const renewalModalVisible = ref(false);
const renewalDate = ref(dayjs());
const renewalVipScheme = ref<string | undefined>(undefined);
const renewalStorageAmount = ref<number | undefined>(undefined);
const renewalSubmitting = ref(false);

const VIP_SCHEME_OPTIONS = [
  { label: '10送1', value: '10_1' },
  { label: '20送3', value: '20_3' },
  { label: '30送5', value: '30_5' },
  { label: '50送10', value: '50_10' },
];

// 选择优惠方案后自动计算存水量
watch(
  () => renewalVipScheme.value,
  (scheme) => {
    if (scheme) {
      const match = scheme.match(/(\d+)_(\d+)/);
      if (match) {
        const buy = Number(match[1]);
        const give = Number(match[2]);
        renewalStorageAmount.value = buy + give;
      }
    }
  },
);

function openRenewalModal() {
  if (!customer.value) return;
  renewalDate.value = dayjs();
  renewalVipScheme.value = customer.value.vip_scheme || undefined;
  renewalStorageAmount.value = undefined;
  renewalModalVisible.value = true;
}

async function handleRenewalSubmit() {
  if (!customer.value?.id) return;
  if (!renewalDate.value) {
    message.warning('请选择续存日期');
    return;
  }
  if (!renewalStorageAmount.value || renewalStorageAmount.value <= 0) {
    message.warning('请输入续存存水量');
    return;
  }

  renewalSubmitting.value = true;
  try {
    const addStorage = renewalStorageAmount.value;
    const dateStr = renewalDate.value.format('YYYY-MM-DD');

    // 从已有送水记录获取当前存水量和欠空桶数，若无记录则取客户初始值
    const lastRecord =
      deliveryRecords.value.length > 0
        ? deliveryRecords.value[deliveryRecords.value.length - 1]
        : null;
    const currentStorage = lastRecord
      ? (lastRecord.storage_amount ?? 0)
      : (customer.value.storage_amount ?? 0);
    const currentOwedEmptyBucket = lastRecord
      ? (lastRecord.owed_empty_buckets ?? 0)
      : 0;
    const newStorage = currentStorage + addStorage;

    // 生成续存备注
    let remarkText: string;
    if (renewalVipScheme.value) {
      const match = renewalVipScheme.value.match(/(\d+)_(\d+)/);
      if (match) {
        const buy = Number(match[1]);
        const give = Number(match[2]);
        remarkText = `订${buy}赠${give}桶，共${addStorage}桶，当前存水量为${newStorage}`;
      } else {
        remarkText = `续存${addStorage}桶，当前存水量为${newStorage}`;
      }
    } else {
      remarkText = `续存${addStorage}桶，当前存水量为${newStorage}`;
    }

    // 创建续存记录（送水量、回桶数默认为0，欠空桶继承上一行数据）
    await createDeliveryRecordApi({
      customer: String(customer.value.id),
      date: dateStr,
      water_delivered: 0,
      buckets_returned: 0,
      owed_empty_buckets: currentOwedEmptyBucket,
      storage_amount: newStorage,
      remark: remarkText,
      vip_scheme: renewalVipScheme.value,
    });

    // 若客户类型非VIP，自动升级为VIP
    if (customer.value.customer_type !== 'vip') {
      await updateCustomerApi(String(customer.value.id), {
        customer_type: 'vip',
        owed_empty_bucket: customer.value.owed_empty_bucket ?? 0,
      });
      message.success('续存成功，客户类型已自动升级为套餐客户');
    } else {
      message.success('续存成功');
    }

    renewalModalVisible.value = false;
    await loadDeliveryRecords();
    // 刷新客户数据以更新页面显示
    await refreshCustomerData();
  } catch (error: any) {
    console.error('续存失败:', error);
    const responseData = error?.response?.data ?? {};
    const msg =
      responseData?.message ||
      responseData?.detail ||
      error?.message ||
      '续存失败';
    message.error(msg);
  } finally {
    renewalSubmitting.value = false;
  }
}

const [VbenModal, modalApi] = useVbenModal({
  onOpenChange(isOpen: boolean) {
    if (isOpen) {
      modalApi.setState({ title: '客户详情' });
      if (!depositConfigLoaded.value) {
        getBucketDepositConfigApi()
          .then((config) => {
            depositPerBucket.value = config.amount_per_bucket;
            depositConfigLoaded.value = true;
          })
          .catch((error) => {
            console.error('加载空桶押金配置失败:', error);
          });
      }
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
      <DescriptionsItem label="开户存水量：">
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
        <template #extra>
          <Button type="primary" size="small" @click="openRenewalModal">
            续存
          </Button>
        </template>
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
    <!-- 续存弹窗 -->
    <Modal
      v-model:open="renewalModalVisible"
      title="客户续存"
      :confirm-loading="renewalSubmitting"
      @ok="handleRenewalSubmit"
    >
      <Form layout="vertical">
        <FormItem label="续存日期" required>
          <DatePicker
            v-model:value="renewalDate"
            format="YYYY-MM-DD"
            style="width: 100%"
          />
        </FormItem>
        <FormItem label="优惠方案">
          <Select
            v-model:value="renewalVipScheme"
            placeholder="请选择优惠方案"
            allow-clear
            style="width: 100%"
          >
            <Select.Option
              v-for="opt in VIP_SCHEME_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </Select.Option>
          </Select>
        </FormItem>
        <FormItem label="存水量" required>
          <InputNumber
            v-model:value="renewalStorageAmount"
            :min="1"
            placeholder="请输入续存存水量"
            style="width: 100%"
          />
        </FormItem>
      </Form>
    </Modal>
  </VbenModal>
</template>

<style>
.detail-modal-no-scroll .ant-modal-body {
  max-height: none !important;
  overflow: visible !important;
  padding-bottom: 16px;
}
</style>
