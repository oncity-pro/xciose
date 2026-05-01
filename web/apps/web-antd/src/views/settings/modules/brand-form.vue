<script lang="ts" setup>
import { computed, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { createWaterBrandApi, updateWaterBrandApi, type WaterBrand } from '#/api/water-brand';

const emit = defineEmits(['success']);

const formData = ref<null | WaterBrand>(null);

const getTitle = computed(() => {
  return formData.value?.id ? '编辑品牌' : '新增品牌';
});

// 表单配置
const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: [
    {
      component: 'Input',
      componentProps: {
        placeholder: '请输入品牌名称',
        maxlength: 50,
      },
      fieldName: 'name',
      label: '品牌名称',
      rules: 'required',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入每桶单价',
        min: 0,
        precision: 2,
        style: { width: '100%' },
      },
      fieldName: 'price_per_bucket',
      label: '每桶单价（元）',
    },
  ],
  showDefaultActions: false,
});

// 弹窗配置
const [Modal, modalApi] = useVbenModal({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      modalApi.lock();
      const values = await formApi.getValues();
      
      try {
        const payload: Record<string, any> = {
          name: values.name,
          // 单价为空时默认传 0，避免后端验证失败
          price_per_bucket: values.price_per_bucket ?? 0,
        };
        
        if (formData.value?.id) {
          // 编辑模式
          await updateWaterBrandApi(formData.value.id, payload);
          message.success('修改成功');
        } else {
          // 新增模式
          await createWaterBrandApi(payload);
          message.success('新增成功');
        }
        modalApi.close();
        emit('success');
      } catch (error: any) {
        console.error('操作失败:', error);
        // 显示后端返回的错误信息
        const errorData = error.response?.data;
        let errorMsg: string;
        if (errorData?.detail) {
          errorMsg = errorData.detail;
        } else if (errorData && typeof errorData === 'object') {
          // 提取第一个验证错误（可能是数组或字符串）
          const firstError = Object.values(errorData).flat()[0];
          errorMsg = typeof firstError === 'string' ? firstError : '操作失败';
        } else {
          errorMsg = '操作失败';
        }
        message.error(errorMsg);
      } finally {
        modalApi.lock(false);
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = modalApi.getData<WaterBrand>();
      formData.value = data || null;
      
      if (data) {
        formApi.setValues(data);
      } else {
        formApi.resetForm();
      }
    }
  },
});
</script>

<template>
  <Modal :title="getTitle">
    <Form class="mx-4" />
  </Modal>
</template>
