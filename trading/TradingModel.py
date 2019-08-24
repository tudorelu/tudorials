import pandas as pd
import requests
import json

import plotly.graph_objs as go
from plotly.offline import plot

from pyti.smoothed_moving_average import smoothed_moving_average as sma
from pyti.bollinger_bands import lower_bollinger_band as lbb

from Binance import Binance

class TradingModel:
	
	def __init__(self, symbol):
		self.symbol = symbol
		self.exchange = Binance()
		self.df = self.exchange.GetSymbolData(symbol, '1h')
		self.last_price = self.df['close'][len(self.df['close'])-1]
		self.buy_signals = []

		try:
			self.df['fast_sma'] = sma(self.df['close'].tolist(), 10)
			self.df['slow_sma'] = sma(self.df['close'].tolist(), 30)
			self.df['low_boll'] = lbb(self.df['close'].tolist(), 14)
		except Exception as e:
			print(" Exception raised when trying to compute indicators on "+self.symbol)
			print(e)
			return None

	def strategy(self):	
		
		'''If Price is 3% below Slow Moving Average, then Buy
		Put selling order for 2% above buying price'''

		df = self.df

		buy_signals = []

		for i in range(1, len(df['close'])):
			if df['slow_sma'][i] > df['low'][i] and (df['slow_sma'][i] - df['low'][i]) > 0.03 * df['low'][i]:
				buy_signals.append([df['time'][i], df['low'][i]])

		self.plotData(buy_signals = buy_signals)

	def plotData(self, buy_signals = False):
		df = self.df

		# plot candlestick chart
		candle = go.Candlestick(
			x = df['time'],
			open = df['open'],
			close = df['close'],
			high = df['high'],
			low = df['low'],
			name = "Candlesticks")

		# plot MAs
		fsma = go.Scatter(
			x = df['time'],
			y = df['fast_sma'],
			name = "Fast SMA",
			line = dict(color = ('rgba(102, 207, 255, 50)')))

		ssma = go.Scatter(
			x = df['time'],
			y = df['slow_sma'],
			name = "Slow SMA",
			line = dict(color = ('rgba(255, 207, 102, 50)')))

		lowbb = go.Scatter(
			x = df['time'],
			y = df['low_boll'],
			name = "Lower Bollinger Band",
			line = dict(color = ('rgba(255, 102, 207, 50)')))

		data = [candle, ssma, fsma, lowbb]

		if buy_signals:
			buys = go.Scatter(
					x = [item[0] for item in buy_signals],
					y = [item[1] for item in buy_signals],
					name = "Buy Signals",
					mode = "markers",
				)

			sells = go.Scatter(
					x = [item[0] for item in buy_signals],
					y = [item[1]*1.05 for item in buy_signals],
					name = "Sell Signals",
					mode = "markers",
				)

			data = [candle, ssma, fsma, buys, sells]


		# style and display
		layout = go.Layout(title = self.symbol)
		fig = go.Figure(data = data, layout = layout)

		plot(fig, filename=self.symbol+'.html')


	def maStrategy(self, i:int):
		''' If price is 10% below the Slow MA, return True'''

		df = self.df
		buy_price = 0.99 * df['slow_sma'][i]
		if buy_price >= df['close'][i]:
			self.buy_signals.append([df['time'][i], df['close'][i], df['close'][i] * 1.045])
			return True

		return False

	def bollStrategy(self, i:int):
		''' If price is 5% below the Lower Bollinger Band, return True'''

		df = self.df
		buy_price = 0.99 * df['low_boll'][i]
		if buy_price >= df['close'][i]:
			self.buy_signals.append([df['time'][i], df['close'][i], df['close'][i] * 1.045])
			return True

		return False


def Main():
	# symbol = "ETHUSDT"
	# model = TradingModel(symbol)
	# model.strategy()
	exchange = Binance()

	symbols = exchange.GetTradingSymbols()

	for symbol in symbols:

		print(symbol)
		
		model = TradingModel(symbol)
		
		plot = False
		
		if model.maStrategy(len(model.df['close'])-1):
			print(" MA Strategy match on "+symbol)
			plot = True

		if model.bollStrategy(len(model.df['close'])-1):
			print(" Boll Strategy match on "+symbol)
			plot = True

		if plot:
			model.plotData()

if __name__ == '__main__':
	Main()























