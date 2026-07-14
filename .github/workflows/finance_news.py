import feedparser
import requests
import json
from datetime import datetime, timedelta

# 配置：权威媒体RSS源（免费、无需API Key）
RSS_FEEDS = [
    "http://feeds.reuters.com/reuters/businessNews",          # 路透
    "https://feeds.bloomberg.com/markets/news.rss",           # 彭博
    "https://www.ft.com/?format=rss",                         # 金融时报
    "https://www.economist.com/feeds/print-sections/77/finance-and-economics.xml",  # 经济学人
    "https://feeds.feedburner.com/wsj/podcast",               # 华尔街日报
]

def fetch_news():
    """抓取近24小时的金融新闻"""
    news_list = []
    cutoff_time = datetime.now() - timedelta(hours=24)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:  # 每个源取前10条
                # 解析发布时间
                pub_time = datetime(*entry.published_parsed[:6])
                if pub_time > cutoff_time:
                    news_list.append({
                        'title': entry.title,
                        'summary': entry.summary[:150],
                        'link': entry.link,
                        'source': feed.feed.title,
                        'time': pub_time
                    })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    return sorted(news_list, key=lambda x: x['time'], reverse=True)

def summarize_news(news_list):
    """压缩为500字以内的简报"""
    lines = []
    lines.append(f"全球金融资讯简报 - {datetime.now().strftime('%Y年%m月%d日')}")
    lines.append("=" * 40)

    count = 0
    for item in news_list[:15]:
        line = f"- {item['title']} ({item['source']})"
        if len(line) > 50:
            line = line[:50] + "..."
        lines.append(line)
        count += 1
        if count >= 10:
            break

    # 添加来源说明
    lines.append("=" * 40)
    lines.append(f"共{len(news_list)}条新闻，以上为摘要。")
    lines.append("数据来源: 路透/彭博/金融时报/经济学人/华尔街日报")

    return "\n".join(lines)

if __name__ == "__main__":
    print("正在获取金融新闻...")
    news = fetch_news()
    print(f"获取到 {len(news)} 条新闻")
    report = summarize_news(news)
    print(report)

    # 保存到文件，供邮件发送
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)
