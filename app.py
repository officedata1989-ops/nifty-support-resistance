import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nifty 50 Advanced Analyzer",
    layout="wide"
)

st.title("📊 Nifty 50 Advanced Trading Analyzer")
st.caption("Support • Resistance • Fibonacci • EMA • Candlestick • Volume Analysis")

STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "INFOSYS": "INFY.NS",
    "TCS": "TCS.NS",
    "ITC": "ITC.NS",
    "SBIN": "SBIN.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "TATA MOTORS": "TMPV.NS",
    "LT": "LT.NS",
    "AXIS BANK": "AXISBANK.NS",
    "KOTAK BANK": "KOTAKBANK.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "MARUTI": "MARUTI.NS",
    "SUN PHARMA": "SUNPHARMA.NS",
    "WIPRO": "WIPRO.NS",
    "HCL TECH": "HCLTECH.NS",
    "ONGC": "ONGC.NS",
    "NTPC": "NTPC.NS",
    "POWER GRID": "POWERGRID.NS"
}

col1, col2 = st.columns(2)

with col1:
    stock_name = st.selectbox("Select Nifty 50 Stock", list(STOCKS.keys()))

with col2:
    timeframe = st.selectbox(
        "Select Timeframe",
        ["Daily", "Weekly", "Monthly"]
    )

period = st.selectbox(
    "Historical Data",
    ["6 Months", "1 Year", "2 Years", "5 Years"],
    index=1
)

period_map = {
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y"
}

interval_map = {
    "Daily": "1d",
    "Weekly": "1wk",
    "Monthly": "1mo"
}

@st.cache_data(ttl=900)
def get_data(ticker, period, interval):
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data.dropna()

if st.button("Analyze Stock", type="primary"):
    with st.spinner("Fetching market data..."):
        df = get_data(
            STOCKS[stock_name],
            period_map[period],
            interval_map[timeframe]
        )

    if df.empty or len(df) < 30:
        st.error("Data unavailable or insufficient. Please try another stock or timeframe.")
        st.stop()

    df = df.copy()

    for length in [9, 20, 50, 200]:
        df[f"EMA {length}"] = df["Close"].ewm(
            span=length, adjust=False
        ).mean()

    close = float(df["Close"].iloc[-1])
    high = float(df["High"].iloc[-1])
    low = float(df["Low"].iloc[-1])
    volume = float(df["Volume"].iloc[-1])

    st.subheader(f"{stock_name} Analysis")

    a, b, c = st.columns(3)
    a.metric("Latest Close", f"₹{close:,.2f}")
    b.metric("Latest High", f"₹{high:,.2f}")
    c.metric("Latest Low", f"₹{low:,.2f}")

    # Automatic Support and Resistance using historical price zones
    recent = df.tail(120)
    support_values = recent["Low"].nsmallest(3).sort_values().tolist()
    resistance_values = recent["High"].nlargest(3).sort_values(ascending=False).tolist()

    # Classic Pivot Points using previous candle
    prev = df.iloc[-2]
    pivot = (prev["High"] + prev["Low"] + prev["Close"]) / 3
    r1 = (2 * pivot) - prev["Low"]
    s1 = (2 * pivot) - prev["High"]
    r2 = pivot + (prev["High"] - prev["Low"])
    s2 = pivot - (prev["High"] - prev["Low"])
    r3 = prev["High"] + 2 * (pivot - prev["Low"])
    s3 = prev["Low"] - 2 * (prev["High"] - pivot)

    # Fibonacci levels from recent swing high and low
    swing_high = recent["High"].max()
    swing_low = recent["Low"].min()
    difference = swing_high - swing_low

    fib_levels = {
        "23.6%": swing_high - difference * 0.236,
        "38.2%": swing_high - difference * 0.382,
        "50.0%": swing_high - difference * 0.500,
        "61.8%": swing_high - difference * 0.618,
        "78.6%": swing_high - difference * 0.786
    }

    # Candlestick pattern checks on the latest completed candle
    candle = df.iloc[-1]
    previous = df.iloc[-2]

    body = abs(candle["Close"] - candle["Open"])
    candle_range = max(candle["High"] - candle["Low"], 0.0001)
    lower_wick = min(candle["Open"], candle["Close"]) - candle["Low"]
    upper_wick = candle["High"] - max(candle["Open"], candle["Close"])

    patterns = []

    if candle["Close"] > candle["Open"] and previous["Close"] < previous["Open"]:
        if candle["Close"] > previous["Open"] and candle["Open"] < previous["Close"]:
            patterns.append("Bullish Engulfing")

    if candle["Close"] < candle["Open"] and previous["Close"] > previous["Open"]:
        if candle["Open"] > previous["Close"] and candle["Close"] < previous["Open"]:
            patterns.append("Bearish Engulfing")

    if lower_wick > 2 * max(body, 0.01) and upper_wick < candle_range * 0.25:
        patterns.append("Hammer-like candle")

    if upper_wick > 2 * max(body, 0.01) and lower_wick < candle_range * 0.25:
        patterns.append("Shooting Star-like candle")

    if body < candle_range * 0.10:
        patterns.append("Doji")

    if not patterns:
        patterns.append("No listed pattern detected")

    # Chart
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles"
    ))

    for length in [9, 20, 50, 200]:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f"EMA {length}"],
            name=f"EMA {length}"
        ))

    for i, value in enumerate(support_values):
        fig.add_hline(
            y=value, line_dash="dot",
            annotation_text=f"Support {i+1}: {value:.2f}"
        )

    for i, value in enumerate(resistance_values):
        fig.add_hline(
            y=value, line_dash="dot",
            annotation_text=f"Resistance {i+1}: {value:.2f}"
        )

    for name, value in fib_levels.items():
        fig.add_hline(
            y=value, line_dash="dash",
            annotation_text=f"Fib {name}: {value:.2f}"
        )

    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        title=f"{stock_name} - {timeframe} Chart"
    )

    st.plotly_chart(fig, use_container_width=True)

    # EMA summary
    st.subheader("EMA Trend Analysis")

    for length in [9, 20, 50, 200]:
        ema_value = df[f"EMA {length}"].iloc[-1]
        status = "Above EMA - Bullish indication" if close > ema_value else "Below EMA - Bearish indication"
        st.write(f"EMA {length}: ₹{ema_value:.2f} — {status}")

    # Support and resistance
    st.subheader("Automatic Support & Resistance")

    x, y = st.columns(2)

    with x:
        st.write("**Support Levels**")
        for i, value in enumerate(support_values):
            st.write(f"S{i+1}: ₹{value:.2f}")

    with y:
        st.write("**Resistance Levels**")
        for i, value in enumerate(resistance_values):
            st.write(f"R{i+1}: ₹{value:.2f}")

    st.subheader("Classic Pivot Points")

    pivot_table = pd.DataFrame({
        "Level": ["S3", "S2", "S1", "Pivot", "R1", "R2", "R3"],
        "Price": [s3, s2, s1, pivot, r1, r2, r3]
    })

    st.dataframe(pivot_table, hide_index=True, use_container_width=True)

    st.subheader("Fibonacci Retracement")

    fib_table = pd.DataFrame({
        "Level": list(fib_levels.keys()),
        "Price": list(fib_levels.values())
    })

    st.dataframe(fib_table, hide_index=True, use_container_width=True)

    st.caption(
        f"Swing High: ₹{swing_high:.2f} | Swing Low: ₹{swing_low:.2f}"
    )

    # Candlestick confirmation
    st.subheader("Candlestick Confirmation")

    for pattern in patterns:
        st.info(pattern)

    # Volume-based order flow proxy
    st.subheader("Volume Pressure (Proxy)")

    df["Volume Delta Proxy"] = np.where(
        df["Close"] > df["Open"],
        df["Volume"],
        np.where(df["Close"] < df["Open"], -df["Volume"], 0)
    )

    delta = df["Volume Delta Proxy"].tail(20).sum()

    st.metric("20-candle Volume Delta Proxy", f"{delta:,.0f}")

    if delta > 0:
        st.success("Positive volume pressure proxy")
    elif delta < 0:
        st.warning("Negative volume pressure proxy")
    else:
        st.info("Neutral volume pressure proxy")

    st.warning(
        "This is an educational analysis tool, not a guaranteed trading signal. "
        "Candlestick and volume calculations are simplified. "
        "Volume Delta Proxy is NOT true Bid/Ask Order Flow or Footprint data."
    )

st.divider()
st.caption("Nifty 50 Advanced Analyzer | Educational use only")
