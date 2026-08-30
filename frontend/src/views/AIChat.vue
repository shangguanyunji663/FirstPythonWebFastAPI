<template>
  <div class="ai-chat-container">
    <van-nav-bar :title="$t('aiChat.title')" fixed />
    
    <div class="chat-content">
      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content">
            <div v-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else v-html="formatMessage(message.content)"></div>
          </div>
        </div>
      </div>
      
      <div class="input-container">
        <van-field
          v-model="userInput"
          rows="1"
          autosize
          type="textarea"
          :placeholder="$t('aiChat.placeholder')"
          class="chat-input"
          @keypress.enter.prevent="sendMessage"
        />
        <van-button
          type="primary"
          class="send-button"
          :disabled="!isLoading && !userInput.trim()"
          @click="isLoading ? stopGeneration() : sendMessage()"
        >
          {{ isLoading ? $t('aiChat.stop') : $t('aiChat.send') }}
        </van-button>
      </div>
    </div>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import TabBar from '../components/TabBar.vue';
import { showToast } from 'vant';
import * as marked from 'marked';
import DOMPurify from 'dompurify';
import { apiConfig, aiConfig } from '../config/api';
import { useUserStore } from '../store/user';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// 聊天消息
const messages = ref([
  { role: 'assistant', content: t('aiChat.welcome') }
]);
const userInput = ref('');
const messagesContainer = ref(null);
const isLoading = ref(false);
// 当前流式请求的中止控制器：停止按钮与组件卸载共用
let abortController = null;

// 停止生成：中止 SSE 流，保留已输出的部分内容
const stopGeneration = () => {
  abortController?.abort();
};

const userStore = useUserStore();

// 格式化消息内容（支持Markdown）
const formatMessage = (content) => {
  if (!content) return '';
  // 使用marked解析Markdown，并用DOMPurify清理HTML
  return DOMPurify.sanitize(marked.parse(content));
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;
  
  // 检查登录状态（AI 接口需要认证）
  if (!userStore.getLoginStatus) {
    showToast(t('aiChat.loginRequired'));
    return;
  }
  
  // 添加用户消息
  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  
  // 添加AI消息占位
  messages.value.push({ role: 'assistant', content: '' });
  
  // 滚动到底部
  await nextTick();
  scrollToBottom();
  
  // 发送请求
  isLoading.value = true;
  try {
    await fetchAIResponse(userMessage);
  } catch (error) {
    if (error?.name === 'AbortError') {
      // 手动停止：占位消息还没有内容时直接移除，已有部分内容则保留
      const last = messages.value[messages.value.length - 1];
      if (last && last.role === 'assistant' && last.content === '') {
        messages.value.pop();
      }
    } else {
      console.error('Error fetching AI response:', error);
      // 更新最后一条消息为错误信息
      messages.value[messages.value.length - 1].content = t('aiChat.errorOccurred', { message: error.message || t('aiChat.networkError') });
    }
  } finally {
    abortController = null;
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 获取AI响应（后端代理接口，SSE 流式）
const fetchAIResponse = async (userMessage) => {
  // 历史对话：排除当前轮（最后的占位 assistant 与当前 user 消息）
  const history = messages.value
    .slice(0, -2)
    .map(msg => ({ role: msg.role, content: msg.content }));

  abortController = new AbortController();
  const response = await fetch(`${apiConfig.baseURL}${aiConfig.chatEndpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userStore.token}`
    },
    body: JSON.stringify({ message: userMessage, history }),
    signal: abortController.signal
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || t('aiChat.requestFailed', { status: response.status }));
  }

  // 处理SSE流（后端透传模型服务的 data: 行）
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let aiResponse = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6);
      if (data === '[DONE]') continue;

      try {
        const json = JSON.parse(data);
        // 后端代理返回的业务错误（如 AI 服务限流/不可用）
        if (json.error) {
          throw new Error(json.error);
        }
        const content = json.choices?.[0]?.delta?.content || '';
        if (content) {
          aiResponse += content;
          // 更新最后一条消息
          messages.value[messages.value.length - 1].content = aiResponse;
          await nextTick();
          scrollToBottom();
        }
      } catch (e) {
        if (e instanceof SyntaxError) {
          console.error('Error parsing SSE data:', e);
        } else {
          throw e;
        }
      }
    }
  }

  // 如果没有收到任何内容
  if (!aiResponse) {
    messages.value[messages.value.length - 1].content = t('aiChat.noResponse');
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(scrollToBottom);
}, { deep: true });

// 组件挂载时滚动到底部
onMounted(() => {
  scrollToBottom();
});

// 离开页面（非 keepAlive 场景，如刷新/关闭）时中止进行中的流，不再白白消耗上游 token
onBeforeUnmount(() => {
  stopGeneration();
});
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 46px;
  padding-bottom: 50px;
  box-sizing: border-box;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin-bottom: 10px;
  max-width: 80%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 10px;
  border-radius: 10px;
  word-break: break-word;
}

.user-message .message-content {
  background-color: #007aff;
  color: white;
}

.ai-message .message-content {
  background-color: #f2f2f2;
  color: #333;
}

.input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #eee;
  background-color: #fff;
}

.chat-input {
  flex: 1;
  margin-right: 10px;
}

.send-button {
  align-self: flex-end;
}

/* Markdown 样式 */
.message-content pre {
  background-color: #f8f8f8;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
}

.message-content code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 3px;
}

.message-content img {
  max-width: 100%;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  padding: 5px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #999;
  border-radius: 50%;
  margin: 0 2px;
  display: inline-block;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}

/* Markdown样式 */
:deep(pre) {
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

:deep(code) {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(p) {
  margin: 8px 0;
}

:deep(ul), :deep(ol) {
  padding-left: 20px;
}

:deep(a) {
  color: #1989fa;
  text-decoration: none;
}
</style>