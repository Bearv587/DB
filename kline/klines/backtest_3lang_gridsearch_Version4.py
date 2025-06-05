import pandas as pd
import os
from itertools import product
import lang3_detect_v2
import conf_3lang_v2

symbols = getattr(conf_3lang_v2, "SYMBOLS", ['BTC','ETH','LPT','SOL','TRB','TRUMP'])
periods = getattr(conf_3lang_v2, "PERIODS", ['1m','5m','30m','1h'])
months = getattr(conf_3lang_v2, "MONTHS", ['2025-03','2025-04','2025-05'])
base_dir = getattr(conf_3lang_v2, "BASE_DIR", '.')
capital = getattr(conf_3lang_v2, "CAPITAL", 100.0)
param_grid = getattr(conf_3lang_v2, "PARAM_GRID", {
    'trend_window': [10, 20, 30],
    'osc_range': [0.02, 0.03, 0.05],
    'div_threshold': [1.5, 2.0, 2.5],
})

# 计算总任务数用于进度条
total_tasks = len(symbols) * len(periods) * len(months) * 1
for v in param_grid.values():
    total_tasks *= len(v)
task_count = 0

results = []

for params in (dict(zip(param_grid.keys(), values)) for values in product(*param_grid.values())):
    for symbol in symbols:
        for period in periods:
            for month in months:
                pair = f"{symbol}USDT"
                path = f"{base_dir}/{symbol}/{period}/{pair}_{period}_{month}.csv"
                task_count += 1
                print(f"[{task_count}/{total_tasks}] Processing: {path} | Params: {params}")
                if not os.path.exists(path):
                    print(f"File not found: {path}")
                    continue
                try:
                    df = pd.read_csv(path)
                except Exception as e:
                    print(f"Read CSV error at {path}: {e}")
                    continue
                try:
                    signals = lang3_detect_v2.detect_signals_3lang(df, period, **params)
                except Exception as e:
                    print(f"Error at {path}: {e}")
                    continue
                trades, win, lose, profit, loss, total = [], 0, 0, 0, 0, 0
                position = 0
                entry_price = 0
                for sig in signals:
                    if sig["type"]=="buy" and position==0:
                        position = capital / sig["price"]
                        entry_price = sig["price"]
                    elif sig["type"]=="sell" and position>0:
                        pnl = position * (sig["price"] - entry_price)
                        trades.append(pnl)
                        if pnl>0: win+=1; profit+=pnl
                        else: lose+=1; loss+=pnl
                        total += pnl
                        position = 0
                results.append({
                    **params,
                    "symbol":pair,
                    "period":period,
                    "month":month,
                    "trades":len(trades),
                    "win":win,
                    "lose":lose,
                    "profit":profit,
                    "loss":loss,
                    "total":total,
                    "winrate":win/max(1,len(trades)),
                })

df_stat = pd.DataFrame(results)
summary = df_stat.groupby(list(param_grid.keys())).agg({"total":"sum", "winrate":"mean", "trades":"sum"}).sort_values("total", ascending=False)
print("\n=== Backtest Summary ===")
print(summary)
df_stat.to_csv("backtest_3lang_gridsearch_result.csv")
summary.to_csv("backtest_3lang_gridsearch_summary.csv")