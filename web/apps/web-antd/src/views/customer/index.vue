<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { Customer } from '#/api/customer';
import type { WaterBrand } from '#/api/water-brand';

import { computed, onMounted, ref, watch, nextTick } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import { Plus } from '@vben/icons';
import { Award, Eye, MoreHorizontal, Package, Pencil, Search, Trash2, User, UserPlus, Users, UserX } from 'lucide-vue-next';

import { Button, Dropdown, Input, Menu, message, Modal } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { 
  deleteCustomerApi,
  getCustomerListApi 
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

// 全部客户数据（用于统计）
const allCustomers = ref<Customer[]>([]);

// 统计数据
const stats = computed(() => {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();

  const isCurrentMonth = (dateStr?: string | null) => {
    if (!dateStr) return false;
    const d = new Date(dateStr);
    return d.getFullYear() === currentYear && d.getMonth() === currentMonth;
  };

  const isLastMonth = (dateStr?: string | null) => {
    if (!dateStr) return false;
    const d = new Date(dateStr);
    if (currentMonth === 0) {
      return d.getFullYear() === currentYear - 1 && d.getMonth() === 11;
    }
    return d.getFullYear() === currentYear && d.getMonth() === currentMonth - 1;
  };

  const total = allCustomers.value.length;
  const newThisMonth = allCustomers.value.filter((c) =>
    isCurrentMonth(c.created_at),
  ).length;
  const closedThisMonth = allCustomers.value.filter((c) =>
    isCurrentMonth(c.close_date),
  ).length;

  const vipCount = allCustomers.value.filter(
    (c) => c.customer_type === 'vip',
  ).length;
  const normalCount = allCustomers.value.filter(
    (c) => c.customer_type === 'normal',
  ).length;
  const pickupCount = allCustomers.value.filter(
    (c) => c.customer_type === 'pickup',
  ).length;

  // 上月数据（用于环比）
  const lastMonthNew = allCustomers.value.filter((c) =>
    isLastMonth(c.created_at),
  ).length;
  const lastMonthClosed = allCustomers.value.filter((c) =>
    isLastMonth(c.close_date),
  ).length;

  const lastMonthVipNew = allCustomers.value.filter(
    (c) => isLastMonth(c.created_at) && c.customer_type === 'vip',
  ).length;
  const lastMonthVipClosed = allCustomers.value.filter(
    (c) => isLastMonth(c.close_date) && c.customer_type === 'vip',
  ).length;

  const lastMonthNormalNew = allCustomers.value.filter(
    (c) => isLastMonth(c.created_at) && c.customer_type === 'normal',
  ).length;
  const lastMonthNormalClosed = allCustomers.value.filter(
    (c) => isLastMonth(c.close_date) && c.customer_type === 'normal',
  ).length;

  const lastMonthPickupNew = allCustomers.value.filter(
    (c) => isLastMonth(c.created_at) && c.customer_type === 'pickup',
  ).length;
  const lastMonthPickupClosed = allCustomers.value.filter(
    (c) => isLastMonth(c.close_date) && c.customer_type === 'pickup',
  ).length;

  const totalChange = lastMonthNew - lastMonthClosed;
  const vipChange = lastMonthVipNew - lastMonthVipClosed;
  const normalChange = lastMonthNormalNew - lastMonthNormalClosed;
  const pickupChange = lastMonthPickupNew - lastMonthPickupClosed;
  const newChange = newThisMonth - lastMonthNew;
  const closedChange = closedThisMonth - lastMonthClosed;

  return {
    total, newThisMonth, closedThisMonth, vipCount, normalCount, pickupCount,
    totalChange, vipChange, normalChange, pickupChange, newChange, closedChange,
  };
});

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

// 品牌饼图
const brandChartRef = ref<EchartsUIType>();
const { renderEcharts: renderBrandChart } = useEcharts(brandChartRef);

// 品牌销量柱形图
const salesChartRef = ref<EchartsUIType>();
const { renderEcharts: renderSalesChart } = useEcharts(salesChartRef);

const brandPieData = computed(() => {
  const map = new Map<number, number>();
  allCustomers.value.forEach((c) => {
    const brandId = c.brand ?? 0;
    map.set(brandId, (map.get(brandId) ?? 0) + 1);
  });
  const result = Array.from(map.entries())
    .map(([brandId, count]) => ({
      name: brandId ? (brandMap.value.get(brandId) ?? `品牌${brandId}`) : '未设置品牌',
      value: count,
    }))
    .sort((a, b) => b.value - a.value);
  return result;
});

const brandSalesData = computed(() => {
  const map = new Map<number, number>();
  allCustomers.value.forEach((c) => {
    const brandId = c.brand ?? 0;
    const usage = c.total_water_usage ?? 0;
    map.set(brandId, (map.get(brandId) ?? 0) + usage);
  });
  const result = Array.from(map.entries())
    .map(([brandId, total]) => ({
      name: brandId ? (brandMap.value.get(brandId) ?? `品牌${brandId}`) : '未设置品牌',
      value: total,
    }))
    .sort((a, b) => b.value - a.value);
  return result;
});

// 渲染/更新品牌饼图
function updateBrandChart() {
  const data = brandPieData.value;
  if (data.length === 0) return;

  renderBrandChart({
    tooltip: {
      formatter: '{b}: {c}户 ({d}%)',
      trigger: 'item',
    },
    legend: {
      bottom: '0%',
      itemGap: 8,
      itemWidth: 10,
      itemHeight: 10,
      left: 'center',
      textStyle: {
        fontSize: 11,
      },
    },
    series: [
      {
        animationEasing: 'cubicOut',
        animationType: 'expansion',
        avoidLabelOverlap: true,
        center: ['55%', '42%'],
        data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
            shadowOffsetX: 0,
          },
          label: {
            fontSize: 12,
            fontWeight: 'bold',
            show: true,
          },
        },
        itemStyle: {
          borderColor: '#fff',
          borderRadius: 6,
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        labelLine: {
          show: false,
        },
        radius: ['28%', '52%'],
        type: 'pie',
      },
    ],
  });
}

// 渲染/更新品牌销量柱形图
function updateSalesChart() {
  const data = brandSalesData.value;
  if (data.length === 0) return;

  renderSalesChart({
    grid: {
      bottom: '18%',
      left: '12%',
      right: '8%',
      top: '12%',
    },
    tooltip: {
      formatter: '{b}: {c}桶',
      trigger: 'axis',
    },
    xAxis: {
      axisLabel: {
        fontSize: 10,
        interval: 0,
        rotate: data.length > 4 ? 30 : 0,
      },
      axisTick: { show: false },
      data: data.map((d) => d.name),
      type: 'category',
    },
    yAxis: {
      axisLabel: { fontSize: 10 },
      splitLine: {
        lineStyle: { type: 'dashed' },
      },
      type: 'value',
    },
    series: [
      {
        barWidth: '50%',
        data: data.map((d) => d.value),
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: {
          fontSize: 10,
          position: 'top',
          show: true,
        },
        type: 'bar',
      },
    ],
  });
}

watch([allCustomers, brandMap], () => {
  if (allCustomers.value.length > 0) {
    updateBrandChart();
    updateSalesChart();
  }
}, { flush: 'post' });
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

// 点击删除菜单项，弹出确认对话框
function handleDeleteClick(row: Customer) {
  Modal.confirm({
    title: '确定要删除这个客户吗？',
    content: '删除后无法恢复，请谨慎操作。',
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => onDelete(row),
  });
}

// 删除客户
async function onDelete(row: Customer) {
  // 验证客户 ID 是否存在
  if (!row.id) {
    message.error('客户编号不存在，无法删除');
    console.error('删除失败：客户数据缺少 ID', row);
    return;
  }
  
  try {
    console.warn(`准备删除客户，ID: ${row.id}`);
    await deleteCustomerApi(row.id);
    message.success('删除成功');
    refreshGrid();
  } catch (error: any) {
    console.error('删除失败:', error);
    
    // 检查错误响应
    let errorMessage = '删除失败';
    if (error.response) {
      // 服务器响应了错误状态码
      if (error.response.status === 404) {
        errorMessage = '客户不存在，无法删除';
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

// 刷新表格
function refreshGrid() {
  gridApi.query();
}

// 表格配置
const gridOptions: VxeTableGridOptions<Customer> = {
  rowConfig: {
    keyField: 'id',  // 使用正确的属性来指定行的唯一标识
  },
  stripe: true,  // 启用斑马纹
  columns: [
    { title: '序号', type: 'seq', width: 60 },
    { field: 'id', title: '客户编号', width: 100 },
    { 
      field: 'name', 
      title: '姓名地址', 
      minWidth: 200,
    },
    { field: 'customer_type_display', title: '客户类型', width: 100 },
    { 
      field: 'brandId', 
      title: '品牌', 
      width: 120,
      slots: { default: 'brand' },
    },
    { field: 'openDate', title: '开户日期', width: 120 },
    { field: 'lastDeliveryDate', title: '最后送水日期', width: 130 },
    { field: 'storage_amount', title: '存水量', width: 100, sortable: true, align: 'right' },
    { field: 'owed_empty_bucket', title: '欠空桶', width: 100, sortable: true, align: 'right' },
    { field: 'bucket_deposit_display', title: '桶押金', width: 150, align: 'center' },
    { field: 'total_water_usage', title: '总用水量', width: 100, sortable: true, align: 'right' },
    {
      title: '操作',
      width: 80,
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
    // 点击整个表头区域（字段名文字）即可排序，不只是小箭头图标
    trigger: 'default',
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
          
          allCustomers.value = data;
          
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

// 组件挂载时加载品牌数据
onMounted(() => {
  loadBrands();
});
</script>

<template>
  <Page auto-content-height>
    <FormModal :customer-data="currentCustomer" @success="refreshGrid" />
    <DetailModal :customer-data="currentDetailCustomer" :brand-name="detailBrandName" />

    <div class="flex h-full gap-4">
      <!-- 左侧：统计卡片 + 客户列表上下对齐 -->
      <div class="flex-1 flex flex-col gap-4 min-h-0">
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
          <Grid table-title="客户列表" :loading="loading" class="h-full">
            <template #toolbar-tools>
              <Button type="primary" @click="onCreate">
                <Plus class="size-5" />
                新增客户
              </Button>
              <Input
                v-model:value="searchKeyword"
                allow-clear
                class="ml-4"
                placeholder="输入编号或姓名地址搜索"
                style="width: 240px"
              >
                <template #prefix>
                  <Search class="size-4 text-gray-400" />
                </template>
              </Input>
            </template>

            <!-- 自定义品牌列的渲染 -->
            <template #brand="{ row }">
              {{ row.brand ? brandMap.get(row.brand) : '-' }}
            </template>

            <!-- 操作列 -->
            <template #action="{ row }">
              <Dropdown :trigger="['click']">
                <Button type="link" size="small">
                  <MoreHorizontal class="size-4" />
                </Button>
                <template #overlay>
                  <Menu>
                    <Menu.Item @click="onViewDetail(row)">
                      <span class="flex items-center gap-1">
                        <Eye class="size-3.5" />
                        详情
                      </span>
                    </Menu.Item>
                    <Menu.Item @click="onEdit(row)">
                      <span class="flex items-center gap-1">
                        <Pencil class="size-3.5" />
                        编辑
                      </span>
                    </Menu.Item>
                    <Menu.Item danger @click="handleDeleteClick(row)">
                      <span class="flex items-center gap-1">
                        <Trash2 class="size-3.5" />
                        删除
                      </span>
                    </Menu.Item>
                  </Menu>
                </template>
              </Dropdown>
            </template>
          </Grid>
        </div>
      </div>

      <!-- 右侧：品牌图表单独展示 -->
      <div class="w-[300px] shrink-0 flex flex-col gap-4">
        <!-- 品牌占比 -->
        <div class="rounded-lg p-3 flex flex-col flex-1 min-h-0">
          <div class="text-sm text-gray-500 dark:text-gray-400 mb-1 shrink-0">品牌占比</div>
          <EchartsUI ref="brandChartRef" height="100%" class="min-h-0 flex-1" />
        </div>
        <!-- 品牌销量 -->
        <div class="rounded-lg p-3 flex flex-col flex-1 min-h-0">
          <div class="text-sm text-gray-500 dark:text-gray-400 mb-1 shrink-0">品牌销量</div>
          <EchartsUI ref="salesChartRef" height="100%" class="min-h-0 flex-1" />
        </div>
      </div>
    </div>
  </Page>
</template>

<style>
/* Ant Design 风格排序图标：未排序时隐藏，悬停时显示淡色双箭头 */
.vxe-table .vxe-sort--asc-btn,
.vxe-table .vxe-sort--desc-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

/* 悬停表头时显示淡色双箭头，提示该列可排序 */
.vxe-header--column:hover .vxe-sort--asc-btn,
.vxe-header--column:hover .vxe-sort--desc-btn {
  opacity: 0.3;
}

/* 升序激活：只显示上箭头（高亮） */
.vxe-table .vxe-cell--sort .vxe-sort--asc-btn.sort--active {
  opacity: 1;
}
.vxe-table .vxe-sort--asc-btn.sort--active + .vxe-sort--desc-btn {
  opacity: 0;
  visibility: hidden;
}

/* 降序激活：只显示下箭头（高亮） */
.vxe-cell--sort-vertical-layout:has(.vxe-sort--desc-btn.sort--active) .vxe-sort--asc-btn {
  opacity: 0;
  visibility: hidden;
}
.vxe-table .vxe-cell--sort .vxe-sort--desc-btn.sort--active {
  opacity: 1;
}
</style>
