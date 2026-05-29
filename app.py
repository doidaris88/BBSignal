import streamlit as str
import pandas as pd
import numpy as np
import requests
import pandas_ta as ta
import time

# Konfigurasi Halaman Streamlit
str.set_page_config(page_title="Real-time Crypto Signal Dashboard", layout="wide")
str.title("🚀 Real-Time Crypto High-Beta Signal Dashboard")
str.caption("Data Source: Binance Public API (No API Key Required) | Update otomatis setiap 10 detik")

# 1. Fungsi untuk mengambil data historis (Klines) dari Binance
def get_binance_data(symbol, interval='15m', limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # Mapping kolom data Binance
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Konversi tipe data ke float
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        # Tambahkan kolom Typical Price untuk keperluan perhitungan VWAP buatan jika diperlukan
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        return df
    except Exception as e:
        str.error(f"Gagal mengambil data untuk {symbol}: {e}")
        return None

# 2. Fungsi hitung indikator & logika Sinyal
def calculate_signals(df):
    # Kloning dataframe untuk menghindari warning
    df_calc = df.copy()
    
    # a. RSI 14
    df_calc['RSI'] = ta.rsi(df_calc['close'], length=14)
    
    # b. MACD (12, 26, 9)
    macd = ta.macd(df_calc['close'], fast=12, slow=26, signal=9)
    df_calc['MACD'] = macd['MACD_12_26_9']
    df_calc['MACD_Signal'] = macd['MACDS_12_26_9']
    
    # c. Stochastic RSI (14, 3, 3) - Standar bursa
    stoch_rsi = ta.stochrsi(df_calc['close'], length=14, k=3, d=3)
    df_calc['Stoch_K'] = stoch_rsi['STOCHRSIk_14_14_3_3']
    df_calc['Stoch_D'] = stoch_rsi['STOCHRSId_14_14_3_3']
    
    # d. EMA Stack (9, 21, 50)
    df_calc['EMA9'] = ta.ema(df_calc['close'], length=9)
    df_calc['EMA21'] = ta.ema(df_calc['close'], length=21)
    df_calc['EMA50'] = ta.ema(df_calc['close'], length=50)
    
    # e. Bollinger Bands (20, 2)
    bbands = ta.bbands(df_calc['close'], length=20, std=2)
    df_calc['BB_Upper'] = bbands['BBU_20_2.0']
    df_calc['BB_Middle'] = bbands['BBM_20_2.0']
    df_calc['BB_Lower'] = bbands['BBL_20_2.0']
    
    # f. VWAP (Pendekatan berbasis jendela data bergerak untuk sesi intraday)
    df_calc['vwap_num'] = (df_calc['typical_price'] * df_calc['volume']).rolling(window=20).sum()
    df_calc['vwap_den'] = df_calc['volume'].rolling(window=20).sum()
    df_calc['VWAP'] = df_calc['vwap_num'] / df_calc['vwap_den']
    
    # g. Volume Ratio Surge (Volume saat ini dibanding rata-rata 20 candle sebelumnya)
    df_calc['Vol_Avg'] = df_calc['volume'].shift(1).rolling(window=20).mean()
    df_calc['Vol_Ratio'] = df_calc['volume'] / df_calc['Vol_Avg']
    
    # --- LOGIKA KEPUTUSAN SINYAL (Baris Terakhir / Terbaru) ---
    row = df_calc.iloc[-1]
    prev_row = df_calc.iloc[-2]
    
    buy_score = 0
    sell_score = 0
    max_score = 5 # Total indikator utama yang dicek
    
    # 1. Cek EMA Stack (Bullish / Bearish Alignment)
    if row['EMA9'] > row['EMA21'] > row['EMA50']:
        buy_score += 1
    elif row['EMA9'] < row['EMA21'] < row['EMA50']:
        sell_score += 1
        
    # 2. Cek VWAP Position
    if row['close'] > row['VWAP']:
        buy_score += 1
    elif row['close'] < row['VWAP']:
        sell_score += 1
        
    # 3. MACD Crossover
    if row['MACD'] > row['MACD_Signal']:
        buy_score += 1
    else:
        sell_score += 1
        
    # 4. Stochastic RSI (Oversold / Overbought thresholds 20, 80)
    if row['Stoch_K'] < 20 or (prev_row['Stoch_K'] < prev_row['Stoch_D'] and row['Stoch_K'] > row['Stoch_D'] and row['Stoch_K'] < 50):
        buy_score += 1
    if row['Stoch_K'] > 80 or (prev_row['Stoch_K'] > prev_row['Stoch_D'] and row['Stoch_K'] < row['Stoch_D'] and row['Stoch_K'] > 50):
        sell_score += 1
        
    # 5. RSI 14 Comfort Zone
    if 45 < row['RSI'] < 65 and row['close'] > row['BB_Middle']:
        buy_score += 0.5
    if row['RSI'] > 70:
        sell_score += 1 # Overbought alert
    elif row['RSI'] < 30:
        buy_score += 1 # Oversold alert

    # Penentuan Sinyal Akhir
    if buy_score > sell_score:
        action = "BUY"
        strength = buy_score / max_score
    elif sell_score > buy_score:
        action = "SELL"
        strength = sell_score / max_score
    else:
        action = "NEUTRAL"
        strength = 0
        
    # Konfirmasi Volume Surge (>2x)
    is_volume_surge = row['Vol_Ratio'] >= 2.0
    
    status_sinyal = f"{action}"
    if is_volume_surge and action != "NEUTRAL":
        status_sinyal += " ⚡ (STRONG SIGNALS - VOL SURGE)"
        
    return {
        "Price": row['close'],
        "RSI": round(row['RSI'], 2),
        "Stoch_K": round(row['Stoch_K'], 2),
        "Stoch_D": round(row['Stoch_D'], 2),
        "MACD_Status": "Bullish" if row['MACD'] > row['MACD_Signal'] else "Bearish",
        "EMA_Status": "Bullish Stack" if row['EMA9'] > row['EMA50'] else "Bearish Stack",
        "VWAP_Pos": "Above VWAP" if row['close'] > row['VWAP'] else "Below VWAP",
        "Vol_Ratio": round(row['Vol_Ratio'], 2),
        "Signal": status_sinyal,
        "Action": action,
        "Surge": is_volume_surge
    }

# 3. Loop Antarmuka Utama Dashboard
crypto_symbols = ["SOLUSDT", "NEARUSDT", "AVAXUSDT", "DOGEUSDT"]

# Sidebar Parameter Interaktif
str.sidebar.header("🛠️ Trading Settings")
timeframe = str.sidebar.selectbox("Pilih Timeframe (Candle):", ['5m', '15m', '1h', '4h'], index=1)
refresh_rate = str.sidebar.slider("Interval Refresh (Detik):", 5, 30, 10)

# Wadah Placeholder untuk update realtime tanpa reload page semenjana
placeholder = str.empty()

while True:
    with placeholder.container():
        cols = str.columns(4)
        
        for idx, symbol in enumerate(crypto_symbols):
            df = get_binance_data(symbol, interval=timeframe)
            
            if df is not None:
                analysis = calculate_signals(df)
                
                with cols[idx]:
                    # Format warna kartu berdasarkan sinyal yang dihasilkan
                    if "STRONG" in analysis['Signal']:
                        str.markdown(f"### 🟣 {symbol.replace('USDT', '')}")
                    elif analysis['Action'] == "BUY":
                        str.markdown(f"### 🟢 {symbol.replace('USDT', '')}")
                    elif analysis['Action'] == "SELL":
                        str.markdown(f"### 🔴 {symbol.replace('USDT', '')}")
                    else:
                        str.markdown(f"### ⚪ {symbol.replace('USDT', '')}")
                        
                    str.metric(label="Current Price", value=f"${analysis['Price']:,}")
                    
                    # Highlight Box untuk Sinyal Utama
                    if analysis['Action'] == "BUY":
                        str.success(f"**Sinyal:** {analysis['Signal']}")
                    elif analysis['Action'] == "SELL":
                        str.error(f"**Sinyal:** {analysis['Signal']}")
                    else:
                        str.info(f"**Sinyal:** {analysis['Signal']}")
                        
                    # Tampilkan rincian indikator teknikal di dalam komponen expander
                    with str.expander("Lihat Detail Indikator"):
                        str.write(f"📊 **Vol Ratio:** {analysis['Vol_Ratio']}x " + ("🔥" if analysis['Surge'] else ""))
                        str.write(f"📈 **RSI (14):** {analysis['RSI']}")
                        str.write(f"🔄 **Stoch RSI (K/D):** {analysis['Stoch_K']} / {analysis['Stoch_D']}")
                        str.write(f"📉 **MACD:** {analysis['MACD_Status']}")
                        str.write(f"🧬 **EMA Stack:** {analysis['EMA_Status']}")
                        str.write(f"🍏 **VWAP:** {analysis['VWAP_Pos']}")
                        
                    str.markdown("---")
                    
    # Delay interval perulangan untuk menghemat beban request data/rate limit
    time.sleep(refresh_rate)
