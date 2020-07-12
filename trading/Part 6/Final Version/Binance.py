import requests 
import json
import decimal
import hmac
import time
import pandas as pd
import hashlib
from decimal import Decimal

# I will show you how exactly to get these API Keys
# But first, let's update our function that gets the candlestick data 
# to get more than just the limit of 1000 candles. It will be useful
# in case we want to backtest our strategies over a longer period

request_delay = 1000

class Binance:

	ORDER_STATUS_NEW = 'NEW'
	ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
	ORDER_STATUS_FILLED = 'FILLED'
	ORDER_STATUS_CANCELED = 'CANCELED'
	ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
	ORDER_STATUS_REJECTED = 'REJECTED'
	ORDER_STATUS_EXPIRED = 'EXPIRED'

	SIDE_BUY = 'BUY'
	SIDE_SELL = 'SELL'

	ORDER_TYPE_LIMIT = 'LIMIT'
	ORDER_TYPE_MARKET = 'MARKET'
	ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
	ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
	ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
	ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
	ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

	KLINE_INTERVALS = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']

	def __init__(self, filename=None):

		self.base = 'https://api.binance.com'

		self.endpoints = {
			"order": '/api/v3/order',
			"testOrder": '/api/v3/order/test',
			"allOrders": '/api/v3/allOrders',
			"klines": '/api/v3/klines',
			"exchangeInfo": '/api/v3/exchangeInfo',
			"24hrTicker" : '/api/v3/ticker/24hr',
			"averagePrice" : '/api/v3/avgPrice',
			"orderBook" : '/api/v3/depth',
			"account" : '/api/v3/account'
		}
		self.account_access = False

		if filename == None:
			return
	
		f = open(filename, "r")
		contents = []
		if f.mode == 'r':
			contents = f.read().split('\n')

		self.binance_keys = dict(api_key = contents[0], secret_key=contents[1])

		self.headers = {"X-MBX-APIKEY": self.binance_keys['api_key']}

		self.account_access = True
	
	def _get(self, url, params=None, headers=None) -> dict:
		""" Makes a Get Request """
		try: 
			response = requests.get(url, params=params, headers=headers)
			data = json.loads(response.text)
			data['url'] = url
		except Exception as e:
			print("Exception occured when trying to access "+url)
			print(e)
			data = {'code': '-1', 'url':url, 'msg': e}
		return data

	def _post(self, url, params=None, headers=None) -> dict:
		""" Makes a Post Request """
		try: 
			response = requests.post(url, params=params, headers=headers)
			data = json.loads(response.text)
			data['url'] = url
		except Exception as e:
			print("Exception occured when trying to access "+url)
			print(e)
			data = {'code': '-1', 'url':url, 'msg': e}
		return data

	def GetTradingSymbols(self, quoteAssets:list=None):
		''' Gets All symbols which are tradable (currently) '''
		url = self.base + self.endpoints["exchangeInfo"]
		data = self._get(url)
		if data.__contains__('code'):
			return []

		symbols_list = []
		for pair in data['symbols']:
			if pair['status'] == 'TRADING':
				if quoteAssets != None and pair['quoteAsset'] in quoteAssets:
					symbols_list.append(pair['symbol'])

		return symbols_list

	def GetSymbolDataOfSymbols(self, symbols:list=None):
		''' Gets All symbols which are tradable (currently) '''
		url = self.base + self.endpoints["exchangeInfo"]
		data = self._get(url)
		if data.__contains__('code'):
			return []

		symbols_list = []

		for pair in data['symbols']:
			if pair['status'] == 'TRADING':
				if symbols != None and pair['symbol'] in symbols:
					symbols_list.append(pair)

		return symbols_list

	def GetSymbolKlinesExtra(self, symbol:str, interval:str, limit:int=1000, end_time=False):
		# Basicall, we will be calling the GetSymbolKlines as many times as we need 
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
		df = self.GetSymbolKlines(symbol, interval, limit=initial_limit, end_time=end_time)
		while repeat_rounds > 0:
			# Then, for every other 1000 candles, we get them, but starting at the beginning
			# of the previously received candles.
			df2 = self.GetSymbolKlines(symbol, interval, limit=1000, end_time=df['time'][0])
			df = df2.append(df, ignore_index = True)
			repeat_rounds = repeat_rounds - 1
		
		return df

	def GetAccountData(self) -> dict:
		""" Gets Balances & Account Data """

		url = self.base + self.endpoints["account"]
		
		params = {
		'recvWindow': 6000,
		'timestamp': int(round(time.time()*1000)) + request_delay
		}
		self.signRequest(params)
		
		return self._get(url, params, self.headers)

	def Get24hrTicker(self, symbol:str):
		url = self.base + self.endpoints['24hrTicker'] + "?symbol="+symbol
		return self._get(url)

	def GetSymbolKlines(self, symbol:str, interval:str, limit:int=1000, end_time=False):
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
			return self.GetSymbolKlinesExtra(symbol, interval, limit, end_time)
		
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
	
	def PlaceOrderFromDict(self, params, test:bool=False):
		""" Places order from params dict """

		params['recvWindow'] = 5000
		params['timestamp'] = int(round(time.time()*1000)) + request_delay
		
		self.signRequest(params)
		url = ''
		if test: 
			url = self.base + self.endpoints['testOrder']
		else:
			url = self.base + self.endpoints['order']
		return self._post(url, params, self.headers)

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
			'timestamp': int(round(time.time()*1000)) + request_delay
		}

		if type != 'MARKET':
			params['timeInForce'] = 'GTC'
			params['price'] = Binance.floatToString(price)

		self.signRequest(params)

		url = ''
		if test: 
			url = self.base + self.endpoints['testOrder']
		else:
			url = self.base + self.endpoints['order']

		return self._post(url, params=params, headers=self.headers)

	def CancelOrder(self, symbol:str, orderId:str):
		'''
			Cancels the order on a symbol based on orderId
		'''

		params = {
			'symbol': symbol,
			'orderId' : orderId,
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000)) + request_delay
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
			'origClientOrderId' : orderId,
			'recvWindow': 5000,
			'timestamp': int(round(time.time()*1000)) + request_delay
		}

		self.signRequest(params)

		url = self.base + self.endpoints['order']

		return self._get(url, params=params, headers=self.headers)

	def GetAllOrderInfo(self, symbol:str):
		'''
			Gets info about all order on a symbol
		'''

		params = {
			'symbol': symbol,
			'timestamp': int(round(time.time()*1000)) + request_delay
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

	def signRequest(self, params:dict):
		''' Signs the request to the Binance API '''

		query_string = '&'.join(["{}={}".format(d, params[d]) for d in params])
		signature = hmac.new(self.binance_keys['secret_key'].encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
		params['signature'] = signature.hexdigest()
	
	@classmethod
	def floatToString(cls, f:float):
		''' Converts the given float to a string,
		without resorting to the scientific notation '''

		ctx = decimal.Context()
		ctx.prec = 12
		d1 = ctx.create_decimal(repr(f))
		return format(d1, 'f')

	@classmethod
	def get10Factor(cls, num):
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

	@classmethod
	def RoundToValidPrice(cls, symbol_data, desired_price, round_up:bool=False) -> Decimal:
		""" Returns the minimum quantity of a symbol we can buy,
		closest to desiredPrice """
		
		pr_filter = {}
		
		for fil in symbol_data["filters"]:
			if fil["filterType"] == "PRICE_FILTER":
				pr_filter = fil
				break
		
		if not pr_filter.keys().__contains__("tickSize"):
			raise Exception("Couldn't find tickSize or PRICE_FILTER in symbol_data.")
			return

		round_off_number = int(cls.get10Factor((float(pr_filter["tickSize"]))))

		number = round(Decimal(desired_price), round_off_number)
		if round_up:
			number = number + Decimal(pr_filter["tickSize"])

		return number

	@classmethod
	def RoundToValidQuantity(cls, symbol_data, desired_quantity, round_up:bool=False) -> Decimal:
		""" Returns the minimum quantity of a symbol we can buy,
		closest to desiredPrice """
		
		lot_filter = {}
		
		for fil in symbol_data["filters"]:
			if fil["filterType"] == "LOT_SIZE":
				lot_filter = fil
				break
		
		if not lot_filter.keys().__contains__("stepSize"):
			raise Exception("Couldn't find stepSize or PRICE_FILTER in symbol_data.")
			return

		round_off_number = int(cls.get10Factor((float(lot_filter["stepSize"]))))

		number = round(Decimal(desired_quantity), round_off_number)
		if round_up:
			number = number + Decimal(lot_filter["stepSize"])

		return number


def Main():

	symbol = 'NEOBTC'
	client_id = '73a40bae-61c7-11ea-8e67-f40f241d61b4'
	exchange = Binance('credentials.txt')

	d = exchange.GetOrderInfo(symbol, client_id)
	print(d)


if __name__ == '__main__':
	Main()
