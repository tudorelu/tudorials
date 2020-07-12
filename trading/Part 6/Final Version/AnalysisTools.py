# sudo pip install numpy pandas plotly scipy
import numpy as np
import pandas as pd
from numpy import linalg as la
import plotly.graph_objs as go
from scipy.signal import argrelextrema
from Binance import Binance
from Plotter import *

# Helper Function
def get10Factor(num):
	""" Returns the number of 0s before the first non-0 digit of a number 
	(if |num| is < than 1) or negative the number of digits between the first 
	integer digit and the last, (if |num| >= 1) 
	
	get10Factor(0.00000164763) = 6
	get10Factor(1600623.3) = -6
	"""
	p = 0
	for i in range(-20, 20):
		if num == num % 10**i:
			p = -(i - 1)
			break
	return p

def FindTrends(df, n:int=25, distance_factor:float=0.1, extend_lines:bool=False):
	''' 
	Finds local extremas & identifies trends using them

		DataFrame df
			Contains 'OHLC' candlestick data. 

		int n 
			the range surrounding the minima/maxima

		float distance factor 
			how far away does a point need to be to a 
			trend in order to be regarded as a validation
	'''
	# store all the trends information here
	trends = []

	# Find local peaks and add to dataframe (thank GOD for argrelextrema)
	df['min'] = df.iloc[argrelextrema(df.close.values, np.less_equal, order=n)[0]]['close']
	df['max'] = df.iloc[argrelextrema(df.close.values, np.greater_equal, order=n)[0]]['close']

	# Extract only rows where local peaks are not null
	dfMax = df[df['max'].notnull()]
	dfMin = df[df['min'].notnull()]

	# Remove all local maximas which have other maximas close to them 
	prevIndex = -1
	currentIndex = 0
	dropRows = []
	# find indices
	for i1, p1 in dfMax.iterrows():
		currentIndex = i1
		if currentIndex <= prevIndex + n * 0.64:
			dropRows.append(currentIndex)
		prevIndex = i1
	# drop them from the max df
	dfMax = dfMax.drop(dropRows)
	# replace with nan in initial df
	for ind in dropRows:
		df.iloc[ind, :]['max'] = np.nan

	# Remove all local minimas which have other minimas close to them 
	prevIndex = -1
	currentIndex = 0
	dropRows = []
	# find indices
	for i1, p1 in dfMin.iterrows():
		currentIndex = i1
		if currentIndex <= prevIndex + n * 0.64:
			dropRows.append(currentIndex)
		prevIndex = i1
	# drop them from the min df
	dfMin = dfMin.drop(dropRows)
	# replace with nan in initial df
	for ind in dropRows:
		df.iloc[ind, :]['min'] = np.nan

	# # Find Trends Made By Local Maximas
	for i1, p1 in dfMax.iterrows():
		for i2, p2 in dfMax.iterrows():
			if i1 + 1 < i2:
				if p1['max'] <= p2['max']:
				# possible uptrend (starting with p1, with p2 along the way)
					trendPoints = []

					# normalize the starting and ending points
					f = get10Factor(p1['max'])
					p1max = p1['max']*10**f
					p2max = p2['max']*10**f

					tf = get10Factor(p1['time'])
					p1time = p1['time']*10**tf
					p2time = p2['time']*10**tf
					# if p1max < 5 or p2max < 5:
					# 	p1max = p1max * 2
					# 	p2max = p2max * 2
					point1 = np.asarray((p1time, p1max))
					point2 = np.asarray((p2time, p2max))

					# length of trend
					line_length = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

					for i3 in range(i1 + 1, i2):
					# we are checking the points along the way to see how many
					# validations happened or if the trend has been broken
						if not pd.isna(df.iloc[i3, :]['max']):
							p3 = df.iloc[i3, :]

							if p3['max'] > p2['max']:
							# if one value between the two points is larger 
							# than the second point, the trend has been broken
								trendPoints = []
								break
							
							# normalizing this point which is along the way
							p3max = p3['max']*10**f
							p3time = p3['time']*10**tf
							# if p3max < 5:
							# 	p3max = p3max * 2

							point3 = np.asarray((p3time, p3max))

							# distance between p3 and the line made by p1 and p2
							d = la.norm(np.cross(point2-point1, point1-point3))/la.norm(point2-point1)

							# cross product between p2p1 and p2p3
							v1 = (point2[0] - point1[0], point2[1] - point1[1])
							v2 = (point3[0] - point1[0], point3[1] - point1[1])
							xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
							
							if xp > 0.0003 * distance_factor:
							# p3 is too far above the line, therfore the trend is not valid
								trendPoints = []
								break

							if d < 0.0006 * distance_factor:
							# p3 close enough to the line to act as a validation

								trendPoints.append({
									'x' : p3["time"], 
									'y' : p3["max"], 
									'x_norm' : p3time, 
									'y_norm' : p3max, 
									'dist' : d, 
									'xp' : xp})

					if len(trendPoints) > 0:
					# if we have at least 1 trend validations, add it to our list of trends
						trends.append({
							"direction": "up", 
							"position": "above",
							"validations": len(trendPoints),   
							"length":line_length, 
							"i1": i1,
							"i2": i2,
							"p1":(p1["time"], p1["max"]), 
							"p2": (p2["time"], p2["max"]), 
							"color" : "Green",
							"points": trendPoints,
							"p1_norm":(p1time, p1max),
							"p2_norm": (p2time, p2max)})

				else:
				# possible downtrend
					trendPoints = []

					# normalize the starting and ending points
					f = get10Factor(p1['max'])
					p1max = p1['max']*10**f
					p2max = p2['max']*10**f
					# if p1max < 5 or p2max < 5:
					# 	p1max = p1max * 2
					# 	p2max = p2max * 2

					tf = get10Factor(p1['time'])
					p1time = p1['time']*10**tf
					p2time = p2['time']*10**tf

					point1 = np.asarray((p1time, p1max))
					point2 = np.asarray((p2time, p2max))

					# length of trend
					line_length = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

					# now we're checking the points along the way
					# to see how many validations happened 
					# and if the trend has ever been broken
					for i3 in range(i1 + 1, i2):
						if not pd.isna(df.iloc[i3, :]['max']):
							p3 = df.iloc[i3, :]

							if p3['max'] > p1['max']:
							# if one value between the two points is larger 
							# than the first point, the trend has been broken
								trendPoints = []
								break

							# normalizing this point along the way
							p3max = p3['max']*10**f
							p3time = p3['time']*10**tf
							# if p3max < 5:
							# 	p3max = p3max * 2
							point3 = np.asarray((p3time, p3max))

							# distance between p3 and the line made by p1 and p2
							d = la.norm(np.cross(point2-point1, point1-point3))/la.norm(point2-point1)
							
							# cross product between p2p1 and p3p1
							v1 = (point2[0] - point1[0], point2[1] - point1[1])
							v2 = (point3[0] - point1[0], point3[1] - point1[1])
							xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
							
							if xp > 0.0003 * distance_factor:
							# p3 is too far above the line, therefore the trend is not valid
								trendPoints = []
								break

							if d < 0.0006 * distance_factor:
							# p3 close enough to the line to act as a validation
								trendPoints.append({
									'x' : p3['time'], 
									'y' : p3["max"], 
									'x_norm' : p3time, 
									'y_norm' : p3max, 
									'dist' : d, 
									'xp' : xp})

					if len(trendPoints) > 0:
						trends.append({
							"direction": "down", 
							"position": "above",
							"validations": len(trendPoints),   
							"length":line_length, 
							"i1": i1,
							"i2": i2,
							"p1":(p1["time"], p1["max"]), 
							"p2": (p2["time"], p2["max"]), 
							"color" : "Red",
							"points": trendPoints,
							"p1_norm":(p1time, p1max),
							"p2_norm": (p2time, p2max)})

	# Find Trends Made By Local Minimas
	for i1, p1 in dfMin.iterrows():
		for i2, p2 in dfMin.iterrows():
			if i1 + 1 <= i2:
				if p1['min'] < p2['min']:
					# possible uptrend (starting with p1, with p2 along the way)
					trendPoints = []

					# normalize the starting and ending points
					f = get10Factor(p1['min'])
					p1min = p1['min']*10**f
					p2min = p2['min']*10**f

					tf = get10Factor(p1['time'])
					p1time = p1['time']*10**tf
					p2time = p2['time']*10**tf

					# if p1max < 5 or p2max < 5:
					# 	p1max = p1max * 2
					# 	p2max = p2max * 2
					
					point1 = np.asarray((p1time, p1min))
					point2 = np.asarray((p2time, p2min))

					# length of trend
					line_length = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
					
					# now we're checking the points along the way
					# to see how many validations happened 
					# and if the trend has ever been broken
					for i3 in range(i1 + 1, i2):
						if not pd.isna(df.iloc[i3, :]['min']):
							p3 = df.iloc[i3, :]
							if p3['min'] < p1['min']:
							# if one value between the two points is smaller 
							# than the first point, the trend has been broken
								trendPoints = []
								break

							p3min = p3['min']*10**f
							p3time = p3['time']*10**tf
							point3 = np.asarray((p3time, p3min))
							d = la.norm(np.cross(point2-point1, point1-point3))/la.norm(point2-point1)

							v1 = (point2[0] - point1[0], point2[1] - point1[1]) 
							v2 = (point3[0] - point1[0], point3[1] - point1[1])
							xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
							
							if xp < -0.0003 * distance_factor:
								trendPoints = []
								break

							if d < 0.0006 * distance_factor:
								trendPoints.append({
									'x' :p3['time'],  
									'y' : p3["min"], 
									'x_norm' : p3time, 
									'y_norm' : p3min, 
									'dist' : d, 
									'xp' : xp})

					if len(trendPoints)> 0:
						trends.append({
							"direction": "up", 
							"position": "below",
							"validations": len(trendPoints),   
							"length":line_length, 
							"i1": i1,
							"i2": i2,
							"p1":(p1["time"], p1["min"]), 
							"p2": (p2["time"], p2["min"]), 
							"color" : "Green",
							"points": trendPoints,
							"p1_norm":(p1time, p1min),
							"p2_norm": (p2time, p2min)})

				else:
				# possible downtrend (starting with p1, with p2 along the way)
					trendPoints = []

					# normalize the starting and ending points
					f = get10Factor(p1['min'])
					p1min = p1['min']*10**f
					p2min = p2['min']*10**f

					tf = get10Factor(p1['time'])
					p1time = p1['time']*10**tf
					p2time = p2['time']*10**tf

					# if p1max < 5 or p2max < 5:
					# 	p1max = p1max * 2
					# 	p2max = p2max * 2
					
					point1 = np.asarray((p1time, p1min))
					point2 = np.asarray((p2time, p2min))

					# length of trend
					line_length = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
					
					# now we're checking the points along the way
					# to see how many validations happened 
					# and if the trend has ever been broken
					for i3 in range(i1 + 1, i2):
						if not pd.isna(df.iloc[i3, :]['min']):
							p3 = df.iloc[i3, :]
							if p3['min'] < p2['min']:
							# if one value between the two points is smaller 
							# than the last point, the trend has been broken
								trendPoints = []
								break

							p3min = p3['min']*10**f
							p3time = p3['time']*10**tf
							point3 = np.asarray((p3time, p3min))
							d = la.norm(np.cross(point2-point1, point1-point3))/la.norm(point2-point1)

							v1 = (point2[0] - point1[0], point2[1] - point1[1]) 
							v2 = (point3[0] - point1[0], point3[1] - point1[1])
							xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
							
							if xp < -0.0003 * distance_factor:
								trendPoints = []
								break

							if d < 0.0006 * distance_factor:
								trendPoints.append({
									'x' : p3['time'], 
									'y' : p3["min"], 
									'x_norm' : p3time, 
									'y_norm' : p3min, 
									'dist' : d, 
									'xp' : xp})

					if len(trendPoints)> 0:
						trends.append({
							"direction": "down", 
							"position": "below",
							"validations": len(trendPoints),   
							"length":line_length, 
							"i1": i1,
							"i2": i2,
							"p1":(p1["time"], p1["min"]), 
							"p2": (p2["time"], p2["min"]), 
							"color" : "Red",
							"points": trendPoints,
							"p1_norm":(p1time, p1min),
							"p2_norm": (p2time, p2min)})

	# print("\nAll Trends for "+model.symbol)
	# print(len(trends))

	# Remove redundant trends
	removeTrends = []
	priceRange = df['max'].max() / df['min'].min()

	# Loop through trends twice
	for trend1 in trends:
		if trend1 in removeTrends:
			continue
		for trend2 in trends:
			if trend2 in removeTrends:
				continue
			# If trends share the same starting or ending point, but not both, and the cross product 
			# between their vectors is small (and so is the angle between them), remove the shortest 
			if trend1["i1"] == trend2["i1"] and trend1["i2"] != trend2["i2"]:
				v1 = (trend1["p2_norm"][0] - trend1["p1_norm"][0], trend1["p2_norm"][1] - trend1["p1_norm"][1]) 
				v2 = (trend2["p2_norm"][0] - trend1["p1_norm"][0], trend2["p2_norm"][1] - trend1["p1_norm"][1])
				xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
				
				if xp < 0.0004 * priceRange and xp > -0.0004 * priceRange:
					# print("p1: Trends are close to each other!")
					# print(str(trend1['p1']) + " " + str(trend1['p2']))
					# print(str(trend2['p1']) + " " + str(trend2['p2']))
					if trend1['length'] > trend2['length']:
						removeTrends.append(trend2)
						# trends.remove(trend2)
						trend1["validations"] = trend1["validations"] + 1
					else:
						removeTrends.append(trend1)
						# trends.remove(trend1)
						trend2["validations"] = trend2["validations"] + 1

			elif trend1["i2"] == trend2["i2"] and trend1["i1"] != trend2["i1"]:
				v1 = (trend1["p1_norm"][0] - trend1["p2_norm"][0], trend1["p1_norm"][1] - trend1["p2_norm"][1]) 
				v2 = (trend2["p1_norm"][0] - trend1["p2_norm"][0], trend2["p1_norm"][1] - trend1["p2_norm"][1])
				xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
				
				if xp < 0.0004 * priceRange and xp > -0.0004 * priceRange:
					# print("p2: Trends are close to each other!")
					# print(str(trend1['p1']) + " " + str(trend1['p2']))
					# print(str(trend2['p1']) + " " + str(trend2['p2']))
					if trend1['length'] > trend2['length']:
						removeTrends.append(trend2)
						# trends.remove(trend2)
						trend1["validations"] = trend1["validations"] + 1
					else:
						removeTrends.append(trend1)
						# trends.remove(trend1)
						trend2["validations"] = trend2["validations"] + 1

	for trend in removeTrends:
		if trend in trends:
			trends.remove(trend)

	# Identify parralel trends (above and below)
	# Get line equations based on points
	# Create lines to draw on graph
	lines = []

	# Also save line equations
	lineEqs = []
	
	for trend in trends:
		# If trend has more than 2 validations, plot the line covering the entire chart
		if extend_lines and trend["validations"] > 2:

			# Find the line equation
			m = (trend["p2"][1] - trend["p1"][1]) / (trend["p2"][0] - trend["p1"][0])
			b = trend["p2"][1] - m * trend["p2"][0]
			lineEqs.append((m, b))

			# Find the last timestamp
			tMax = df['time'].max()

			# Add those points on the graph too
			line2 = go.layout.Shape(
				type="line",
				x0=trend["p1"][0], y0=trend["p1"][1],
				x1=tMax, y1=m * tMax + b,
				line=dict(
					color=trend["color"],
					width=max(1, trend["validations"]),
					dash="dot",
				))
			lines.append(line2)
		else:
			line = go.layout.Shape(
				type="line",
				x0=trend["p1"][0], y0=trend["p1"][1],
				x1=trend["p2"][0], y1=trend["p2"][1],
				line=dict(
					color=trend["color"],
					width=max(1, trend["validations"]/2),
					dash="dot",
				))
			lines.append(line)

	return lines

def Main():
	""""""
	exchange = Binance(filename = 'credentials.txt')
	symbol = 'LTCUSDT'
	df = exchange.GetSymbolKlines(symbol, '5m', 1000)
	lines = FindTrends(df, distance_factor=0.01, n=20)
	PlotData(df, trends=lines, plot_title=symbol+" trends")

if __name__ == '__main__':
	Main()






