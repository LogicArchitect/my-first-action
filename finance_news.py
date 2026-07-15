import feedparser
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator
import time
import re

# ============ 1. RSS 源 ============
RSS_FEEDS = [
    "http://feeds.reuters.com/reuters/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.ft.com/?format=rss",
    "https://www.economist.com/feeds/print-sections/77/finance-and-economics.xml",
]

# ============ 2. 金融关键词过滤 ============
FINANCE_KEYWORDS = [
    'stock', 'market', 'fed', 'rate', 'inflation', 'oil', 'gold',
    'dollar', 'bond', 'yield', 'earnings', 'profit', 'revenue',
    'forex', 'cpi', 'ppi', '加息', '降息', '通胀', '美联储',
    '央行', '股市', '油价', '金价', '美元', '汇率', '国债',
    'quarterly', 'annual', 'dividend', 'share', 'buyback',
    'tariff', 'trade', 'economic', 'growth', 'gdp'
]

def is_finance_news(title):
    title_lower = title.lower()
    return any(kw in title_lower for kw in FINANCE_KEYWORDS)

# ============ 3. 格式化涨跌符号 ============
def format_change(change_val):
    if change_val > 0:
        return f"📈 +{change_val:.2f}%"
    elif change_val < 0:
        return f"📉 {change_val:.2f}%"
    else:
        return "➖ 0.00%"

def format_abs_change(change_val):
    if change_val > 0:
        return f"📈 +{change_val:.2f}"
    elif change_val < 0:
        return f"📉 {change_val:.2f}"
    else:
        return "➖ 0.00"

# ============ 4. 获取市场数据 ============
def get_market_data():
    data = {}
    try:
        # 美股
        us = {
            '标普500': '^GSPC',
            '纳斯达克': '^IXIC',
            '道琼斯': '^DJI'
        }
        for name, symbol in us.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 亚太
        asia = {
            '恒生指数': '^HSI',
            '上证指数': '000001.SS',
            '日经225': '^N225'
        }
        for name, symbol in asia.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 欧洲
        eu = {
            '富时100': '^FTSE',
            '德国DAX': '^GDAXI'
        }
        for name, symbol in eu.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 商品
        comm = {
            '黄金': 'GC=F',
            'WTI原油': 'CL=F',
            '布伦特原油': 'BZ=F'
        }
        for name, symbol in comm.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                data[name] = f"{last:.2f} ({format_abs_change(change)})"

        # 比特币
        try:
            btc = yf.Ticker("BTC-USD")
            hist = btc.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data['比特币'] = f"${last:,.0f} ({format_change(change_pct)})"
        except:
            pass

        # 汇率
        cnh = yf.Ticker("CNH=X")
        hist = cnh.history(period="1d")
        if not hist.empty:
            data['美元/人民币'] = f"{hist['Close'].iloc[-1]:.4f}"

        # 美债收益率
        try:
            bond = yf.Ticker("^TNX")
            hist = bond.history(period="1d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                change_str = f"📈 +{change:.2f}%" if change > 0 else f"📉 {change:.2f}%" if change < 0 else "➖ 0.00%"
                data['10年期美债收益率'] = f"{val:.2f}% ({change_str})"
        except:
            pass

        # VIX
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                change_str = f"📈 +{change:.2f}" if change > 0 else f"📉 {change:.2f}" if change < 0 else "➖ 0.00"
                data['VIX恐慌指数'] = f"{last:.2f} ({change_str})"
        except:
            pass

    except Exception as e:
        print(f"市场数据获取失败: {e}")
    return data

# ============ 5. 抓取并翻译新闻 ============
def fetch_and_translate_news():
    news_list = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    translator = Translator()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                pub_time = datetime(*entry.published_parsed[:6])
                if pub_time > cutoff_time:
                    title_en = entry.title
                    if not is_finance_news(title_en):
                        continue
                    try:
                        title_zh = translator.translate(title_en, dest='zh-cn').text
                    except:
                        title_zh = title_en
                    news_list.append({
                        'title_zh': title_zh,
                        'title_en': title_en,
                        'link': entry.link,
                        'source': feed.feed.title,
                        'time': pub_time
                    })
                    time.sleep(0.3)
        except Exception as e:
            print(f"抓取 {feed_url} 失败: {e}")

    sorted_news = sorted(news_list, key=lambda x: x['time'], reverse=True)[:12]
    return sorted_news

# ============ 6. 生成纯文本报告（无分析） ============
def generate_text_report(news_list, market_data):
    date_str = datetime.now().strftime('%Y年%m月%d日')
    lines = []
    lines.append(f"📈 全球金融早报 - {date_str}")
    lines.append("=" * 60)

    lines.append("📊 全球市场概览")
    for name, value in market_data.items():
        lines.append(f"  {name}: {value}")
    lines.append("")

    if len(news_list) == 0:
        lines.append("📰 热点新闻")
        lines.append("  暂无新闻")
    else:
        lines.append("📰 热点新闻")
        for i, item in enumerate(news_list, 1):
            lines.append(f"{i}. {item['title_zh']}")
            lines.append(f"   来源: {item['source']}  {item['time'].strftime('%H:%M')}")
            lines.append(f"   原文: {item['title_en']}")
            lines.append("")

    lines.append("=" * 60)
    lines.append("本简报由 GitHub Actions 自动生成 · 不构成投资建议")
    lines.append("数据来源：路透社、彭博社、金融时报、经济学人")
    return "\n".join(lines)

# ============ 主函数 ============
if __name__ == "__main__":
    print("⏳ 获取全球市场数据...")
    market = get_market_data()

    print("⏳ 抓取并翻译新闻...")
    news = fetch_and_translate_news()
    print(f"✅ 获取到 {len(news)} 条新闻")

    report = generate_text_report(news, market)

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ 报告生成完成！")
