<template>
  <div>
    <div class="record-list" v-if="items.length">
      <div class="record-item" v-for="item in items" :key="item.id">
        <van-cell @click="goToDetail(item.id)" :border="false">
          <template #title>
            <div class="news-item">
              <div class="news-image" v-if="item.image">
                <img :src="item.image" :alt="item.title">
              </div>
              <div class="news-info">
                <div class="news-title">{{ item.title }}</div>
                <div class="news-meta">
                  <span>{{ item.author }}</span>
                  <span>{{ item.publishTime }}</span>
                  <span>{{ timeLabel }}: {{ itemTime(item) }}</span>
                </div>
              </div>
            </div>
          </template>
        </van-cell>
        <van-button
          class="delete-btn"
          type="danger"
          size="mini"
          icon="cross"
          @click="emit('delete', item)"
        ></van-button>
      </div>
    </div>

    <van-empty v-else :description="emptyText" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  // 列表数据：每项含 id/title/description/image/author/publishTime/views + favoriteTime 或 viewTime
  items: {
    type: Array,
    default: () => []
  },
  // 'favorite' | 'history'，决定时间标签文案与删除语义
  type: {
    type: String,
    default: 'history',
    validator: (value) => ['favorite', 'history'].includes(value)
  },
  // 空态文案
  emptyText: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['delete', 'clear']);

const router = useRouter();
const { t } = useI18n();

// 时间标签文案
const timeLabel = computed(() =>
  props.type === 'favorite' ? t('favorite.timeLabel') : t('history.timeLabel')
);

// 条目对应的时间字段
const itemTime = (item) =>
  props.type === 'favorite' ? item.favoriteTime : item.viewTime;

// 跳转到新闻详情
const goToDetail = (id) => {
  router.push(`/news/detail/${id}`);
};
</script>

<style scoped>
.record-list {
  padding: 10px;
}

.record-item {
  position: relative;
  margin-bottom: 10px;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.news-item {
  display: flex;
  padding: 10px 0;
}

.news-image {
  width: 120px;
  height: 80px;
  margin-right: 12px;
  flex-shrink: 0;
}

.news-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.news-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.news-title {
  font-size: 16px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.news-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  flex-wrap: wrap;
}

.news-meta span {
  margin-right: 10px;
}

.delete-btn {
  position: absolute;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  z-index: 10;
  width: 24px;
  height: 24px;
  padding: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
