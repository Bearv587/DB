# ===【分型过滤参数模块】===
fenxing_window = 4            # 分型窗口，决定分型的灵敏度。建议3~8
fenxing_price_delta = 0.0018  # 分型最小价差。建议1m:0.0015~0.003, 5m:0.002~0.006, 30m:0.005~0.015, 1h:0.01~0.03
fenxing_atr_mult = 1.7        # ATR过滤强度。建议1.2~2.5
fenxing_vol_mult = 2.0        # 成交量过滤强度。建议1.2~3.0
auto_fenxing_filter = True    # 启用ATR/成交量分位动态调整分型阈值
fenxing_min_percentile = 0.4  # 分型过滤的ATR/vol分位下限，低于此按高门槛过滤。建议0.3~0.6

# ===【分型有效性与权重】===
vol_spike_mult = 2.0         # 分型K线需成交量激增倍数。建议1.5~3.0
dir_kline_min_body = 0.0010  # 方向K线最小实体
fx_atr_and_vol = True        # 分型需同时满足ATR与成交量过滤，否则信号无效
fx_weight_strong = 2.0       # 分型权重提升（极端放量+大阳/大阴赋权）

# ===【三浪递推与买点模块】===
allow_buy2_buy3_higher = True # 允许买二买三冲高
buy2_3_delta = 0.0012         # 买二/买三高于前买点的最小阈值
pairing_window = 12           # 买卖区间窗口。建议8~20
pairing_min_profit = 0.0020   # 配对区间内最小盈亏比，达不到不信号。建议0.001~0.003

# ===【成交量/波动率检测】===
atr_window = 10               # ATR均线窗口
vol_window = 10               # 成交量均线窗口
vol_mult = 1.7                # 分型/信号判定成交量倍数

# ===【丢失/极端行情检测】===
max_lost_kline = 12           # 最大买点丢失容忍。建议8~20
lost_type = "soft"            # soft:允许一定回撤，hard:严格计数
extreme_down_kline = 2.5      # 极端下杀倍数
chase_up_kline = 2.5          # 极端上涨倍数
chase_buy_enabled = False     # 是否允许极端上涨追涨买入信号
extreme_cooldown = 5          # 极端信号后冷却期，避免插针追涨追跌

# ===【K线数据与多周期辅助】===
kline_api_init_num = 200
ws_update = True
ws_kline_type = "1m"
price_realtime_source = "ws"
trend_kline_periods = ["5m", "30m", "1h"]  # 趋势分析辅助周期

# ===【周期参数覆盖】===
period_settings = {
    "1m": dict(fenxing_window=4, fenxing_price_delta=0.0018, fenxing_atr_mult=1.7, fenxing_vol_mult=2.0),
    "5m": dict(fenxing_window=4, fenxing_price_delta=0.0032, fenxing_atr_mult=1.6, fenxing_vol_mult=1.8),
    "30m":dict(fenxing_window=5, fenxing_price_delta=0.009,  fenxing_atr_mult=1.5, fenxing_vol_mult=1.7),
    "1h": dict(fenxing_window=6, fenxing_price_delta=0.016, fenxing_atr_mult=1.4, fenxing_vol_mult=1.5)
}

# ===【其他】===
debug_mode = False

# === 参数上下限建议 ===
# 低阈值信号更灵敏，适合趋势，易噪声；高阈值信号更稳健易漏机会
# ATR/成交量倍数建议1.2~3.0，分型窗口3~8，买卖配对区间8~20