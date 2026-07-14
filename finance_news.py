import feedparser
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator
import html
import time
import re

# ============ 1. 英文 RSS 源 ============
RSS_FEEDS = [
    "http://feeds.reuters.com/reuters/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.ft.com/?format=rss",
    "https://www.economist.com/feeds/print-sections/77/finance-and-economics.xml",
]

# ============ 2. 获取市场数据 ============
def get_market_data():
    data = {}
    try:
        indices = {'标普500': '^GSPC', '纳斯达克': '^IXIC', '道琼斯': '^DJI'}
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                data[name] = f"{last:.2f} ({change:+.2f})"

        commodities = {'黄金': 'GC=F', 'WTI原油': 'CL=F'}
        for name, symbol in commodities.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                data[name] = f"{hist['Close'].iloc[-1]:.2f}"

        cnh = yf.Ticker("CNH=X")
        hist = cnh.history(period="1d")
        if not hist.empty:
            data['美元/人民币'] = f"{hist['Close'].iloc[-1]:.4f}"
    except Exception as e:
        print(f"市场数据获取失败: {e}")
    return data

# ============ 3. 抓取并翻译新闻 ============
def fetch_and_translate_news():
    news_list = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    translator = Translator()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:6]:
                pub_time = datetime(*entry.published_parsed[:6])
                if pub_time > cutoff_time:
                    title_en = entry.title
                    try:
                        title_zh = translator.translate(title_en, dest='zh-cn').text
                    except:
                        title_zh = title_en
                    summary = entry.summary[:300] if hasattr(entry, 'summary') else ''
                    news_list.append({
                        'title_zh': title_zh,
                        'title_en': title_en,
                        'summary': summary,
                        'link': entry.link,
                        'source': feed.feed.title,
                        'time': pub_time
                    })
                    time.sleep(0.5)
        except Exception as e:
            print(f"抓取 {feed_url} 失败: {e}")

    sorted_news = sorted(news_list, key=lambda x: x['time'], reverse=True)[:12]
    return sorted_news

# ============ 4. 生成短期展望 ============
def generate_outlook(news_list, market_data):
    keywords = ['outlook', 'forecast', 'expect', 'predict', 'analyst', '摩根', '高盛', '预计', '预测', '展望']
    outlook_articles = []
    translator = Translator()
    for item in news_list:
        text = (item['title_en'] + ' ' + item['summary']).lower()
        if any(kw in text for kw in keywords):
            summary = item['summary']
            if summary:
                try:
                    summary_zh = translator.translate(summary[:200], dest='zh-cn').text
                except:
                    summary_zh = summary
                outlook_articles.append(summary_zh)

    if len(outlook_articles) >= 2:
        outlook_text = '；'.join(outlook_articles[:3])
        outlook_text = '📌 机构观点：' + outlook_text
    else:
        oil = market_data.get('WTI原油', '')
        gold = market_data.get('黄金', '')
        sp = market_data.get('标普500', '')
        def extract_change(val):
            match = re.search(r'\(([+-][\d.]+)\)', val)
            return float(match.group(1)) if match else 0
        oil_change = extract_change(oil) if 'WTI' in oil else 0
        sp_change = extract_change(sp) if '标普' in sp else 0

        lines = []
        lines.append("📌 短期展望：")
        if oil_change > 1:
            lines.append("受地缘冲突影响，原油价格大幅上涨，推升通胀预期，美联储加息压力增大，短期股市可能承压。")
        elif sp_change < -0.5:
            lines.append("美股昨日下跌，市场情绪谨慎，投资者关注今夜CPI数据及美联储主席讲话，短期波动或将加大。")
        else:
            lines.append("市场等待关键数据指引，短期维持震荡格局，建议关注CPI和美联储官员发言。")
        if gold:
            lines.append(f"黄金报{gold}美元/盎司，受美元走强压制，短期或延续震荡。")
        outlook_text = ' '.join(lines)
    return outlook_text

# ============ 5. 生成 HTML 邮件 ============
def generate_html_report(news_list, market_data, outlook):
    date_str = datetime.now().strftime('%Y年%m月%d日')
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
            .container {{ max-width: 720px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a2a3a; border-left: 5px solid #2e86de; padding-left: 15px; }}
            .sub {{ color: #6c7a8a; font-size: 14px; margin-top: -10px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; }}
            th {{ background: #2e86de; color: #fff; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }}
            .news-item {{ padding: 10px 0; border-bottom: 1px solid #e2e8f0; }}
            .news-item a {{ color: #1a2a3a; text-decoration: none; font-weight: 500; }}
            .news-item a:hover {{ color: #2e86de; text-decoration: underline; }}
            .meta {{ color: #6c7a8a; font-size: 12px; display: block; margin-top: 4px; }}
            .en {{ color: #94a3b8; font-size: 12px; }}
            .outlook-box {{ background: #f0f7ff; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2e86de; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 全球金融早报</h1>
            <div class="sub">{date_str} · 数据来源：路透、彭博、金融时报、经济学人</div>

            <div style="font-weight: bold; color: #1a2a3a; margin: 20px 0 10px 0;">📊 市场概览</div>
            <table>
                <tr><th>品种</th><th>最新价格（涨跌）</th></tr>
    """
    for name, value in market_data.items():
        html_content += f"<tr><td>{name}</td><td>{value}</td></tr>"
    html_content += """
            </table>

            <div class="outlook-box">
                <strong>🔮 短期预测与分析</strong><br>
                """ + outlook + """
            </div>

            <div style="font-weight: bold; color: #1a2a3a; margin: 25px 0 10px 0;">📰 热点新闻</div>
    """
    for item in news_list:
        html_content += f"""
            <div class="news-item">
                <a href="{item['link']}" target="_blank">{html.escape(item['title_zh'])}</a>
                <div class="meta">{item['source']} · {item['time'].strftime('%H:%M')}</div>
                <div class="en">原文：{html.escape(item['title_en'])}</div>
            </div>
        """

    html_content += f"""
            <div class="footer">
                本简报由 GitHub Actions 自动生成 · 不构成投资建议<br>
                如内容有翻译偏差，请以英文原文为准。
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# ============ 主函数 ============
if __name__ == "__main__":
    print("⏳ 获取市场数据...")
    market = get_market_data()

    print("⏳ 抓取并翻译新闻...")
    news = fetch_and_translate_news()
    print(f"✅ 获取到 {len(news)} 条新闻")

    print("⏳ 生成短期展望...")
    outlook = generate_outlook(news, market)

    html = generate_html_report(news, market, outlook)

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
