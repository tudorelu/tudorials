import requests 
import json
import decimal
import hmac
import time
import pandas as pd

binance_keys = {
	'api_key': "PASTE API KEY HERE",
	'secret_key': "PASTE SECRET KEY HERE"
}

class Binance:
	def __init__(self):

		self.base = 'https://api.binance.com'

		self.endpoints = {
			"order": '/api/v1/order',
			"testOrder": '/api/v1/order/test',
			"allOrders": '/api/v1/allOrders',
			"klines": '/api/v1/klines',
			"exchangeInfo": '/api/v1/exchangeInfo'
		}

	def GetTradingSymbols(self):
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
				symbols_list.append(pair['symbol'])

		return symbols_list

	def GetSymbolData(self, symbol:str, interval:str):
		''' Gets trading data for one symbol '''

		params = '?&symbol='+symbol+'&interval='+interval

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

		return df


	def PlaceOrder(self, symbol:str, side:str, type:str, quantity:float, price:float, test:bool=True):

		'''
		Symbol: ETHBTC

		ETH - base Asset (what we buy)
		BTC - quote Asset (what we sell for)
		quantity - how much ETH we want
		price - how much BTC we're willing to sell it for

		'''

		params = {
			'symbol': symbol,
			'side': side, 			# BUY or SELL
			'type': type,				# MARKET, LIMIT, STOP LOSS etc
			'timeInForce': 'GTC',
			'quantity': quantity,
			'price' : self.floatToString(price),
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = ''
		if test: 
			url = self.base + self.endpoints['testOrder']
		else:
			url = self.base + self.endpoints['order']


		try: 
			response = requests.post(url, params=params, headers={"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print(" Exception occured when trying to palce order on "+url)
			print(e)
			response = {'code': '-1', 'msg':e}
			return None

		return json.loads(response.text)

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
			response = requests.delete(url, params=params, headers={"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print(" Exception occured when trying to cancel order on "+url)
			print(e)
			response = {'code': '-1', 'msg':e}
			return None

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
			response = requests.get(url, params=params, headers={"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print(" Exception occured when trying to get order info on "+url)
			print(e)
			response = {'code': '-1', 'msg':e}
			return None

		return json.loads(response.text)


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
			response = requests.get(url, params=params, headers={"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print(" Exception occured when trying to get info on all orders on "+url)
			print(e)
			response = {'code': '-1', 'msg':e}
			return None

		return json.loads(response.text)

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




