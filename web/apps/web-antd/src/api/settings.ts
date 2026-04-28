/**
 * 基础设置 API
 * 与 Django 后端的配置接口对接
 */

import { requestClient } from './request';

// ==================== 类型定义 ====================

export interface BucketDepositConfig {
  id: number;
  amount_per_bucket: number;
  updated_at: string;
}

// ==================== API 函数 ====================

/**
 * 获取空桶押金配置
 */
export async function getBucketDepositConfigApi(): Promise<BucketDepositConfig> {
  return requestClient.get<BucketDepositConfig>('/v1/bucket-deposit-config');
}

/**
 * 更新空桶押金配置
 * @param data 配置数据
 */
export async function updateBucketDepositConfigApi(
  data: Partial<BucketDepositConfig>,
): Promise<BucketDepositConfig> {
  return requestClient.put<BucketDepositConfig>('/v1/bucket-deposit-config', data);
}
