<template>
  <div class="category">
    <van-nav-bar 
      :title="$t('common.allCategories')" 
      :left-text="$t('common.back')"
      left-arrow
      @click-left="onClickLeft"
      fixed 
    />
    
    <div class="category-container">
      <van-grid v-if="newsStore.categories.length" :column-num="3" :border="false">
        <van-grid-item
          v-for="category in newsStore.categories"
          :key="category.id"
          :text="getCategoryTranslation(category.name)"
          icon="newspaper-o"
          @click="goToCategoryNews(category.id)"
        />
      </van-grid>

      <van-empty
        v-else-if="!newsStore.categoriesLoading"
        :description="$t('common.loadFailed')"
      >
        <van-button round type="primary" class="retry-button" @click="loadCategories">
          {{ $t('common.retry') }}
        </van-button>
      </van-empty>
    </div>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { useNewsStore } from '../store/modules/news'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import TabBar from '../components/TabBar.vue'
import { onMounted } from 'vue'
import { CATEGORY_NAME_KEY_MAP } from '../constants/categories'

const newsStore = useNewsStore()
const router = useRouter()
const { t } = useI18n()

// 加载分类（进入本页时 store 可能还没有数据）
const loadCategories = () => {
  newsStore.getCategories()
}

// 直接进入本页（如刷新落在 /category）时自动拉取
onMounted(() => {
  if (!newsStore.categories.length) {
    loadCategories()
  }
})

// 返回上一页
const onClickLeft = () => {
  router.back()
}

// 跳转到对应分类的新闻列表
const goToCategoryNews = (categoryId) => {
  // 先切换分类
  newsStore.changeCategory(categoryId)
  
  // 使用路由参数传递分类ID
  router.push({
    path: '/home',
    query: { categoryId: categoryId }
  })
}

// 获取分类名称的翻译（映射统一在 constants/categories.js 维护）
const getCategoryTranslation = (categoryName) => {
  const key = CATEGORY_NAME_KEY_MAP[categoryName];
  return key ? t(`home.categories.${key}`) : categoryName;
}
</script>

<style scoped>
.category {
  padding-top: 46px;
  padding-bottom: 50px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.category-container {
  padding: 16px;
  background-color: #fff;
  margin-top: 12px;
  border-radius: 8px;
}

:deep(.van-grid-item__content) {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 20px 0;
}

:deep(.van-grid-item__icon) {
  font-size: 28px;
  color: #1989fa;
}

:deep(.van-grid-item__text) {
  margin-top: 8px;
  color: #333;
  font-size: 14px;
}

.retry-button {
  margin-top: 12px;
  padding: 0 40px;
}
</style>