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
}

/**
 * 获取客户的送水记录列表
 * @param customerId 客户编号
 */
export async function getDeliveryRecordListApi(
  customerId: string,
): Promise<DeliveryRecord[]> {
  const res = await requestClient.get<{ code: number; data: DeliveryRecord[] }>(
    `/v1/customers/${customerId}/delivery-records`,
  );
  return res.data || [];
}

/**
 * 创建送水记录（商品出单）
 * @param data 送水记录数据
 */
export async function createDeliveryRecordApi(
  data: DeliveryRecordCreateData,
): Promise<DeliveryRecord> {
  const res = await requestClient.post<{ code: number; data: DeliveryRecord }>(
    '/v1/delivery-records',
    data,
  );
  return res.data;
}
