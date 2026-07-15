import feedparser
import yfinance as yf
from datetime import datetime, timedelta
from googletrans import Translator
import time
import re

# ============ 1. RSS 源（英文权威媒体） ============
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

# ============ 3. 获取市场数据（扩展版） ============
def get_market_data():
    data = {}
    try:
        # 美股指数
        indices = {'标普500': '^GSPC', '纳斯达克': '^IXIC', '道琼斯': '^DJI'}
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                data[name] = f"{last:.2f} ({change:+.2f})"

        # 商品
        commodities = {'黄金': 'GC=F', 'WTI原油': 'CL=F'}
        for name, symbol in commodities.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                data[name] = f"{hist['Close'].iloc[-1]:.2f}"

        # 汇率
        cnh = yf.Ticker("CNH=X")
        hist = cnh.history(period="1d")
        if not hist.empty:
            data['美元/人民币'] = f"{hist['Close'].iloc[-1]:.4f}"

        # 新增：10年期美债收益率（^TNX 的 Close 即为收益率百分比）
        try:
            bond = yf.Ticker("^TNX")
            hist = bond.history(period="1d")
            if not hist.empty:
                data['10年期美债收益率'] = f"{hist['Close'].iloc[-1]:.2f}%"
        except:
            pass

        # 新增：VIX 恐慌指数
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")
            if not hist.empty:
                data['VIX恐慌指数'] = f"{hist['Close'].iloc[-1]:.2f}"
        except:
            pass

    except Exception as e:
        print(f"市场数据获取失败: {e}")
    return data

# ============ 4. 抓取并翻译新闻 ============
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
                    summary = entry.summary[:300] if hasattr(entry, 'summary') else ''
                    news_list.append({
                        'title_zh': title_zh,
                        'title_en': title_en,
                        'summary': summary,
                        'link': entry.link,
                        'source': feed.feed.title,
                        'time': pub_time
                    })
                    time.sleep(0.3)
        except Exception as e:
            print(f"抓取 {feed_url} 失败: {e}")

    sorted_news = sorted(news_list, key=lambda x: x['time'], reverse=True)[:12]
    return sorted_news

# ============ 5. 生成短期展望 ============
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
        vix = market_data.get('VIX恐慌指数', '')
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
        if vix:
            try:
                vix_val = float(vix)
                if vix_val > 25:
                    lines.append(f"VIX恐慌指数报{vix}，市场恐慌情绪较高，短期波动风险上升。")
                elif vix_val < 15:
                    lines.append(f"VIX恐慌指数报{vix}，市场情绪平稳，风险偏好回升。")
            except:
                pass
        outlook_text = ' '.join(lines)
    return outlook_text

# ============ 6. 生成每日一句话总结 ============
def generate_daily_summary(market_data):
    """
    基于市场数据生成一句话核心结论
    """
    sp = market_data.get('标普500', '')
    oil = market_data.get('WTI原油', '')
    gold = market_data.get('黄金', '')
    bond = market_data.get('10年期美债收益率', '')
    vix = market_data.get('VIX恐慌指数', '')

    def extract_change(val):
        match = re.search(r'\(([+-][\d.]+)\)', val)
        return float(match.group(1)) if match else 0

    sp_change = extract_change(sp) if '标普' in sp else 0
    oil_change = extract_change(oil) if 'WTI' in oil else 0

    parts = []
    # 股市方向
    if sp_change > 0.5:
        parts.append("美股小幅上涨")
    elif sp_change < -0.5:
        parts.append("美股承压下跌")
    else:
        parts.append("美股震荡整理")

    # 油价影响
    if oil_change > 1:
        parts.append("油价大涨推升通胀担忧")
    elif oil_change < -1:
        parts.append("油价下跌缓解通胀压力")
    else:
        parts.append("油价相对平稳")

    # 债市
    if bond:
        try:
            bond_val = float(bond.replace('%', ''))
            if bond_val > 4.5:
                parts.append("美债收益率高位运行")
            elif bond_val < 4.0:
                parts.append("美债收益率回落")
            else:
                parts.append("美债收益率窄幅波动")
        except:
            pass

    # 恐慌情绪
    if vix:
        try:
            vix_val = float(vix)
            if vix_val > 25:
                parts.append("恐慌情绪蔓延")
            elif vix_val > 18:
                parts.append("市场情绪谨慎")
            else:
                parts.append("市场情绪稳定")
        except:
            pass

    summary = "📌 今日总结：" + "，".join(parts) + "。"
    return summary

# ============ 7. 生成纯文本报告 ============
def generate_text_report(news_list, market_data, outlook, summary):
    date_str = datetime.now().strftime('%Y年%m月%d日')
    lines = []
    lines.append(f"📈 全球金融早报 - {date_str}")
    lines.append("=" * 50)

    # 一句话总结（新）
    lines.append(summary)
    lines.append("")

    lines.append("📊 市场概览")
    for name, value in market_data.items():
        lines.append(f"  {name}: {value}")
    lines.append("")

    lines.append("🔮 短期预测与分析")
    lines.append(outlook)
    lines.append("")

    # 空报告检测（新闻少于3条时提示）
    if len(news_list) < 3:
        lines.append("⚠️ 今日财经新闻较少（可能源站异常），以上为全部可获取内容。")
        lines.append("")

    lines.append("📰 热点新闻")
    if len(news_list) == 0:
        lines.append("  暂无新闻")
    else:
        for i, item in enumerate(news_list, 1):
            lines.append(f"{i}. {item['title_zh']}")
            lines.append(f"   来源: {item['source']}  {item['time'].strftime('%H:%M')}")
            lines.append(f"   原文: {item['title_en']}")
            lines.append("")

    lines.append("=" * 50)
    lines.append("本简报由 GitHub Actions 自动生成 · 不构成投资建议")
    lines.append("数据来源：路透社、彭博社、金融时报、经济学人")
    return "\n".join(lines)

# ============ 主函数 ============
if __name__ == "__main__":
    print("⏳ 获取市场数据...")
    market = get_market_data()

    print("⏳ 抓取并翻译新闻...")
    news = fetch_and_translate_news()
    print(f"✅ 获取到 {len(news)} 条新闻")

    print("⏳ 生成短期展望...")
    outlook = generate_outlook(news, market)

    print("⏳ 生成每日总结...")
    summary = generate_daily_summary(market)

    report = generate_text_report(news, market, outlook, summary)

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)
