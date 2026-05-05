<script lang="ts" setup>

import type { 
  Customer, 
  CustomerCreateData,
  CustomerUpdateData,
} from '#/api/customer';
import type { WaterBrand } from '#/api/water-brand';

import { computed, ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';
import { useDebounceFn } from '@vueuse/core';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import {
  checkCustomerIdApi,
  createCustomerApi,
  CUSTOMER_TYPE_OPTIONS,
  getNextCustomerIdApi,
  updateCustomerApi,
} from '#/api/customer';
import { getBucketDepositConfigApi } from '#/api/settings';
import {
  getWaterBrandListApi,
} from '#/api/water-brand';
import { Pencil, UserPlus } from 'lucide-vue-next';

// 定义 props 接收客户数据（作为备用方案）
const props = defineProps<{
  customerData?: Customer | null;
}>();

const emit = defineEmits<{ success: [] }>();

// 每桶押金金额（从全局配置获取）
const depositPerBucket = ref<number>(30);

// 品牌单价映射（用于自动计算桶装水价格）
const brandPriceMap = ref<Map<number, number>>(new Map());

// 怡宝品牌ID（加载品牌列表后动态获取）
let defaultBrandId: number | null = null;

// 根据当前品牌和客户类型自动计算桶装水价格
async function updatePricePerBucket() {
  const values = await formApi.getValues();
  const brandId = values?.brand;
  const customerType = values?.customer_type;
  if (!brandId || !brandPriceMap.value.has(brandId)) return;
  const basePrice = brandPriceMap.value.get(brandId) || 0;
  const finalPrice = customerType === 'pickup' ? Math.max(0, basePrice - 2) : basePrice;
  formApi.setValues({ price_per_bucket: finalPrice });
}

// 是否为编辑模式
const isEdit = computed(() => {
  return props.customerData && Object.keys(props.customerData).length > 0;
});

// 编号检查中状态
const idChecking = ref(false);

// 防抖检查客户编号是否已存在
const debouncedCheckId = useDebounceFn(async (id: string) => {
  if (!id || isEdit.value) return;
  idChecking.value = true;
  try {
    const exists = await checkCustomerIdApi(id);
    if (exists) {
      formApi.setFieldError('id', '客户编号已存在，请重新输入');
    } else {
      formApi.setFieldError('id', undefined);
    }
  } catch (error) {
    console.error('检查客户编号失败:', error);
  } finally {
    idChecking.value = false;
  }
}, 300);

// 品牌列表 - 现在由ApiSelect组件内部处理
// const brandOptions = ref<Array<{ label: string; value: number }>>([]);
// const allBrands = ref<WaterBrand[]>([]); // 存储完整品牌信息

// 加载品牌选项 - 现在由ApiSelect组件内部处理
// async function loadBrandOptions() {
//   try {
//     const brands = await getWaterBrandListApi();
//     console.log('加载的品牌数据:', brands); // 添加调试信息
//     allBrands.value = brands;
//     brandOptions.value = brands.map((brand: WaterBrand) => ({
//       label: brand.name,
//       value: brand.id,
//     }));
//     console.log('转换后的品牌选项:', brandOptions.value); // 添加调试信息
//   } catch (error) {
//     console.error('加载品牌选项失败:', error);
//   }
// }

// 表单配置
const [Form, formApi] = useVbenForm({
  schema: [
    {
      component: 'Input',
      componentProps: {
        placeholder: '请输入客户编号',
        onBlur: (e: any) => {
          const val = e?.target?.value || '';
          const num = val.replace(/\D/g, '');
          if (num) {
            const cleanId = String(Number(num)).padStart(3, '0');
            formApi.setValues({ id: cleanId });
            debouncedCheckId(cleanId);
          }
        },
        onFocus: (e: any) => {
          const val = e?.target?.value || '';
          if (val && !isEdit.value) {
            debouncedCheckId(val);
          }
        },
        onInput: (e: any) => {
          const val = e?.target?.value || '';
          const num = val.replace(/\D/g, '');
          if (num) {
            debouncedCheckId(String(Number(num)));
          }
        },
      },
      fieldName: 'id',
      label: '客户编号',
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: '请输入联系电话',
      },
      fieldName: 'phone',
      label: '联系电话',
      // 移除必填规则
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: '请输入姓名或地址',
      },
      fieldName: 'name',
      label: '姓名地址',
      rules: 'required',
      formItemClass: 'col-span-2',
    },
    {
      component: 'Select',
      componentProps: {
        placeholder: '请选择客户类型',
        options: CUSTOMER_TYPE_OPTIONS,
        onChange: () => updatePricePerBucket(),
        popupMatchSelectWidth: false,
        dropdownStyle: { minWidth: '160px' },
      },
      fieldName: 'customer_type',
      label: '客户类型',
      defaultValue: 'normal',
    },
    {
      component: 'Select',
      componentProps: {
        placeholder: '请选择客户来源',
        options: [
          { label: '微信', value: 'wechat' },
          { label: '互联网', value: 'internet' },
          { label: '电话', value: 'phone' },
        ],
      },
      fieldName: 'source',
      label: '客户来源',
      defaultValue: 'wechat',
    },
    {
      component: 'Select',
      componentProps: {
        placeholder: '请选择楼层',
        options: [
          { label: '默认', value: 'default' },
          { label: '电梯', value: 'elevator' },
          { label: '步梯', value: 'stair' },
          { label: '住宅', value: 'residential' },
        ],
      },
      fieldName: 'floor_type',
      label: '楼层',
      defaultValue: 'default',
    },
    {
      component: 'RadioGroup',
      componentProps: {
        options: [
          { label: '加收桶/2元', value: '2' },
          { label: '加收桶/3元', value: '3' },
          { label: '其它', value: 'other' },
        ],
      },
      dependencies: {
        show(values) {
          return values.floor_type === 'stair';
        },
        triggerFields: ['floor_type'],
      },
      fieldName: 'stair_extra_charge_type',
      label: '步梯加收',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入加收金额',
        min: 0,
        precision: 2,
        addonAfter: '元/桶',
      },
      dependencies: {
        show(values) {
          return values.floor_type === 'stair' && values.stair_extra_charge_type === 'other';
        },
        triggerFields: ['floor_type', 'stair_extra_charge_type'],
      },
      fieldName: 'stair_extra_charge_custom',
      label: '自定义加收',
    },
    {
      component: 'ApiSelect',
      fieldName: 'brand',
      label: '桶装水品牌',
      componentProps: {
        api: getWaterBrandListApi,
        labelField: 'name',
        valueField: 'id',
        placeholder: '请选择品牌',
        allowClear: true,
        popupMatchSelectWidth: false, // 下拉框不与选择框宽度匹配
        dropdownStyle: { minWidth: '200px' }, // 设置下拉框最小宽度
        onChange: () => updatePricePerBucket(),
      },
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '自动计算或手动输入',
        min: 0,
        precision: 2,
        addonAfter: '元',
      },
      fieldName: 'price_per_bucket',
      label: '桶装水价格',
    },
    {
      component: 'RadioGroup',
      componentProps: {
        options: [
          { label: '10送1', value: '10_1' },
          { label: '20送3', value: '20_3' },
          { label: '30送5', value: '30_5' },
          { label: '50送10', value: '50_10' },
        ],
        onChange: (e: any) => {
          const value = e?.target?.value ?? e;
          if (value && typeof value === 'string') {
            const parts = value.split('_');
            const buy = Number(parts[0] || 0);
            const gift = Number(parts[1] || 0);
            formApi.setValues({ storage_amount: buy + gift });
          }
        },
      },
      dependencies: {
        show(values) {
          return values.customer_type === 'vip';
        },
        triggerFields: ['customer_type'],
      },
      fieldName: 'vip_scheme',
      label: '优惠方案',
      formItemClass: 'col-span-2',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入存水量',
        min: 0,
      },
      fieldName: 'storage_amount',
      label: '存水量',
      rules: 'required',  // 设置为必填
      defaultValue: 0,  // 设置默认值为0
      formItemClass: 'col-span-2',
    },
    {
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入押桶数',
        min: 0,
        onChange: (value: number | null) => {
          const owed = value || 0;
          formApi.setValues({
            empty_bucket_deposit: Number((owed * depositPerBucket.value).toFixed(2)),
          });
        },
      },
      fieldName: 'owed_empty_bucket',
      label: '押桶数',
      rules: 'required',  // 设置为必填
    },
    {
      component: 'InputNumber',
      componentProps: {
        disabled: true,
        placeholder: '自动计算',
        addonAfter: '元',
      },
      fieldName: 'empty_bucket_deposit',
      label: '合计',
    },
    {
      component: 'DatePicker',
      componentProps: {
        placeholder: '请选择开户日期',
        format: 'YYYY-MM-DD',
        valueFormat: 'YYYY-MM-DD',
      },
      fieldName: 'open_date',
      label: '开户日期',
      // 移除必填规则，因为将设置默认值
    },
    {
      component: 'DatePicker',
      componentProps: {
        placeholder: '请选择送水日期',
        format: 'YYYY-MM-DD',
        valueFormat: 'YYYY-MM-DD',
        allowClear: true,
      },
      fieldName: 'last_delivery_date',
      label: '送水日期',
      rules: 'required',  // 设置为必填
    },
    // 删除详细地址字段
    {
      component: 'Textarea',
      componentProps: {
        placeholder: '请输入备注信息',
        rows: 2,
      },
      fieldName: 'remark',
      label: '备注',
      formItemClass: 'col-span-2',
    },
  ],
  layout: 'horizontal',
  wrapperClass: 'grid-cols-2',
  showDefaultActions: false,  // 隐藏表单自带的提交和重置按钮
  commonConfig: {
    colon: true,
  },
});

// 弹窗配置
const [Modal, modalApi] = useVbenModal({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    // 禁用确认按钮，防止重复提交
    modalApi.setState({ confirmLoading: true });

    const values = await formApi.getValues();

    // 如果客户类型不是VIP，清空优惠方案
    if (values.customer_type !== 'vip') {
      values.vip_scheme = undefined;
    }

    // 处理步梯加收费用
    if (values.floor_type === 'stair' && values.stair_extra_charge_type) {
      if (values.stair_extra_charge_type === 'other') {
        values.stair_extra_charge = values.stair_extra_charge_custom;
      } else {
        values.stair_extra_charge = Number(values.stair_extra_charge_type);
      }
    } else {
      values.stair_extra_charge = null;
    }
    delete values.stair_extra_charge_type;
    delete values.stair_extra_charge_custom;
    
    // 只使用 props 传递的数据
    const customerData = props.customerData;
    const isEdit = !!(customerData && Object.keys(customerData).length > 0);
    
    try {
      if (isEdit) {
        // 编辑模式：剔除 id，防止尝试修改主键
        if (customerData) {
          const { id: _id, ...updateValues } = values;
          await updateCustomerApi(customerData.id, updateValues as CustomerUpdateData);
          message.success('更新成功');
        }
      } else {
        // 新增模式
        await createCustomerApi(values as CustomerCreateData);
        message.success('创建成功');
      }
      
      modalApi.close();
      emit('success');
    } catch (error: any) {
      console.error('保存失败:', error);
      console.error('错误对象详情:', { 
        errorInstance: error.constructor.name, 
        hasResponse: !!error.response, 
        responseStatus: error.response?.status,
        responseData: error.response?.data,
        hasRequest: !!error.request,
        message: error.message
      });
      
      // 检查错误响应结构并显示相应消息
      // RequestClient 在 HTTP 错误时直接抛出 error.response.data，
      // 因此 error 本身可能就是响应体，需要兼容处理
      const isRawResponseData =
        error &&
        typeof error === 'object' &&
        !error.response &&
        !error.request &&
        Object.keys(error).length > 0;

      if (error.response || isRawResponseData) {
        const responseData = error.response?.data ?? error;
        
        // 检查是否包含 detail 字段（一般错误）
        if (responseData && typeof responseData === 'object' && responseData.detail) {
          message.error(responseData.detail);
        } 
        // 处理字段验证错误对象，例如：{'id': [ErrorDetail], 'customer_number': [ErrorDetail]}
        else if (Array.isArray(responseData)) {
          // 处理数组形式的错误
          responseData.forEach(_error => {
            const errorMessage = typeof _error === 'object' 
              ? (_error.string || _error.message || _error.msg || _error.detail || String(_error))
              : String(_error);
            message.error(errorMessage);
          });
        }
        else if (responseData && typeof responseData === 'object') {
          let hasFieldErrors = false;
          
          // 遍历所有可能的字段错误
          for (const [field, messages] of Object.entries(responseData)) {
            // 检查是否是非字段错误（如non_field_errors）
            if (Array.isArray(messages) && messages.length > 0) {
              hasFieldErrors = true;  // 仅在数组有内容时才标记有字段错误
              
              // 处理ErrorDetail对象数组
              for (const msg of messages) {
                // 尝试不同的可能属性名称，合并声明和赋值
                const errorMessage = typeof msg === 'object' ? (msg.string || msg.message || msg.msg || msg.detail || String(msg)) : String(msg);
                
                // 针对唯一性错误提供更友好的提示
                const isUniqueError = errorMessage.includes('已存在') || errorMessage.toLowerCase().includes('unique');
                const displayMessage = isUniqueError && field === 'id'
                  ? '客户编号已存在，请重新输入'
                  : `${field}: ${errorMessage}`;
                
                message.error(displayMessage);
              }
            } else if (typeof messages === 'string') {
              // 处理直接的字符串错误
              hasFieldErrors = true;
              message.error(`${field}: ${messages}`);
            } else if (typeof messages === 'object' && messages !== null) {
              // 处理嵌套对象
              hasFieldErrors = true;
              message.error(`${field}: ${JSON.stringify(messages)}`);
            }
          }
          
          // 如果没有处理过任何字段错误，显示通用消息
          if (!hasFieldErrors) {
            message.error('数据验证失败');
          }
        } 
        // 如果响应数据是字符串
        else if (typeof responseData === 'string') {
          message.error(responseData);
        } 
        // 其他情况
        else {
          message.error(`数据验证失败：${JSON.stringify(responseData)}`);
        }
      } else {
        // 网络错误或请求配置错误
        if (error.request) {
          // 请求已发出但没有收到响应（网络错误）
          message.error('网络连接错误或服务器无响应');
        } else {
          // 其他错误（如请求配置错误）
          message.error(`请求配置错误: ${error.message}`);
        }
      }
    } finally {
      // 确保无论成功或失败都要重新启用确认按钮
      modalApi.setState({ confirmLoading: false });
    }
  },
  async onOpenChange(isOpen: boolean) {
    if (isOpen) {
      // 优先使用 props 传递的数据
      const data = props.customerData;
      console.warn('=== 表单组件 onOpenChange ===');
      console.warn('onOpenChange - props.customerData:', props.customerData);
      console.warn('onOpenChange - data:', data);
      console.warn('onOpenChange - data 是否为空对象:', data && Object.keys(data).length === 0);
      console.warn('onOpenChange - data 所有键名:', data ? Object.keys(data) : []);
      console.warn('===========================');

      // 同时加载空桶押金配置和品牌列表
      try {
        const [config, brands] = await Promise.all([
          getBucketDepositConfigApi(),
          getWaterBrandListApi(),
        ]);
        depositPerBucket.value = config.amount_per_bucket;
        brands.forEach((brand: WaterBrand) => {
          brandPriceMap.value.set(brand.id, brand.price_per_bucket || 0);
          if (brand.name === '怡宝') {
            defaultBrandId = brand.id;
          }
        });
      } catch (error) {
        console.error('加载配置失败:', error);
      }
      
      if (data && Object.keys(data).length > 0) {
        // 编辑模式：填充表单数据
        console.warn('进入编辑模式，准备设置表单值');
        await formApi.setValues(data);
        // 计算空桶押金
        const owed = data.owed_empty_bucket || 0;
        await formApi.setValues({
          empty_bucket_deposit: Number((owed * depositPerBucket.value).toFixed(2)),
        });
        // 处理步梯加收费用的回显
        if (data.floor_type === 'stair' && data.stair_extra_charge) {
          const charge = Number(data.stair_extra_charge);
          if (charge === 2) {
            await formApi.setValues({ stair_extra_charge_type: '2' });
          } else if (charge === 3) {
            await formApi.setValues({ stair_extra_charge_type: '3' });
          } else {
            await formApi.setValues({
              stair_extra_charge_type: 'other',
              stair_extra_charge_custom: charge,
            });
          }
        }
        // 标题通过插槽设置
      } else {
        // 新增模式：重置表单并设置默认值
        console.warn('进入新增模式，重置表单');
        await formApi.resetForm();

        // 自动获取并填入下一个可用客户编号
        try {
          const nextId = await getNextCustomerIdApi();
          const formattedNextId = /^\d+$/.test(String(nextId))
            ? String(Number(nextId)).padStart(3, '0')
            : String(nextId);
          await formApi.setValues({ id: formattedNextId });
        } catch (error) {
          console.error('获取下一个客户编号失败:', error);
        }

        // 设置默认值（使用本地时间避免 UTC 偏移导致日期差一天）
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        const today = `${y}-${m}-${d}`;
        await formApi.setValues({
          open_date: today, // 设置开户日期为今天
          last_delivery_date: today, // 设置送水日期为今天
          owed_empty_bucket: 2, // 押桶数默认为2
          empty_bucket_deposit: Number((2 * depositPerBucket.value).toFixed(2)),

          // 设置怡宝为默认品牌
          brand: defaultBrandId,
        });
        
        // 根据默认品牌自动计算桶装水价格
        if (defaultBrandId && brandPriceMap.value.has(defaultBrandId)) {
          const basePrice = brandPriceMap.value.get(defaultBrandId) || 0;
          await formApi.setValues({ price_per_bucket: basePrice });
        }
        
        // 标题通过插槽设置
      }
    }
  },
});
</script>

<template>
  <Modal :footer="true">
    <template #title>
      <span class="flex items-center gap-2">
        <UserPlus v-if="!isEdit" class="size-5" />
        <Pencil v-else class="size-5" />
        {{ isEdit ? '编辑客户' : '新增客户' }}
      </span>
    </template>
    <Form />
  </Modal>
</template>