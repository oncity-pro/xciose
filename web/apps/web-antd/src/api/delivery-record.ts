/**
 * 送水记录 API
 */

import { requestClient } from './request';

export interface DeliveryRecord {
  id: number;
  customer: string;
  date: string;
  water_delivered: number;
  buckets_returned: number;
  owed_empty_buckets: number;
  storage_amount: number;
  remark: string;
  created_at?: string;
  updated_at?: string;
}

export interface DeliveryRecordCreateData {
  customer: string;
  date: string;
  water_delivered: number;
  buckets_returned: number;
  owed_empty_buckets?: number;
  storage_amount?: number;
  remark?: string;
  vip_scheme?: string;
}

/**
 * 获取客户的送水记录列表
 * @param customerId 客户编号
 */
export async function getDeliveryRecordListApi(
  customerId: string,
): Promise<DeliveryRecord[]> {
  const res = await requestClient.get<any>(
    `/v1/customers/${customerId}/delivery-records`,
  );
  // 兼容拦截器提取后的直接数据和原始响应
  return Array.isArray(res) ? res : res?.data ?? [];
}

/**
 * 创建送水记录（商品出单）
 * @param data 送水记录数据
 */
export async function createDeliveryRecordApi(
  data: DeliveryRecordCreateData,
): Promise<DeliveryRecord> {
  const res = await requestClient.post<any>('/v1/delivery-records', data);
  // 兼容拦截器提取后的直接数据和原始响应
  return res?.id ? res : res?.data;
}

/**
 * 更新送水记录
 * @param id 记录ID
 * @param data 更新数据
 */
export async function updateDeliveryRecordApi(
  id: number,
  data: Partial<DeliveryRecordCreateData>,
): Promise<DeliveryRecord> {
  const res = await requestClient.put<any>(`/v1/delivery-records/${id}`, data);
  // 兼容拦截器提取后的直接数据和原始响应
  return res?.id ? res : res?.data;
}

/**
 * 删除送水记录
 * @param id 记录ID
 */
export async function deleteDeliveryRecordApi(id: number): Promise<void> {
  await requestClient.delete<any>(`/v1/delivery-records/${id}/delete`);
}
