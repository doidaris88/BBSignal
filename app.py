import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Crypto Signal Dashboard",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DARK THEME CSS ───────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Dark background */
  .stApp { background-color: #030508; color: #e8eaf0; }
  [data-testid="stSidebar"] { background-color: #07090f; border-right: 1px solid #0f1525; }
  [data-testid="stMetricValue"] { color: #e8eaf0; font-family: monospace; }

  /* Cards */
  .signal-card {
    background: #07090f;
    border: 1px solid #0f1525;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
  }
  .buy-card  { border-color: #00ff8855; background: linear-gradient(135deg, #00ff8808, #07090f); }
  .sell-card { border-color: #ff446655; background: linear-gradient(135deg, #ff446608, #07090f); }
  .hold-card { border-color: #ffaa0055; background: linear-gradient(135deg, #ffaa0008, #07090f); }

  /* Action badges */
  .badge-buy  { color: #00ff88; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #00ff8888; }
  .badge-sell { color: #ff4466; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #ff446688; }
  .badge-hold { color: #ffaa00; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #ffaa0088; }

  /* Labels */
  .label-dim  { color: #3a4560; font-size: 11px; font-family: monospace; letter-spacing: 2px; }
  .price-main { color: #e8eaf0; font-size: 20px; font-weight: 700; font-family: monospace; }
  .change-pos { color: #00ff88; font-family: monospace; }
  .change-neg { color: #ff4466; font-family: monospace; }

  /* Hide default streamlit elements */
  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }
  header     { visibility: hidden; }

  /* Metrics override */
  [data-testid="stMetric"] {
    background: #07090f;
    border: 1px solid #0f1525;
    border-radius: 10px;
    padding: 12px 16px;
  }
  div[data-testid="stMetricLabel"] > div { color: #3a4560 !important; font-family: monospace; font-size: 11px; letter-spacing: 2px; }

  /* Signal indicator dot */
  .dot-buy  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 6px #00ff88; margin-right: 6px; }
  .dot-sell { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ff4466; box-shadow: 0 0 6px #ff4466; margin-right: 6px; }
  .dot-hold { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ffaa00; box-shadow: 0 0 6px #ffaa00; margin-right: 6px; }
  .dot-neu  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3a4560; margin-right: 6px; }

  /* Progress bar */
  .prog-bar-bg { background: #1a2040; border-radius: 4px; height: 6px; width: 100%; }
  .prog-bar-fill-buy  { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #00ff8866, #00ff88); box-shadow: 0 0 8px #00ff8844; transition: width 0.5s; }
  .prog-bar-fill-sell { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #ff446666, #ff4466); box-shadow: 0 0 8px #ff446644; transition: width 0.5s; }
  .prog-bar-fill-hold { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #ffaa0066, #ffaa00); box-shadow: 0 0 8px #ffaa0044; transition: width 0.5s; }

  /* Grid separator */
  hr { border-color: #0f1525; }

  /* Streamlit button */
  .stButton > button {
    background: #07090f;
    color: #00ff88;
    border: 1px solid #0f1525;
    border-radius: 8px;
    font-family: monospace;
    letter-spacing: 2px;
    font-size: 11px;
  }
  .stButton > button:hover {
    border-color: #00ff8844;
    color: #00ff88;
    background: #0a0e18;
  }

  /* Selectbox */
  .stSelectbox > div > div {
    background: #07090f;
    border-color: #0f1525;
    color: #e8eaf0;
  }
</style>
""", unsafe_allow_html=True)

# ─── COIN CONFIG ─────────────────────────────────────────────────────────────

COINS = [
    {"symbol": "BTCUSDT",  "name": "Bitcoin",        "short": "BTC",  "color": "#f7931a", "icon": "₿"},
    {"symbol": "ETHUSDT",  "name": "Ethereum",       "short": "ETH",  "color": "#627eea", "icon": "Ξ"},
    {"symbol": "SOLUSDT",  "name": "Solana",         "short": "SOL",  "color": "#9945ff", "icon": "◎"},
    {"symbol": "BNBUSDT",  "name": "BNB",            "short": "BNB",  "color": "#f0b90b", "icon": "B"},
    {"symbol": "XRPUSDT",  "name": "XRP",            "short": "XRP",  "color": "#00aae4", "icon": "✕"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin",       "short": "DOGE", "color": "#c2a633", "icon": "Ð"},
    {"symbol": "ADAUSDT",  "name": "Cardano",        "short": "ADA",  "color": "#0077cc", "icon": "₳"},
    {"symbol": "AVAXUSDT", "name": "Avalanche",      "short": "AVAX", "color": "#e84142", "icon": "A"},
    {"symbol": "LINKUSDT", "name": "Chainlink",      "short": "LINK", "color": "#2a5ada", "icon": "⬡"},
    {"symbol": "POLUSDT",  "name": "Polygon (POL)",  "short": "POL",  "color": "#8247e5", "icon": "M"},
]

COIN_MAP = {c["symbol"]: c for c in COINS}
BASE_URL = "https://api.binance.com/api/v3"

# ─── TECHNICAL INDICATORS ────────────────────────────────────────────────────

def calc_ema(prices: np.ndarray, period: int) -> np.ndarray:
    k = 2 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    return ema

def calc_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    diffs = np.diff(prices)
    gains  = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    avg_g = gains[:period].mean()
    avg_l = losses[:period].mean()
    for i in range(period, len(diffs)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    return 100.0 - 100.0 / (1 + avg_g / avg_l)

def calc_macd_hist(prices: np.ndarray) -> float:
    if len(prices) < 27:
        return 0.0
    e12   = calc_ema(prices, 12)
    e26   = calc_ema(prices, 26)
    line  = e12 - e26
    sig   = calc_ema(line[25:], 9)
    return float(line[-1] - sig[-1])

def calc_stoch_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period * 2:
        return 50.0
    rsi_arr = np.array([calc_rsi(prices[i - period: i + 1], period)
                        for i in range(period, len(prices))])
    window   = rsi_arr[-period:]
    rng      = window.max() - window.min()
    if rng == 0:
        return 50.0
    return float((rsi_arr[-1] - window.min()) / rng * 100)

def calc_bb_position(prices: np.ndarray, current_price: float) -> float:
    if len(prices) < 20:
        return 0.5
    window = prices[-20:]
    ma  = window.mean()
    std = window.std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    rng = upper - lower
    if rng == 0:
        return 0.5
    return float(np.clip((current_price - lower) / rng, 0, 1))

def calc_vwap(klines: list) -> float:
    sum_pv = sum_v = 0.0
    for k in klines:
        tp = (float(k[2]) + float(k[3]) + float(k[4])) / 3
        v  = float(k[5])
        sum_pv += tp * v
        sum_v  += v
    return sum_pv / sum_v if sum_v else 0.0

# ─── BINANCE FETCH ────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_coin(symbol: str) -> dict | None:
    try:
        ticker_r = requests.get(f"{BASE_URL}/ticker/24hr", params={"symbol": symbol}, timeout=10)
        klines_r = requests.get(f"{BASE_URL}/klines", params={"symbol": symbol, "interval": "15m", "limit": 100}, timeout=10)
        if not ticker_r.ok or not klines_r.ok:
            return None
        ticker = ticker_r.json()
        klines = klines_r.json()
        if "code" in ticker:
            return None

        price     = float(ticker["lastPrice"])
        change24h = float(ticker["priceChangePercent"])
        high24h   = float(ticker["highPrice"])
        low24h    = float(ticker["lowPrice"])
        volume24h = float(ticker["quoteVolume"])

        closes = np.array([float(k[4]) for k in klines])
        vols   = np.array([float(k[5]) for k in klines])

        avg_vol   = vols[-21:-1].mean() if len(vols) >= 21 else vols.mean()
        vol_ratio = float(vols[-1] / avg_vol) if avg_vol > 0 else 1.0

        ema9  = float(calc_ema(closes, 9)[-1])
        ema21 = float(calc_ema(closes, 21)[-1])
        ema50 = float(calc_ema(closes, 50)[-1])

        return {
            "price":      price,
            "change24h":  change24h,
            "high24h":    high24h,
            "low24h":     low24h,
            "volume24h":  volume24h,
            "sparkline":  closes[-30:].tolist(),
            "closes":     closes.tolist(),
            "rsi":        calc_rsi(closes),
            "macd_hist":  calc_macd_hist(closes),
            "stoch_rsi":  calc_stoch_rsi(closes),
            "bb":         calc_bb_position(closes, price),
            "vwap":       calc_vwap(klines),
            "ema9":       ema9,
            "ema21":      ema21,
            "ema50":      ema50,
            "vol_ratio":  vol_ratio,
            "klines":     klines,
        }
    except Exception:
        return None

# ─── SIGNAL ENGINE ────────────────────────────────────────────────────────────

def compute_signal(data: dict) -> dict:
    if not data:
        return {"action": "HOLD", "color": "#ffaa00", "strength": 0, "buy": 0, "sell": 0, "signals": []}

    price, rsi, macd_hist = data["price"], data["rsi"], data["macd_hist"]
    stoch_rsi, bb         = data["stoch_rsi"], data["bb"]
    vwap_val              = data["vwap"]
    ema9, ema21, ema50    = data["ema9"], data["ema21"], data["ema50"]
    vol_ratio             = data["vol_ratio"]

    signals, buy, sell = [], 0, 0

    # RSI
    if   rsi < 30: signals.append(("RSI",       f"{rsi:.0f}",     "buy",  "Sangat Oversold",   3)); buy  += 3
    elif rsi < 40: signals.append(("RSI",       f"{rsi:.0f}",     "buy",  "Oversold",          1)); buy  += 1
    elif rsi > 70: signals.append(("RSI",       f"{rsi:.0f}",     "sell", "Sangat Overbought", 3)); sell += 3
    elif rsi > 60: signals.append(("RSI",       f"{rsi:.0f}",     "sell", "Overbought",        1)); sell += 1
    else:          signals.append(("RSI",       f"{rsi:.0f}",     "neu",  "Netral",            0))

    # MACD (normalised by price)
    macd_norm = (macd_hist / price * 1000) if price else 0
    macd_disp = f"{macd_hist:.6f}" if abs(macd_hist) < 100 else f"{macd_hist:.2f}"
    if   macd_norm >  0.08: signals.append(("MACD",      f"▲ {macd_disp}", "buy",  "Bullish momentum", 2)); buy  += 2
    elif macd_norm < -0.08: signals.append(("MACD",      f"▼ {macd_disp}", "sell", "Bearish momentum", 2)); sell += 2
    else:                   signals.append(("MACD",      macd_disp,        "neu",  "Lemah / ranging",  0))

    # Stoch RSI
    if   stoch_rsi < 20: signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "buy",  "Extreme oversold",  2)); buy  += 2
    elif stoch_rsi > 80: signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "sell", "Extreme overbought",2)); sell += 2
    else:                signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "neu",  "Normal",            0))

    # VWAP
    if   price > vwap_val * 1.002: signals.append(("VWAP",       fmt_price(vwap_val), "buy",  "Di atas VWAP",  1)); buy  += 1
    elif price < vwap_val * 0.998: signals.append(("VWAP",       fmt_price(vwap_val), "sell", "Di bawah VWAP", 1)); sell += 1
    else:                          signals.append(("VWAP",       fmt_price(vwap_val), "neu",  "Di VWAP",       0))

    # EMA Stack
    if   ema9 > ema21 > ema50: signals.append(("EMA Stack", "BULL 9>21>50", "buy",  "Bullish stack", 2)); buy  += 2
    elif ema9 < ema21 < ema50: signals.append(("EMA Stack", "BEAR 9<21<50", "sell", "Bearish stack", 2)); sell += 2
    elif ema9 > ema21:         signals.append(("EMA Stack", "GOLDEN",       "buy",  "EMA9 > EMA21",  1)); buy  += 1
    else:                      signals.append(("EMA Stack", "DEATH",        "sell", "EMA9 < EMA21",  1)); sell += 1

    # Bollinger Bands
    if   bb < 0.1: signals.append(("BB Band",   "LOWER", "buy",  "Near lower band",  1)); buy  += 1
    elif bb > 0.9: signals.append(("BB Band",   "UPPER", "sell", "Near upper band",  1)); sell += 1
    else:          signals.append(("BB Band",   f"{bb*100:.0f}%", "neu", "Dalam bands", 0))

    # Volume
    if   vol_ratio > 2.0: signals.append(("Volume",    f"{vol_ratio:.1f}x", "buy", "Volume surge!", 2)); buy  += 2
    elif vol_ratio > 1.3: signals.append(("Volume",    f"{vol_ratio:.1f}x", "buy", "Volume tinggi", 1)); buy  += 1
    elif vol_ratio < 0.5: signals.append(("Volume",    f"{vol_ratio:.1f}x", "neu", "Volume rendah", 0))
    else:                 signals.append(("Volume",    f"{vol_ratio:.1f}x", "neu", "Normal",        0))

    total = buy + sell
    net   = (buy - sell) / max(total, 1)

    if   net >  0.28: action, color, strength = "BUY",  "#00ff88", min(net * 95, 95)
    elif net < -0.28: action, color, strength = "SELL", "#ff4466", min(abs(net) * 95, 95)
    else:             action, color, strength = "HOLD", "#ffaa00", abs(net) * 55

    return {"action": action, "color": color, "strength": strength, "buy": buy, "sell": sell, "signals": signals}

# ─── FORMATTERS ───────────────────────────────────────────────────────────────

def fmt_price(v: float) -> str:
    if v is None or np.isnan(v): return "—"
    if v >= 10000: return f"{v:,.0f}"
    if v >= 1000:  return f"{v:,.2f}"
    if v >= 1:     return f"{v:.4f}"
    if v >= 0.001: return f"{v:.5f}"
    return f"{v:.8f}"

def fmt_vol(v: float) -> str:
    if not v: return "—"
    if v >= 1e9: return f"${v/1e9:.2f}B"
    if v >= 1e6: return f"${v/1e6:.1f}M"
    if v >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"

# ─── CHART ────────────────────────────────────────────────────────────────────

def make_candle_chart(data: dict, coin: dict) -> go.Figure:
    klines = data["klines"]
    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","vol","close_time",
        "qvol","trades","tbase","tquote","ignore"
    ])
    df["time"]  = pd.to_datetime(df["time"], unit="ms")
    df["open"]  = df["open"].astype(float)
    df["high"]  = df["high"].astype(float)
    df["low"]   = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["vol"]   = df["vol"].astype(float)

    closes = df["close"].values
    ema9_arr  = calc_ema(closes, 9)
    ema21_arr = calc_ema(closes, 21)
    ema50_arr = calc_ema(closes, 50)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.02,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color="#00ff88", decreasing_line_color="#ff4466",
        increasing_fillcolor="#00ff8833", decreasing_fillcolor="#ff446633",
        name="Price", showlegend=False,
    ), row=1, col=1)

    # EMAs
    for arr, color, name in [(ema9_arr, "#ffaa00", "EMA9"), (ema21_arr, "#4488ff", "EMA21"), (ema50_arr, "#ff8844", "EMA50")]:
        fig.add_trace(go.Scatter(x=df["time"], y=arr, line=dict(color=color, width=1), name=name, opacity=0.85), row=1, col=1)

    # VWAP
    vwap_line = np.full(len(df), data["vwap"])
    fig.add_trace(go.Scatter(x=df["time"], y=vwap_line, line=dict(color="#cc88ff", width=1, dash="dot"), name="VWAP"), row=1, col=1)

    # Volume bars
    vol_colors = ["#00ff8855" if c >= o else "#ff446655" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df["time"], y=df["vol"], marker_color=vol_colors, name="Volume", showlegend=False), row=2, col=1)

    # RSI
    closes_arr = np.array(closes)
    rsi_arr = [calc_rsi(closes_arr[:i+1]) for i in range(14, len(closes_arr))]
    fig.add_trace(go.Scatter(
        x=df["time"].iloc[14:], y=rsi_arr,
        line=dict(color="#9955ff", width=1.5), name="RSI", showlegend=False,
    ), row=3, col=1)
    fig.add_hline(y=70, line=dict(color="#ff446666", width=1, dash="dot"), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="#00ff8866", width=1, dash="dot"), row=3, col=1)
    fig.add_hline(y=50, line=dict(color="#3a456088", width=1, dash="dot"), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#07090f",
        plot_bgcolor="#030508",
        font=dict(family="monospace", color="#8890b0", size=10),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            bgcolor="#07090f", bordercolor="#0f1525", borderwidth=1,
            font=dict(size=9), orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
        ),
    )
    for axis in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{axis: dict(
            gridcolor="#0f1525", gridwidth=1,
            zerolinecolor="#0f1525",
            showgrid=True,
        )})

    fig.update_yaxes(title_text="Price", row=1, col=1, title_font=dict(size=9))
    fig.update_yaxes(title_text="Vol",   row=2, col=1, title_font=dict(size=9))
    fig.update_yaxes(title_text="RSI",   row=3, col=1, title_font=dict(size=9), range=[0, 100])

    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("<p class='label-dim'>CRYPTO SIGNAL DASHBOARD</p>", unsafe_allow_html=True)
    st.markdown("---")

    coin_options = {f"{c['icon']} {c['short']} — {c['name']}": c["symbol"] for c in COINS}
    selected_label = st.selectbox("Pilih Coin", list(coin_options.keys()), index=0)
    selected_symbol = coin_options[selected_label]

    st.markdown("---")
    refresh = st.button("⟳  REFRESH DATA", use_container_width=True)
    if refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<p class='label-dim'>AUTO REFRESH</p>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Aktifkan (30 detik)", value=False)

    st.markdown("---")
    st.markdown("<p class='label-dim'>DATA SOURCE</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00ff88;font-family:monospace;font-size:11px;'>● Binance Public API</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#3a4560;font-family:monospace;font-size:10px;'>Real-time · No API key required<br>Timeframe: 15m candles</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p class='label-dim'>INDIKATOR</p>", unsafe_allow_html=True)
    for ind in ["RSI (14)", "MACD (12,26,9)", "Stochastic RSI", "VWAP", "EMA 9/21/50", "Bollinger Bands", "Volume Ratio"]:
        st.markdown(f"<p style='color:#3a4560;font-family:monospace;font-size:10px;'>• {ind}</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<p style='color:#1e2850;font-family:monospace;font-size:9px;'>⚠ Bukan financial advice.<br>Selalu DYOR & manage risiko.</p>",
        unsafe_allow_html=True
    )

# ─── FETCH ALL DATA ───────────────────────────────────────────────────────────

all_data = {}
progress = st.progress(0, text="Fetching data dari Binance...")
for i, coin in enumerate(COINS):
    all_data[coin["symbol"]] = fetch_coin(coin["symbol"])
    progress.progress((i + 1) / len(COINS), text=f"Loading {coin['short']}...")
progress.empty()

selected_data = all_data.get(selected_symbol)
selected_coin = COIN_MAP[selected_symbol]

# Compute signals
signals_map = {sym: compute_signal(d) for sym, d in all_data.items()}
selected_sig = signals_map[selected_symbol]

# ─── HEADER ───────────────────────────────────────────────────────────────────

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    st.markdown(f"""
    <div style='margin-bottom:4px'>
      <span style='color:#00ff88;font-family:monospace;font-size:10px;letter-spacing:3px;'>
        ● LIVE · BINANCE API · {now_str}
      </span>
    </div>
    <h1 style='color:#e8eaf0;font-family:monospace;font-size:26px;font-weight:900;letter-spacing:4px;margin:0;'>
      CRYPTO <span style='color:#00ff88;'>SIGNAL</span>
      <span style='color:#1e2850;font-size:14px;margin-left:12px;'>BUY / SELL</span>
    </h1>
    """, unsafe_allow_html=True)

# Market summary
total_buys  = sum(1 for s in signals_map.values() if s["action"] == "BUY")
total_sells = sum(1 for s in signals_map.values() if s["action"] == "SELL")
total_holds = sum(1 for s in signals_map.values() if s["action"] == "HOLD")
total_vol   = sum((d or {}).get("volume24h", 0) for d in all_data.values())

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("🟢 BUY",  total_buys)
mc2.metric("🔴 SELL", total_sells)
mc3.metric("🟡 HOLD", total_holds)
mc4.metric("📊 VOL 24H", fmt_vol(total_vol))

st.markdown("---")

# ─── COIN GRID ────────────────────────────────────────────────────────────────

st.markdown("<p class='label-dim'>SEMUA COIN · KLIK UNTUK DETAIL DI SIDEBAR</p>", unsafe_allow_html=True)

grid_cols = st.columns(5)
for idx, coin in enumerate(COINS):
    d   = all_data.get(coin["symbol"])
    sig = signals_map.get(coin["symbol"], {})
    action   = sig.get("action", "HOLD")
    strength = sig.get("strength", 0)
    a_color  = sig.get("color", "#ffaa00")
    pos = (d or {}).get("change24h", 0) >= 0

    card_class = f"{action.lower()}-card"
    change_str = ""
    price_str  = "———"
    if d:
        price_str  = f"${fmt_price(d['price'])}"
        sign       = "▲" if pos else "▼"
        chg_class  = "change-pos" if pos else "change-neg"
        change_str = f"<span class='{chg_class}'>{sign} {abs(d['change24h']):.2f}%</span>"

    bar_class = f"prog-bar-fill-{action.lower()}"

    with grid_cols[idx % 5]:
        st.markdown(f"""
        <div class='signal-card {card_class}'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>
            <span style='font-family:monospace;font-weight:700;color:#e8eaf0;font-size:13px;letter-spacing:1px;'>{coin['icon']} {coin['short']}</span>
            <span class='badge-{action.lower()}'>{action}</span>
          </div>
          <div style='font-family:monospace;font-size:13px;color:#e8eaf0;font-weight:700;'>{price_str}</div>
          <div style='font-size:11px;margin-top:2px;'>{change_str}</div>
          <div class='prog-bar-bg' style='margin-top:8px;'>
            <div class='{bar_class}' style='width:{strength:.0f}%;'></div>
          </div>
          <div style='color:#2a3560;font-family:monospace;font-size:9px;margin-top:4px;'>{strength:.0f}% CONVICTION</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ─── SELECTED COIN DETAIL ─────────────────────────────────────────────────────

if not selected_data:
    st.error(f"Tidak bisa memuat data untuk {selected_coin['short']}. Coba refresh.")
    st.stop()

action   = selected_sig["action"]
a_color  = selected_sig["color"]
strength = selected_sig["strength"]
buy_sc   = selected_sig["buy"]
sell_sc  = selected_sig["sell"]
sigs     = selected_sig["signals"]
pos      = selected_data["change24h"] >= 0

# Title row
d1, d2, d3 = st.columns([1, 2, 1])
with d1:
    st.markdown(f"""
    <div style='text-align:center;padding:16px;background:#07090f;border:1px solid {a_color}44;border-radius:12px;'>
      <div style='font-size:32px;color:{selected_coin["color"]};font-weight:900;'>{selected_coin['icon']}</div>
      <div style='font-family:monospace;font-size:16px;font-weight:700;color:#e8eaf0;letter-spacing:2px;margin-top:4px;'>{selected_coin['short']}/USDT</div>
      <div style='color:#3a4560;font-size:10px;font-family:monospace;margin-top:2px;'>{selected_coin['name']}</div>
      <hr style='border-color:#0f1525;margin:12px 0;'>
      <div style='font-family:monospace;font-size:22px;font-weight:700;color:#e8eaf0;'>${fmt_price(selected_data['price'])}</div>
      <div style='font-size:13px;color:{"#00ff88" if pos else "#ff4466"};font-family:monospace;margin-top:4px;'>
        {"▲" if pos else "▼"} {abs(selected_data["change24h"]):.2f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

with d2:
    st.markdown(f"""
    <div style='text-align:center;padding:20px;background:linear-gradient(135deg,{a_color}14,#07090f);
         border:1px solid {a_color}55;border-radius:12px;margin-bottom:10px;'>
      <div style='font-family:monospace;font-size:36px;font-weight:900;color:{a_color};
           letter-spacing:5px;text-shadow:0 0 20px {a_color};'>{action}</div>
      <div style='color:{a_color}99;font-family:monospace;font-size:11px;margin-top:4px;'>{strength:.0f}% CONVICTION</div>
      <div class='prog-bar-bg' style='margin:10px 20px 6px;'>
        <div class='prog-bar-fill-{action.lower()}' style='width:{strength:.0f}%;'></div>
      </div>
      <div style='display:flex;justify-content:space-between;padding:0 20px;font-family:monospace;font-size:9px;color:#1e2850;'>
        <span>WEAK</span><span>MODERATE</span><span>STRONG</span>
      </div>
      <div style='margin-top:10px;'>
        <span style='color:#00ff88;font-family:monospace;font-size:11px;margin-right:16px;'>▲ {buy_sc} BUY</span>
        <span style='color:#ff4466;font-family:monospace;font-size:11px;'>▼ {sell_sc} SELL</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with d3:
    st.markdown(f"""
    <div style='background:#07090f;border:1px solid #0f1525;border-radius:12px;padding:16px;'>
      <p class='label-dim'>24H STATS</p>
      <div style='margin-top:10px;'>
    """, unsafe_allow_html=True)
    st.markdown(f"""
      <div style='display:flex;flex-direction:column;gap:8px;'>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>HIGH</span>
          <span style='color:#00ff88;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['high24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>LOW</span>
          <span style='color:#ff4466;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['low24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>VWAP</span>
          <span style='color:#4488ff;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['vwap'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>VOL</span>
          <span style='color:#8890b0;font-family:monospace;font-size:11px;font-weight:700;'>{fmt_vol(selected_data['volume24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>RSI</span>
          <span style='color:{"#00ff88" if selected_data["rsi"]<40 else "#ff4466" if selected_data["rsi"]>60 else "#8890b0"};font-family:monospace;font-size:11px;font-weight:700;'>{selected_data['rsi']:.0f}</span>
        </div>
      </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ─── CHART ───────────────────────────────────────────────────────────────────

st.markdown("<p class='label-dim'>CANDLESTICK CHART · EMA 9/21/50 · VWAP · VOLUME · RSI</p>", unsafe_allow_html=True)
fig = make_candle_chart(selected_data, selected_coin)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─── SIGNALS TABLE ────────────────────────────────────────────────────────────

sig_col, lv_col = st.columns(2)

with sig_col:
    st.markdown("<p class='label-dim'>SINYAL TEKNIKAL (7 INDIKATOR)</p>", unsafe_allow_html=True)
    sig_rows = []
    for name, val, direction, note, weight in sigs:
        if   direction == "buy":  icon, color = "🟢", "#00ff88"
        elif direction == "sell": icon, color = "🔴", "#ff4466"
        else:                     icon, color = "⚪", "#3a4560"
        sig_rows.append({
            "Indikator": f"{icon} {name}",
            "Nilai":     val,
            "Sinyal":    note,
        })
    st.dataframe(
        pd.DataFrame(sig_rows),
        hide_index=True,
        use_container_width=True,
    )

with lv_col:
    st.markdown("<p class='label-dim'>LEVEL KUNCI</p>", unsafe_allow_html=True)
    p = selected_data["price"]
    if action == "BUY":
        levels = [
            ("Entry Zone",   f"${fmt_price(p*0.995)}–${fmt_price(p)}",  "🟢"),
            ("Target 1",     f"${fmt_price(p*1.03)} (+3%)",              "🟢"),
            ("Target 2",     f"${fmt_price(p*1.07)} (+7%)",              "🟢"),
            ("Stop Loss",    f"${fmt_price(p*0.97)} (–3%)",              "🔴"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
        ]
    elif action == "SELL":
        levels = [
            ("Short Entry",  f"${fmt_price(p)}–${fmt_price(p*1.005)}",  "🔴"),
            ("Target 1",     f"${fmt_price(p*0.97)} (–3%)",              "🔴"),
            ("Target 2",     f"${fmt_price(p*0.93)} (–7%)",              "🔴"),
            ("Stop Loss",    f"${fmt_price(p*1.03)} (+3%)",              "🟢"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
        ]
    else:
        levels = [
            ("24H Support",  f"${fmt_price(selected_data['low24h'])}",   "🟢"),
            ("24H Resist",   f"${fmt_price(selected_data['high24h'])}",  "🔴"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
            ("EMA 21",       f"${fmt_price(selected_data['ema21'])}",    "🟡"),
            ("EMA 50",       f"${fmt_price(selected_data['ema50'])}",    "🟠"),
        ]
    st.dataframe(
        pd.DataFrame(levels, columns=["Level", "Nilai", ""]),
        hide_index=True,
        use_container_width=True,
    )

# ─── ALL COINS SUMMARY TABLE ──────────────────────────────────────────────────

st.markdown("---")
st.markdown("<p class='label-dim'>RINGKASAN SEMUA COIN</p>", unsafe_allow_html=True)

rows = []
for coin in COINS:
    d   = all_data.get(coin["symbol"])
    sig = signals_map.get(coin["symbol"], {})
    if not d:
        continue
    action   = sig.get("action", "HOLD")
    strength = sig.get("strength", 0)
    pos      = d["change24h"] >= 0
    rows.append({
        "Coin":       f"{coin['icon']} {coin['short']}",
        "Harga":      f"${fmt_price(d['price'])}",
        "24H %":      f"{'▲' if pos else '▼'} {abs(d['change24h']):.2f}%",
        "RSI":        f"{d['rsi']:.0f}",
        "Signal":     f"{'🟢' if action=='BUY' else '🔴' if action=='SELL' else '🟡'} {action}",
        "Conviction": f"{strength:.0f}%",
        "Vol 24H":    fmt_vol(d["volume24h"]),
    })

st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
  .sell-card { border-color: #ff446655; background: linear-gradient(135deg, #ff446608, #07090f); }
  .hold-card { border-color: #ffaa0055; background: linear-gradient(135deg, #ffaa0008, #07090f); }

  /* Action badges */
  .badge-buy  { color: #00ff88; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #00ff8888; }
  .badge-sell { color: #ff4466; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #ff446688; }
  .badge-hold { color: #ffaa00; font-weight: 900; font-size: 18px; letter-spacing: 3px; text-shadow: 0 0 12px #ffaa0088; }

  /* Labels */
  .label-dim  { color: #3a4560; font-size: 11px; font-family: monospace; letter-spacing: 2px; }
  .price-main { color: #e8eaf0; font-size: 20px; font-weight: 700; font-family: monospace; }
  .change-pos { color: #00ff88; font-family: monospace; }
  .change-neg { color: #ff4466; font-family: monospace; }

  /* Hide default streamlit elements */
  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }
  header     { visibility: hidden; }

  /* Metrics override */
  [data-testid="stMetric"] {
    background: #07090f;
    border: 1px solid #0f1525;
    border-radius: 10px;
    padding: 12px 16px;
  }
  div[data-testid="stMetricLabel"] > div { color: #3a4560 !important; font-family: monospace; font-size: 11px; letter-spacing: 2px; }

  /* Signal indicator dot */
  .dot-buy  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 6px #00ff88; margin-right: 6px; }
  .dot-sell { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ff4466; box-shadow: 0 0 6px #ff4466; margin-right: 6px; }
  .dot-hold { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ffaa00; box-shadow: 0 0 6px #ffaa00; margin-right: 6px; }
  .dot-neu  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3a4560; margin-right: 6px; }

  /* Progress bar */
  .prog-bar-bg { background: #1a2040; border-radius: 4px; height: 6px; width: 100%; }
  .prog-bar-fill-buy  { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #00ff8866, #00ff88); box-shadow: 0 0 8px #00ff8844; transition: width 0.5s; }
  .prog-bar-fill-sell { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #ff446666, #ff4466); box-shadow: 0 0 8px #ff446644; transition: width 0.5s; }
  .prog-bar-fill-hold { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #ffaa0066, #ffaa00); box-shadow: 0 0 8px #ffaa0044; transition: width 0.5s; }

  /* Grid separator */
  hr { border-color: #0f1525; }

  /* Streamlit button */
  .stButton > button {
    background: #07090f;
    color: #00ff88;
    border: 1px solid #0f1525;
    border-radius: 8px;
    font-family: monospace;
    letter-spacing: 2px;
    font-size: 11px;
  }
  .stButton > button:hover {
    border-color: #00ff8844;
    color: #00ff88;
    background: #0a0e18;
  }

  /* Selectbox */
  .stSelectbox > div > div {
    background: #07090f;
    border-color: #0f1525;
    color: #e8eaf0;
  }
</style>
""", unsafe_allow_html=True)

# ─── COIN CONFIG ─────────────────────────────────────────────────────────────

COINS = [
    {"symbol": "BTCUSDT",  "name": "Bitcoin",        "short": "BTC",  "color": "#f7931a", "icon": "₿"},
    {"symbol": "ETHUSDT",  "name": "Ethereum",       "short": "ETH",  "color": "#627eea", "icon": "Ξ"},
    {"symbol": "SOLUSDT",  "name": "Solana",         "short": "SOL",  "color": "#9945ff", "icon": "◎"},
    {"symbol": "BNBUSDT",  "name": "BNB",            "short": "BNB",  "color": "#f0b90b", "icon": "B"},
    {"symbol": "XRPUSDT",  "name": "XRP",            "short": "XRP",  "color": "#00aae4", "icon": "✕"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin",       "short": "DOGE", "color": "#c2a633", "icon": "Ð"},
    {"symbol": "ADAUSDT",  "name": "Cardano",        "short": "ADA",  "color": "#0077cc", "icon": "₳"},
    {"symbol": "AVAXUSDT", "name": "Avalanche",      "short": "AVAX", "color": "#e84142", "icon": "A"},
    {"symbol": "LINKUSDT", "name": "Chainlink",      "short": "LINK", "color": "#2a5ada", "icon": "⬡"},
    {"symbol": "POLUSDT",  "name": "Polygon (POL)",  "short": "POL",  "color": "#8247e5", "icon": "M"},
]

COIN_MAP = {c["symbol"]: c for c in COINS}
BASE_URL = "https://api.binance.com/api/v3"

# ─── TECHNICAL INDICATORS ────────────────────────────────────────────────────

def calc_ema(prices: np.ndarray, period: int) -> np.ndarray:
    k = 2 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    return ema

def calc_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    diffs = np.diff(prices)
    gains  = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    avg_g = gains[:period].mean()
    avg_l = losses[:period].mean()
    for i in range(period, len(diffs)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    return 100.0 - 100.0 / (1 + avg_g / avg_l)

def calc_macd_hist(prices: np.ndarray) -> float:
    if len(prices) < 27:
        return 0.0
    e12   = calc_ema(prices, 12)
    e26   = calc_ema(prices, 26)
    line  = e12 - e26
    sig   = calc_ema(line[25:], 9)
    return float(line[-1] - sig[-1])

def calc_stoch_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period * 2:
        return 50.0
    rsi_arr = np.array([calc_rsi(prices[i - period: i + 1], period)
                        for i in range(period, len(prices))])
    window   = rsi_arr[-period:]
    rng      = window.max() - window.min()
    if rng == 0:
        return 50.0
    return float((rsi_arr[-1] - window.min()) / rng * 100)

def calc_bb_position(prices: np.ndarray, current_price: float) -> float:
    if len(prices) < 20:
        return 0.5
    window = prices[-20:]
    ma  = window.mean()
    std = window.std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    rng = upper - lower
    if rng == 0:
        return 0.5
    return float(np.clip((current_price - lower) / rng, 0, 1))

def calc_vwap(klines: list) -> float:
    sum_pv = sum_v = 0.0
    for k in klines:
        tp = (float(k[2]) + float(k[3]) + float(k[4])) / 3
        v  = float(k[5])
        sum_pv += tp * v
        sum_v  += v
    return sum_pv / sum_v if sum_v else 0.0

# ─── BINANCE FETCH ────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_coin(symbol: str) -> dict | None:
    try:
        ticker_r = requests.get(f"{BASE_URL}/ticker/24hr", params={"symbol": symbol}, timeout=10)
        klines_r = requests.get(f"{BASE_URL}/klines", params={"symbol": symbol, "interval": "15m", "limit": 100}, timeout=10)
        if not ticker_r.ok or not klines_r.ok:
            return None
        ticker = ticker_r.json()
        klines = klines_r.json()
        if "code" in ticker:
            return None

        price     = float(ticker["lastPrice"])
        change24h = float(ticker["priceChangePercent"])
        high24h   = float(ticker["highPrice"])
        low24h    = float(ticker["lowPrice"])
        volume24h = float(ticker["quoteVolume"])

        closes = np.array([float(k[4]) for k in klines])
        vols   = np.array([float(k[5]) for k in klines])

        avg_vol   = vols[-21:-1].mean() if len(vols) >= 21 else vols.mean()
        vol_ratio = float(vols[-1] / avg_vol) if avg_vol > 0 else 1.0

        ema9  = float(calc_ema(closes, 9)[-1])
        ema21 = float(calc_ema(closes, 21)[-1])
        ema50 = float(calc_ema(closes, 50)[-1])

        return {
            "price":      price,
            "change24h":  change24h,
            "high24h":    high24h,
            "low24h":     low24h,
            "volume24h":  volume24h,
            "sparkline":  closes[-30:].tolist(),
            "closes":     closes.tolist(),
            "rsi":        calc_rsi(closes),
            "macd_hist":  calc_macd_hist(closes),
            "stoch_rsi":  calc_stoch_rsi(closes),
            "bb":         calc_bb_position(closes, price),
            "vwap":       calc_vwap(klines),
            "ema9":       ema9,
            "ema21":      ema21,
            "ema50":      ema50,
            "vol_ratio":  vol_ratio,
            "klines":     klines,
        }
    except Exception:
        return None

# ─── SIGNAL ENGINE ────────────────────────────────────────────────────────────

def compute_signal(data: dict) -> dict:
    if not data:
        return {"action": "HOLD", "color": "#ffaa00", "strength": 0, "buy": 0, "sell": 0, "signals": []}

    price, rsi, macd_hist = data["price"], data["rsi"], data["macd_hist"]
    stoch_rsi, bb         = data["stoch_rsi"], data["bb"]
    vwap_val              = data["vwap"]
    ema9, ema21, ema50    = data["ema9"], data["ema21"], data["ema50"]
    vol_ratio             = data["vol_ratio"]

    signals, buy, sell = [], 0, 0

    # RSI
    if   rsi < 30: signals.append(("RSI",       f"{rsi:.0f}",     "buy",  "Sangat Oversold",   3)); buy  += 3
    elif rsi < 40: signals.append(("RSI",       f"{rsi:.0f}",     "buy",  "Oversold",          1)); buy  += 1
    elif rsi > 70: signals.append(("RSI",       f"{rsi:.0f}",     "sell", "Sangat Overbought", 3)); sell += 3
    elif rsi > 60: signals.append(("RSI",       f"{rsi:.0f}",     "sell", "Overbought",        1)); sell += 1
    else:          signals.append(("RSI",       f"{rsi:.0f}",     "neu",  "Netral",            0))

    # MACD (normalised by price)
    macd_norm = (macd_hist / price * 1000) if price else 0
    macd_disp = f"{macd_hist:.6f}" if abs(macd_hist) < 100 else f"{macd_hist:.2f}"
    if   macd_norm >  0.08: signals.append(("MACD",      f"▲ {macd_disp}", "buy",  "Bullish momentum", 2)); buy  += 2
    elif macd_norm < -0.08: signals.append(("MACD",      f"▼ {macd_disp}", "sell", "Bearish momentum", 2)); sell += 2
    else:                   signals.append(("MACD",      macd_disp,        "neu",  "Lemah / ranging",  0))

    # Stoch RSI
    if   stoch_rsi < 20: signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "buy",  "Extreme oversold",  2)); buy  += 2
    elif stoch_rsi > 80: signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "sell", "Extreme overbought",2)); sell += 2
    else:                signals.append(("Stoch RSI", f"{stoch_rsi:.0f}", "neu",  "Normal",            0))

    # VWAP
    if   price > vwap_val * 1.002: signals.append(("VWAP",       fmt_price(vwap_val), "buy",  "Di atas VWAP",  1)); buy  += 1
    elif price < vwap_val * 0.998: signals.append(("VWAP",       fmt_price(vwap_val), "sell", "Di bawah VWAP", 1)); sell += 1
    else:                          signals.append(("VWAP",       fmt_price(vwap_val), "neu",  "Di VWAP",       0))

    # EMA Stack
    if   ema9 > ema21 > ema50: signals.append(("EMA Stack", "BULL 9>21>50", "buy",  "Bullish stack", 2)); buy  += 2
    elif ema9 < ema21 < ema50: signals.append(("EMA Stack", "BEAR 9<21<50", "sell", "Bearish stack", 2)); sell += 2
    elif ema9 > ema21:         signals.append(("EMA Stack", "GOLDEN",       "buy",  "EMA9 > EMA21",  1)); buy  += 1
    else:                      signals.append(("EMA Stack", "DEATH",        "sell", "EMA9 < EMA21",  1)); sell += 1

    # Bollinger Bands
    if   bb < 0.1: signals.append(("BB Band",   "LOWER", "buy",  "Near lower band",  1)); buy  += 1
    elif bb > 0.9: signals.append(("BB Band",   "UPPER", "sell", "Near upper band",  1)); sell += 1
    else:          signals.append(("BB Band",   f"{bb*100:.0f}%", "neu", "Dalam bands", 0))

    # Volume
    if   vol_ratio > 2.0: signals.append(("Volume",    f"{vol_ratio:.1f}x", "buy", "Volume surge!", 2)); buy  += 2
    elif vol_ratio > 1.3: signals.append(("Volume",    f"{vol_ratio:.1f}x", "buy", "Volume tinggi", 1)); buy  += 1
    elif vol_ratio < 0.5: signals.append(("Volume",    f"{vol_ratio:.1f}x", "neu", "Volume rendah", 0))
    else:                 signals.append(("Volume",    f"{vol_ratio:.1f}x", "neu", "Normal",        0))

    total = buy + sell
    net   = (buy - sell) / max(total, 1)

    if   net >  0.28: action, color, strength = "BUY",  "#00ff88", min(net * 95, 95)
    elif net < -0.28: action, color, strength = "SELL", "#ff4466", min(abs(net) * 95, 95)
    else:             action, color, strength = "HOLD", "#ffaa00", abs(net) * 55

    return {"action": action, "color": color, "strength": strength, "buy": buy, "sell": sell, "signals": signals}

# ─── FORMATTERS ───────────────────────────────────────────────────────────────

def fmt_price(v: float) -> str:
    if v is None or np.isnan(v): return "—"
    if v >= 10000: return f"{v:,.0f}"
    if v >= 1000:  return f"{v:,.2f}"
    if v >= 1:     return f"{v:.4f}"
    if v >= 0.001: return f"{v:.5f}"
    return f"{v:.8f}"

def fmt_vol(v: float) -> str:
    if not v: return "—"
    if v >= 1e9: return f"${v/1e9:.2f}B"
    if v >= 1e6: return f"${v/1e6:.1f}M"
    if v >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"

# ─── CHART ────────────────────────────────────────────────────────────────────

def make_candle_chart(data: dict, coin: dict) -> go.Figure:
    klines = data["klines"]
    df = pd.DataFrame(klines, columns=[
        "time","open","high","low","close","vol","close_time",
        "qvol","trades","tbase","tquote","ignore"
    ])
    df["time"]  = pd.to_datetime(df["time"], unit="ms")
    df["open"]  = df["open"].astype(float)
    df["high"]  = df["high"].astype(float)
    df["low"]   = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["vol"]   = df["vol"].astype(float)

    closes = df["close"].values
    ema9_arr  = calc_ema(closes, 9)
    ema21_arr = calc_ema(closes, 21)
    ema50_arr = calc_ema(closes, 50)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.02,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color="#00ff88", decreasing_line_color="#ff4466",
        increasing_fillcolor="#00ff8833", decreasing_fillcolor="#ff446633",
        name="Price", showlegend=False,
    ), row=1, col=1)

    # EMAs
    for arr, color, name in [(ema9_arr, "#ffaa00", "EMA9"), (ema21_arr, "#4488ff", "EMA21"), (ema50_arr, "#ff8844", "EMA50")]:
        fig.add_trace(go.Scatter(x=df["time"], y=arr, line=dict(color=color, width=1), name=name, opacity=0.85), row=1, col=1)

    # VWAP
    vwap_line = np.full(len(df), data["vwap"])
    fig.add_trace(go.Scatter(x=df["time"], y=vwap_line, line=dict(color="#cc88ff", width=1, dash="dot"), name="VWAP"), row=1, col=1)

    # Volume bars
    vol_colors = ["#00ff8855" if c >= o else "#ff446655" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df["time"], y=df["vol"], marker_color=vol_colors, name="Volume", showlegend=False), row=2, col=1)

    # RSI
    closes_arr = np.array(closes)
    rsi_arr = [calc_rsi(closes_arr[:i+1]) for i in range(14, len(closes_arr))]
    fig.add_trace(go.Scatter(
        x=df["time"].iloc[14:], y=rsi_arr,
        line=dict(color="#9955ff", width=1.5), name="RSI", showlegend=False,
    ), row=3, col=1)
    fig.add_hline(y=70, line=dict(color="#ff446666", width=1, dash="dot"), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="#00ff8866", width=1, dash="dot"), row=3, col=1)
    fig.add_hline(y=50, line=dict(color="#3a456088", width=1, dash="dot"), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#07090f",
        plot_bgcolor="#030508",
        font=dict(family="monospace", color="#8890b0", size=10),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            bgcolor="#07090f", bordercolor="#0f1525", borderwidth=1,
            font=dict(size=9), orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
        ),
    )
    for axis in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{axis: dict(
            gridcolor="#0f1525", gridwidth=1,
            zerolinecolor="#0f1525",
            showgrid=True,
        )})

    fig.update_yaxes(title_text="Price", row=1, col=1, title_font=dict(size=9))
    fig.update_yaxes(title_text="Vol",   row=2, col=1, title_font=dict(size=9))
    fig.update_yaxes(title_text="RSI",   row=3, col=1, title_font=dict(size=9), range=[0, 100])

    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("<p class='label-dim'>CRYPTO SIGNAL DASHBOARD</p>", unsafe_allow_html=True)
    st.markdown("---")

    coin_options = {f"{c['icon']} {c['short']} — {c['name']}": c["symbol"] for c in COINS}
    selected_label = st.selectbox("Pilih Coin", list(coin_options.keys()), index=0)
    selected_symbol = coin_options[selected_label]

    st.markdown("---")
    refresh = st.button("⟳  REFRESH DATA", use_container_width=True)
    if refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<p class='label-dim'>AUTO REFRESH</p>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Aktifkan (30 detik)", value=False)

    st.markdown("---")
    st.markdown("<p class='label-dim'>DATA SOURCE</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#00ff88;font-family:monospace;font-size:11px;'>● Binance Public API</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#3a4560;font-family:monospace;font-size:10px;'>Real-time · No API key required<br>Timeframe: 15m candles</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p class='label-dim'>INDIKATOR</p>", unsafe_allow_html=True)
    for ind in ["RSI (14)", "MACD (12,26,9)", "Stochastic RSI", "VWAP", "EMA 9/21/50", "Bollinger Bands", "Volume Ratio"]:
        st.markdown(f"<p style='color:#3a4560;font-family:monospace;font-size:10px;'>• {ind}</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<p style='color:#1e2850;font-family:monospace;font-size:9px;'>⚠ Bukan financial advice.<br>Selalu DYOR & manage risiko.</p>",
        unsafe_allow_html=True
    )

# ─── FETCH ALL DATA ───────────────────────────────────────────────────────────

all_data = {}
progress = st.progress(0, text="Fetching data dari Binance...")
for i, coin in enumerate(COINS):
    all_data[coin["symbol"]] = fetch_coin(coin["symbol"])
    progress.progress((i + 1) / len(COINS), text=f"Loading {coin['short']}...")
progress.empty()

selected_data = all_data.get(selected_symbol)
selected_coin = COIN_MAP[selected_symbol]

# Compute signals
signals_map = {sym: compute_signal(d) for sym, d in all_data.items()}
selected_sig = signals_map[selected_symbol]

# ─── HEADER ───────────────────────────────────────────────────────────────────

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    st.markdown(f"""
    <div style='margin-bottom:4px'>
      <span style='color:#00ff88;font-family:monospace;font-size:10px;letter-spacing:3px;'>
        ● LIVE · BINANCE API · {now_str}
      </span>
    </div>
    <h1 style='color:#e8eaf0;font-family:monospace;font-size:26px;font-weight:900;letter-spacing:4px;margin:0;'>
      CRYPTO <span style='color:#00ff88;'>SIGNAL</span>
      <span style='color:#1e2850;font-size:14px;margin-left:12px;'>BUY / SELL</span>
    </h1>
    """, unsafe_allow_html=True)

# Market summary
total_buys  = sum(1 for s in signals_map.values() if s["action"] == "BUY")
total_sells = sum(1 for s in signals_map.values() if s["action"] == "SELL")
total_holds = sum(1 for s in signals_map.values() if s["action"] == "HOLD")
total_vol   = sum((d or {}).get("volume24h", 0) for d in all_data.values())

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("🟢 BUY",  total_buys)
mc2.metric("🔴 SELL", total_sells)
mc3.metric("🟡 HOLD", total_holds)
mc4.metric("📊 VOL 24H", fmt_vol(total_vol))

st.markdown("---")

# ─── COIN GRID ────────────────────────────────────────────────────────────────

st.markdown("<p class='label-dim'>SEMUA COIN · KLIK UNTUK DETAIL DI SIDEBAR</p>", unsafe_allow_html=True)

grid_cols = st.columns(5)
for idx, coin in enumerate(COINS):
    d   = all_data.get(coin["symbol"])
    sig = signals_map.get(coin["symbol"], {})
    action   = sig.get("action", "HOLD")
    strength = sig.get("strength", 0)
    a_color  = sig.get("color", "#ffaa00")
    pos = (d or {}).get("change24h", 0) >= 0

    card_class = f"{action.lower()}-card"
    change_str = ""
    price_str  = "———"
    if d:
        price_str  = f"${fmt_price(d['price'])}"
        sign       = "▲" if pos else "▼"
        chg_class  = "change-pos" if pos else "change-neg"
        change_str = f"<span class='{chg_class}'>{sign} {abs(d['change24h']):.2f}%</span>"

    bar_class = f"prog-bar-fill-{action.lower()}"

    with grid_cols[idx % 5]:
        st.markdown(f"""
        <div class='signal-card {card_class}'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>
            <span style='font-family:monospace;font-weight:700;color:#e8eaf0;font-size:13px;letter-spacing:1px;'>{coin['icon']} {coin['short']}</span>
            <span class='badge-{action.lower()}'>{action}</span>
          </div>
          <div style='font-family:monospace;font-size:13px;color:#e8eaf0;font-weight:700;'>{price_str}</div>
          <div style='font-size:11px;margin-top:2px;'>{change_str}</div>
          <div class='prog-bar-bg' style='margin-top:8px;'>
            <div class='{bar_class}' style='width:{strength:.0f}%;'></div>
          </div>
          <div style='color:#2a3560;font-family:monospace;font-size:9px;margin-top:4px;'>{strength:.0f}% CONVICTION</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ─── SELECTED COIN DETAIL ─────────────────────────────────────────────────────

if not selected_data:
    st.error(f"Tidak bisa memuat data untuk {selected_coin['short']}. Coba refresh.")
    st.stop()

action   = selected_sig["action"]
a_color  = selected_sig["color"]
strength = selected_sig["strength"]
buy_sc   = selected_sig["buy"]
sell_sc  = selected_sig["sell"]
sigs     = selected_sig["signals"]
pos      = selected_data["change24h"] >= 0

# Title row
d1, d2, d3 = st.columns([1, 2, 1])
with d1:
    st.markdown(f"""
    <div style='text-align:center;padding:16px;background:#07090f;border:1px solid {a_color}44;border-radius:12px;'>
      <div style='font-size:32px;color:{selected_coin["color"]};font-weight:900;'>{selected_coin['icon']}</div>
      <div style='font-family:monospace;font-size:16px;font-weight:700;color:#e8eaf0;letter-spacing:2px;margin-top:4px;'>{selected_coin['short']}/USDT</div>
      <div style='color:#3a4560;font-size:10px;font-family:monospace;margin-top:2px;'>{selected_coin['name']}</div>
      <hr style='border-color:#0f1525;margin:12px 0;'>
      <div style='font-family:monospace;font-size:22px;font-weight:700;color:#e8eaf0;'>${fmt_price(selected_data['price'])}</div>
      <div style='font-size:13px;color:{"#00ff88" if pos else "#ff4466"};font-family:monospace;margin-top:4px;'>
        {"▲" if pos else "▼"} {abs(selected_data["change24h"]):.2f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

with d2:
    st.markdown(f"""
    <div style='text-align:center;padding:20px;background:linear-gradient(135deg,{a_color}14,#07090f);
         border:1px solid {a_color}55;border-radius:12px;margin-bottom:10px;'>
      <div style='font-family:monospace;font-size:36px;font-weight:900;color:{a_color};
           letter-spacing:5px;text-shadow:0 0 20px {a_color};'>{action}</div>
      <div style='color:{a_color}99;font-family:monospace;font-size:11px;margin-top:4px;'>{strength:.0f}% CONVICTION</div>
      <div class='prog-bar-bg' style='margin:10px 20px 6px;'>
        <div class='prog-bar-fill-{action.lower()}' style='width:{strength:.0f}%;'></div>
      </div>
      <div style='display:flex;justify-content:space-between;padding:0 20px;font-family:monospace;font-size:9px;color:#1e2850;'>
        <span>WEAK</span><span>MODERATE</span><span>STRONG</span>
      </div>
      <div style='margin-top:10px;'>
        <span style='color:#00ff88;font-family:monospace;font-size:11px;margin-right:16px;'>▲ {buy_sc} BUY</span>
        <span style='color:#ff4466;font-family:monospace;font-size:11px;'>▼ {sell_sc} SELL</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with d3:
    st.markdown(f"""
    <div style='background:#07090f;border:1px solid #0f1525;border-radius:12px;padding:16px;'>
      <p class='label-dim'>24H STATS</p>
      <div style='margin-top:10px;'>
    """, unsafe_allow_html=True)
    st.markdown(f"""
      <div style='display:flex;flex-direction:column;gap:8px;'>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>HIGH</span>
          <span style='color:#00ff88;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['high24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>LOW</span>
          <span style='color:#ff4466;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['low24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>VWAP</span>
          <span style='color:#4488ff;font-family:monospace;font-size:11px;font-weight:700;'>${fmt_price(selected_data['vwap'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>VOL</span>
          <span style='color:#8890b0;font-family:monospace;font-size:11px;font-weight:700;'>{fmt_vol(selected_data['volume24h'])}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
          <span style='color:#3a4560;font-family:monospace;font-size:10px;'>RSI</span>
          <span style='color:{"#00ff88" if selected_data["rsi"]<40 else "#ff4466" if selected_data["rsi"]>60 else "#8890b0"};font-family:monospace;font-size:11px;font-weight:700;'>{selected_data['rsi']:.0f}</span>
        </div>
      </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ─── CHART ───────────────────────────────────────────────────────────────────

st.markdown("<p class='label-dim'>CANDLESTICK CHART · EMA 9/21/50 · VWAP · VOLUME · RSI</p>", unsafe_allow_html=True)
fig = make_candle_chart(selected_data, selected_coin)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─── SIGNALS TABLE ────────────────────────────────────────────────────────────

sig_col, lv_col = st.columns(2)

with sig_col:
    st.markdown("<p class='label-dim'>SINYAL TEKNIKAL (7 INDIKATOR)</p>", unsafe_allow_html=True)
    sig_rows = []
    for name, val, direction, note, weight in sigs:
        if   direction == "buy":  icon, color = "🟢", "#00ff88"
        elif direction == "sell": icon, color = "🔴", "#ff4466"
        else:                     icon, color = "⚪", "#3a4560"
        sig_rows.append({
            "Indikator": f"{icon} {name}",
            "Nilai":     val,
            "Sinyal":    note,
        })
    st.dataframe(
        pd.DataFrame(sig_rows),
        hide_index=True,
        use_container_width=True,
    )

with lv_col:
    st.markdown("<p class='label-dim'>LEVEL KUNCI</p>", unsafe_allow_html=True)
    p = selected_data["price"]
    if action == "BUY":
        levels = [
            ("Entry Zone",   f"${fmt_price(p*0.995)}–${fmt_price(p)}",  "🟢"),
            ("Target 1",     f"${fmt_price(p*1.03)} (+3%)",              "🟢"),
            ("Target 2",     f"${fmt_price(p*1.07)} (+7%)",              "🟢"),
            ("Stop Loss",    f"${fmt_price(p*0.97)} (–3%)",              "🔴"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
        ]
    elif action == "SELL":
        levels = [
            ("Short Entry",  f"${fmt_price(p)}–${fmt_price(p*1.005)}",  "🔴"),
            ("Target 1",     f"${fmt_price(p*0.97)} (–3%)",              "🔴"),
            ("Target 2",     f"${fmt_price(p*0.93)} (–7%)",              "🔴"),
            ("Stop Loss",    f"${fmt_price(p*1.03)} (+3%)",              "🟢"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
        ]
    else:
        levels = [
            ("24H Support",  f"${fmt_price(selected_data['low24h'])}",   "🟢"),
            ("24H Resist",   f"${fmt_price(selected_data['high24h'])}",  "🔴"),
            ("VWAP",         f"${fmt_price(selected_data['vwap'])}",     "🔵"),
            ("EMA 21",       f"${fmt_price(selected_data['ema21'])}",    "🟡"),
            ("EMA 50",       f"${fmt_price(selected_data['ema50'])}",    "🟠"),
        ]
    st.dataframe(
        pd.DataFrame(levels, columns=["Level", "Nilai", ""]),
        hide_index=True,
        use_container_width=True,
    )

# ─── ALL COINS SUMMARY TABLE ──────────────────────────────────────────────────

st.markdown("---")
st.markdown("<p class='label-dim'>RINGKASAN SEMUA COIN</p>", unsafe_allow_html=True)

rows = []
for coin in COINS:
    d   = all_data.get(coin["symbol"])
    sig = signals_map.get(coin["symbol"], {})
    if not d:
        continue
    action   = sig.get("action", "HOLD")
    strength = sig.get("strength", 0)
    pos      = d["change24h"] >= 0
    rows.append({
        "Coin":       f"{coin['icon']} {coin['short']}",
        "Harga":      f"${fmt_price(d['price'])}",
        "24H %":      f"{'▲' if pos else '▼'} {abs(d['change24h']):.2f}%",
        "RSI":        f"{d['rsi']:.0f}",
        "Signal":     f"{'🟢' if action=='BUY' else '🔴' if action=='SELL' else '🟡'} {action}",
        "Conviction": f"{strength:.0f}%",
        "Vol 24H":    fmt_vol(d["volume24h"]),
    })

st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
