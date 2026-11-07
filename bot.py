from SmartApi import SmartConnect
import pyotp
import urllib.request
import json
import pandas as pd
import requests

# ==========================================
# ૧. ક્રિડેન્શિયલ (એન્જલ વન અને ટેલિગ્રામ)
# ==========================================
API_KEY = 'tVjVRYJ2'
CLIENT_ID = 'J277377'
PIN = '1349'
TOTP_SECRET = 'XFREBXKVT764SELNM2GCMY3M4Q'

TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # તમારો ટેલિગ્રામ બોટ ટોકન અહીં નાખવો
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'      # તમારી ચેટ આઈડી અહીં નાખવી

# ==========================================
# ૨. એન્જલ વન સાથે કનેક્ટ થવા માટેનું ફંક્શન
# ==========================================
def connect_angel_one():
    print("\nએન્જલ વન સાથે કનેક્ટ થઈ રહ્યું છે...")
    obj = SmartConnect(api_key=API_KEY)
    try:
        totp = pyotp.TOTP(TOTP_SECRET).now()
        data = obj.generateSession(CLIENT_ID, PIN, totp)
        if data['status']:
            print("સફળતા! એન્જલ વન લોગિન થઈ ગયું છે.")
            return obj
        else:
            print("લોગિનમાં ભૂલ:", data)
            return None
    except Exception as e:
        print("લોગિન એરર:", e)
        return None

# ==========================================
# ૩. પ્યોર NSE સ્ટોક્સ મેળવવાનું ફંક્શન
# ==========================================
def get_nse_stocks():
    print("\nNSE પરથી ઇક્વિટી સ્ટોક્સનું લિસ્ટ મેળવાઈ રહ્યું છે...")
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        df_symbols = pd.read_csv(response)
        
        # SYMBOL મેળવીને પાછળ .NS લગાવવું
        stock_list = [str(sym).strip() + ".NS" for sym in df_symbols['SYMBOL'].tolist()]
        print(f"કમાલ થઈ ગઈ! કુલ {len(stock_list)} સ્ટોક્સ તૈયાર છે.")
        return stock_list
    except Exception as e:
        print("સ્ટોક લિસ્ટ લાવવામાં એરર:", e)
        return []

# ==========================================
# ૪. ટેલિગ્રામ પર એલર્ટ મોકલવાનું ફંક્શન
# ==========================================
def send_telegram_alert(stock_name, entry, stop_loss, target, volume_mult):
    try:
        message = (
            f"🔥 *ટ્રેડિંગ એલર્ટ!*\n"
            f"📌 સ્ટોક: `{stock_name}`\n"
            f"🟢 એન્ટ્રી ભાવ: `₹{entry:.2f}`\n"
            f"🛑 સ્ટોપ-લોး: `₹{stop_loss:.2f}`\n"
            f"🎯 ટાર્ગેટ: `₹{target:.2f}`\n"
            f"📊 વોલ્યુમ સ્પાઈક: `{volume_mult:.1f}x`"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print("ટેલિગ્રામ મેસેજ મોકલવામાં એરર:", e)

# ==========================================
# મુખ્ય પ્રોગ્રામ ફ્લો
# ==========================================
if __name__ == "__main__":
    # ૧. એન્જલ વન લોગિન ચેક કરો
    client = connect_angel_one()
    
    # ૨. સ્ટોક્સ લિસ્ટ મેળવો
    if client:
        stocks = get_nse_stocks()
        print(f"બેઝ ફાઉન્ડેશન કમ્પ્લીટ! સ્કેનર માટે કુલ {len(stocks)} સ્ટોક્સ રેડી છે.")




        # ==========================================
# ૫. RSI ગણતરી માટેનું ફંક્શન
# ==========================================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ==========================================
# ૬. બોલિંજર + RSI ઓવરસોલ્ડ રિવર્સલ સ્કેનર (મુખ્ય સ્ટ્રેટેજી)
# ==========================================
def run_reversal_scanner():
    # ઉપરના ફાઉન્ડેશનમાંથી સ્ટોક લિસ્ટ મેળવો
    stock_list = get_nse_stocks()
    if not stock_list:
        print("સ્ટોક્સનું લિસ્ટ મળ્યું નથી!")
        return

    print("\n--- બોલિંજર + RSI ઓવરસોલ્ડ રિવર્સલ સ્કેનર શરૂ થઈ ગયું છે ---")
    final_picks = []
    total_stocks = len(stock_list)

    for i, sym in enumerate(stock_list):
        try:
            print(f"[{i+1}/{total_stocks}] ચેક કરી રહ્યો છે: {sym}", end="\r")
            
            df = yf.download(sym, period="3mo", interval="1d", progress=False)
            
            if df.empty or len(df) < 40:
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # બોલિંજર બેન્ડ (20 Period, 2 Std Dev)
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

            # RSI (14 Period)
            df['RSI'] = calculate_rsi(df['Close'], 14)

            # વોલ્યુમ સરેરાશ (20 Period)
            df['Volume_Avg'] = df['Volume'].rolling(window=20).mean()

            last_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]

            close_price = float(last_candle['Close'])
            open_price = float(last_candle['Open'])
            low_price = float(last_candle['Low'])
            volume = float(last_candle['Volume'])
            avg_volume = float(df['Volume_Avg'].iloc[-1])
            curr_rsi = float(last_candle['RSI'])

            # 🚨 તમારી સ્ટ્રેટેજીની શરતો:
            # ૧. RSI ઓવરસોલ્ડ ઝોનમાં હોય (દા.ત. RSI < 35)
            # ૨. ગ્રીન કેન્ડલ રિવર્સલ કન્ફર્મેશન
            # ૩. વોલ્યુમ સ્પાઈક >= 1.5x
            is_oversold = curr_rsi < 35.0
            is_green_reversal = close_price > open_price and close_price > prev_candle['Close']
            
            volume_multiplier = volume / avg_volume if avg_volume > 0 else 0
            is_volume_spike = volume_multiplier >= 1.5

            if is_oversold and is_green_reversal and is_volume_spike:
                
                entry_price = close_price
                stop_loss = low_price * 0.98
                risk = entry_price - stop_loss
                target = entry_price + (risk * 2.5)

                msg = (
                    f"🔥 *બોલિંજર & RSI રિવર્સલ એલર્ટ!*\n"
                    f"📌 સ્ટોક: `{sym}`\n"
                    f"🟢 એન્ટ્રી ભાવ: `₹{entry_price:.2f}`\n"
                    f"🛑 સ્ટોપ-લોસ: `₹{stop_loss:.2f}`\n"
                    f"🎯 ટાર્ગેટ: `₹{target:.2f}`\n"
                    f"📉 RSI (ઓવરસોલ્ડ): `{curr_rsi:.1f}`\n"
                    f"📊 વોલ્યુમ સ્પાઈક: `{volume_multiplier:.1f}x`"
                )
                
                print(f"\n🔥 રિવર્સલ મળ્યું: {sym} | Price: ₹{entry_price:.2f} | RSI: {curr_rsi:.1f}")
                send_telegram_alert(msg)
                final_picks.append(sym)

        except Exception as e:
            continue

    print(f"\n\n✨ સ્કેનિંગ પૂરું થયું! કુલ રિવર્સલ સિગ્નલ મળ્યા: {len(final_picks)}")

# ==========================================
# મુખ્ય પ્રોગ્રામ રનિંગ બ્લોક
# ==========================================
if __name__ == "__main__":
    client = connect_angel_one()
    if client:
        run_reversal_scanner()