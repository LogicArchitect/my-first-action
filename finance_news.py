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

# ============ 3. 提取涨跌幅并添加视觉符号 ============
def format_change(change_val):
    """将涨跌幅数值格式化为带符号和表情的字符串"""
    if change_val > 0:
        return f"📈 +{change_val:.2f}%"
    elif change_val < 0:
        return f"📉 {change_val:.2f}%"
    else:
        return "➖ 0.00%"

def extract_change_percent(val_str):
    """从 '价格 (涨跌值)' 中提取涨跌百分比"""
    match = re.search(r'\(([+-][\d.]+)\)', val_str)
    if match:
        return float(match.group(1))
    return 0.0

# ============ 4. 获取市场数据（全面版） ============
def get_market_data():
    data = {}
    try:
        # 美股指数
        us_indices = {
            '标普500': '^GSPC',
            '纳斯达克': '^IXIC',
            '道琼斯': '^DJI'
        }
        for name, symbol in us_indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 亚太指数（新增）
        asia_indices = {
            '恒生指数': '^HSI',
            '上证指数': '000001.SS',
            '日经225': '^N225'
        }
        for name, symbol in asia_indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 欧洲指数（新增）
        eu_indices = {
            '富时100': '^FTSE',
            '德国DAX': '^GDAXI'
        }
        for name, symbol in eu_indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change_pct = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                data[name] = f"{last:.2f} ({format_change(change_pct)})"

        # 商品
        commodities = {
            '黄金': 'GC=F',
            'WTI原油': 'CL=F',
            '布伦特原油': 'BZ=F'   # 新增
        }
        for name, symbol in commodities.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                # 商品我们用绝对涨跌值，而不是百分比（因为原油波动通常是绝对值）
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                if change > 0:
                    change_str = f"📈 +{change:.2f}"
                elif change < 0:
                    change_str = f"📉 {change:.2f}"
                else:
                    change_str = "➖ 0.00"
                data[name] = f"{last:.2f} ({change_str})"

        # 加密货币（新增）
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

        # 10年期美债收益率
        try:
            bond = yf.Ticker("^TNX")
            hist = bond.history(period="1d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                if change > 0:
                    change_str = f"📈 +{change:.2f}%"
                elif change < 0:
                    change_str = f"📉 {change:.2f}%"
                else:
                    change_str = "➖ 0.00"
                data['10年期美债收益率'] = f"{val:.2f}% ({change_str})"
        except:
            pass

        # VIX 恐慌指数
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                if change > 0:
                    change_str = f"📈 +{change:.2f}"
                elif change < 0:
                    change_str = f"📉 {change:.2f}"
                else:
                    change_str = "➖ 0.00"
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

# ============ 6. 综合关联分析（深度版） ============
def generate_deep_analysis(market_data, news_list):
    """
    基于跨资产联动关系，生成有深度的宏观分析
    """
    # 提取关键数据
    sp = market_data.get('标普500', '')
    nasdaq = market_data.get('纳斯达克', '')
    oil = market_data.get('WTI原油', '')
    brent = market_data.get('布伦特原油', '')
    bond = market_data.get('10年期美债收益率', '')
    vix = market_data.get('VIX恐慌指数', '')
    gold = market_data.get('黄金', '')
    hsi = market_data.get('恒生指数', '')
    btc = market_data.get('比特币', '')

    def extract_pct(val):
        match = re.search(r'([+-][\d.]+)%', val)
        return float(match.group(1)) if match else 0.0

    def extract_abs_change(val):
        """提取绝对涨跌值（用于商品）"""
        match = re.search(r'([+-][\d.]+)(?=\))', val)
        return float(match.group(1)) if match else 0.0

    sp_change = extract_pct(sp)
    nasdaq_change = extract_pct(nasdaq)
    oil_change = extract_abs_change(oil)
    bond_val = float(re.search(r'([\d.]+)%', bond).group(1)) if bond and re.search(r'([\d.]+)%', bond) else 0
    vix_val = float(re.search(r'([\d.]+)', vix).group(1)) if vix and re.search(r'([\d.]+)', vix) else 0

    analysis_parts = []
    trigger_conditions = []

    # 1. 油价与股市的联动（滞胀逻辑）
    if oil_change > 1.0 and nasdaq_change < -0.5:
        analysis_parts.append("🔗 **滞胀交易逻辑**：WTI原油大涨{:.1f}%，同时纳斯达克下跌{:.1f}%，形成典型的“滞胀”交易组合。能源成本急升侵蚀企业利润，尤其是科技等依赖资本开支的板块首当其冲。同时油价上行推高通胀预期，迫使美联储维持鹰派立场，股债双杀压力持续。".format(oil_change, abs(nasdaq_change)))
        trigger_conditions.append("滞胀")
    elif oil_change > 1.0:
        analysis_parts.append("🛢️ **能源冲击**：油价单日大涨{:.1f}%，地缘政治风险溢价显著升温。若油价持续高位运行，全球通胀回落进程将被打断，央行降息预期或进一步延后。".format(oil_change))

    # 2. 美债收益率与股市估值
    if bond_val > 4.5 and (sp_change < -0.3 or nasdaq_change < -0.5):
        analysis_parts.append("📊 **利率压制估值**：10年期美债收益率报{:.2f}%，处于高位运行。无风险利率上升直接打压风险资产估值，对久期较长的成长股（纳斯达克）形成双重打击。若明日CPI超预期，收益率或进一步冲高至4.7%以上。".format(bond_val))
        trigger_conditions.append("利率压制")
    elif bond_val > 4.5:
        analysis_parts.append("📊 **利率高位运行**：10年期美债收益率维持在{:.2f}%的高位，对全球风险资产的估值中枢构成持续压制。".format(bond_val))

    # 3. VIX恐慌情绪
    if vix_val > 25:
        analysis_parts.append("😱 **恐慌情绪蔓延**：VIX恐慌指数报{:.2f}，处于极度恐慌区间（>25）。历史经验表明，当VIX持续高于25时，市场短期波动率将显著上升，建议投资者控制仓位风险。".format(vix_val))
        trigger_conditions.append("恐慌")
    elif vix_val > 18:
        analysis_parts.append("⚖️ **情绪谨慎**：VIX恐慌指数报{:.2f}，市场处于谨慎观望状态，等待关键数据（CPI/美联储讲话）落地。".format(vix_val))

    # 4. 黄金与地缘风险
    gold_match = re.search(r'([\d.]+)', gold)
    if gold_match:
        gold_val = float(gold_match.group(1))
        if oil_change > 1.0:
            analysis_parts.append("🥇 **黄金避险逻辑**：黄金报{:.0f}美元，在地缘风险升温、实际利率高位震荡的背景下，黄金短期承压但中期配置价值仍在。若后续油价引发通胀失控预期，黄金有望重获上行动能。".format(gold_val))

    # 5. 比特币与风险偏好（新增）
    if btc:
        btc_change = extract_pct(btc)
        if abs(btc_change) > 3:
            direction = "大涨" if btc_change > 0 else "大跌"
            analysis_parts.append("₿ **风险偏好风向标**：比特币今日{} {:.1f}%，作为全球流动性敏感资产，其剧烈波动反映了市场对美联储利率路径的分歧加剧。".format(direction, abs(btc_change)))

    # 6. 亚太市场联动（新增）
    if hsi:
        hsi_change = extract_pct(hsi)
        if abs(hsi_change) > 1.5:
            direction = "涨幅" if hsi_change > 0 else "跌幅"
            analysis_parts.append("🌏 **亚太联动**：恒生指数今日{} {:.1f}%，反映外资对中国经济复苏预期及中美关系走向的定价。".format(direction, abs(hsi_change)))

    # 7. 综合后市展望（基于以上所有条件）
    outlook_conclusion = []
    if "滞胀" in trigger_conditions:
        outlook_conclusion.append("短期市场核心矛盾仍为"滞胀"交易，建议关注能源板块及防御性资产。")
    elif "利率压制" in trigger_conditions:
        outlook_conclusion.append("短期市场聚焦美债收益率走势，若CPI超预期，利率风险将主导市场。")
    elif "恐慌" in trigger_conditions:
        outlook_conclusion.append("恐慌情绪处于高位，短期波动加大，谨慎追高。")
    else:
        outlook_conclusion.append("市场处于震荡格局，方向性突破需等待CPI及美联储讲话的明确信号。")

    if analysis_parts:
        analysis_text = "📌 **综合关联分析**：\n" + "\n".join(["- " + part for part in analysis_parts])
        analysis_text += "\n\n📌 **后市展望**：\n" + " ".join(outlook_conclusion)
        return analysis_text
    else:
        # 如果没有触发任何条件，从新闻中提取机构观点
        return generate_outlook_from_news(news_list)

# ============ 7. 从新闻提取机构观点（备用） ============
def generate_outlook_from_news(news_list):
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
        return "📌 **机构观点**：" + outlook_text
    else:
        return "📌 **短期展望**：市场等待关键数据指引，方向不明，建议关注今夜CPI数据及美联储官员讲话。"

# ============ 8. 生成每日一句话总结 ============
def generate_daily_summary(market_data):
    sp = market_data.get('标普500', '')
    oil = market_data.get('WTI原油', '')
    bond = market_data.get('10年期美债收益率', '')
    vix = market_data.get('VIX恐慌指数', '')

    def extract_pct(val):
        match = re.search(r'([+-][\d.]+)%', val)
        return float(match.group(1)) if match else 0.0

    def extract_abs_change(val):
        match = re.search(r'([+-][\d.]+)(?=\))', val)
        return float(match.group(1)) if match else 0.0

    sp_change = extract_pct(sp)
    oil_change = extract_abs_change(oil)
    bond_val = float(re.search(r'([\d.]+)%', bond).group(1)) if bond and re.search(r'([\d.]+)%', bond) else 0
    vix_val = float(re.search(r'([\d.]+)', vix).group(1)) if vix and re.search(r'([\d.]+)', vix) else 0

    parts = []
    if sp_change > 0.5:
        parts.append("美股走高")
    elif sp_change < -0.5:
        parts.append("美股承压")
    else:
        parts.append("美股震荡")

    if oil_change > 1.0:
        parts.append("油价暴涨推升通胀担忧")
    elif oil_change < -1.0:
        parts.append("油价回落缓解通胀压力")
    else:
        parts.append("油价平稳")

    if bond_val > 4.5:
        parts.append("美债收益率高位运行")
    elif bond_val < 4.0:
        parts.append("美债收益率回落")

    if vix_val > 25:
        parts.append("恐慌情绪蔓延")
    elif vix_val > 18:
        parts.append("市场情绪谨慎")

    summary = "📌 今日总结：" + "，".join(parts) + "。"
    if sp_change < -0.5 and oil_change > 1.0:
        summary += " 呈现"滞胀"交易特征。"
    return summary

# ============ 9. 生成纯文本报告 ============
def generate_text_report(news_list, market_data, deep_analysis, summary):
    date_str = datetime.now().strftime('%Y年%m月%d日')
    lines = []
    lines.append(f"📈 全球金融早报 - {date_str}")
    lines.append("=" * 60)
    lines.append(summary)
    lines.append("")

    lines.append("📊 全球市场概览")
    for name, value in market_data.items():
        lines.append(f"  {name}: {value}")
    lines.append("")

    lines.append(deep_analysis)
    lines.append("")

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

    print("⏳ 生成深度关联分析...")
    deep_analysis = generate_deep_analysis(market, news)

    print("⏳ 生成每日总结...")
    summary = generate_daily_summary(market)

    report = generate_text_report(news, market, deep_analysis, summary)

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ 报告生成完成！")
