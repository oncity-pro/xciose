<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';
import { Plus } from '@vben/icons';
import { DollarSign, Droplets, Wine, Package } from 'lucide-vue-next';

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
import { Pencil } from 'lucide-vue-next';

import BrandForm from './modules/brand-form.vue';

// 品牌列表（按类型）
const bucketBrandList = ref<WaterBrand[]>([]);
const bottleBrandList = ref<WaterBrand[]>([]);
const disposableBrandList = ref<WaterBrand[]>([]);
const loading = ref({
  bucket: false,
  bottle: false,
  disposable: false,
});

// 空桶押金
const depositAmount = ref<number | undefined>(30);
const depositLoading = ref(false);

// 创建弹窗
const [BrandFormModal, brandFormModalApi] = useVbenModal({
  connectedComponent: BrandForm,
  destroyOnClose: true,
});

// 加载品牌数据（按类型分别加载）
async function loadBrands() {
  loading.value.bucket = true;
  loading.value.bottle = true;
  loading.value.disposable = true;
  try {
    const [bucketData, bottleData, disposableData] = await Promise.all([
      getWaterBrandListApi('bucket'),
      getWaterBrandListApi('bottle'),
      getWaterBrandListApi('disposable'),
    ]);
    bucketBrandList.value = bucketData;
    bottleBrandList.value = bottleData;
    disposableBrandList.value = disposableData;
  } catch (error) {
    console.error('加载品牌数据失败:', error);
    message.error('加载品牌数据失败');
  } finally {
    loading.value.bucket = false;
    loading.value.bottle = false;
    loading.value.disposable = false;
  }
}

// 新增品牌
function onCreate(brandType: string) {
  brandFormModalApi.setData({ brand_type: brandType }).open();
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

      <!-- 桶装水品牌管理 -->
      <Card :loading="loading.bucket" :style="{ width: '20%' }">
        <template #title>
          <span class="flex items-center gap-2">
            <Droplets class="size-4" />
            桶装水品牌管理
          </span>
        </template>
        <template #extra>
          <Button type="primary" @click="onCreate('bucket')">
            <Plus class="size-5" />
            新增品牌
          </Button>
        </template>

        <div v-if="bucketBrandList.length > 0">
          <Row :gutter="[16, 16]">
            <Col v-for="item in bucketBrandList" :key="item.id" :span="24">
              <Card size="small" hoverable>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="text-base font-medium">{{ item.name }}</div>
                    <div class="mt-1 text-xs text-gray-400">
                      <span>进货: ¥{{ item.purchase_price || 0 }}</span>
                      <span class="ml-3">零售: ¥{{ item.price_per_bucket || 0 }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <Button type="link" size="small" @click="onEdit(item)">
                      <Pencil class="size-3.5" />
                    </Button>
                    <Button type="link" danger size="small" @click="onDelete(item)">
                      删除
                    </Button>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
        <Empty v-else description="暂无品牌数据" />
      </Card>

      <!-- 支装水品牌管理 -->
      <Card :loading="loading.bottle" :style="{ width: '20%' }">
        <template #title>
          <span class="flex items-center gap-2">
            <Wine class="size-4" />
            支装水品牌管理
          </span>
        </template>
        <template #extra>
          <Button type="primary" @click="onCreate('bottle')">
            <Plus class="size-5" />
            新增品牌
          </Button>
        </template>

        <div v-if="bottleBrandList.length > 0">
          <Row :gutter="[16, 16]">
            <Col v-for="item in bottleBrandList" :key="item.id" :span="24">
              <Card size="small" hoverable>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="text-base font-medium">{{ item.name }}</div>
                    <div class="mt-1 text-xs text-gray-400">
                      <span>进货: ¥{{ item.purchase_price || 0 }}</span>
                      <span class="ml-3">零售: ¥{{ item.price_per_bucket || 0 }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <Button type="link" size="small" @click="onEdit(item)">
                      <Pencil class="size-3.5" />
                    </Button>
                    <Button type="link" danger size="small" @click="onDelete(item)">
                      删除
                    </Button>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
        <Empty v-else description="暂无品牌数据" />
      </Card>

      <!-- 一次性桶装水品牌管理 -->
      <Card :loading="loading.disposable" :style="{ width: '20%' }">
        <template #title>
          <span class="flex items-center gap-2">
            <Package class="size-4" />
            一次性桶装水品牌管理
          </span>
        </template>
        <template #extra>
          <Button type="primary" @click="onCreate('disposable')">
            <Plus class="size-5" />
            新增品牌
          </Button>
        </template>

        <div v-if="disposableBrandList.length > 0">
          <Row :gutter="[16, 16]">
            <Col v-for="item in disposableBrandList" :key="item.id" :span="24">
              <Card size="small" hoverable>
                <div class="flex items-center justify-between">
                  <div>
                    <div class="text-base font-medium">{{ item.name }}</div>
                    <div class="mt-1 text-xs text-gray-400">
                      <span>进货: ¥{{ item.purchase_price || 0 }}</span>
                      <span class="ml-3">零售: ¥{{ item.price_per_bucket || 0 }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <Button type="link" size="small" @click="onEdit(item)">
                      <Pencil class="size-3.5" />
                    </Button>
                    <Button type="link" danger size="small" @click="onDelete(item)">
                      删除
                    </Button>
                  </div>
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
