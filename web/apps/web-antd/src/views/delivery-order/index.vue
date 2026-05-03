<script lang="ts" setup>
import type { Customer } from '#/api/customer';

import { computed, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { ClipboardList, Search, UserCheck } from 'lucide-vue-next';

import { Button, Card, Col, DatePicker, Input, InputNumber, message, Row, Textarea } from 'ant-design-vue';

import { getCustomerDetailApi } from '#/api/customer';
import { createDeliveryRecordApi } from '#/api/delivery-record';

// 客户编号输入
const customerIdInput = ref('');

// 加载状态
const loading = ref(false);
const submitting = ref(false);

// 当前客户
const currentCustomer = ref<Customer | null>(null);

// 表单数据
const deliveryDate = ref<string>('');
const waterDelivered = ref<number>(0);
const bucketsReturned = ref<number>(0);
const storageAmount = ref<number>(0);
const remark = ref('');

// 获取今天日期
function getToday(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 初始化日期为今天
deliveryDate.value = getToday();

// 计算目前欠空桶
const currentOwedBuckets = computed(() => {
  if (!currentCustomer.value) return 0;
  const original = currentCustomer.value.owed_empty_bucket || 0;
  const delivered = waterDelivered.value || 0;
  const returned = bucketsReturned.value || 0;
  return original + delivered - returned;
});

// 搜索客户
async function handleSearchCustomer() {
  const id = customerIdInput.value.trim();
  if (!id) {
    message.warning('请输入客户编号');
    return;
  }

  loading.value = true;
  try {
    const customer = await getCustomerDetailApi(id);
    currentCustomer.value = customer;
    // 初始化存水量为客户当前存水量
    storageAmount.value = customer.storage_amount ?? 0;
    message.success('客户查找成功');
  } catch (error: any) {
    console.error('查找客户失败:', error);
    currentCustomer.value = null;
    const responseData = error?.response?.data ?? {};
    const msg = responseData?.message || responseData?.detail || error?.message || '客户不存在或查询失败';
    message.error(msg);
  } finally {
    loading.value = false;
  }
}

// 确定出单
async function handleSubmit() {
  if (!currentCustomer.value) {
    message.warning('请先搜索并选择客户');
    return;
  }

  if (!deliveryDate.value) {
    message.warning('请选择送水日期');
    return;
  }

  const delivered = waterDelivered.value || 0;
  if (delivered <= 0) {
    message.warning('送水量必须大于0');
    return;
  }

  submitting.value = true;
  try {
    await createDeliveryRecordApi({
      customer: currentCustomer.value.id,
      date: deliveryDate.value,
      water_delivered: delivered,
      buckets_returned: bucketsReturned.value || 0,
      owed_empty_buckets: currentOwedBuckets.value,
      storage_amount: storageAmount.value || 0,
      remark: remark.value,
    });

    message.success('出单成功');

    // 重置表单
    currentCustomer.value = null;
    customerIdInput.value = '';
    waterDelivered.value = 0;
    bucketsReturned.value = 0;
    storageAmount.value = 0;
    remark.value = '';
    deliveryDate.value = getToday();
  } catch (error: any) {
    console.error('出单失败:', error);
    const responseData = error?.response?.data ?? {};
    const msg = responseData?.message || responseData?.detail || error?.message || '出单失败';
    message.error(msg);
  } finally {
    submitting.value = false;
  }
}

// 键盘回车搜索
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    handleSearchCustomer();
  }
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex flex-col gap-6 max-w-3xl mx-auto py-6">
      <!-- 页面标题 -->
      <div class="flex items-center gap-3">
        <ClipboardList class="size-7 text-blue-500" />
        <h1 class="text-2xl font-bold">商品出单</h1>
      </div>

      <!-- 客户搜索区域 -->
      <Card title="搜索客户" :bordered="false">
        <div class="flex gap-3">
          <Input
            v-model:value="customerIdInput"
            placeholder="请输入客户编号"
            style="width: 280px"
            size="large"
            allow-clear
            @keydown="handleKeydown"
          >
            <template #prefix>
              <Search class="size-4 text-gray-400" />
            </template>
          </Input>
          <Button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSearchCustomer"
          >
            确定
          </Button>
        </div>
      </Card>

      <!-- 客户信息卡片 -->
      <Card v-if="currentCustomer" title="客户信息" :bordered="false">
        <template #extra>
          <span class="flex items-center gap-1 text-green-600">
            <UserCheck class="size-4" />
            已选中
          </span>
        </template>
        <Row :gutter="[16, 16]">
          <Col :span="8">
            <div class="text-sm text-gray-500">客户编号</div>
            <div class="text-lg font-semibold">{{ /^\d+$/.test(currentCustomer.id) ? String(Number(currentCustomer.id)) : currentCustomer.id }}</div>
          </Col>
          <Col :span="16">
            <div class="text-sm text-gray-500">姓名地址</div>
            <div class="text-lg font-semibold">{{ currentCustomer.name }}</div>
          </Col>
          <Col :span="8">
            <div class="text-sm text-gray-500">客户类型</div>
            <div class="text-base">{{ currentCustomer.customer_type_display || '-' }}</div>
          </Col>
          <Col :span="8">
            <div class="text-sm text-gray-500">当前欠空桶</div>
            <div class="text-base font-semibold" :class="(currentCustomer.owed_empty_bucket || 0) > 0 ? 'text-orange-600' : 'text-gray-700'">
              {{ currentCustomer.owed_empty_bucket || 0 }} 桶
            </div>
          </Col>
          <Col :span="8">
            <div class="text-sm text-gray-500">当前存水量</div>
            <div class="text-base font-semibold text-blue-600">{{ currentCustomer.storage_amount || 0 }} 桶</div>
          </Col>
        </Row>
      </Card>

      <!-- 出单表单 -->
      <Card title="出单信息" :bordered="false">
        <div class="flex flex-col gap-5">
          <Row :gutter="[16, 16]">
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">
                送水日期 <span class="text-red-500">*</span>
              </div>
              <DatePicker
                v-model:value="deliveryDate"
                placeholder="请选择送水日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                size="large"
              />
            </Col>
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">
                送水量 <span class="text-red-500">*</span>
              </div>
              <InputNumber
                v-model:value="waterDelivered"
                placeholder="请输入送水量"
                :min="0"
                :precision="0"
                style="width: 100%"
                size="large"
                addon-after="桶"
              />
            </Col>
          </Row>

          <Row :gutter="[16, 16]">
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">回收空桶</div>
              <InputNumber
                v-model:value="bucketsReturned"
                placeholder="请输入回收空桶数"
                :min="0"
                :precision="0"
                style="width: 100%"
                size="large"
                addon-after="桶"
              />
            </Col>
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">目前欠空桶</div>
              <div
                class="flex items-center h-10 px-3 rounded border border-gray-200 bg-gray-50 dark:bg-gray-800 dark:border-gray-700"
              >
                <span
                  class="text-base font-semibold"
                  :class="currentOwedBuckets > 0 ? 'text-orange-600' : 'text-gray-700'"
                >
                  {{ currentOwedBuckets }}
                </span>
                <span class="ml-1 text-sm text-gray-500">桶</span>
              </div>
            </Col>
          </Row>

          <Row :gutter="[16, 16]">
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">存水量</div>
              <InputNumber
                v-model:value="storageAmount"
                placeholder="请输入存水量"
                :min="0"
                :precision="0"
                style="width: 100%"
                size="large"
                addon-after="桶"
              />
            </Col>
            <Col :span="12">
              <div class="mb-1.5 text-sm font-medium">备注</div>
              <Textarea
                v-model:value="remark"
                placeholder="请输入备注信息"
                :rows="1"
                size="large"
              />
            </Col>
          </Row>

          <!-- 提交按钮 -->
          <div class="pt-4">
            <Button
              type="primary"
              size="large"
              block
              :loading="submitting"
              :disabled="!currentCustomer"
              @click="handleSubmit"
            >
              确定出单
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </Page>
</template>
