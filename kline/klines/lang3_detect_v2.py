import pandas as pd
import numpy as np
from conf_3lang_v2 import *

def set_period_params(period):
    params = dict(
        fenxing_window=fenxing_window,
        fenxing_price_delta=fenxing_price_delta,
        fenxing_atr_mult=fenxing_atr_mult,
        fenxing_vol_mult=fenxing_vol_mult
    )
    params.update(period_settings.get(period, {}))
    return params

def dynamic_fenxing_filter(df, idx, params):
    if not auto_fenxing_filter:
        return params["fenxing_price_delta"], params["fenxing_vol_mult"], params["fenxing_atr_mult"]
    atr = df["atr"].iloc[idx]
    vol = df["volume"].iloc[idx]
    atrs = df["atr"].iloc[max(0,idx-50):idx].dropna()
    vols = df["volume"].iloc[max(0,idx-50):idx].dropna()
    atr_pct = (atrs < atr).mean() if len(atrs)>0 else 0.5
    vol_pct = (vols < vol).mean() if len(vols)>0 else 0.5
    fpd = params["fenxing_price_delta"]
    fvm = params["fenxing_vol_mult"]
    fam = params["fenxing_atr_mult"]
    if atr_pct < fenxing_min_percentile or vol_pct < fenxing_min_percentile:
        return fpd * 1.5, fvm * 1.2, fam * 1.2
    return fpd, fvm, fam

def is_valid_fenxing(df, idx, typ, params):
    price = df["close"].iloc[idx]
    vol = df["volume"].iloc[idx]
    atr = df["atr"].iloc[idx]
    body = abs(df["close"].iloc[idx] - df["open"].iloc[idx])
    fpd, fvm, fam = dynamic_fenxing_filter(df, idx, params)
    if body < dir_kline_min_body:
        return False, 0
    atr_cond = atr > fam * df["atr"].iloc[max(0, idx-atr_window):idx].mean()
    vol_cond = vol > fvm * df["volume"].iloc[max(0, idx-vol_window):idx].mean()
    if fx_atr_and_vol:
        if not (atr_cond and vol_cond):
            return False, 0
    else:
        if not (atr_cond or vol_cond):
            return False, 0
    win = params["fenxing_window"]
    if typ == "top":
        local_max = df["close"].iloc[idx-win:idx+win+1].max()
        if price < local_max or (price - df["close"].iloc[idx-win:idx+win+1].min()) < fpd:
            return False, 0
    if typ == "bottom":
        local_min = df["close"].iloc[idx-win:idx+win+1].min()
        if price > local_min or (df["close"].iloc[idx-win:idx+win+1].max() - price) < fpd:
            return False, 0
    weight = 1
    if vol > vol_spike_mult * df["volume"].iloc[max(0, idx-vol_window):idx].mean() and body > dir_kline_min_body*2:
        weight = fx_weight_strong
    return True, weight

def find_fenxing(df, params):
    fx = []
    for i in range(params["fenxing_window"], len(df)-params["fenxing_window"]):
        if df["close"].iloc[i] == df["close"].iloc[i-params["fenxing_window"]:i+params["fenxing_window"]+1].max():
            ok, weight = is_valid_fenxing(df, i, "top", params)
            if ok:
                fx.append({"idx": i, "type": "top", "price": df["close"].iloc[i], "weight": weight})
        if df["close"].iloc[i] == df["close"].iloc[i-params["fenxing_window"]:i+params["fenxing_window"]+1].min():
            ok, weight = is_valid_fenxing(df, i, "bottom", params)
            if ok:
                fx.append({"idx": i, "type": "bottom", "price": df["close"].iloc[i], "weight": weight})
    return fx

def match_3lang_signals(fx, df, params):
    buy_signals, sell_signals = [], []
    for i in range(2, len(fx)):
        if (fx[i-2]["type"] == "bottom" and fx[i-1]["type"] == "top" and fx[i]["type"] == "bottom"
            and (fx[i]["price"] > fx[i-2]["price"] + buy2_3_delta or allow_buy2_buy3_higher)):
            buy_signals.append({"idx": fx[i]["idx"], "type": "buy", "price": fx[i]["price"], "fx_weight": fx[i]["weight"]})
        if (fx[i-2]["type"] == "top" and fx[i-1]["type"] == "bottom" and fx[i]["type"] == "top"
            and (fx[i]["price"] < fx[i-2]["price"] - buy2_3_delta or allow_buy2_buy3_higher)):
            sell_signals.append({"idx": fx[i]["idx"], "type": "sell", "price": fx[i]["price"], "fx_weight": fx[i]["weight"]})
    return buy_signals, sell_signals

def interval_pairing_signals(df, buy_signals, sell_signals, params):
    paired_buys, paired_sells = [], []
    for sig in buy_signals:
        idx = sig["idx"]
        window = df.iloc[idx:idx+pairing_window]
        max_profit = (window["close"].max() - sig["price"]) if not window.empty else 0
        if max_profit >= pairing_min_profit:
            paired_buys.append(sig)
    for sig in sell_signals:
        idx = sig["idx"]
        window = df.iloc[idx:idx+pairing_window]
        max_profit = (sig["price"] - window["close"].min()) if not window.empty else 0
        if max_profit >= pairing_min_profit:
            paired_sells.append(sig)
    return paired_buys, paired_sells

def main_detect(df, period="1m"):
    params = set_period_params(period)
    df = df.copy()
    df["atr"] = (df["high"] - df["low"]).rolling(atr_window).mean()
    fx = find_fenxing(df, params)
    buy, sell = match_3lang_signals(fx, df, params)
    buy, sell = interval_pairing_signals(df, buy, sell, params)
    return {
        "buy": buy,
        "sell": sell,
        "fenxing": fx,
    }

def detect_signals_3lang(df, period, **params):
    """
    回测标准接口（历史数据批量分析专用）
    """
    r = main_detect(df, period)
    if not isinstance(r, dict) or "buy" not in r or "sell" not in r:
        return []
    signals = []
    for b in r["buy"]:
        signals.append({"type": "buy", "idx": b["idx"], "price": b["price"]})
    for s in r["sell"]:
        signals.append({"type": "sell", "idx": s["idx"], "price": s["price"]})
    signals = sorted(signals, key=lambda x: x["idx"])
    return signals