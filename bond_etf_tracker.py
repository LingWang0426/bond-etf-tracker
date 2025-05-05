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


# --------------------- 提醒模块 ---------------------
st.subheader("⏰ 降息新闻关注提醒")
if "last_check" not in st.session_state:
    st.session_state["last_check"] = datetime.date.today() - datetime.timedelta(days=7)
days_since = (datetime.date.today() - st.session_state["last_check"]).days
if days_since >= 3:
    st.warning(f"⚠️ 距离你上次查看降息新闻已过去 **{days_since} 天**，建议及时关注并考虑操作。")
else:
    st.success(f"✅ 你最近查看过降息新闻（{days_since} 天前）")
if st.button("📌 我已查看最新新闻"):
    st.session_state["last_check"] = datetime.date.today()
    st.success("✔️ 已记录查看时间，感谢你的关注！")

# --------------------- PRICE FETCHING ---------------------
def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except:
        return "N/A"

def get_history(ticker, period="6mo"):
    try:
        return yf.Ticker(ticker).history(period=period)
    except:
        return None

etf_prices = {
    "VGOV": get_price("VGOV.L"),
    "IEF": get_price("IEF"),
    "TLT": get_price("TLT"),
    "AGGH": get_price("AGGH")  # 使用 AGGH 美股主代码
}

# --------------------- ETF PRICE TREND ---------------------
st.subheader("📈 ETF 价格走势图（过去6个月）")
selected_etf = st.selectbox("选择查看的ETF", list(etf_prices.keys()))
data = get_history(selected_etf if selected_etf != "VGOV" else "VGOV.L")
if data is not None and not data.empty:
    st.line_chart(data["Close"])
else:
    st.warning("⚠️ 未能获取该ETF的历史价格数据")



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

# --------------------- 汇率 / 利率变化追踪 ---------------------
st.subheader("💱 汇率与利率变化追踪（近30天）")

@st.cache_data(ttl=3600)
def get_fx_and_rate():
    fx_data = yf.download("GBPUSD=X", period="1mo")
    rate_data = yf.download("^IRX", period="1mo")  # 美国13周国债利率
    return fx_data["Close"], rate_data["Close"]

fx, rate = get_fx_and_rate()
col1, col2 = st.columns(2)
with col1:
    st.write("📊 英镑兑美元汇率")
    st.line_chart(fx)
with col2:
    st.write("📈 美国短期利率 (^IRX)")
    st.line_chart(rate)

# --------------------- END ---------------------
st.markdown("---")
st.caption("如需提醒功能，可结合 email + GitHub Actions 定时运行此页面逻辑。")
