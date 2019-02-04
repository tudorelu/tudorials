
import requests
import json
import pandas as pd

from pyti.smoothed_moving_average import smoothed_moving_average as sma

import plotly
import plotly.plotly as py
import plotly.graph_objs as go

class TradingModel:

	def __init__(self, symbol):
		self.symbol = symbol
		self.df = self.getData('1h')

	def getData(self, interval='1h'):
		
		# define url
		base = 'https://api.binance.com'
		endpoint = '/api/v1/klines'
		params = '?&symbol='+self.symbol+'&interval='+interval

		url = base + endpoint + params

		# get actual data
		data = requests.get(url)
		dictionary = json.loads(data.text)

		# put data in dataframe and cleanup
		df = pd.DataFrame.from_dict(dictionary)
		df = df.drop(range(6, 12), axis = 1) # drops columns 6 tp 12

		# rename columns
		cols = ['time_stamp', 'open', 'high', 'low', 'close', 'volume']
		df.columns = cols

		# transform values from string to floats
		for col in cols:
			df[col] = df[col].astype(float)

		# technical indicators (moving averages)
		df['fast_sma'] = sma(df['close'].tolist(), 7)
		df['slow_sma'] = sma(df['close'].tolist(), 25)

		return df


	def plotData(self):

		df = self.df

		candle = go.Candlestick(
			x = df['time_stamp'],
			open = df['open'],
			high = df['high'],
			low = df['low'],
			close = df['close'],
			name = "Candlesticks")

		# plot MAs
		fsma = go.Scatter(
			x = df['time_stamp'],
			y = df['fast_sma'],
			name = 'Fast SMA',
			line = dict(
				color = ('rgba(102, 207, 255, 50)'),
				width = 2))

		ssma = go.Scatter(
			x = df['time_stamp'],
			y = df['slow_sma'],
			name = 'Slow SMA',
			line = dict(
				color = ('rgba(255, 207, 102, 50)'),
				width = 2))

		data = [candle, fsma, ssma]

		# style the plot
		layout = go.Layout(title = self.symbol)
		fig = go.Figure(data = data, layout = layout)

		# display
		py.plot(fig, filename=self.symbol+' candlestick & MAs')


def Main():
	symbols = ["BTCUSDT", "ETHUSDT", "ETHBTC"]

	for symbol in symbols:
		print("Checking out "+symbol)
		model = TradingModel(symbol)
		print(model.getData())
		model.plotData()

if __name__ == '__main__':
	Main()

