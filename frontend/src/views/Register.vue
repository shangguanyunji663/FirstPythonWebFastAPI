<template>
  <div class="register-page">
    <van-nav-bar
      :title="$t('register.title')"
      left-arrow
      @click-left="onClickLeft"
      fixed
    />
    
    <div class="register-container">
      <div class="register-logo">
        <van-image
          width="80"
          height="80"
          src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
          round
        />
        <h2>{{ $t('home.title') }}</h2>
      </div>
      
      <van-form @submit="onSubmit" class="register-form">
        <van-cell-group inset>
          <van-field
            v-model="username"
            name="username"
            :label="$t('login.username')"
            :placeholder="$t('login.usernamePlaceholder')"
            :rules="[{ required: true, message: $t('login.usernameRequired') }]"
          />
          <van-field
            v-model="password"
            type="password"
            name="password"
            :label="$t('login.password')"
            :placeholder="$t('login.passwordPlaceholder')"
            :rules="[{ required: true, message: $t('login.passwordRequired') }]"
          />
          <van-field
            v-model="confirmPassword"
            type="password"
            name="confirmPassword"
            :label="$t('register.confirmPassword')"
            :placeholder="$t('register.confirmPasswordPlaceholder')"
            :rules="[
              { required: true, message: $t('register.confirmPasswordRequired') },
              { validator: validatePassword, message: $t('register.passwordMismatch') }
            ]"
          />
        </van-cell-group>
        
        <div class="submit-btn">
          <van-button round block type="primary" native-type="submit" size="large">
            {{ $t('register.submit') }}
          </van-button>
        </div>
        
        <div class="login-link">
          {{ $t('register.hasAccount') }}<span @click="goToLogin">{{ $t('register.goLogin') }}</span>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useUserStore } from '../store/user';
import { useI18n } from 'vue-i18n';

const router = useRouter();
const userStore = useUserStore();
const { t } = useI18n();

const username = ref('');
const password = ref('');
const confirmPassword = ref('');

// 验证两次密码是否一致
const validatePassword = () => {
  return password.value === confirmPassword.value;
};

const onSubmit = async () => {
  // 显示加载提示
  showToast({
    type: 'loading',
    message: t('register.submitting'),
    forbidClick: true,
    duration: 0
  });
  
  try {
    // 调用API注册
    const result = await userStore.register({
      username: username.value,
      password: password.value
    });
    
    if (result.success) {
      showToast({
        type: 'success',
        message: result.message
      });
      
      router.push('/');
    } else {
      showToast({
        type: 'fail',
        message: result.message
      });
    }
  } catch {
    showToast({
      type: 'fail',
      message: t('register.failed')
    });
  }
};

const onClickLeft = () => {
  router.back();
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.register-container {
  padding-top: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.register-logo {
  margin: 40px 0;
  text-align: center;
}

.register-logo h2 {
  margin-top: 16px;
  color: #323233;
  font-size: 22px;
}

.register-form {
  width: 100%;
  padding: 0 16px;
}

.submit-btn {
  margin: 24px 16px;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  color: #969799;
  font-size: 14px;
}

.login-link span {
  color: #1989fa;
}
</style>