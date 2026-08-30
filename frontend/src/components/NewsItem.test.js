import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const pushSpy = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushSpy }),
}))

import NewsItem from './NewsItem.vue'

const news = {
  id: 7,
  title: '测试标题',
  description: '测试简介',
  author: '测试作者',
  publishTime: '2026-08-30 10:00',
  views: 42,
  image: 'http://img.example/x.png',
}

describe('NewsItem 组件', () => {
  beforeEach(() => {
    pushSpy.mockClear()
  })

  it('渲染标题、作者与阅读数', () => {
    const wrapper = mount(NewsItem, { props: { news } })
    expect(wrapper.find('.news-title').text()).toBe('测试标题')
    expect(wrapper.text()).toContain('测试作者')
    expect(wrapper.text()).toContain('42 阅读')
    expect(wrapper.find('img').attributes('alt')).toBe('测试标题')
  })

  it('点击卡片跳转对应新闻详情', async () => {
    const wrapper = mount(NewsItem, { props: { news } })
    await wrapper.find('.news-item').trigger('click')
    expect(pushSpy).toHaveBeenCalledWith('/news/detail/7')
  })
})
