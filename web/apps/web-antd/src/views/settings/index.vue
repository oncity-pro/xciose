<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import type { VxeTableGridOptions } from '#/adapter/vxe-table';
import type { WaterBrand } from '#/api/water-brand';

import { Page, useVbenModal } from '@vben/common-ui';
import { Plus } from '@vben/icons';
import { DollarSign, Pencil, Trash2 } from 'lucide-vue-next';

import {
  Button,
  Card,
  InputNumber,
  Modal as AntdModal,
  message,
} from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  getBucketDepositConfigApi,
  updateBucketDepositConfigApi,
} from '#/api/settings';
import { deleteWaterBrandApi, getAllWaterBrandsApi } from '#/api/water-brand';

import BrandForm from './modules/brand-form.vue';

const loading = ref(false);

// 空桶押金
const depositAmount = ref<number | undefined>(30);
const depositLoading = ref(false);

// 创建弹窗
const [BrandFormModal, brandFormModalApi] = useVbenModal({
  connectedComponent: BrandForm,
  destroyOnClose: true,
});

// 新增品牌
function onCreate() {
  brandFormModalApi.setData({ brand_type: 'bucket' }).open();
}

// 编辑品牌
function onEdit(row: WaterBrand) {
  brandFormModalApi.setData(row).open();
}

// 删除品牌
function onDelete(row: WaterBrand) {
  AntdModal.confirm({
    title: '确认删除',
    content: `确定要删除品牌"${row.name}"吗？`,
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteWaterBrandApi(row.id);
        message.success('删除成功');
        refreshGrid();
      } catch (error) {
        console.error('删除失败:', error);
        message.error('删除失败');
      }
    },
  });
}

// 刷新表格
function refreshGrid() {
  gridApi.query();
}

// 加载空桶押金配置
async function loadDepositConfig() {
  depositLoading.value = true;
  try {
    const config = await getBucketDepositConfigApi();
    depositAmount.value = config.amount_per_bucket;
  } catch (error) {
    console.error('加载空桶押金配置失败:', error);
    message.error('加载空桶押金配置失败');
  } finally {
    depositLoading.value = false;
  }
}

// 保存空桶押金配置
async function saveDepositConfig() {
  if (depositAmount.value === null || depositAmount.value === undefined) {
    message.warning('请输入押金金额');
    return;
  }
  depositLoading.value = true;
  try {
    await updateBucketDepositConfigApi({ amount_per_bucket: depositAmount.value });
    message.success('保存成功');
  } catch (error) {
    console.error('保存空桶押金配置失败:', error);
    message.error('保存失败');
  } finally {
    depositLoading.value = false;
  }
}

// 表格配置
const gridOptions: VxeTableGridOptions<WaterBrand> = {
  rowConfig: {
    keyField: 'id',
  },
  stripe: true,
  align: 'center',
  columns: [
    { title: '序号', type: 'seq', width: 60 },
    { field: 'name', title: '品牌名称', minWidth: 160 },
    { field: 'brand_type_display', title: '品牌类型', width: 120 },
    { field: 'specification', title: '规格', width: 120 },
    {
      field: 'purchase_price',
      title: '进货价',
      width: 120,
      formatter: ({ cellValue }: { cellValue: number }) =>
        cellValue ? `¥${Number(cellValue).toFixed(2)}` : '¥0.00',
    },
    {
      field: 'price_per_bucket',
      title: '零售价',
      width: 120,
      formatter: ({ cellValue }: { cellValue: number }) =>
        cellValue ? `¥${Number(cellValue).toFixed(2)}` : '¥0.00',
    },
    {
      title: '操作',
      width: 100,
      fixed: 'right',
      slots: { default: 'action' },
    },
  ],
  height: '100%',
  keepSource: true,
  pagerConfig: {
    enabled: true,
    pageSize: 10,
    pageSizes: [10, 20, 50],
  },
  proxyConfig: {
    ajax: {
      query: async ({ page }) => {
        loading.value = true;
        try {
          let data = await getAllWaterBrandsApi();
          // 模拟分页
          const total = data.length;
          const start = (page.currentPage - 1) * page.pageSize;
          const end = start + page.pageSize;
          const items = data.slice(start, end);
          return {
            items,
            total,
          };
        } catch (error) {
          console.error('获取品牌列表失败:', error);
          message.error('获取品牌列表失败');
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
    search: false,
    refresh: true,
    custom: true,
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });

onMounted(() => {
  loadDepositConfig();
});
</script>

<template>
  <Page auto-content-height title="基础设置">
    <BrandFormModal @success="refreshGrid" />

    <div class="flex flex-col gap-4 h-full min-h-0">
      <!-- 空桶押金 -->
      <Card :loading="depositLoading" class="shrink-0">
        <template #title>
          <span class="flex items-center gap-2">
            <DollarSign class="size-4" />
            空桶押金
          </span>
        </template>
        <div class="flex items-center gap-2">
          <InputNumber
            v-model:value="depositAmount"
            :min="0"
            :precision="2"
            placeholder="请输入每桶押金金额"
            style="width: 140px"
          />
          <span class="text-gray-500">元/桶</span>
          <Button type="primary" @click="saveDepositConfig">保存</Button>
        </div>
      </Card>

      <!-- 品牌列表 -->
      <div class="min-h-0 flex-1">
        <Grid :loading="loading" class="h-full">
          <template #toolbar-tools>
            <Button type="primary" @click="onCreate">
              <Plus class="size-5" />
              新增品牌
            </Button>
          </template>

          <!-- 操作列 -->
          <template #action="{ row }">
            <div class="flex items-center justify-center gap-1">
              <Button type="link" size="small" title="编辑" @click="onEdit(row)">
                <Pencil class="size-4" />
              </Button>
              <Button type="link" size="small" danger title="删除" @click="onDelete(row)">
                <Trash2 class="size-4" />
              </Button>
            </div>
          </template>
        </Grid>
      </div>
    </div>
  </Page>
</template>
