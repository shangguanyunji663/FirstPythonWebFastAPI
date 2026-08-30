<template>
  <div class="profile-page">
    <van-nav-bar
      :title="$t('profile.title')"
      left-arrow
      @click-left="$router.back()"
      fixed
    />

    <div class="profile-container">
      <van-cell-group inset class="avatar-group">
        <van-cell :title="$t('profile.avatar')" center>
          <template #right-icon>
            <van-image
              round
              width="60"
              height="60"
              src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <van-cell-group inset class="info-group">
        <van-cell :title="$t('profile.username')" :value="userInfo.username || 'admin'" />
        <van-cell :title="$t('profile.accountId')" :value="`ID: heima-${userId || 'N/A'}`" />
        <van-cell :title="$t('profile.bio')" :value="userBio || $t('profile.noBio')" is-link @click="showBioDialog" />
      </van-cell-group>

      <van-cell-group inset class="security-group">
        <van-cell :title="$t('profile.changePassword')" is-link @click="showPasswordConfirm" />
      </van-cell-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue';
import { useUserStore } from '../store/user';
import { showDialog, showToast, showLoadingToast, showSuccessToast, showFailToast, closeToast } from 'vant';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const router = useRouter();
const userStore = useUserStore();
const { t } = useI18n();

// 初始化用户状态
onMounted(async () => {
  // 如果用户未登录，跳转到登录页面
  if (!userStore.getLoginStatus) {
    router.push('/login');
    return;
  }

  // 获取用户信息
  try {
    // 显示加载提示
    const loadingInstance = showLoadingToast({
      message: t('common.loading'),
      forbidClick: true,
      duration: 0
    });

    // 使用新的 getUserInfoDetail 方法
    const result = await userStore.getUserInfoDetail();

    // 手动关闭加载提示
    loadingInstance.close();

    if (result.success) {
      // 显示成功提示
      // showSuccessToast(t('profile.title'));
    } else {
      console.error('获取用户信息失败:', result.message);
      showFailToast(result.message || t('profile.getUserInfoFailed'));
    }
  } catch (error) {
    console.error('获取用户信息请求失败:', error);
    // 确保关闭加载提示
    closeToast();
    showToast({ type: 'fail', message: t('profile.getUserInfoFailed') });
  }
});

const userInfo = computed(() => userStore.userInfo);
const userId = computed(() => userStore.token ? userStore.token.substring(0, 5) : '');
const userBio = computed(() => userStore.userInfo?.bio || t('profile.noBio'));

const showPasswordConfirm = () => {
  // 使用ref创建响应式变量
  const oldPassword = ref('');
  const newPassword = ref('');
  const confirmPassword = ref('');

  showDialog({
    title: t('profile.changePassword'),
    showCancelButton: true,
    className: 'password-dialog',
    message: h('div', { style: 'text-align: left; padding: 10px 0;' }, [
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, t('profile.currentPassword')),
        h('input', {
          type: 'password',
          value: oldPassword.value,
          onInput: (e) => { oldPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ]),
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, t('profile.newPassword')),
        h('input', {
          type: 'password',
          value: newPassword.value,
          onInput: (e) => { newPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ]),
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, t('profile.confirmPassword')),
        h('input', {
          type: 'password',
          value: confirmPassword.value,
          onInput: (e) => { confirmPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ])
    ]),
  }).then(async () => {
    // 点击确认按钮
    if (!oldPassword.value) {
      showToast(t('profile.currentPasswordRequired'));
      return;
    }

    if (!newPassword.value) {
      showToast(t('profile.newPasswordRequired'));
      return;
    }

    if (newPassword.value !== confirmPassword.value) {
      showToast(t('profile.passwordMismatch'));
      return;
    }

    try {
      // 显示加载提示
      const loadingInstance = showLoadingToast({
        message: t('profile.updating'),
        forbidClick: true,
        duration: 0
      });

      // 调用API更新密码
      const result = await userStore.updatePassword(oldPassword.value, newPassword.value);

      // 关闭加载提示
      loadingInstance.close();

      if (result && result.success) {
        showSuccessToast(t('profile.passwordChangeSuccess'));
      } else {
        showFailToast((result && result.message) || t('profile.passwordChangeFailed'));
      }
    } catch (error) {
      console.error('修改密码失败:', error);
      closeToast();
      showToast({ type: 'fail', message: t('profile.passwordChangeFailed') });
    }
  }).catch(() => {
    // 点击取消按钮
  });
};

const showBioDialog = () => {
  // 使用ref创建响应式变量
  const newBioValue = ref(userBio.value);

  showDialog({
    title: t('profile.editBio'),
    showCancelButton: true,
    confirmButtonText: t('common.confirm'),
    className: 'bio-dialog',
    message: h('div', { style: 'text-align: left; padding: 10px 0;' }, [
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, t('profile.bioLabel')),
        h('textarea', {
          value: newBioValue.value,
          onInput: (e) => { newBioValue.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box; min-height: 100px; resize: vertical;'
        })
      ])
    ])
  }).then(async () => {
    // 点击确认按钮
    try {
      // 显示加载提示
      const loadingInstance = showLoadingToast({
        message: t('profile.saving'),
        forbidClick: true,
        duration: 0
      });

      // 调用API更新个人简介
      const result = await userStore.updateUserBio(newBioValue.value);

      // 关闭加载提示
      loadingInstance.close();

      if (result && result.success) {
        showSuccessToast(t('profile.bioUpdateSuccess'));
      } else {
        showFailToast((result && result.message) || t('profile.bioUpdateFailed'));
      }
    } catch (error) {
      console.error('更新个人简介失败:', error);
      closeToast();
      showToast({ type: 'fail', message: t('profile.bioUpdateFailed') });
    }
  }).catch(() => {
    // 点击取消按钮
  });
};
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.profile-container {
  padding-top: 56px;
  padding-bottom: 20px;
}

.avatar-group,
.info-group,
.security-group {
  margin-top: 12px;
}

.password-dialog .van-dialog__content {
  padding: 20px;
}

.password-form .form-item {
  margin-bottom: 15px;
  text-align: left;
}

.password-form .form-item span {
  display: block;
  margin-bottom: 5px;
  text-align: left;
}

.password-form .password-input {
  width: 100%;
  border: 1px solid #dcdee0;
  border-radius: 4px;
  padding: 8px;
  outline: none;
  box-sizing: border-box;
}
</style>
