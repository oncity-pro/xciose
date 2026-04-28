<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
import { Plus } from '@vben/icons';
import { DollarSign, Droplets } from 'lucide-vue-next';

import {
  Button,
  Card,
  Col,
  Empty,
  InputNumber,
  Modal as AntdModal,
  Row,
  message,
} from 'ant-design-vue';

import {
  getBucketDepositConfigApi,
  updateBucketDepositConfigApi,
} from '#/api/settings';
import { deleteWaterBrandApi, getWaterBrandListApi, type WaterBrand } from '#/api/water-brand';

import BrandForm from './modules/brand-form.vue';

// 品牌列表
const brandList = ref<WaterBrand[]>([]);
const loading = ref(false);

// 空桶押金
const depositAmount = ref<number | undefined>(30);
const depositLoading = ref(false);

// 创建弹窗
const [BrandFormModal, brandFormModalApi] = useVbenModal({
  connectedComponent: BrandForm,
  destroyOnClose: true,
});

// 加载品牌数据
async function loadBrands() {
  loading.value = true;
  try {
    const data = await getWaterBrandListApi();
    brandList.value = data;
  } catch (error) {
    console.error('加载品牌数据失败:', error);
    message.error('加载品牌数据失败');
  } finally {
    loading.value = false;
  }
}

// 新增品牌
function onCreate() {
  brandFormModalApi.setData(null).open();
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
        loadBrands();
      } catch (error) {
        console.error('删除失败:', error);
        message.error('删除失败');
      }
    },
  });
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

onMounted(() => {
  loadBrands();
  loadDepositConfig();
});
</script>

<template>
  <Page auto-content-height title="基础设置">
    <BrandFormModal @success="loadBrands" />

    <div class="flex gap-4">
      <Card :loading="depositLoading" :style="{ width: '20%' }">
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

      <Card :loading="loading" :style="{ width: '20%' }">
        <template #title>
          <span class="flex items-center gap-2">
            <Droplets class="size-4" />
            桶装水品牌管理
          </span>
        </template>
      <template #extra>
        <Button type="primary" @click="onCreate">
          <Plus class="size-5" />
          新增品牌
        </Button>
      </template>

      <div v-if="brandList.length > 0">
        <Row :gutter="[16, 16]">
          <Col v-for="item in brandList" :key="item.id" :span="24">
            <Card size="small" hoverable>
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-base font-medium">{{ item.name }}</div>
                  <div class="mt-1 text-xs text-gray-400">ID: {{ item.id }}</div>
                </div>
                <Button type="link" danger size="small" @click="onDelete(item)">
                  删除
                </Button>
              </div>
            </Card>
          </Col>
        </Row>


      </div>

      <Empty v-else description="暂无品牌数据" />
    </Card>
    </div>
  </Page>
</template>
