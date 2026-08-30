# AI 问答提供方配置（均使用 OpenAI 兼容接口）
# 密钥只从环境变量读取（backend/.env），绝不写入源码
import os

from dotenv import load_dotenv

load_dotenv()  # 读取 backend/.env

# 提供方：zhipu（智谱云端）| ollama（本地）
AI_PROVIDER = os.getenv("AI_PROVIDER", "zhipu")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "glm-4.7-flash")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

if AI_PROVIDER == "ollama":
    # Ollama 本地服务，不校验 Key，但 Bearer 头需非空值
    AI_BASE_URL = f"{OLLAMA_BASE_URL}/v1/chat/completions"
    AI_HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer ollama"}
else:
    # 智谱 OpenAI 兼容端点：走自建中转/代理时用 AI_BASE_URL 环境变量覆盖
    # 用 or 而不是 getenv 默认值参数：.env 里"设了但为空"也回退官方端点
    AI_BASE_URL = os.getenv("AI_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    AI_HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {AI_API_KEY}"}
