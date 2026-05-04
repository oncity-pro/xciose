/**
 * 客户管理 API
 * 与 Django 后端的客户接口对接
 */

import { requestClient } from './request';

// ==================== 常量定义 ====================

/**
 * 客户类型选项
 */
export const CUSTOMER_TYPE_OPTIONS = [
  { label: '套餐客户', value: 'vip' },
  { label: '普通客户', value: 'normal' },
  { label: '自提客户', value: 'pickup' },
  { label: '已注销', value: 'closed' },
  { label: '收款慢', value: 'slow_pay' },
  { label: '黑名单', value: 'blacklist' },
] as const;

// ==================== 类型定义 ====================

export interface Customer {
  customer_type?:
    | 'normal'
    | 'pickup'
    | 'vip'
    | 'closed'
    | 'slow_pay'
    | 'blacklist';
  customer_type_display?: string;
  id: string;
  name: string;
  brand?: number;
  brandId?: number; // 驼峰命名（供前端使用）
  brand_name?: string;
  open_date: string;
  openDate?: string; // 驼峰命名（供前端使用）
  last_delivery_date?: null | string;
  lastDeliveryDate?: string; // 驼峰命名（供前端使用）
  close_date?: null | string;
  closeDate?: string; // 驼峰命名（供前端使用）
  phone?: string;
  remark?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  // 新增字段：存水量
  storage_amount?: number;
  // 新增字段：欠空桶
  owed_empty_bucket?: number;
  // 新增字段：总用水量
  total_water_usage?: number;
  totalWaterUsage?: number; // 驼峰命名（供前端使用）
  // 新增字段：消费总额
  total_consumption?: number;
  totalConsumption?: number; // 驼峰命名（供前端使用）
  // 新增字段：桶装水价格（自提客户自动减2元）
  price_per_bucket?: number;
  pricePerBucket?: number; // 驼峰命名（供前端使用）
  // 新增字段：VIP优惠方案
  vip_scheme?: '10_1' | '20_3' | '30_5' | '50_10' | null;
  // 新增字段：楼层类型
  floor_type?: 'default' | 'elevator' | 'stair' | 'residential';
  // 新增字段：步梯加收费用
  stair_extra_charge?: number | null;
  // 新增字段：客户来源
  source?: 'wechat' | 'internet' | 'phone';
  // 桶押金显示
  bucket_deposit_display?: string;
}

export interface CustomerListParams {
  keyword?: string;
  customer_id?: string;
  name?: string;
  page?: number;
  pageSize?: number;
}

export interface CustomerCreateData {
  customer_type?:
    | 'normal'
    | 'pickup'
    | 'vip'
    | 'closed'
    | 'slow_pay'
    | 'blacklist';
  id: string;
  name: string;
  brand?: number;
  open_date: string;
  last_delivery_date: string;  // 改为必填
  phone?: string;  // 改为可选
  remark?: string;
  is_active?: boolean;
  // 新增字段：存水量
  storage_amount: number;  // 改为必填
  // 新增字段：欠空桶
  owed_empty_bucket: number;  // 改为必填
  // 新增字段：桶装水价格
  price_per_bucket?: number;
  // 新增字段：VIP优惠方案
  vip_scheme?: '10_1' | '20_3' | '30_5' | '50_10' | null;
  // 新增字段：楼层类型
  floor_type?: 'default' | 'elevator' | 'stair' | 'residential';
  // 新增字段：步梯加收费用
  stair_extra_charge?: number | null;
  // 新增字段：客户来源
  source?: 'wechat' | 'internet' | 'phone';
}

export interface CustomerUpdateData {
  customer_type?:
    | 'normal'
    | 'pickup'
    | 'vip'
    | 'closed'
    | 'slow_pay'
    | 'blacklist';
  name?: string;
  brand?: number;
  open_date?: string;
  last_delivery_date?: null | string;
  phone?: string;
  remark?: string;
  is_active?: boolean;
  // 新增字段：存水量
  storage_amount?: number;
  // 新增字段：欠空桶
  owed_empty_bucket: number;
  // 新增字段：桶装水价格
  price_per_bucket?: number;
  // 新增字段：VIP优惠方案
  vip_scheme?: '10_1' | '20_3' | '30_5' | '50_10' | null;
  // 新增字段：楼层类型
  floor_type?: 'default' | 'elevator' | 'stair' | 'residential';
  // 新增字段：步梯加收费用
  stair_extra_charge?: number | null;
  // 新增字段：客户来源
  source?: 'wechat' | 'internet' | 'phone';
}

// ==================== 统计数据类型 ====================

export interface CustomerStats {
  total: number;
  vipCount: number;
  normalCount: number;
  pickupCount: number;
  newThisMonth: number;
  lastMonthNew: number;
  closedThisMonth: number;
  lastMonthClosed: number;
}

// ==================== API 函数 ====================

/**
 * 获取客户统计（全局统计，不受搜索影响）
 */
export async function getCustomerStatsApi(): Promise<CustomerStats> {
  return requestClient.get<CustomerStats>('/v1/customers/stats');
}

/**
 * 获取客户列表
 * @param params 查询参数(支持 keyword 搜索)
 */
export async function getCustomerListApi(
  params?: CustomerListParams,
): Promise<Customer[]> {
  return requestClient.get<Customer[]>('/v1/customers/all', { params });
}

/**
 * 获取所有客户(包括搜索)
 * @param params 查询参数
 */
export async function getAllCustomersApi(
  params?: CustomerListParams,
): Promise<Customer[]> {
  return requestClient.get<Customer[]>('/v1/customers/all', { params });
}

/**
 * 获取客户详情
 * @param id 客户编号
 */
export async function getCustomerDetailApi(id: string): Promise<Customer> {
  return requestClient.get<Customer>(`/v1/customers/${id}`);
}

/**
 * 创建客户
 * @param data 客户数据
 */
export async function createCustomerApi(
  data: CustomerCreateData,
): Promise<Customer> {
  return requestClient.post<Customer>('/v1/customers/all', data);
}

/**
 * 更新客户(完整更新)
 * @param id 客户编号
 * @param data 客户数据
 */
export async function updateCustomerApi(
  id: string,
  data: CustomerUpdateData,
): Promise<Customer> {
  return requestClient.put<Customer>(`/v1/customers/${id}`, data);
}

/**
 * 更新客户(部分更新)
 * @param id 客户编号
 * @param data 客户数据
 */
export async function patchCustomerApi(
  id: string,
  data: Partial<CustomerUpdateData>,
): Promise<Customer> {
  // Vben RequestClient 可能不支持 patch，使用 put 替代
  return requestClient.put<Customer>(`/v1/customers/${id}`, data);
}

/**
 * 删除客户
 * @param id 客户编号
 */
export async function deleteCustomerApi(id: string): Promise<void> {
  return requestClient.delete(`/v1/customers/${id}`);
}

/**
 * 获取下一个可用客户编号
 */
export async function getNextCustomerIdApi(): Promise<string> {
  const res = await requestClient.get<{ nextId: string }>('/v1/customers/next-id');
  return res.nextId;
}

/**
 * 检查客户编号是否已存在
 * @param id 客户编号
 */
export async function checkCustomerIdApi(id: string): Promise<boolean> {
  const res = await requestClient.get<{ exists: boolean }>('/v1/customers/check-id', {
    params: { id },
  });
  return res.exists;
}