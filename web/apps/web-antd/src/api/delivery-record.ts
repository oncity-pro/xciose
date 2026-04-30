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
