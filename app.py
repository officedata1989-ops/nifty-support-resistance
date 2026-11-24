import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Nifty Advanced Analyzer", page_icon="📈", layout="wide")
st.markdown("""
<style>
.stApp{background:#0b1220;color:#eef2ff}
[data-testid="stSidebar"]{background:#111c2f}
.block-container{padding-top:1.2rem}
.metric-card{background:linear-gradient(135deg,#17263d,#101a2c);border:1px solid #263a57;border-radius:14px;padding:15px;min-height:100px}
.metric-label{color:#9fb2cc;font-size:13px}
.metric-value{color:#f8fafc;font-size:24px;font-weight:700}
.metric-note{color:#9fb2cc;font-size:12px}
</style>
""", unsafe_allow_html=True)

st.title("📈 Nifty Advanced Analyzer")
st.caption("Support & Resistance • Fibonacci • EMA • Candlestick • Volume Analysis")

INDEXES = {"NIFTY 50":"^NSEI", "BANK NIFTY":"^NSEBANK", "FINNIFTY":"^CNXFINANCE"}
STOCKS = {
"RELIANCE":"RELIANCE.NS","HDFC BANK":"HDFCBANK.NS","ICICI BANK":"ICICIBANK.NS",
"INFOSYS":"INFY.NS","TCS":"TCS.NS","ITC":"ITC.NS","STATE BANK OF INDIA":"SBIN.NS",
"BHARTI AIRTEL":"BHARTIARTL.NS","LARSEN & TOUBRO":"LT.NS","AXIS BANK":"AXISBANK.NS",
"KOTAK MAHINDRA BANK":"KOTAKBANK.NS","BAJFINANCE":"BAJFINANCE.NS","MARUTI SUZUKI":"MARUTI.NS",
"SUN PHARMA":"SUNPHARMA.NS","WIPRO":"WIPRO.NS","HCL TECHNOLOGIES":"HCLTECH.NS",
"ONGC":"ONGC.NS","NTPC":"NTPC.NS","POWER GRID":"POWERGRID.NS","TATA STEEL":"TATASTEEL.NS",
"ADANI PORTS":"ADANIPORTS.NS","ASIAN PAINTS":"ASIANPAINT.NS","TITAN":"TITAN.NS",
"ULTRATECH CEMENT":"ULTRACEMCO.NS","NESTLE INDIA":"NESTLEIND.NS","HINDUSTAN UNILEVER":"HINDUNILVR.NS",
"BAJAJ FINSERV":"BAJAJFINSV.NS","COAL INDIA":"COALINDIA.NS","JSW STEEL":"JSWSTEEL.NS",
"TATA MOTORS":"TMPV.NS","TECH MAHINDRA":"TECHM.NS","INDUSIND BANK":"INDUSINDBK.NS",
"GRASIM":"GRASIM.NS","CIPLA":"CIPLA.NS","DR REDDYS":"DRREDDY.NS","EICHER MOTORS":"EICHERMOT.NS",
"APOLLO HOSPITALS":"APOLLOHOSP.NS","BRITANNIA":"BRITANNIA.NS","HINDALCO":"HINDALCO.NS",
"TATA CONSUMER":"TATACONSUM.NS","DIVIS LAB":"DIVISLAB.NS","HEROMOTOCO":"HEROMOTOCO.NS",
"BPCL":"BPCL.NS","SHRIRAM FINANCE":"SHRIRAMFIN.NS","BEL":"BEL.NS","TRENT":"TRENT.NS",
"MAX HEALTHCARE":"MAXHEALTH.NS","BAJAJ AUTO":"BAJAJ-AUTO.NS","ADANI ENTERPRISES":"ADANIENT.NS",
"ETERNAL":"ETERNAL.NS","JIO FINANCIAL":"JIOFIN.NS"
}

@st.cache_data(ttl=900)
def load_data(symbol, period, interval):
    d = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty: return pd.DataFrame()
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    cols = ["Open","High","Low","Close","Volume"]
    if not all(c in d.columns for c in cols): return pd.DataFrame()
    return d[cols].dropna()

st.sidebar.header("⚙️ Analysis Settings")
kind = st.sidebar.radio("Market", ["Indices","Nifty 50 Stocks"])
if kind == "Indices":
    name = st.sidebar.selectbox("Select Index", list(INDEXES))
    ticker = INDEXES[name]
else:
    name = st.sidebar.selectbox("Select Stock", list(STOCKS))
    ticker = STOCKS[name]
tf = st.sidebar.selectbox("Timeframe", ["Daily","Weekly","Monthly"])
hist = st.sidebar.selectbox("History", ["6 Months","1 Year","2 Years","5 Years"], index=1)
period = {"6 Months":"6mo","1 Year":"1y","2 Years":"2y","5 Years":"5y"}[hist]
interval = {"Daily":"1d","Weekly":"1wk","Monthly":"1mo"}[tf]
st.sidebar.divider()
st.sidebar.subheader("Chart Layers")
show_ema = st.sidebar.checkbox("EMA 9 / 20 / 50 / 200", True)
show_sr = st.sidebar.checkbox("Automatic Support / Resistance", True)
show_fib = st.sidebar.checkbox("Fibonacci", True)
show_pivot = st.sidebar.checkbox("Pivot Points", False)
show_volume = st.sidebar.checkbox("Volume panel", True)

st.markdown(f"### {name} · {tf} Chart")
with st.spinner("Loading market data..."):
    df = load_data(ticker, period, interval)
if df.empty or len(df) < 30:
    st.error("Data unavailable or insufficient. Try another selection. Yahoo Finance data can be delayed or unavailable.")
    st.stop()

for n in [9,20,50,200]:
    df[f"EMA{n}"] = df["Close"].ewm(span=n, adjust=False).mean()
last, prev = df.iloc[-1], df.iloc[-2]
close = float(last["Close"])
chg = close-float(prev["Close"])
pct = chg/float(prev["Close"])*100 if float(prev["Close"]) else 0
ema20, ema50 = float(df["EMA20"].iloc[-1]), float(df["EMA50"].iloc[-1])
bias = "BULLISH" if close>ema50 and ema20>ema50 else ("BEARISH" if close<ema50 and ema20<ema50 else "SIDEWAYS / MIXED")

a,b,c,d = st.columns(4)
def card(col, label, value, note):
    col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)
card(a,"LAST CLOSE",f"₹{close:,.2f}",f"{chg:+.2f} ({pct:+.2f}%)")
card(b,"MARKET BIAS",bias,"Based on EMA 20 and EMA 50")
card(c,"EMA 20",f"₹{ema20:,.2f}","Short-term trend guide")
card(d,"EMA 200",f"₹{float(df['EMA200'].iloc[-1]):,.2f}","Long-term trend guide")

recent = df.tail(120)
supports = sorted(recent["Low"].nsmallest(3).tolist())
resists = sorted(recent["High"].nlargest(3).tolist(), reverse=True)
ph,pl,pc = map(float,[prev["High"],prev["Low"],prev["Close"]])
p=(ph+pl+pc)/3
piv={"S3":pl-2*(ph-p),"S2":p-(ph-pl),"S1":2*p-ph,"Pivot":p,"R1":2*p-pl,"R2":p+(ph-pl),"R3":ph+2*(p-pl)}
hi,lo=float(recent["High"].max()),float(recent["Low"].min())
diff=hi-lo
fib={k:hi-diff*r for k,r in [("23.6%",.236),("38.2%",.382),("50%",.5),("61.8%",.618),("78.6%",.786)]} if diff>0 else {}

st.markdown("#### 🕯️ Price Action Chart")
fig=make_subplots(rows=2 if show_volume else 1, cols=1, shared_xaxes=True,
    vertical_spacing=.035, row_heights=[.78,.22] if show_volume else [1],
    subplot_titles=("Candlesticks & Indicators","Volume") if show_volume else ("Candlesticks & Indicators",))
fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,
    name="Price",increasing_line_color="#20c997",decreasing_line_color="#ff5c70"),row=1,col=1)
colors={9:"#facc15",20:"#38bdf8",50:"#c084fc",200:"#fb923c"}
if show_ema:
    for n,col in colors.items():
        fig.add_trace(go.Scatter(x=df.index,y=df[f"EMA{n}"],name=f"EMA {n}",line=dict(color=col,width=2)),row=1,col=1)
if show_sr:
    for i,v in enumerate(supports,1):
        fig.add_hline(y=v,line=dict(color="#22c55e",dash="dot"),annotation_text=f"S{i} ₹{v:.0f}",row=1,col=1)
    for i,v in enumerate(resists,1):
        fig.add_hline(y=v,line=dict(color="#fb7185",dash="dot"),annotation_text=f"R{i} ₹{v:.0f}",row=1,col=1)
if show_fib:
    for label,v in fib.items():
        fig.add_hline(y=v,line=dict(color="#94a3b8",dash="dash",width=1),annotation_text=f"Fib {label}",row=1,col=1)
if show_pivot:
    fig.add_hline(y=p,line=dict(color="#f59e0b",width=2),annotation_text=f"Pivot ₹{p:.0f}",row=1,col=1)
if show_volume:
    volcolors=np.where(df.Close>=df.Open,"#20c997","#ff5c70")
    fig.add_trace(go.Bar(x=df.index,y=df.Volume,name="Volume",marker_color=volcolors),row=2,col=1)
    fig.update_yaxes(title_text="Volume",row=2,col=1)
fig.update_layout(template="plotly_dark",height=760,paper_bgcolor="#0b1220",plot_bgcolor="#0f1b2d",
    font=dict(color="#e5e7eb"),xaxis_rangeslider_visible=False,hovermode="x unified",
    legend=dict(orientation="h",y=1.04,x=0),margin=dict(l=15,r=25,t=65,b=15))
fig.update_xaxes(showgrid=True,gridcolor="#23334a")
fig.update_yaxes(showgrid=True,gridcolor="#23334a",title_text="Price",row=1,col=1)
st.plotly_chart(fig,use_container_width=True,config={"scrollZoom":True,"displaylogo":False})

left,right=st.columns(2)
with left:
    st.markdown("#### 🟢 Automatic Support")
    st.dataframe(pd.DataFrame({"Level":["S1","S2","S3"],"Price (₹)":[round(x,2) for x in supports]}),hide_index=True,use_container_width=True)
    st.markdown("#### 🔴 Automatic Resistance")
    st.dataframe(pd.DataFrame({"Level":["R1","R2","R3"],"Price (₹)":[round(x,2) for x in resists]}),hide_index=True,use_container_width=True)
with right:
    st.markdown("#### 🧭 Fibonacci Retracement")
    st.dataframe(pd.DataFrame({"Level":list(fib),"Price (₹)":[round(x,2) for x in fib.values()]}),hide_index=True,use_container_width=True)
    st.markdown("#### 📐 Classic Pivot Points")
    st.dataframe(pd.DataFrame({"Level":list(piv),"Price (₹)":[round(x,2) for x in piv.values()]}),hide_index=True,use_container_width=True)

candle, before = df.iloc[-1], df.iloc[-2]
body=abs(float(candle.Close)-float(candle.Open))
rng=max(float(candle.High)-float(candle.Low),1e-9)
lw=min(float(candle.Open),float(candle.Close))-float(candle.Low)
uw=float(candle.High)-max(float(candle.Open),float(candle.Close))
patterns=[]
if candle.Close>candle.Open and before.Close<before.Open and candle.Close>=before.Open and candle.Open<=before.Close: patterns.append("Bullish Engulfing")
if candle.Close< candle.Open and before.Close>before.Open and candle.Open>=before.Close and candle.Close<=before.Open: patterns.append("Bearish Engulfing")
if lw>2*max(body,.01) and uw<rng*.25: patterns.append("Hammer-like candle")
if uw>2*max(body,.01) and lw<rng*.25: patterns.append("Shooting Star-like candle")
if body<rng*.1: patterns.append("Doji")
st.markdown("#### 🔎 Latest Candle Confirmation")
st.write("Latest candle date:",df.index[-1].strftime("%d %b %Y"))
for pat in (patterns or ["No listed pattern detected"]): st.info(pat)
st.caption("Pattern labels are simplified rules. Confirm after candle close and consider trend, price level and volume.")

delta_series=np.where(df.Close>df.Open,df.Volume,np.where(df.Close<df.Open,-df.Volume,0))
delta=float(pd.Series(delta_series,index=df.index).tail(20).sum())
st.markdown("#### 🌊 Volume Pressure (Proxy only)")
x,y=st.columns(2)
x.metric("20-candle Volume Delta Proxy",f"{delta:,.0f}")
y.metric("Latest Volume",f"{float(last.Volume):,.0f}")
st.caption("This is a candle-colour volume estimate, NOT true Bid/Ask Order Flow, CVD or Footprint data.")

with st.expander("📘 How to read this dashboard"):
    st.markdown("""
    - Green candles closed above their open; red candles closed below their open.
    - EMA 9/20 are faster trend guides; EMA 50/200 show broader trend context.
    - Support and resistance are historical price areas, not guaranteed turning points.
    - Fibonacci levels are calculated from the highest high and lowest low in the latest 120 candles.
    - Candle patterns are clues, not standalone Buy/Sell signals.
    - Volume Pressure is only a proxy. Real Footprint/CVD requires trade-level bid/ask data.
    """)
st.warning("Educational charting tool only. Yahoo Finance data may be delayed or unavailable. Verify prices with your broker; no signal is guaranteed.")
st.caption("Nifty Advanced Analyzer • Learning and chart study")
