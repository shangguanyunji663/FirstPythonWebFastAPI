import { describe, expect, it } from 'vitest'
import { CATEGORY_NAME_KEY_MAP } from './categories'
import zhCN from '../i18n/locales/zh-CN'
import enUS from '../i18n/locales/en-US'

describe('分类名 → i18n key 映射', () => {
  it('映射里的每个 key 在中英文语言包 home.categories 下都存在', () => {
    for (const key of Object.values(CATEGORY_NAME_KEY_MAP)) {
      expect(zhCN.home.categories[key], `zh-CN 缺少 ${key}`).toBeTruthy()
      expect(enUS.home.categories[key], `en-US 缺少 ${key}`).toBeTruthy()
    }
  })

  it('中英文语言包收录的分类完全一致', () => {
    expect(Object.keys(zhCN.home.categories).sort())
      .toEqual(Object.keys(enUS.home.categories).sort())
  })

  it('核心分类都在映射表中', () => {
    expect(CATEGORY_NAME_KEY_MAP['头条']).toBe('headline')
    expect(CATEGORY_NAME_KEY_MAP['财经']).toBe('finance')
    expect(CATEGORY_NAME_KEY_MAP['更多']).toBe('more')
  })
})
