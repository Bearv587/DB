import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

BINANCE_API_WEIGHT_LIMIT_PER_MIN = 1200
KLINE_REQ_WEIGHT = 2

class ApiWeightManager:
    def __init__(self, weight_limit=BINANCE_API_WEIGHT_LIMIT_PER_MIN, interval_sec=60):
        self.weight_limit = weight_limit
        self.interval_sec = interval_sec
        self.reset_time = time.time() + interval_sec
        self.used_weight = 0

    def add_weight(self, weight):
        now = time.time()
        if now > self.reset_time:
            self.used_weight = 0
            self.reset_time = now + self.interval_sec
        self.used_weight += weight

    def can_request(self, next_weight):
        now = time.time()
        if now > self.reset_time:
            self.used_weight = 0
            self.reset_time = now + self.interval_sec
        return (self.used_weight + next_weight) <= self.weight_limit

    def wait_for_slot(self, next_weight):
        while not self.can_request(next_weight):
            sleep_time = max(1, int(self.reset_time - time.time()) + 1)
            print(f"API权重超限，休眠{sleep_time}秒...")
            time.sleep(sleep_time)

def fetch_klines(symbol, interval, start_time, end_time, limit=1000, weight_mgr=None):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": int(start_time),
        "endTime": int(end_time),
        "limit": limit
    }
    if weight_mgr:
        weight_mgr.wait_for_slot(KLINE_REQ_WEIGHT)
        weight_mgr.add_weight(KLINE_REQ_WEIGHT)
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def save_monthly_klines(symbol, intervals, months=3, save_dir="klines"):
    if isinstance(intervals, str):
        intervals = [intervals]
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    weight_mgr = ApiWeightManager()
    for interval in intervals:
        now_iter = now
        for m in range(months):
            month_start = (now_iter.replace(day=1) - timedelta(days=1)).replace(day=1)
            now_iter = month_start
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(milliseconds=1)
            print(f"Fetching {symbol} {interval} {month_start.strftime('%Y-%m')} ...")
            fname = f"{symbol}_{interval}_{month_start.strftime('%Y-%m')}.csv"
            os.makedirs(save_dir, exist_ok=True)
            full_path = os.path.join(save_dir, fname)
            all_klines = []
            since = int(month_start.timestamp() * 1000)
            end = int(month_end.timestamp() * 1000)
            while since < end:
                data = fetch_klines(symbol, interval, since, end, weight_mgr=weight_mgr)
                if not data:
                    break
                all_klines.extend(data)
                last_time = data[-1][0]
                # 计算步进
                if interval.endswith("m"):
                    step = int(interval[:-1]) * 60 * 1000
                elif interval.endswith("h"):
                    step = int(interval[:-1]) * 60 * 60 * 1000
                elif interval.endswith("d"):
                    step = int(interval[:-1]) * 24 * 60 * 60 * 1000
                elif interval.endswith("w"):
                    step = int(interval[:-1]) * 7 * 24 * 60 * 60 * 1000
                elif interval.endswith("M"):
                    step = int(interval[:-1]) * 30 * 24 * 60 * 60 * 1000  # 近似月
                else:
                    step = 60 * 1000  # 默认1m
                since = last_time + step
                time.sleep(0.2)
                if len(data) < 1000:
                    break
            if all_klines:
                df = pd.DataFrame(all_klines, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_asset_vol", "num_trades",
                    "taker_buy_base", "taker_buy_quote", "ignore"
                ])
                df.to_csv(full_path, index=False)
                print(f"Saved {full_path} ({len(df)} rows)")
            else:
                print(f"No data for {symbol} {interval} {month_start.strftime('%Y-%m')}")

if __name__ == "__main__":
    # === 配置区 ===
    symbol = "LPTUSDT"    # 现货币对
    intervals = ["1m", "5m", "30m", "1h"]  # 支持多周期，如 ["1m", "5m", "1h"]
    months = 3            # 获取最近几个月
    save_dir = "klines"   # 保存路径
    save_monthly_klines(symbol, intervals, months, save_dir)
