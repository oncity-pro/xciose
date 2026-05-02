<script lang="ts" setup>
// 库存管理页面组件
import type { VxeTableGridOptions } from '#/adapter/vxe-table';

import { computed, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { Plus } from '@vben/icons';

import { Button } from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { $t } from '#/locales';

// 进货记录数据类型
interface PurchaseRecord {
  id: number;
  productName: string;
  purchaseDate: string;
  quantity: number;
  unitPrice: number;
  totalAmount: number;
}

// 模拟进货数据
const purchaseData = ref<PurchaseRecord[]>([
  { id: 1, productName: '农夫山泉桶装水', purchaseDate: '2026-04-15', quantity: 100, unitPrice: 8.50, totalAmount: 850.00 },
  { id: 2, productName: '怡宝桶装水', purchaseDate: '2026-04-18', quantity: 80, unitPrice: 9.00, totalAmount: 720.00 },
  { id: 3, productName: '娃哈哈桶装水', purchaseDate: '2026-04-20', quantity: 120, unitPrice: 7.50, totalAmount: 900.00 },
  { id: 4, productName: '景田桶装水', purchaseDate: '2026-04-22', quantity: 60, unitPrice: 10.00, totalAmount: 600.00 },
  { id: 5, productName: '康师傅桶装水', purchaseDate: '2026-04-25', quantity: 90, unitPrice: 6.50, totalAmount: 585.00 },
  { id: 6, productName: '百岁山桶装水', purchaseDate: '2026-04-28', quantity: 50, unitPrice: 12.00, totalAmount: 600.00 },
  { id: 7, productName: '农夫山泉桶装水', purchaseDate: '2026-05-01', quantity: 150, unitPrice: 8.50, totalAmount: 1275.00 },
  { id: 8, productName: '怡宝桶装水', purchaseDate: '2026-05-02', quantity: 100, unitPrice: 9.00, totalAmount: 900.00 },
]);

// 计算进货总额
const grandTotal = computed(() => {
  return purchaseData.value.reduce((sum, item) => sum + item.totalAmount, 0);
});

// 表格配置
const gridOptions: VxeTableGridOptions<PurchaseRecord> = {
  rowConfig: {
    keyField: 'id',
  },
  stripe: true,
  align: 'center',
  columns: [
    { title: '序号', type: 'seq', width: 60 },
    { field: 'productName', title: '商品名称', minWidth: 180 },
    { field: 'purchaseDate', title: '进货日期', width: 120 },
    { field: 'quantity', title: '进货数量', width: 100, sortable: true },
    {
      field: 'unitPrice',
      title: '进货单价',
      width: 110,
      sortable: true,
      formatter: ({ cellValue }: { cellValue: number }) => `¥${Number(cellValue).toFixed(2)}`,
    },
    {
      field: 'totalAmount',
      title: '进货总额',
      width: 120,
      sortable: true,
      formatter: ({ cellValue }: { cellValue: number }) => `¥${Number(cellValue).toFixed(2)}`,
    },
  ],
  height: 'auto',
  pagerConfig: {
    enabled: true,
    pageSize: 10,
    pageSizes: [10, 20, 50],
  },
  sortConfig: {
    trigger: 'cell',
    orders: ['asc', 'desc', null],
  },
  proxyConfig: {
    sort: true,
    ajax: {
      query: async ({ page, sort }) => {
        let data = [...purchaseData.value];

        // 前端排序
        if (sort && sort.field && sort.order) {
          const order = sort.order;
          const field = sort.field as keyof PurchaseRecord;
          data = data.sort((a, b) => {
            const va = a[field];
            const vb = b[field];
            if (va === null || va === undefined) return order === 'asc' ? -1 : 1;
            if (vb === null || vb === undefined) return order === 'asc' ? 1 : -1;
            if (typeof va === 'number' && typeof vb === 'number') {
              return order === 'asc' ? va - vb : vb - va;
            }
            const sa = String(va);
            const sb = String(vb);
            return order === 'asc'
              ? sa.localeCompare(sb, 'zh-CN')
              : sb.localeCompare(sa, 'zh-CN');
          });
        }

        // 前端分页
        const total = data.length;
        const start = (page.currentPage - 1) * page.pageSize;
        const end = start + page.pageSize;
        const items = data.slice(start, end);

        return { items, total };
      },
    },
  },
  toolbarConfig: {
    search: false,
    refresh: true,
    custom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

defineOptions({
  name: 'InventoryManagement',
});
</script>

<template>
  <Page auto-content-height>
    <div class="flex flex-col gap-4 h-full min-h-0 p-5">
      <!-- 页面标题 -->
      <div class="mb-2 flex items-center justify-between">
        <h2 class="text-xl font-semibold">{{ $t('page.inventory.title') }}</h2>
      </div>

      <!-- 进货统计卡片 -->
      <div class="flex shrink-0 gap-4">
        <div class="flex-1 rounded-lg bg-blue-50 p-4 dark:bg-blue-950/30 flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-500 dark:text-blue-300">进货总次数</div>
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ purchaseData.length }}</div>
          </div>
        </div>
        <div class="flex-1 rounded-lg bg-green-50 p-4 dark:bg-green-950/30 flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-500 dark:text-green-300">进货总金额</div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">¥{{ grandTotal.toFixed(2) }}</div>
          </div>
        </div>
      </div>

      <!-- 进货记录表格 -->
      <div class="min-h-0 flex-1">
        <Grid class="h-full">
          <template #toolbar-tools>
            <Button type="primary">
              <Plus class="size-5" />
              新增进货
            </Button>
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
</style>