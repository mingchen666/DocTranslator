{
  path: '/system',
  component: Layout,
  meta: { title: '系统设置', icon: 'Setting' },
  children: [
    {
      path: 'announcement',
      component: () => import('@/views/system/announcement.vue'),
      name: 'Announcement',
      meta: { title: '公告设置' }
    }
  ]
} 