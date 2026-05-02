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

// 品牌类型选项
const brandTypeOptions = [
  { label: '桶装水', value: 'bucket' },
  { label: '支装水', value: 'bottle' },
  { label: '一次性桶装水', value: 'disposable' },
];

// 规格选项
const bucketSpecOptions = [
  { label: '18.9L', value: '18.9L' },
  { label: '19L', value: '19L' },
  { label: '16.8L', value: '16.8L' },
  { label: '其它', value: '其它' },
];

const bottleSpecOptions = [
  { label: '380mL', value: '380mL' },
  { label: '550mL', value: '550mL' },
  { label: '1.5L', value: '1.5L' },
  { label: '其它', value: '其它' },
];

const disposableSpecOptions = [
  { label: '12.8L', value: '12.8L' },
  { label: '18.9L', value: '18.9L' },
  { label: '其它', value: '其它' },
];

function getSpecOptions(brandType: string) {
  switch (brandType) {
    case 'bucket':
      return bucketSpecOptions;
    case 'bottle':
      return bottleSpecOptions;
    case 'disposable':
      return disposableSpecOptions;
    default:
      return bucketSpecOptions;
  }
}

function getDefaultSpec(brandType: string) {
  switch (brandType) {
    case 'bucket':
      return '18.9L';
    case 'bottle':
      return '380mL';
    case 'disposable':
      return '12.8L';
    default:
      return '18.9L';
  }
}

// 解析规格值：如果在预定义选项中则直接使用，否则归为"其它"
function resolveSpecValues(
  specification: string | undefined,
  brandType: string,
) {
  const options = getSpecOptions(brandType).map((o) => o.value);
  if (specification && options.includes(specification)) {
    return { specification, specification_custom: '' };
  }
  return {
    specification: '其它',
    specification_custom: specification || '',
  };
}

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
      component: 'Select',
      componentProps: {
        placeholder: '请选择品牌类型',
        options: brandTypeOptions,
        dropdownMatchSelectWidth: false,
        onChange: (value: string) => {
          // 品牌类型变化时更新规格选项和默认值
          const newOptions = getSpecOptions(value);
          formApi.updateSchema([
            {
              componentProps: { options: newOptions },
              fieldName: 'specification',
            },
          ]);
          formApi.setValues({
            specification: getDefaultSpec(value),
            specification_custom: '',
          });
          // 自定义规格输入框通过 dependencies.show 自动控制显示/隐藏
        },
      },
      fieldName: 'brand_type',
      label: '品牌类型',
      rules: 'required',
    },
    {
      component: 'Select',
      componentProps: {
        placeholder: '请选择规格',
        options: bucketSpecOptions,
        onChange: (value: string) => {
          // 选择"其它"时显示自定义输入框
          const isCustom = value === '其它';
          // 自定义规格输入框通过 dependencies.show 自动控制显示/隐藏
          if (!isCustom) {
            formApi.setValues({ specification_custom: '' });
          }
        },
      },
      fieldName: 'specification',
      label: '规格',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: '请输入自定义规格',
        maxlength: 50,
      },
      dependencies: {
        show(values) {
          return values.specification === '其它';
        },
        triggerFields: ['specification'],
      },
      fieldName: 'specification_custom',
      label: '自定义规格',
      rules: 'required',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入进货价',
        min: 0,
        precision: 2,
        style: { width: '100%' },
      },
      fieldName: 'purchase_price',
      label: '进货价（元）',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入零售价',
        min: 0,
        precision: 2,
        style: { width: '100%' },
      },
      fieldName: 'price_per_bucket',
      label: '零售价（元）',
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
        // 处理规格值：选择"其它"时使用自定义输入框的值
        const specValue =
          values.specification === '其它'
            ? values.specification_custom
            : values.specification;

        const payload: Record<string, any> = {
          name: values.name,
          brand_type: values.brand_type || 'bucket',
          specification: specValue || getDefaultSpec(values.brand_type),
          // 价格为空时默认传 0，避免后端验证失败
          purchase_price: values.purchase_price ?? 0,
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

      if (data && data.id) {
        // 编辑模式：解析规格值，处理"其它"选项
        const brandType = data.brand_type || 'bucket';
        const specOptions = getSpecOptions(brandType);
        const { specification, specification_custom } = resolveSpecValues(
          data.specification,
          brandType,
        );

        // 先更新规格选项
        (formApi as any).updateSchema([
          {
            componentProps: { options: specOptions },
            fieldName: 'specification',
          },
        ]);

        formApi.setValues({
          ...data,
          specification,
          specification_custom,
        });
      } else {
        // 新增模式：根据默认品牌类型设置规格选项和默认值
        const defaultType = data?.brand_type || 'bucket';
        const defaultSpec = getDefaultSpec(defaultType);
        (formApi as any).updateSchema([
          {
            componentProps: { options: getSpecOptions(defaultType) },
            fieldName: 'specification',
          },
        ]);
        formApi.resetForm();
        formApi.setValues({
          brand_type: defaultType,
          specification: defaultSpec,
        });
      }
    }
  },
});
</script>

<template>
  <Modal :title="getTitle" width="520">
    <Form class="mx-4" />
  </Modal>
</template>
