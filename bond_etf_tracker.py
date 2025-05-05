# bond_etf_tracker.py
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import requests

# --------------------- CONFIG ---------------------
target_allocations = {
    "VGOV": 21000,
    "IEF": 18000,
    "TLT": 12000,
    "AGGH": 9000
}
total_investment = sum(target_allocations.values())

# --------------------- PAGE SETUP ---------------------
st.set_page_config(page_title="债券ETF建仓追踪器", layout="wide")
st.title("📊 债券ETF建仓追踪器")

# --------------------- PRICE FETCHING ---------------------
def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except:
        return "N/A"

etf_prices = {
    "VGOV": get_price("VGOV.L"),
    "IEF": get_price("IEF"),
    "TLT": get_price("TLT"),
    "AGGH": get_price("AGGH.L")
}

# --------------------- INPUT TRACKER ---------------------
st.subheader("✅ 当前持仓记录（手动输入或连接账户）")
input_data = []

for etf, target in target_allocations.items():
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        bought = st.number_input(f"{etf} 已买入金额 (£)", min_value=0, max_value=int(target), value=0, step=100)
    with col2:
        st.markdown(f"**当前价格：** {etf_prices[etf]} $")
    with col3:
        pct = (bought / target) * 100 if target > 0 else 0
        st.markdown(f"**建仓进度：** {pct:.1f}%")
    input_data.append((etf, bought, target, pct))

# --------------------- PROGRESS TABLE ---------------------
st.subheader("📋 建仓进度汇总")
df = pd.DataFrame(input_data, columns=["ETF", "已买入 (£)", "目标金额 (£)", "进度 (%)"])
st.dataframe(df.set_index("ETF"))

# --------------------- NEWSAPI 替代爬虫 ---------------------
st.subheader("📰 最新央行降息信号追踪（来自 NewsAPI）")

NEWS_API_KEY = "4b52930471c045eaab3717fe4a3acd8d"

@st.cache_data(ttl=3600)
def fetch_news(query):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        resp = requests.get(url)
        data = resp.json()
        articles = data.get("articles", [])[:5]
        return [(a['title'], a['url']) for a in articles]
    except:
        return []

with st.expander("🇬🇧 英国央行降息相关新闻（关键词：Bank of England rate cut）"):
    for title, link in fetch_news("Bank of England rate cut"):
        st.markdown(f"- [{title}]({link})")

with st.expander("🇺🇸 美国联储降息相关新闻（关键词：Fed interest rate cut）"):
    for title, link in fetch_news("Fed interest rate cut"):
        st.markdown(f"- [{title}]({link})")

# --------------------- END ---------------------
st.markdown("---")
st.caption("如需提醒功能，可结合 email + GitHub Actions 定时运行此页面逻辑。")
# --------------------- TICKER 测试 ---------------------
st.subheader("🔍 AGGH 当前价格测试")

for ticker in ["AGGH", "AGGH.L", "AGGH.AS"]:
    try:
        p = get_price(ticker)
        st.write(f"{ticker} 当前价格：{p}")
    except Exception as e:
        st.write(f"{ticker} 错误：{e}")
