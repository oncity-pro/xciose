<script lang="ts" setup>
import { ArrowDown, ArrowUp } from 'lucide-vue-next';
import { VbenCountToAnimator } from '@vben/common-ui';

interface Props {
  total: number;
  newThisMonth: number;
  closedThisMonth: number;
}

const props = withDefaults(defineProps<Props>(), {
  total: 0,
  newThisMonth: 0,
  closedThisMonth: 0,
});
</script>

<template>
  <div class="card-box w-full rounded-lg border border-border bg-card">
    <!-- CardHeader -->
    <div class="flex flex-col space-y-1 px-6 pt-4 pb-0">
      <div class="text-lg font-semibold leading-none tracking-tight">总客户数</div>
    </div>

    <!-- CardContent -->
    <div class="flex items-center justify-between px-6 py-4">
      <VbenCountToAnimator :end-val="props.total" :start-val="1" class="text-lg font-bold" prefix="" suffix="位" />
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="size-7 shrink-0"
      >
        <rect width="20" height="14" x="2" y="5" rx="2" />
        <line x1="2" x2="22" y1="10" y2="10" />
      </svg>
    </div>
    
    <!-- 分隔线 -->
    <div class="mx-6">
      <div class="border-t"></div>
    </div>
    
    <!-- CardFooter -->
    <div class="flex items-center justify-between px-6 py-4">
      <div class="flex items-center gap-2">
        <span class="text-xs">本月新增：</span>
        <VbenCountToAnimator :end-val="props.newThisMonth" :start-val="1" class="text-base font-semibold" prefix="" suffix="位" />
        <ArrowUp class="size-3.5 text-green-500" />
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs">本月注销：</span>
        <VbenCountToAnimator :end-val="props.closedThisMonth" :start-val="1" class="text-base font-semibold" prefix="" suffix="位" />
        <ArrowDown class="size-3.5 text-red-500" />
      </div>
    </div>
  </div>
</template>
