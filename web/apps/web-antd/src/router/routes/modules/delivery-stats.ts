import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'DeliveryStats',
    path: '/delivery-stats',
    component: () => import('#/views/delivery-stats/index.vue'),
    meta: {
      icon: 'lucide:bar-chart-3',
      order: 16,
      title: '送水统计',
    },
  },
];

export default routes;
