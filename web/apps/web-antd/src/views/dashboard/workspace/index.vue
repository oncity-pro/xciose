<script lang="ts" setup>
import type {
  WorkbenchProjectItem,
  WorkbenchQuickNavItem,
  WorkbenchTrendItem,
} from '@vben/common-ui';

import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { useDebounceFn } from '@vueuse/core';

import {
  AnalysisChartCard,
  useVbenModal,
  WorkbenchHeader,
  WorkbenchProject,
  WorkbenchQuickNav,
  WorkbenchTrends,
} from '@vben/common-ui';
import { preferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';
import { openWindow } from '@vben/utils';

import { Button, Card, Input } from 'ant-design-vue';
import { Plus, Search } from 'lucide-vue-next';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import { getAllCustomersApi, type Customer } from '#/api/customer';

import Detail from '../../customer/modules/detail.vue';
import AnalyticsVisitsSource from '../analytics/analytics-visits-source.vue';

const userStore = useUserStore();

// 这是一个示例数据，实际项目中需要根据实际情况进行调整
// url 也可以是内部路由，在 navTo 方法中识别处理，进行内部跳转
// 例如：url: /dashboard/workspace
const projectItems: WorkbenchProjectItem[] = [
  {
    color: '',
    content: '不要等待机会，而要创造机会。',
    date: '2021-04-01',
    group: '开源组',
    icon: 'carbon:logo-github',
    title: 'Github',
    url: 'https://github.com',
  },
  {
    color: '#3fb27f',
    content: '现在的你决定将来的你。',
    date: '2021-04-01',
    group: '算法组',
    icon: 'ion:logo-vue',
    title: 'Vue',
    url: 'https://vuejs.org',
  },
  {
    color: '#e18525',
    content: '没有什么才能比努力更重要。',
    date: '2021-04-01',
    group: '上班摸鱼',
    icon: 'ion:logo-html5',
    title: 'Html5',
    url: 'https://developer.mozilla.org/zh-CN/docs/Web/HTML',
  },
  {
    color: '#bf0c2c',
    content: '热情和欲望可以突破一切难关。',
    date: '2021-04-01',
    group: 'UI',
    icon: 'ion:logo-angular',
    title: 'Angular',
    url: 'https://angular.io',
  },
  {
    color: '#00d8ff',
    content: '健康的身体是实现目标的基石。',
    date: '2021-04-01',
    group: '技术牛',
    icon: 'bx:bxl-react',
    title: 'React',
    url: 'https://reactjs.org',
  },
  {
    color: '#EBD94E',
    content: '路是走出来的，而不是空想出来的。',
    date: '2021-04-01',
    group: '架构组',
    icon: 'ion:logo-javascript',
    title: 'Js',
    url: 'https://developer.mozilla.org/zh-CN/docs/Web/JavaScript',
  },
];

// 同样，这里的 url 也可以使用以 http 开头的外部链接
const quickNavItems: WorkbenchQuickNavItem[] = [
  {
    color: '#1fdaca',
    icon: 'ion:home-outline',
    title: '首页',
    url: '/',
  },
  {
    color: '#bf0c2c',
    icon: 'ion:grid-outline',
    title: '仪表盘',
    url: '/dashboard',
  },
  {
    color: '#e18525',
    icon: 'ion:layers-outline',
    title: '组件',
    url: '/demos/features/icons',
  },
  {
    color: '#3fb27f',
    icon: 'ion:settings-outline',
    title: '系统管理',
    url: '/demos/features/login-expired', // 这里的 URL 是示例，实际项目中需要根据实际情况进行调整
  },
  {
    color: '#4daf1bc9',
    icon: 'ion:key-outline',
    title: '权限管理',
    url: '/demos/access/page-control',
  },
  {
    color: '#00d8ff',
    icon: 'ion:bar-chart-outline',
    title: '图表',
    url: '/analytics',
  },
];

const trendItems: WorkbenchTrendItem[] = [
  {
    avatar: 'svg:avatar-1',
    content: `在 <a>开源组</a> 创建了项目 <a>Vue</a>`,
    date: '刚刚',
    title: '威廉',
  },
  {
    avatar: 'svg:avatar-2',
    content: `关注了 <a>威廉</a> `,
    date: '1个小时前',
    title: '艾文',
  },
  {
    avatar: 'svg:avatar-3',
    content: `发布了 <a>个人动态</a> `,
    date: '1天前',
    title: '克里斯',
  },
  {
    avatar: 'svg:avatar-4',
    content: `发表文章 <a>如何编写一个Vite插件</a> `,
    date: '2天前',
    title: 'Vben',
  },
  {
    avatar: 'svg:avatar-1',
    content: `回复了 <a>杰克</a> 的问题 <a>如何进行项目优化？</a>`,
    date: '3天前',
    title: '皮特',
  },
  {
    avatar: 'svg:avatar-2',
    content: `关闭了问题 <a>如何运行项目</a> `,
    date: '1周前',
    title: '杰克',
  },
  {
    avatar: 'svg:avatar-3',
    content: `发布了 <a>个人动态</a> `,
    date: '1周前',
    title: '威廉',
  },
  {
    avatar: 'svg:avatar-4',
    content: `推送了代码到 <a>Github</a>`,
    date: '2021-04-01 20:00',
    title: '威廉',
  },
  {
    avatar: 'svg:avatar-4',
    content: `发表文章 <a>如何编写使用 Admin Vben</a> `,
    date: '2021-03-01 20:00',
    title: 'Vben',
  },
];

const router = useRouter();

// ============ 今日送水客户名单 ============
const searchCustomerId = ref('');
const searchName = ref('');
const searchResults = ref<Customer[]>([]);
const showSearchResults = ref(false);
const activeField = ref<'id' | 'name' | null>(null);
const selectedCustomers = ref<Customer[]>([]);
const searchLoading = ref(false);
const completedCustomers = ref<Customer[]>([]);
const completedTodayIds = ref<Set<string>>(new Set());

function completeCustomer(row: Customer) {
  selectedCustomers.value = selectedCustomers.value.filter((c) => c.id !== row.id);
  if (!completedTodayIds.value.has(row.id)) {
    completedCustomers.value.push(row);
    completedTodayIds.value.add(row.id);
  }
}

// ============ 本地持久化（按天） ============
const STORAGE_KEY = 'workstation_today_delivery';
const STORAGE_DATE_KEY = 'workstation_today_date';

function saveState() {
  const data = {
    selected: selectedCustomers.value,
    completed: completedCustomers.value,
    completedIds: Array.from(completedTodayIds.value),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  localStorage.setItem(STORAGE_DATE_KEY, new Date().toDateString());
}

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const data = JSON.parse(saved);
      selectedCustomers.value = data.selected || [];
      completedCustomers.value = data.completed || [];
      completedTodayIds.value = new Set(data.completedIds || []);
    } catch (e) {
      console.error('加载今日送水数据失败:', e);
    }
  }
}

loadState();

watch([selectedCustomers, completedCustomers], saveState, { deep: true });

// 详情弹窗
const [DetailModal, detailModalApi] = useVbenModal({
  connectedComponent: Detail,
  destroyOnClose: true,
});

const currentDetailCustomer = ref<Customer | null>(null);
const detailBrandName = ref<string>('');

function onViewDetail(row: Customer) {
  currentDetailCustomer.value = { ...row };
  detailBrandName.value = row.brand_name ?? '';
  detailModalApi.open();
}

const debouncedSearch = useDebounceFn(async () => {
  const customerId = searchCustomerId.value.trim();
  const name = searchName.value.trim();

  if (!customerId && !name) {
    searchResults.value = [];
    searchLoading.value = false;
    return;
  }

  searchLoading.value = true;
  showSearchResults.value = true;
  try {
    const params: any = {};
    if (customerId) {
      params.customer_id = customerId;
    }
    if (name) {
      params.name = name;
    }
    console.log('开始搜索客户:', params);
    const res = await getAllCustomersApi(params);
    console.log('搜索结果:', res);
    const existingIds = new Set(selectedCustomers.value.map((c) => c.id));
    console.log('已有客户ID:', existingIds);
    searchResults.value = (res || []).filter((c) => !existingIds.has(c.id));
    console.log('过滤后结果数量:', searchResults.value.length);
  } catch (error) {
    console.error('搜索客户失败:', error);
  } finally {
    searchLoading.value = false;
  }
}, 100);

watch(searchCustomerId, (val) => {
  console.log('客户编号搜索变化:', val);
  activeField.value = 'id';
  debouncedSearch();
});

watch(searchName, (val) => {
  console.log('姓名地址搜索变化:', val);
  activeField.value = 'name';
  debouncedSearch();
});

function handleSearchFocus(field: 'id' | 'name') {
  activeField.value = field;
  if (searchResults.value.length > 0) {
    showSearchResults.value = true;
  }
}

function handleSearchBlur() {
  setTimeout(() => {
    showSearchResults.value = false;
  }, 200);
}

function handleEnter() {
  if (showSearchResults.value && searchResults.value.length > 0) {
    addCustomer(searchResults.value[0]!);
  }
}

function handleResetSearch() {
  searchCustomerId.value = '';
  searchName.value = '';
  searchResults.value = [];
  showSearchResults.value = false;
}

function addCustomer(customer: Customer) {
  if (completedTodayIds.value.has(customer.id)) {
    return;
  }
  selectedCustomers.value.push(customer);
  searchCustomerId.value = '';
  searchName.value = '';
  searchResults.value = [];
  showSearchResults.value = false;
}

function removeCustomer(id: string) {
  selectedCustomers.value = selectedCustomers.value.filter((c) => c.id !== id);
}

const gridOptions: VxeTableGridOptions<Customer> = {
  stripe: true,
  align: 'center',
  columns: [
    {
      field: 'id',
      title: '客户编号',
      width: 100,
      formatter: ({ cellValue }: { cellValue: string }) => {
        if (!cellValue || cellValue.startsWith('__empty__')) {
          return '';
        }
        if (/^\d+$/.test(cellValue)) {
          return String(Number(cellValue));
        }
        return cellValue;
      },
    },
    { field: 'name', title: '姓名地址', minWidth: 200 },
    { field: 'brand_name', title: '品牌', width: 120 },
    {
      field: 'storage_amount',
      title: '存水量',
      width: 100,
      formatter: ({ cellValue }: { cellValue: number | string }) => {
        if (cellValue !== undefined && cellValue !== null && cellValue !== '') {
          return `${cellValue}桶`;
        }
        return '';
      },
    },
    {
      title: '操作',
      width: 150,
      slots: { default: 'action' },
    },
  ],
  pagerConfig: { enabled: false },
  height: 457,
  rowConfig: {
    height: 40,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

const tableData = computed(() => {
  const data = selectedCustomers.value.map((c) => ({ ...c }));
  while (data.length < 10) {
    data.push({
      id: `__empty__${data.length}`,
      name: '',
      brand_name: '',
      storage_amount: '',
    } as any);
  }
  return data;
});

const selectedRealCount = computed(
  () => selectedCustomers.value.filter((c) => !c.id?.startsWith('__empty__')).length,
);
const totalCount = computed(() => selectedRealCount.value + completedCustomers.value.length);
const completedCount = computed(() => completedCustomers.value.length);
const inProgressCount = computed(() => selectedRealCount.value);

watch(
  tableData,
  (data) => {
    gridApi.setGridOptions({ data });
  },
  { deep: true, immediate: true },
);

function navTo(nav: WorkbenchProjectItem | WorkbenchQuickNavItem) {
  if (nav.url?.startsWith('http')) {
    openWindow(nav.url);
    return;
  }
  if (nav.url?.startsWith('/')) {
    router.push(nav.url).catch((error) => {
      console.error('Navigation failed:', error);
    });
  } else {
    console.warn(`Unknown URL for navigation item: ${nav.title} -> ${nav.url}`);
  }
}
</script>

<template>
  <div class="p-5">
    <WorkbenchHeader
      :avatar="userStore.userInfo?.avatar || preferences.app.defaultAvatar"
    >
      <template #title>
        早安, {{ userStore.userInfo?.realName }}, 开始您一天的工作吧！
      </template>
      <template #description> 今日晴，20℃ - 32℃！ </template>
    </WorkbenchHeader>

    <div class="mt-5 flex flex-col lg:flex-row">
      <div class="mr-4 w-full lg:w-3/5">
        <!-- 今日送水客户名单 -->
        <Card class="mt-5" title="今日送水客户名单" :body-style="{ padding: 0 }">
          <div class="px-4 pt-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="relative">
                  <Input
                    v-model:value="searchCustomerId"
                    allow-clear
                    placeholder="搜索客户编号"
                    style="width: 160px"
                    @blur="handleSearchBlur"
                    @focus="() => handleSearchFocus('id')"
                    @keydown.enter="handleEnter"
                  >
                    <template #prefix>
                      <Search class="size-4 text-gray-400" />
                    </template>
                  </Input>
                  <div
                    v-if="activeField === 'id' && (searchResults.length > 0 || searchLoading) && showSearchResults"
                    class="absolute top-full left-0 z-50 mt-1 min-w-full w-max max-w-[400px] rounded border bg-white shadow-lg dark:border-gray-700 dark:bg-[#1e1e1e]"
                  >
                    <div v-if="searchLoading" class="px-3 py-2 text-sm text-gray-400 dark:text-gray-500">
                      搜索中...
                    </div>
                    <div
                      v-for="customer in searchResults"
                      v-else
                      :key="customer.id"
                      class="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                      @click="addCustomer(customer)"
                    >
                      <div class="flex items-center gap-3 text-sm whitespace-nowrap">
                        <span class="w-10 shrink-0 font-medium">
                          {{ /^\d+$/.test(customer.id) ? String(Number(customer.id)) : customer.id }}
                        </span>
                        <span class="text-gray-700 dark:text-gray-200">
                          {{ customer.name }}
                        </span>
                      </div>
                      <Button type="link" size="small" @click.stop="addCustomer(customer)">
                        <Plus class="size-4" />
                      </Button>
                    </div>
                    <div v-if="!searchLoading && searchResults.length === 0 && (searchCustomerId.trim() || searchName.trim())" class="px-3 py-2 text-sm text-gray-400 dark:text-gray-500">
                      未找到匹配客户
                    </div>
                  </div>
                </div>
                <div class="relative">
                  <Input
                    v-model:value="searchName"
                    allow-clear
                    placeholder="搜索姓名地址"
                    style="width: 160px"
                    @blur="handleSearchBlur"
                    @focus="() => handleSearchFocus('name')"
                    @keydown.enter="handleEnter"
                  >
                    <template #prefix>
                      <Search class="size-4 text-gray-400" />
                    </template>
                  </Input>
                  <div
                    v-if="activeField === 'name' && (searchResults.length > 0 || searchLoading) && showSearchResults"
                    class="absolute top-full left-0 z-50 mt-1 min-w-full w-max max-w-[400px] rounded border bg-white shadow-lg dark:border-gray-700 dark:bg-[#1e1e1e]"
                  >
                    <div v-if="searchLoading" class="px-3 py-2 text-sm text-gray-400 dark:text-gray-500">
                      搜索中...
                    </div>
                    <div
                      v-for="customer in searchResults"
                      v-else
                      :key="customer.id"
                      class="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                      @click="addCustomer(customer)"
                    >
                      <div class="flex items-center gap-3 text-sm whitespace-nowrap">
                        <span class="w-10 shrink-0 font-medium">
                          {{ /^\d+$/.test(customer.id) ? String(Number(customer.id)) : customer.id }}
                        </span>
                        <span class="text-gray-700 dark:text-gray-200">
                          {{ customer.name }}
                        </span>
                      </div>
                      <Button type="link" size="small" @click.stop="addCustomer(customer)">
                        <Plus class="size-4" />
                      </Button>
                    </div>
                    <div v-if="!searchLoading && searchResults.length === 0 && (searchCustomerId.trim() || searchName.trim())" class="px-3 py-2 text-sm text-gray-400 dark:text-gray-500">
                      未找到匹配客户
                    </div>
                  </div>
                </div>
                <Button size="small" @click="handleResetSearch">
                  重置
                </Button>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <span>进行中：{{ inProgressCount }}位</span>
                <span>已完成：{{ completedCount }}位</span>
              </div>
            </div>
          </div>
          <div class="pt-2">
            <Grid class="w-full">
              <template #action="{ row }">
                <div v-if="!row.id?.startsWith('__empty__')" class="flex items-center justify-center gap-1">
                  <Button danger size="small" type="link" @click="onViewDetail(row)">
                    出单
                  </Button>
                  <Button class="text-white" size="small" type="link" @click="completeCustomer(row)">
                    已完成
                  </Button>
                  <Button size="small" type="link" @click="removeCustomer(row.id)">
                    移除
                  </Button>
                </div>
              </template>
            </Grid>
          </div>
          <DetailModal :customer-data="currentDetailCustomer" :brand-name="detailBrandName" />
        </Card>
        <WorkbenchTrends :items="trendItems" class="mt-5" title="最新动态" />
      </div>
      <div class="w-full lg:w-2/5">
        <WorkbenchQuickNav
          :items="quickNavItems"
          class="mt-5 lg:mt-0"
          title="快捷导航"
          @click="navTo"
        />
        <WorkbenchProject :items="projectItems" title="项目" @click="navTo" />
        <AnalysisChartCard class="mt-5" title="访问来源">
          <AnalyticsVisitsSource />
        </AnalysisChartCard>
      </div>
    </div>
  </div>
</template>


