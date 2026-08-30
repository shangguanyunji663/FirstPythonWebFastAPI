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
    AI_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    AI_HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {AI_API_KEY}"}
