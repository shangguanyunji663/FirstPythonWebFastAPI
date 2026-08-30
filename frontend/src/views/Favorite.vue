<template>
  <div class="favorite-container">
    <van-nav-bar
      :title="$t('my.myFavorite')"
      :left-text="$t('common.back')"
      left-arrow
      @click-left="onClickLeft"
      :right-text="$t('favorite.clear')"
      @click-right="onClickClear"
      fixed
    />

    <NewsRecordList
      :items="favoriteStore.getFavorites"
      type="favorite"
      :empty-text="$t('favorite.empty')"
      @delete="confirmDelete"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useFavoriteStore } from '../store/modules/favorite';
import { showDialog } from 'vant';
import { useI18n } from 'vue-i18n';
import NewsRecordList from '../components/NewsRecordList.vue';

const router = useRouter();
const favoriteStore = useFavoriteStore();
const { t } = useI18n();

// 返回上一页
const onClickLeft = () => {
  router.back();
};

// 删除单条收藏
const removeFavorite = async (id) => {
  const result = await favoriteStore.removeFavoriteApi(id);
  if (result.success) {
    // API请求成功后，更新本地收藏列表
    favoriteStore.removeFavorite(id);
  }
};

// 确认删除
const confirmDelete = (item) => {
  showDialog({
    title: t('common.tip'),
    message: t('favorite.confirmDelete'),
    showCancelButton: true,
  }).then((action) => {
    if (action === 'confirm') {
      removeFavorite(item.id);
    }
  }).catch(() => {});
};

// 清空收藏
const onClickClear = async () => {
  showDialog({
    title: t('common.tip'),
    message: t('favorite.confirmClear'),
    showCancelButton: true,
  }).then(async (action) => {
    if (action === 'confirm') {
      const result = await favoriteStore.clearFavoritesApi();
      if (!result || !result.success) {
        // 如果API请求失败，回退到本地清空
        // favoriteStore.clearFavorites();
      }
    }
  }).catch(() => {});
};

// 组件挂载时加载收藏数据
onMounted(async () => {
  // 使用API请求获取收藏列表
  try {
    const result = await favoriteStore.getFavoriteListApi();
    if (!result || !result.success) {
      // 如果API请求失败，回退到本地存储
      // favoriteStore.loadFavorites();
    }
  } catch {
    favoriteStore.loadFavorites();
  }
});
</script>

<style scoped>
.favorite-container {
  padding-top: 46px;
  padding-bottom: 20px;
  background-color: #f7f8fa;
  min-height: 100vh;
}
</style>
