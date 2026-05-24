import streamlit as st
import pandas as pd
import requests
import pandas_ta as ta
import streamlit.components.v1 as components

st.set_page_config(page_title="Crypto AI Futures Signals & Charts", layout="wide", page_icon="📈")

st.title("🚀 Binance Futures AI Signals & Live Charts")
st.markdown("### Real-Time Algorithmic Buy/Sell Signals & Technical Charts")

@st.cache_data(ttl=30)
def get_binance_futures_data():
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        response = requests.get(url).json()
        data = [coin for coin in response if coin['symbol'].endswith('USDT')]
        df = pd.DataFrame(data)
        df = df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']]
        df['lastPrice'] = df['lastPrice'].astype(float)
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['quoteVolume'] = df['quoteVolume'].astype(float)
        df = df.sort_values(by='quoteVolume', ascending=False).head(20)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Binance API: {e}")
        return pd.DataFrame()

def generate_ai_signal(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1h&limit=100"
        res = requests.get(url).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['EMA_20'] = ta.ema(df['close'], length=20)
        latest_rsi = df['RSI'].iloc[-1]
        latest_close = df['close'].iloc[-1]
        latest_ema = df['EMA_20'].iloc[-1]
        
        if latest_rsi < 32 and latest_close > latest_ema:
            return "🟢 STRONG BUY", "Oversold & Reversal Confirmed"
        elif latest_rsi < 42:
            return "🟢 BUY", "Accumulation Zone (Low RSI)"
        elif latest_rsi > 68 and latest_close < latest_ema:
            return "🔴 STRONG SELL", "Overbought & Bearish Reversal"
        elif latest_rsi > 58:
            return "🔴 SELL", "Distribution Zone (High RSI)"
        else:
            return "⚪ HOLD", "Neutral Market Consolidation"
    except:
        return "⚠️ ERROR", "Data Processing Failed"

with st.spinner("Fetching live market data..."):
    trending_coins = get_binance_futures_data()

if not trending_coins.empty:
    signals = []
    reasons = []
    for index, row in trending_coins.iterrows():
        sig, res = generate_ai_signal(row['symbol'])
        signals.append(sig)
        reasons.append(res)

    trending_coins['Signal'] = signals
    trending_coins['Analysis'] = reasons
    trending_coins.columns = ['Trading Pair', 'Last Price ($)', '24h Change (%)', '24h Volume ($)', 'AI Signal', 'Market Condition']
    
    display_df = trending_coins.copy()
    display_df['24h Volume ($)'] = display_df['24h Volume ($)'].map('{:,.2f}'.format)
    display_df['Last Price ($)'] = display_df['Last Price ($)'].map(lambda x: f"{x:,.4f}" if x < 1 else f"{x:,.2f}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Top Volumetric Leader", trending_coins['Trading Pair'].iloc[0], f"{trending_coins['24h Change (%)'].iloc[0]}%")
    avg_volatility = trending_coins['24h Change (%)'].abs().mean()
    col2.metric("Market Sentiment Status", "⚡ High Volatility" if avg_volatility > 6 else "💤 Scalping Environment")
    col3.metric("Monitored Assets", f"{len(trending_coins)} Futures Pairs")

    st.markdown("---")
    left_column, right_column = st.columns([1.2, 1])

    with left_column:
        st.subheader("📊 Live Algorithmic Signals Feed")
        def style_rows(val):
            if "BUY" in str(val):
                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
            elif "SELL" in str(val):
                return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
            return ''
        styled_df = display_df.style.applymap(style_rows, subset=['AI Signal'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=520)

    with right_column:
        st.subheader("📈 Live TradingView Interactive Chart")
        pair_list = trending_coins['Trading Pair'].tolist()
        selected_pair = st.selectbox("Select a pair to load live chart:", pair_list, index=0)
        tv_symbol = f"BINANCE:{selected_pair}.P" if "USDT" in selected_pair else f"BINANCE:{selected_pair}"

        tradingview_html = f"""
        <div class="tradingview-widget-container" style="height:450px;width:100%;">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_html, height=460)
else:
    st.warning("Unable to fetch data.")

st.markdown("---")
st.caption("⚠️ **Risk Disclaimer:** Crypto Futures trading carries an extremely high level of risk. Automated signals are for **educational purposes only**.")
      
