"""RSS 源配置：只使用公开可订阅的源；category 必须与 news_category.name 对应。
单个源抓取失败只记日志跳过，不影响其他源（2026-08 实测全部可用）"""
import os

RSS_SOURCES = [
    {"url": "https://sspai.com/feed", "category": "科技"},
    {"url": "https://www.solidot.org/index.rss", "category": "科技"},
    {"url": "https://www.ithome.com/rss/", "category": "科技"},
    {"url": "https://www.geekpark.net/rss", "category": "科技"},
    {"url": "http://www.people.com.cn/rss/politics.xml", "category": "头条"},
    {"url": "https://dedicated.wallstreetcn.com/rss.xml", "category": "财经"},
]

# 定时抓取间隔（小时），环境变量 CRAWL_INTERVAL_HOURS 可调；应用启动时也会先抓一次
CRAWL_INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "6"))

# 环境变量开关：CRAWLER_ENABLED=false 可整体关闭定时抓取
CRAWLER_ENABLED_ENV = "CRAWLER_ENABLED"
