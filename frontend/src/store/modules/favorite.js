import { defineStore } from 'pinia';
import request from '../../api/request';
import { useUserStore } from '../user';

export const useFavoriteStore = defineStore('favorite', {
  state: () => ({
    favorites: [],
    loading: false,
  }),

  getters: {
    getFavorites: (state) => state.favorites,
    isFavorite: (state) => (id) => state.favorites.some(item => item.id === id),
  },

  actions: {
    // 检查文章收藏状态 - API请求（Token 由 request 拦截器统一携带）
    async checkFavoriteStatusApi(newsId) {
      const userStore = useUserStore();
      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return {
          success: true,
          isFavorite: this.isFavorite(newsId),
          isLocal: true
        };
      }

      try {
        this.loading = true;
        const response = await request.get('/api/favorite/check', {
          params: { newsId }
        });

        if (response.data.code === 200) {
          return {
            success: true,
            isFavorite: response.data.data.isFavorite
          };
        } else {
          return { success: false, message: response.data.message || '获取收藏状态失败' };
        }
      } catch (error) {
        console.error('检查收藏状态请求失败:', error);
        // 如果API请求失败，回退到本地状态检查
        return {
          success: true,
          isFavorite: this.isFavorite(newsId),
          isLocal: true
        };
      } finally {
        this.loading = false;
      }
    },

    // 添加收藏 - API请求
    async addFavoriteApi(newsId) {
      const userStore = useUserStore();

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }

      try {
        this.loading = true;
        const response = await request.post('/api/favorite/add', { newsId });

        if (response.data.code === 200) {
          return { success: true, data: response.data.data };
        } else {
          return { success: false, message: response.data.message || '收藏失败' };
        }
      } catch (error) {
        console.error('添加收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },

    // 取消收藏 - API请求
    async removeFavoriteApi(newsId) {
      const userStore = useUserStore();

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }

      try {
        this.loading = true;
        const response = await request.delete('/api/favorite/remove', { params: { newsId } });

        if (response.data.code === 200) {
          return { success: true };
        } else {
          return { success: false, message: response.data.message || '取消收藏失败' };
        }
      } catch (error) {
        console.error('取消收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },

    // 添加收藏 - 本地
    addFavorite(news) {
      // 检查是否已存在相同ID的新闻
      if (!this.isFavorite(news.id)) {
        // 添加到收藏列表
        this.favorites.unshift({
          ...news,
          favoriteTime: new Date().toLocaleString()
        });

        // 保存到本地存储
        this.saveFavorites();
      }
    },

    // 取消收藏 - 本地
    removeFavorite(id) {
      this.favorites = this.favorites.filter(item => item.id !== id);
      this.saveFavorites();
    },

    // 切换收藏状态 - 结合API和本地
    async toggleFavorite(news) {
      // 确保news对象存在且有id属性
      if (!news || !news.id) {
        console.error('无效的新闻对象:', news);
        return null;
      }

      if (this.isFavorite(news.id)) {
        // 取消收藏
        const result = await this.removeFavoriteApi(news.id);
        if (result.success) {
          this.removeFavorite(news.id);
          return false;
        } else {
          return null; // 返回null表示操作失败
        }
      } else {
        // 添加收藏
        const result = await this.addFavoriteApi(news.id);
        if (result.success) {
          this.addFavorite(news);
          return true;
        } else {
          return null; // 返回null表示操作失败
        }
      }
    },


    // 清空收藏
    clearFavorites() {
      this.favorites = [];
      this.saveFavorites();
    },

    // 清空收藏 - API请求
    async clearFavoritesApi() {
      const userStore = useUserStore();

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }

      try {
        this.loading = true;
        const response = await request.delete('/api/favorite/clear');

        if (response.data.code === 200) {
          // 清空本地收藏列表
          this.clearFavorites();
          return { success: true };
        } else {
          return { success: false, message: response.data.message || '清空收藏失败' };
        }
      } catch (error) {
        console.error('清空收藏请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },

    // 保存到本地存储
    saveFavorites() {
      localStorage.setItem('news_favorites', JSON.stringify(this.favorites));
    },

    // 从本地存储加载
    loadFavorites() {
      const savedFavorites = localStorage.getItem('news_favorites');
      if (savedFavorites) {
        this.favorites = JSON.parse(savedFavorites);
      }
    },

    // 获取收藏列表 - API请求
    async getFavoriteListApi(page = 1, pageSize = 10) {
      const userStore = useUserStore();

      // 检查用户是否登录
      if (!userStore.getLoginStatus) {
        return { success: false, message: '请先登录' };
      }

      try {
        this.loading = true;
        const response = await request.get('/api/favorite/list', {
          params: { page, pageSize }
        });

        if (response.data.code === 200) {
          // 更新本地收藏列表
          this.favorites = response.data.data.list;
          return { success: true, data: response.data.data };
        } else {
          return { success: false, message: response.data.message || '获取收藏列表失败' };
        }
      } catch (error) {
        console.error('获取收藏列表请求失败:', error);
        return { success: false, message: '网络请求失败' };
      } finally {
        this.loading = false;
      }
    },
  },
});
