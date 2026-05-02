import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'DeliveryOrder',
    path: '/delivery-order',
    component: () => import('#/views/delivery-order/index.vue'),
    meta: {
      icon: 'lucide:clipboard-list',
      order: 15,
      title: '商品出单',
    },
  },
];

export default routes;
