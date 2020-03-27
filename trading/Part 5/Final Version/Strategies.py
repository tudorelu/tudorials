from Indicators import Indicators

# But first, because we're not computing the indicators in TradingModel anymore,
# if they don't already exist within the df, we will be computing them here

def maCrossoverStrategy(df, i:int):
	''' If price is 10% below the Slow MA, return True'''

	if not df.__contains__('50_ema') and not df.__contains__('200_ema'):
		Indicators.AddIndicator(df, indicator_name="ema", col_name="50_ema", args=50)
		Indicators.AddIndicator(df, indicator_name="ema", col_name="200_ema", args=200)

	if i > 0 and df['50_ema'][i-1] <= df['200_ema'][i-1] and \
		df['50_ema'][i] > df['200_ema'][i]:
		return df['close'][i]

	return False

def maStrategy(df, i:int):
	''' If price is 10% below the Slow MA, return True'''

	if not df.__contains__('slow_sma'):
		Indicators.AddIndicator(df, indicator_name="sma", col_name="slow_sma", args=30)

	buy_price = 0.96 * df['slow_sma'][i]
	if buy_price >= df['close'][i]:
		return min(buy_price, df['high'][i])

	return False

def bollStrategy(df, i:int):
	''' If price is 2.5% below the Lower Bollinger Band, return True'''

	if not df.__contains__('low_boll'):
		Indicators.AddIndicator(df, indicator_name="lbb", col_name="low_boll", args=14)

	buy_price = 0.975 * df['low_boll'][i]
	if buy_price >= df['close'][i]:
		return min(buy_price, df['high'][i])

	return False

# Now, we will write our Ichimoku Strategy. We will follow the one from ChartSchool:

def ichimokuBullish(df, i:int):
	''' If price is above the Cloud formed by the Senkou Span A and B, 
	and it moves above Tenkansen (from below), that is a buy signal.'''

	if not df.__contains__('tenkansen') or not df.__contains__('kijunsen') or \
		not df.__contains__('senkou_a') or not df.__contains__('senkou_b'):
		Indicators.AddIndicator(df, indicator_name="ichimoku", col_name=None, args=None)

	if i - 1 > 0 and i < len(df):
		if df['senkou_a'][i] is not None and df['senkou_b'][i] is not None:
			if df['tenkansen'][i] is not None and df['tenkansen'][i-1] is not None:
				if df['close'][i-1] < df['tenkansen'][i-1] and \
					df['close'][i] > df['tenkansen'][i] and \
					df['close'][i] > df['senkou_a'][i] and \
					df['close'][i] > df['senkou_b'][i]:
						return df['close'][i]
	
	return False

strategies_dict = dict(
	ma_crossover = maCrossoverStrategy,
	ma_simple = maStrategy,
	bollinger_simple = bollStrategy,
	ichimoku_bullish = ichimokuBullish,
)