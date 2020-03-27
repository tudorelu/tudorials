import requests 
import json
import decimal
import hmac
import time
import pandas as pd
import hashlib

# I will show you how exactly to get these API Keys
# But first, let's update our function that gets the candlestick data 
# to get more than just the limit of 1000 candles. It will be useful
# in case we want to backtest our strategies over a longer period

binance_keys = {
	'api_key': "PLACE_API_KEY_HERE",
	'secret_key': "PLACE_SECRET_KEY_HERE"
}

class Binance:
	def __init__(self):

		self.base = 'https://api.binance.com'

		self.endpoints = {
			"order": '/api/v3/order',
			"testOrder": '/api/v3/order/test',
			"allOrders": '/api/v3/allOrders',
			"klines": '/api/v3/klines',
			"exchangeInfo": '/api/v3/exchangeInfo'
		}

		self.headers = {"X-MBX-APIKEY": binance_keys['api_key']}
	
	def GetTradingSymbols(self, quoteAssets:list=None):
		''' Gets All symbols which are tradable (currently) '''
		url = self.base + self.endpoints["exchangeInfo"]

		try: 
			response = requests.get(url)
			data = json.loads(response.text)
		except Exception as e:
			print(" Exception occured when trying to access "+url)
			print(e)
			return []

		symbols_list = []

		for pair in data['symbols']:
			if pair['status'] == 'TRADING':
				if quoteAssets != None and pair['quoteAsset'] in quoteAssets:
					symbols_list.append(pair['symbol'])

		return symbols_list

	def GetLongerSymbolData(self, symbol:str, interval:str, limit:int=1000, end_time=False):
		# Basicall, we will be calling the GetSymbolData as many times as we need 
		# in order to get all the historical data required (based on the limit parameter)
		# and we'll be merging the results into one long dataframe.

		repeat_rounds = 0
		if limit > 1000:
			repeat_rounds = int(limit/1000)
		initial_limit = limit % 1000
		if initial_limit == 0:
			initial_limit = 1000
		# First, we get the last initial_limit candles, starting at end_time and going
		# backwards (or starting in the present moment, if end_time is False)
		df = self.GetSymbolData(symbol, interval, limit=initial_limit, end_time=end_time)
		while repeat_rounds > 0:
			# Then, for every other 1000 candles, we get them, but starting at the beginning
			# of the previously received candles.
			df2 = self.GetSymbolData(symbol, interval, limit=1000, eend_time=df['time'[0]])
			df = df2.append(df, ignore_index = True)
			repeat_rounds = repeat_rounds - 1
		
		return df

	def GetSymbolData(self, symbol:str, interval:str, limit:int=1000, end_time=False):
		''' 
		Gets trading data for one symbol 
		
		Parameters
		--
			symbol str:        The symbol for which to get the trading data

			interval str:      The interval on which to get the trading data
				minutes      '1m' '3m' '5m' '15m' '30m'
				hours        '1h' '2h' '4h' '6h' '8h' '12h'
				days         '1d' '3d'
				weeks        '1w'
				months       '1M;
		'''

		if limit > 1000:
			return self.GetLongerSymbolData(symbol, interval, limit. end_time)
		
		params = '?&symbol='+symbol+'&interval='+interval+'&limit='+str(limit)
		if end_time:
			params = params + '&endTime=' + str(int(end_time))

		url = self.base + self.endpoints['klines'] + params

		# download data
		data = requests.get(url)
		dictionary = json.loads(data.text)

		# put in dataframe and clean-up
		df = pd.DataFrame.from_dict(dictionary)
		df = df.drop(range(6, 12), axis=1)

		# rename columns
		col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
		df.columns = col_names

		# transform values from strings to floats
		for col in col_names:
			df[col] = df[col].astype(float)

		df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)

		return df


	def PlaceOrder(self, symbol:str, side:str, type:str, quantity:float=0, price:float=0, test:bool=True):

		'''
		Places an order on Binance

		Parameters
		--
			symbol str:        The symbol for which to get the trading data

			side str:          The side of the order 'BUY' or 'SELL'

			type str:          The type, 'LIMIT', 'MARKET', 'STOP_LOSS'

			quantity float:    .....

		'''

		params = {
			'symbol': symbol,
			'side': side, 			# BUY or SELL
			'type': type,				# MARKET, LIMIT, STOP LOSS etc
			'quoteOrderQty': quantity,
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000))
		}

		if type != 'MARKET':
			params['timeInForce'] = 'GTC'
			params['price'] = self.floatToString(price)

		self.signRequest(params)

		url = ''
		if test: 
			url = self.base + self.endpoints['testOrder']
		else:
			url = self.base + self.endpoints['order']

		try: 
			response = requests.post(url, params=params, headers=self.headers)
			data = response.text
		except Exception as e:
			print(" Exception occured when trying to palce order on "+url)
			print(e)
			data = {'code': '-1', 'msg':e}

		return json.loads(data)

	def CancelOrder(self, symbol:str, orderId:str):
		'''
			Cancels the order on a symbol based on orderId
		'''

		params = {
			'symbol': symbol,
			'orderId' : orderId,
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = self.base + self.endpoints['order']

		try: 
			response = requests.delete(url, params=params, headers=self.headers)
			data = response.text
		except Exception as e:
			print("Exception occured when trying to cancel order on "+url)
			print(e)
			data = {'code': '-1', 'msg':e}
		
		return json.loads(data)

	def GetOrderInfo(self, symbol:str, orderId:str):
		'''
			Gets info about an order on a symbol based on orderId
		'''

		params = {
			'symbol': symbol,
			'orderId' : orderId,
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = self.base + self.endpoints['order']

		try: 
			response = requests.get(url, params=params, headers=self.headers)
			data = response.text
		except Exception as e:
			print(" Exception occured when trying to get order info on "+url)
			print(e)
			data = {'code': '-1', 'msg':e}

		return json.loads(data)


	def GetAllOrderInfo(self, symbol:str):
		'''
			Gets info about all order on a symbol
		'''

		params = {
			'symbol': symbol,
			'timestamp': int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = self.base + self.endpoints['allOrders']

		try: 
			response = requests.get(url, params=params, headers=self.headers)
			data = response.text
		except Exception as e:
			print("Exception occured when trying to get info on all orders on "+url)
			print(e)
			data = {'code': '-1', 'msg':e}

		return json.loads(data)

	def floatToString(self, f:float):
		''' Converts the given float to a string,
		without resorting to the scientific notation '''

		ctx = decimal.Context()
		ctx.prec = 12
		d1 = ctx.create_decimal(repr(f))
		return format(d1, 'f')

	def signRequest(self, params:dict):
		''' Signs the request to the Binance API '''

		query_string = '&'.join(["{}={}".format(d, params[d]) for d in params])
		signature = hmac.new(binance_keys['secret_key'].encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
		params['signature'] = signature.hexdigest()
