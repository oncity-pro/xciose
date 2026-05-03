<script lang="ts" setup>
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { Customer, CustomerStats } from '#/api/customer';
import type { WaterBrand } from '#/api/water-brand';

import { computed, onMounted, ref, watch, nextTick } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
import { Plus } from '@vben/icons';
import { Award, Ban, Clock, Crown, Eye, Lock, Package, Pencil, Search, User, UserPlus, Users, UserX } from 'lucide-vue-next';

import { Button, Input, message, Modal, Tooltip } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getCustomerListApi,
  getCustomerStatsApi,
  updateCustomerApi,
} from '#/api/customer';
import { 
  getWaterBrandListApi
} from '#/api/water-brand';

import Detail from './modules/detail.vue';
import Form from './modules/form.vue';

// 品牌列表（用于显示品牌名称）
const brandMap = ref<Map<number, string>>(new Map());

// 加载状态
const loading = ref(false);

// 搜索关键词
const searchKeyword = ref('');

// 统计数据（从后端全局统计接口获取）
const statsData = ref<CustomerStats>({
  total: 0,
  vipCount: 0,
  normalCount: 0,
  pickupCount: 0,
  newThisMonth: 0,
  lastMonthNew: 0,
  closedThisMonth: 0,
  lastMonthClosed: 0,
});

// 统计数据（直接展示后端返回的全局统计）
const stats = computed(() => {
  const {
    total, vipCount, normalCount, pickupCount,
    newThisMonth, lastMonthNew, closedThisMonth, lastMonthClosed,
  } = statsData.value;

  const totalChange = lastMonthNew - lastMonthClosed;
  const vipChange = newThisMonth - lastMonthNew; // 简化：用新增环比
  const normalChange = newThisMonth - lastMonthNew;
  const pickupChange = newThisMonth - lastMonthNew;
  const newChange = newThisMonth - lastMonthNew;
  const closedChange = closedThisMonth - lastMonthClosed;

  return {
    total, newThisMonth, closedThisMonth, vipCount, normalCount, pickupCount,
    totalChange, vipChange, normalChange, pickupChange, newChange, closedChange,
  };
});

// 加载统计数据
async function loadStats() {
  try {
    const data = await getCustomerStatsApi();
    statsData.value = data;
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
}

// 实时搜索
watch(searchKeyword, () => {
  gridApi.query();
});

// 加载品牌数据
async function loadBrands() {
  try {
    const brands = await getWaterBrandListApi();
    const map = new Map<number, string>();
    brands.forEach((brand: WaterBrand) => {
      map.set(brand.id, brand.name);
    });
    brandMap.value = map;
  } catch (error) {
    console.error('加载品牌数据失败:', error);
    message.error('加载品牌数据失败');
  }
}


const [FormModal, formModalApi] = useVbenModal({
  connectedComponent: Form,
  destroyOnClose: true,
});

// 详情弹窗
const [DetailModal, detailModalApi] = useVbenModal({
  connectedComponent: Detail,
  destroyOnClose: true,
});

// 当前编辑的客户数据（用于替代 modalApi.setData/getData）
const currentCustomer = ref<Customer | null>(null);

// 当前查看详情的客户数据
const currentDetailCustomer = ref<Customer | null>(null);
const detailBrandName = ref<string>('');

// 新增客户
function onCreate() {
  currentCustomer.value = null;
  formModalApi.open();
}

// 查看详情
function onViewDetail(row: Customer) {
  currentDetailCustomer.value = { ...row };
  detailBrandName.value = row.brand ? (brandMap.value.get(row.brand) ?? '') : '';
  detailModalApi.open();
}

// 编辑客户
async function onEdit(row: Customer) {
  // 使用 toRaw 避免响应式代理对象问题
  const { toRaw } = await import('vue');
  currentCustomer.value = toRaw({...row}); // 使用展开运算符复制对象
  console.warn('onEdit - 设置 currentCustomer:', currentCustomer.value);
  console.warn('onEdit - currentCustomer.id:', currentCustomer.value?.id);
  console.warn('onEdit - 准备打开弹窗');
  
  // 使用 nextTick 替代 setTimeout
  await nextTick();
  formModalApi.open();
}

// 点击注销按钮，弹出确认对话框
function handleCloseClick(row: Customer) {
  Modal.confirm({
    title: '确定要注销这个客户吗？',
    content: '注销后客户状态将变为"已注销"，可在后端恢复。',
    okText: '确定注销',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => onCloseCustomer(row),
  });
}

// 注销客户（将客户类型改为已注销）
async function onCloseCustomer(row: Customer) {
  // 验证客户 ID 是否存在
  if (!row.id) {
    message.error('客户编号不存在，无法注销');
    console.error('注销失败：客户数据缺少 ID', row);
    return;
  }

  try {
    console.warn(`准备注销客户，ID: ${row.id}`);
    await updateCustomerApi(row.id, { customer_type: 'closed' } as any);
    message.success('注销成功');
    refreshGrid();
  } catch (error: any) {
    console.error('注销失败:', error);

    // 检查错误响应
    let errorMessage = '注销失败';
    if (error.response) {
      // 服务器响应了错误状态码
      if (error.response.status === 404) {
        errorMessage = '客户不存在，无法注销';
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    message.error(errorMessage);
  }
}

// 刷新表格和统计数据
function refreshGrid() {
  gridApi.query();
  loadStats();
}

// 存水量相关计算
function getStorageRemaining(row: Customer): number {
  const total = row.storage_amount || 0;
  const used = row.total_water_usage || 0;
  return Math.max(0, total - used);
}

function getStoragePercent(row: Customer): number {
  const total = row.storage_amount || 0;
  if (total <= 0) return 0;
  const remaining = getStorageRemaining(row);
  return Math.round((remaining / total) * 100);
}

function getStorageBarColor(row: Customer): string {
  const percent = getStoragePercent(row);
  if (percent === 0) return 'bg-gray-400';
  if (percent <= 20) return 'bg-red-500';
  if (percent <= 50) return 'bg-orange-500';
  return 'bg-blue-500';
}

// 表格配置
const gridOptions: VxeTableGridOptions<Customer> = {
  rowConfig: {
    keyField: 'id',  // 使用正确的属性来指定行的唯一标识
  },
  stripe: true,  // 启用斑马纹
  align: 'center',  // 所有列默认居中
  columns: [
    { title: '序号', type: 'seq', width: 60, visible: false },
    {
      field: 'id',
      title: '客户编号',
      width: 100,
      formatter: ({ cellValue }: { cellValue: string }) => {
        // 纯数字编号去掉前导零显示
        if (/^\d+$/.test(cellValue)) {
          return String(Number(cellValue));
        }
        return cellValue;
      },
    },
    { 
      field: 'name', 
      title: '姓名地址', 
      minWidth: 200,
    },
    {
      field: 'customer_type_display',
      title: '客户类型',
      width: 100,
      slots: { default: 'customerType' },
    },
    { 
      field: 'brandId', 
      title: '品牌', 
      width: 120,
      slots: { default: 'brand' },
    },
    { field: 'openDate', title: '开户日期', width: 120 },
    { field: 'lastDeliveryDate', title: '送水日期', width: 130 },
    { field: 'storage_amount', title: '存水量', width: 150, sortable: true, align: 'center', slots: { default: 'storage', header: 'sortHeader' } },
    { field: 'owed_empty_bucket', title: '欠空桶', width: 110, sortable: true, align: 'center', slots: { header: 'sortHeader' } },
    { field: 'bucket_deposit_display', title: '桶押金', width: 150, align: 'center' },
    { field: 'total_water_usage', title: '总用水量', width: 110, sortable: true, align: 'center', slots: { header: 'sortHeader' } },
    { field: 'total_consumption', title: '消费总额', width: 120, sortable: true, align: 'center', slots: { header: 'sortHeader' }, formatter: ({ cellValue }: { cellValue: number }) => cellValue ? `¥${Number(cellValue).toFixed(2)}` : '¥0.00' },
    {
      title: '操作',
      width: 120,
      fixed: 'right',
      slots: { default: 'action' },
    },
  ],
  height: '100%',
  keepSource: true,
  pagerConfig: {
    enabled: true,
    pageSize: 12,  // ✅ 修改为每页默认显示12条
    pageSizes: [12, 13, 14, 15],  // ✅ 更新分页选项为12/13/14/15
  },
  sortConfig: {
    // 点击整个表头单元格即可排序（因默认排序图标已被隐藏）
    trigger: 'cell',
    orders: ['asc', 'desc', null],
  },
  proxyConfig: {
    sort: true,
    ajax: {
      query: async ({ page, sort }) => {
        
        loading.value = true;
        
        try {
          // 加载品牌数据（如果还没有加载）
          if (brandMap.value.size === 0) {
            await loadBrands();
          }
          
          // 调用真实 API 获取数据
          const params: any = {};
          if (searchKeyword.value) {
            params.keyword = searchKeyword.value;
          }
          
          let data = await getCustomerListApi(params);
          
          // 调试：打印第一条数据的结构
          if (data && data.length > 0) {
            console.warn('客户数据结构示例:', data[0]);
            const firstItem = data[0];
            if (firstItem) {
              console.warn('客户数据所有键名:', Object.keys(firstItem));
            }
          }
          
          // 如果有排序参数，对所有数据进行排序
          if (sort && sort.field && sort.order) {
            const order = sort.order;
            const field = sort.field as keyof Customer;
            data = [...data].sort((a, b) => {
              const va = a[field];
              const vb = b[field];
              // 处理 null/undefined
              if (va === null || va === undefined) return order === 'asc' ? -1 : 1;
              if (vb === null || vb === undefined) return order === 'asc' ? 1 : -1;
              // 数字排序
              if (typeof va === 'number' && typeof vb === 'number') {
                return order === 'asc' ? va - vb : vb - va;
              }
              // 字符串排序
              const sa = String(va);
              const sb = String(vb);
              return order === 'asc'
                ? sa.localeCompare(sb, 'zh-CN')
                : sb.localeCompare(sa, 'zh-CN');
            });
          }
          
          // 模拟分页（后端暂未支持分页，前端处理）
          const total = data.length;
          const start = (page.currentPage - 1) * page.pageSize;
          const end = start + page.pageSize;
          const items = data.slice(start, end);
          
          return {
            items,
            total,
          };
        } catch (error) {
          console.error('获取客户列表失败:', error);
          message.error('获取客户列表失败');
          return {
            items: [],
            total: 0,
          };
        } finally {
          loading.value = false;
        }
      },
    },
  },
  toolbarConfig: {
    // 隐藏默认搜索按钮（搜索框已自定义放到 toolbar-tools 中）
    search: false,
    refresh: true,
    custom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

// 组件挂载时加载品牌数据和统计数据
onMounted(() => {
  loadBrands();
  loadStats();
});
</script>

<template>
  <Page auto-content-height>
    <FormModal :customer-data="currentCustomer" @success="refreshGrid" />
    <DetailModal :customer-data="currentDetailCustomer" :brand-name="detailBrandName" />

    <div class="flex flex-col gap-4 h-full min-h-0">
        <!-- 统计卡片 -->
        <div class="flex shrink-0 gap-4">
          <div class="flex-1 rounded-lg bg-blue-50 p-4 dark:bg-blue-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-blue-300">客户总数</div>
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ stats.total }}</div>
              <div class="text-xs mt-1" :class="stats.totalChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.totalChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.totalChange) }}
              </div>
            </div>
            <Users class="size-10 text-blue-500 dark:text-blue-400" />
          </div>
          <div class="flex-1 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-yellow-300">套餐客户</div>
              <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ stats.vipCount }}</div>
              <div class="text-xs mt-1" :class="stats.vipChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.vipChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.vipChange) }}
              </div>
            </div>
            <Award class="size-10 text-yellow-500 dark:text-yellow-400" />
          </div>
          <div class="flex-1 rounded-lg bg-green-50 p-4 dark:bg-green-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-green-300">普通客户</div>
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ stats.normalCount }}</div>
              <div class="text-xs mt-1" :class="stats.normalChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.normalChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.normalChange) }}
              </div>
            </div>
            <User class="size-10 text-green-500 dark:text-green-400" />
          </div>
          <div class="flex-1 rounded-lg bg-cyan-50 p-4 dark:bg-cyan-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-cyan-300">自提客户</div>
              <div class="text-2xl font-bold text-cyan-600 dark:text-cyan-400">{{ stats.pickupCount }}</div>
              <div class="text-xs mt-1" :class="stats.pickupChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.pickupChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.pickupChange) }}
              </div>
            </div>
            <Package class="size-10 text-cyan-500 dark:text-cyan-400" />
          </div>
          <div class="flex-1 rounded-lg bg-emerald-50 p-4 dark:bg-emerald-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-emerald-300">本月新增</div>
              <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ stats.newThisMonth }}</div>
              <div class="text-xs mt-1" :class="stats.newChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.newChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.newChange) }}
              </div>
            </div>
            <UserPlus class="size-10 text-emerald-500 dark:text-emerald-400" />
          </div>
          <div class="flex-1 rounded-lg bg-red-50 p-4 dark:bg-red-950/30 flex items-center justify-between">
            <div>
              <div class="text-sm text-gray-500 dark:text-red-300">本月注销</div>
              <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ stats.closedThisMonth }}</div>
              <div class="text-xs mt-1" :class="stats.closedChange >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ stats.closedChange >= 0 ? '↑' : '↓' }} 较上月 {{ Math.abs(stats.closedChange) }}
              </div>
            </div>
            <UserX class="size-10 text-red-500 dark:text-red-400" />
          </div>
        </div>

        <!-- 客户列表 -->
        <div class="min-h-0 flex-1">
          <Grid :loading="loading" class="h-full">
            <template #toolbar-actions>
              <Input
                v-model:value="searchKeyword"
                allow-clear
                placeholder="输入编号或姓名地址搜索"
                style="width: 240px"
              >
                <template #prefix>
                  <Search class="size-4 text-gray-400" />
                </template>
              </Input>
            </template>
            <template #toolbar-tools>
              <Button type="primary" @click="onCreate">
                <Plus class="size-5" />
                新增客户
              </Button>
            </template>

            <!-- 自定义客户类型列的渲染 -->
            <template #customerType="{ row }">
              <span class="flex items-center justify-center">
                <Tooltip v-if="row.customer_type === 'closed'" :title="row.customer_type_display">
                  <Lock class="size-4 text-red-500" />
                </Tooltip>
                <Tooltip v-else-if="row.customer_type === 'vip'" :title="row.customer_type_display">
                  <Crown class="size-4 text-yellow-500" />
                </Tooltip>
                <Tooltip v-else-if="row.customer_type === 'normal'" :title="row.customer_type_display">
                  <User class="size-4 text-blue-500" />
                </Tooltip>
                <Tooltip v-else-if="row.customer_type === 'pickup'" :title="row.customer_type_display">
                  <Package class="size-4 text-cyan-500" />
                </Tooltip>
                <Tooltip v-else-if="row.customer_type === 'slow_pay'" :title="row.customer_type_display">
                  <Clock class="size-4 text-orange-500" />
                </Tooltip>
                <Tooltip v-else-if="row.customer_type === 'blacklist'" :title="row.customer_type_display">
                  <Ban class="size-4 text-red-600" />
                </Tooltip>
              </span>
            </template>

            <!-- 自定义品牌列的渲染 -->
            <template #brand="{ row }">
              {{ row.brand ? brandMap.get(row.brand) : '-' }}
            </template>

            <!-- 排序表头 -->
            <template #sortHeader="{ column, $table }">
              <span
                class="cursor-pointer select-none"
                @click="$table && $table.sort(column.field, column.order === 'asc' ? 'desc' : column.order === 'desc' ? null : 'asc')"
              >
                {{ column.title }}<span class="sort-arrows">↓↑</span>
              </span>
            </template>

            <!-- 自定义存水量列的渲染 -->
            <template #storage="{ row }">
              <div class="flex items-center justify-center gap-1.5">
                <span class="text-xs whitespace-nowrap">{{ getStorageRemaining(row) }}</span>
                <div class="w-12 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all"
                    :class="getStorageBarColor(row)"
                    :style="{ width: getStoragePercent(row) + '%' }"
                  />
                </div>
              </div>
            </template>

            <!-- 操作列 -->
            <template #action="{ row }">
              <div class="flex items-center justify-center gap-1">
                <Button type="link" size="small" title="详情" @click="onViewDetail(row)">
                  <Eye class="size-4" />
                </Button>
                <Button type="link" size="small" title="编辑" @click="onEdit(row)">
                  <Pencil class="size-4" />
                </Button>
                <Button type="link" size="small" danger title="注销" @click="handleCloseClick(row)">
                  <UserX class="size-4" />
                </Button>
              </div>
            </template>
          </Grid>
        </div>
      </div>
  </Page>
</template>

<style>
/* 隐藏默认排序图标 */
.vxe-table .vxe-sort--asc-btn,
.vxe-table .vxe-sort--desc-btn {
  display: none !important;
}

/* 排序箭头文字样式（继承表头字号） */
.sort-arrows {
  margin-left: 2px;
  color: #999;
  letter-spacing: -1px;
}
</style>
