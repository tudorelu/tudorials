import pandas as pd
import requests
import json

import plotly.graph_objs as go
from plotly.offline import plot

# As you can see, the only thing this class does is plot data, so we will remove all
# unnecessary elements, and only leave the essential.

def PlotData(df, buy_signals = False, sell_signals = False, plot_title:str="",
trends = False,
indicators=[
	dict(col_name="fast_ema", color="indianred", name="FAST EMA"), 
	dict(col_name="50_ema", color="indianred", name="50 EMA"), 
	dict(col_name="200_ema", color="indianred", name="200 EMA")]):

	# plot candlestick chart
	candle = go.Candlestick(
		x = df['time'],
		open = df['open'],
		close = df['close'],
		high = df['high'],
		low = df['low'],
		name = "Candlesticks")

	data = [candle]

	for item in indicators:
		if df.__contains__(item['col_name']):
			fsma = go.Scatter(
				x = df['time'],
				y = df[item['col_name']],
				name = item['name'],
				line = dict(color = (item['color'])))
			data.append(fsma)

	if buy_signals:
		buys = go.Scatter(
				x = [item[0] for item in buy_signals],
				y = [item[1] for item in buy_signals],
				name = "Buy Signals",
				mode = "markers",
				marker_size = 20
			)
		data.append(buys)

	if sell_signals:
		sells = go.Scatter(
			x = [item[0] for item in sell_signals],
			y = [item[1] for item in sell_signals],
			name = "Sell Signals",
			mode = "markers",
			marker_size = 20
		)
		data.append(sells)

	# style and display
	# let's customize our layout a little bit:
	layout = go.Layout(
		title=plot_title,
		xaxis = {
			"title" : plot_title,
			"rangeslider" : {"visible": False},
			"type" : "date"
		},
		yaxis = {
			"fixedrange" : False,
		})

	if trends is not False:
		layout['shapes'] = trends
		
	fig = go.Figure(data = data, layout = layout)

	plot(fig, filename='graphs/'+plot_title+'.html')
