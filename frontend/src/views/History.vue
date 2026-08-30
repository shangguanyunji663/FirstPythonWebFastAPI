<template>
  <div class="history-container">
    <van-nav-bar
      :title="$t('my.browsingHistory')"
      :left-text="$t('common.back')"
      left-arrow
      @click-left="onClickLeft"
      :right-text="$t('history.clear')"
      @click-right="onClickClear"
      fixed
    />

    <NewsRecordList
      :items="historyStore.getHistory"
      type="history"
      :empty-text="$t('history.empty')"
      @delete="confirmDelete"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useHistoryStore } from '../store/modules/history';
import { showDialog } from 'vant';
import { useI18n } from 'vue-i18n';
import NewsRecordList from '../components/NewsRecordList.vue';

const router = useRouter();
const historyStore = useHistoryStore();
const { t } = useI18n();

// 返回上一页
const onClickLeft = () => {
  router.back();
};

// 删除单条历史记录
const removeHistory = async (id) => {
  try {
    const result = await historyStore.removeHistoryApi(id);

    // 如果API请求失败且不是本地操作，则显示错误提示
    if (!result.success && !result.isLocal) {
      showDialog({
        title: t('common.tip'),
        message: result.message || t('history.deleteFailed'),
      }).catch(() => {});
    }
  } catch (error) {
    console.error('删除历史记录失败:', error);
    // 出错时仍然尝试本地删除
    // historyStore.removeHistory(id);
  }
};

// 确认删除
const confirmDelete = (item) => {
  showDialog({
    title: t('common.tip'),
    message: t('history.confirmDelete'),
    showCancelButton: true,
  }).then((action) => {
    if (action === 'confirm') {
      removeHistory(item.id);
    }
  }).catch(() => {});
};

// 清空历史记录
const onClickClear = async () => {
  showDialog({
    title: t('common.tip'),
    message: t('history.confirmClear'),
    showCancelButton: true,
  }).then(async (action) => {
    if (action === 'confirm') {
      try {
        const result = await historyStore.clearHistoryApi();

        // 如果API请求失败且不是本地操作，则显示错误提示
        if (!result.success && !result.isLocal) {
          showDialog({
            title: t('common.tip'),
            message: result.message || t('history.clearFailed'),
          }).catch(() => {});
        }
      } catch (error) {
        console.error('清空历史记录失败:', error);
        // 出错时仍然尝试本地清空
        // historyStore.clearHistory();
      }
    }
  }).catch(() => {});
};

// 组件挂载时加载历史记录
onMounted(async () => {
  // 先尝试从API获取浏览历史
  try {
    const result = await historyStore.getHistoryListApi();

    // 如果API请求失败或用户未登录，则从本地加载
    if (!result || !result.success) {
      historyStore.loadHistory();
    }
  } catch (error) {
    console.error('浏览历史页面：API请求异常', error);
    // 出错时从本地加载
    historyStore.loadHistory();
  }
});
</script>

<style scoped>
.history-container {
  padding-top: 46px;
  padding-bottom: 20px;
  background-color: #f7f8fa;
  min-height: 100vh;
}
</style>
