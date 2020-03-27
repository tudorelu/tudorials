import time
from requests import exceptions 

from uuid import uuid1
from decimal import Decimal, getcontext
from yaspin import yaspin
from Binance import Binance

from multiprocessing.pool import ThreadPool as Pool
from functools import partial
from Database import BotDatabase

from TradingModel import TradingModel

from Strategies import *

class BotRunner:

	def __init__(self, sp, exchange, database):
		self.sp = sp
		self.exchange = exchange
		self.database = database
		self.update_balance = True
		self.ask_permission = True
		getcontext().prec = 33

	def EntryOrder(self, bot_params, strategy_function, pairs, symbol_data):
		sp = self.sp
		exchange = self.exchange
		database = self.database

		# get dataframe & check for signal
		symbol = symbol_data['symbol']
		df = exchange.GetSymbolKlines(symbol, bot_params['interval'])	
		buy = strategy_function(df, len(df['close'])-1)

		sp.text = "Checking signals on "+symbol
		# if signal, place buy order
		if buy is not False:
			i = len(df) - 1
			order_id = str(uuid1())
			# buy at 0.4% lower than current price
			q_qty = Decimal(bot_params['trade_allocation'])
			buy_price = exchange.RoundToValidPrice(
				symbol_data = symbol_data, 
				desired_price = Decimal(df['close'][i]) * Decimal(0.99))
			quantity = exchange.RoundToValidQuantity(
				symbol_data = symbol_data, 
				desired_quantity = q_qty / buy_price)
			
			order_params = dict(
				symbol = symbol,
				side = "BUY",
				type = "LIMIT",
				timeInForce = "GTC",
				price = format(buy_price, 'f'),
				quantity = format(quantity, 'f'),
				newClientOrderId = order_id)

			if self.ask_permission:

				model = TradingModel(symbol, bot_params['interval'])
				model.df = df
				model.plotData(buy_signals=[(df['time'][i], buy)], plot_title=symbol)

				sp.stop()
				print(order_params)
				print("Signal found on "+ symbol +", place order (y / n)?")
				permission = input()
				sp.start()
				if permission != 'y':
					return

			# buy from exchange
			order_result = self.PlaceOrder(order_params, bot_params['test_run'])

			if order_result is not False:
				# Save order
				self.update_balance = True
				db_order = self.OrderResultToDatabase(order_result, symbol_data, bot_params, True)
				database.SaveOrder(db_order)

				pairs[symbol]['is_active'] = False
				pairs[symbol]['current_order_id'] = order_id

				# Change pair state to inactive
				database.UpdatePair(
					bot=bot_params, 
					symbol=symbol, 
					pair=pairs[symbol]
				)

	def ExitOrder(self, bot_params, pairs, order:dict):
		# Check order has been filled, if it has, update order in database and then
		# place a new order at target price, OCO-type if we also have stop loss enabled
		sp = self.sp
		exchange = self.exchange
		database = self.database

		if order['is_closed']:
			return
		
		symbol = order['symbol']
		exchange_order_info = exchange.GetOrderInfo(symbol, order['id'])

		if not self.CheckRequestValue(exchange_order_info):
			return 

		pair = pairs[symbol]
		
		sp.text = "Looking for an Exit on "+symbol
		# update old order in database
		order['status'] = exchange_order_info['status']
		order['executed_quantity'] = Decimal(exchange_order_info['executedQty'])
		if exchange_order_info['status'] == exchange.ORDER_STATUS_FILLED:
			if order['is_entry_order']:
				# place the exit order
				order_id = str(uuid1())
				price = exchange.RoundToValidPrice(symbol_data = self.all_symbol_datas[symbol], desired_price = Decimal(order['take_profit_price']))
				quantity = exchange.RoundToValidQuantity(symbol_data = self.all_symbol_datas[symbol], desired_quantity = Decimal(order['executed_quantity']))
				order_params = dict(
					symbol = symbol,
					side = "SELL",
					type = "LIMIT",
					timeInForce = "GTC",
					price = format(price, 'f'),
					quantity = format(quantity, 'f'),
					newClientOrderId = order_id)

				if self.ask_permission:
					sp.stop()
					print("Exit found on "+ symbol)

					print("Entry Order ")
					print(exchange_order_info)
					print()
					print("Potential Exit Order ")
					print(order_params)
					print()
					print("Place exit order (y / n)?")

					permission = input()
				
					if permission != 'y':	
						return
					
				# buy from exchange
				order_result = self.PlaceOrder(order_params, bot_params['test_run'])

				if order_result is not False:

					self.update_balance = True
					
					# Save order
					db_order = self.OrderResultToDatabase(\
						order_result, None, bot_params, False, False, order['id'])
					database.SaveOrder(db_order)

					order['is_closed'] = True
					order['closing_order_id'] = order_id
					# Change pair state to inactive
					pair['is_active'] = False
					pair['current_order_id'] = order_id
			else:
				self.update_balance = True
				sp.stop()
				print("Succesfully exited order on "+ symbol +"!")
				print(order)
				print(exchange_order_info)
				sp.start()
				order['is_closed'] = True
				# order['closing_order_id'] = order['id']
				pair['is_active'] = True
				pair['current_order_id'] = None
				# pairs[symbol]['profit_loss'] = Decimal(pairs[symbol]['profit_loss']) * \
				# 	(Decimal(order['price']) / 

			pairs[symbol] = pair
			
			database.UpdatePair(
				bot=bot_params,
				symbol=symbol,
				pair=pair
			)

		database.UpdateOrder(order)

	def PlaceOrder(self, params, test):
		''' Places order on Pair based on params. Returns False if unsuccesful, 
		or the order_info received from the exchange if succesful '''
		sp = self.sp
		exchange = self.exchange

		order_info = exchange.PlaceOrderFromDict(params, test=test)
		# IF ORDER PLACING UNSUCCESFUL, CLOSE THIS POSITION
		sp.stop()
		if "code" in order_info:
			print("ERROR placing order !!!! ")
			print(params)
			print(order_info)
			print()
			sp.start()
			return False
		# IF ORDER SUCCESFUL, SET PAIR TO ACTIVE
		else:
			print("SUCCESS placing ORDER !!!!")
			print(params)
			print(order_info)
			print()
			sp.start()
			return order_info

	def CheckRequestValue(self, response, text='Error getting request from exchange!', print_response=True):
		""" Checks return value of request """
		sp = self.sp

		if "code" in response:
			sp.stop()
			print(text)
			if print_response:
				print(response)
				print()
			sp.start()
			return False
		else:
			return True

	def OrderResultToDatabase(self, order_result, symbol_data, bot_params, is_entry_order=False, is_closed=False, closing_order_id=False):
		
		sp = self.sp
		exchange = self.exchange

		order = dict()
		if symbol_data == None:
			symbol_data = exchange.GetSymbolDataOfSymbols([order_result['symbol']])
		order['id'] = order_result['clientOrderId']
		order['bot_id'] = bot_params['id']
		order['symbol'] = order_result['symbol']
		order['time'] = order_result['transactTime']
		order['price'] = order_result['price']
		order['take_profit_price'] = exchange.RoundToValidPrice(
			symbol_data = symbol_data,
			desired_price = Decimal(order_result['price']) * Decimal(bot_params['profit_target']), 
			round_up=True)
		order['original_quantity'] =  Decimal(order_result['origQty'])
		order['executed_quantity'] =  Decimal(order_result['executedQty'])
		order['status'] = order_result['status']
		order['side'] = order_result['side']
		order['is_entry_order'] = is_entry_order
		order['is_closed'] = is_closed
		order['closing_order_id'] = closing_order_id

		sp.stop()
		print("In db, order will be saved as ")
		print(order)
		sp.start()

		return order

	def CreateBot(self,
		name='Nin9_Bot', 
		strategy_name='ma_crossover', 
		interval='3m',
		trade_allocation=0.1, 
		profit_target=1.012, 
		test=False, 
		symbols=[]):

		sp = self.sp
		exchange = self.exchange
		database = self.database

		assert interval in exchange.KLINE_INTERVALS, interval+" is not a valid interval."
		assert trade_allocation > 0 and trade_allocation <= 1, "Trade allocation should be in (0, 1]"
		assert profit_target > 0, "Profit target should be above 0"

		symbol_datas = exchange.GetSymbolDataOfSymbols(symbols)
		symbol_datas_dict = dict()
		for sd in symbol_datas:
			symbol_datas_dict[sd['symbol']] = sd

		bot_id = str(uuid1())
		bot_params = dict(
			id = bot_id,
			name = name,
			strategy_name = strategy_name,
			interval = interval,
			trade_allocation = Decimal(trade_allocation), 
			profit_target = Decimal(profit_target),
			test_run = test
		)
		database.SaveBot(bot_params)
		
		pairs = []
		for symbol_data in symbol_datas:
			pair_id = str(uuid1())
			pair_params = dict(
				id = pair_id,
				bot_id = bot_id,
				symbol = symbol_data['symbol'],
				is_active = True,
				current_order_id = None,
				profit_loss = Decimal(1)
			)
			database.SavePair(pair_params)
			pairs.append(pair_params)

		bot_params['pairs'] = pairs

		return bot_params, symbol_datas_dict

	def GetBotFromDb(self, id):
		""" Returns a Bot from the DB given an ID """

		sp = self.sp
		exchange = self.exchange
		database = self.database

		bot = database.GetBot(id)
		pairs = database.GetAllPairsOfBot(bot)

		symbols = []
		for pair in pairs:
			symbols.append(pair['symbol'])

		symbol_datas = exchange.GetSymbolDataOfSymbols(symbols)
		
		symbol_datas_dict = dict()
		for sd in symbol_datas:
			symbol_datas_dict[sd['symbol']] = sd

		return bot, symbol_datas_dict

	def GetAllBotsFromDb(self):
		""" Returns all Bots from the DB """
		
		sp = self.sp
		exchange = self.exchange
		database = self.database

		bot_sds = []
		bots = database.GetAllBots()
		for bot in bots:
			pairs = database.GetAllPairsOfBot(bot)

			symbols = []
			for pair in pairs:
				symbols.append(pair['symbol'])

			symbol_datas = exchange.GetSymbolDataOfSymbols(symbols)
			
			symbol_datas_dict = dict()
			for sd in symbol_datas:
				symbol_datas_dict[sd['symbol']] = sd

			bot_sds.append((bot, symbol_datas_dict))

		return bot_sds

	def GetBalances(self, bots):
		""" Get Balances of all Assets From Exchange """
		exchange = self.exchange
		account_data = exchange.GetAccountData()
		requested_times = 0
		while not self.CheckRequestValue(account_data, text="\nError getting account balance, retrying..."):
			requested_times = requested_times + 1
			time.sleep(1)
			account_data = exchange.GetAccountData()
			if requested_times > 15:
				self.sp.stop()
				print("\nCan't get balance from exchange, tried more than 15 times.\n", "Stopping.\n")
				return False, False, False

		balances_text = "BALANCES \n"
		buy_on_bot = dict()
		quote_assets = []
		for bot, symbol_datas_dict in bots:
			for sd in symbol_datas_dict.values():
				if sd['quoteAsset'] not in quote_assets:
					quote_assets.append(sd['quoteAsset'])

			for bal in account_data['balances']:
				if bal['asset'] in quote_assets:
					balances_text = balances_text + " | " + bal['asset'] + ": " + str(round(Decimal(bal['free']), 5))
					if Decimal(bal['free']) > Decimal(bot['trade_allocation']):
						buy_on_bot[bal['asset']] = dict(buy = True, balance = Decimal(bal['free']))
					else:
						buy_on_bot[bal['asset']] = dict(buy = False, balance = Decimal(bal['free']))
		
		return account_data, balances_text+"\n", buy_on_bot

	def StartExecution(self, bots):
		exchange = self.exchange
		database = self.database

		if len(bots) == 0:
			self.sp.text = "No bots available, exiting..."
			return

		self.sp.text = "Getting balances of all bots..."
		account_data, balances_text, buy_on_bot = self.GetBalances(bots)

		self.all_symbol_datas = dict()

		for bot, sd in bots:
			pairs = database.GetAllPairsOfBot(bot)
			for pair in pairs:
				self.all_symbol_datas[pair['symbol']] = sd[pair['symbol']]

		while True:
			with yaspin() as sp:
				self.sp = sp
				try:
					# Get All Pairs
					aps = [] 
					for bot, sd in bots:
						aps.extend(database.GetAllPairsOfBot(bot))
					all_pairs = dict()
					for pair in aps:
						all_pairs[pair['symbol']] = pair

					# Only request balances if order was placed recently
					if self.update_balance:
						account_data, balances_text, buy_on_bot = self.GetBalances(bots)
						if account_data is False:
							return
						sp.stop()
						print(balances_text)
						sp.start()
						self.update_balance = False
					
					# Find Signals on Bots
					for bot, symbol_datas_dict in bots:

						# Get Active Pairs per Bot
						ap_symbol_datas = []
						aps = database.GetActivePairsOfBot(bot)	
						pairs = dict()
						for pair in aps:
							if symbol_datas_dict.get(pair['symbol'], None) == None:
								sp.text = "Couldn't find " + pair['symbol'] + " looking for it later..."
							else:
								ap_symbol_datas.append(symbol_datas_dict[pair['symbol']])
								pairs[pair['symbol']] = pair

						# If Enough Balance on bot, try finding signals
						try:
							self.Run(bot, strategies_dict[bot['strategy_name']], pairs, ap_symbol_datas)
						except exceptions.SSLError:
							sp.text = "SSL Error caught!"
						except exceptions.ConnectionError:
							sp.text = "Having trouble connecting... retry"
					
						open_orders = database.GetOpenOrdersOfBot(bot)

						# If we have open orders saved in the DB, see if they exited
						if len(open_orders) > 0:
							sp.text = (str(len(open_orders)) + " orders open on " + bot['name'] + ", looking to close.")
							try:
								self.Exit(bot, all_pairs, open_orders)
							except exceptions.SSLError:
								sp.text = "SSL Error caught!"
							except exceptions.ConnectionError:
								sp.text = "Having trouble connecting... retry"
						else:
							sp.text = "No orders open on "+ bot['name']

				except KeyboardInterrupt:
					sp.stop()
					print("\nExiting...\n")
					return

	def Run(self, bot_params, strategy_function, pairs, symbol_datas):
		sp = self.sp
		exchange = self.exchange
		database = self.database

		pool = Pool(4)
		func1 = partial(self.EntryOrder, bot_params, strategy_function, pairs)
		pool.map(func1, symbol_datas)
		pool.close()
		pool.join()

	def Exit(self, bot_params, pairs, orders):
		sp = self.sp
		exchange = self.exchange
		database = self.database

		pool = Pool(4)
		func1 = partial(self.ExitOrder, bot_params, pairs)
		pool.map(func1, orders)
		pool.close()
		pool.join()

def Main():

	sp = yaspin()
	exchange = Binance(filename = 'credentials.txt')
	database = BotDatabase("database.db")
	prog = BotRunner(sp, exchange, database)

	i = input("Execute or Quit? (e or q)\n")
	bot_symbol_datas = []
	while i not in ['q']:
		if i == 'e':
			i = input("Create a new bot? (y or n)\n")
			if i == 'y':

				symbols = ['ETHBTC', 'NEOBTC', 'EOSETH', 'BNBETH', 'BTCUSDT', \
				'ETHUSDT', 'WTCBTC', 'KNCETH', 'IOTABTC', 'LINKBTC', 'ENGBTC', \
				'DNTBTC', 'BTGBTC', 'XRPBTC', 'ENJBTC', 'BNBUSDT', 'XMRBTC', 'BATBTC', \
				'NEOUSDT', 'LTCUSDT', 'WAVESBTC', 'IOSTBTC', 'QTUMUSDT', 'XEMBTC', \
				'ADAUSDT', 'XRPUSDT', 'EOSUSDT', 'THETABTC', 'IOTAUSDT', 'XLMUSDT', \
				'ONTUSDT', 'TRXUSDT', 'ETCUSDT', 'ICXUSDT', 'VETUSDT', 'POLYBTC', \
				'LINKUSDT', 'WAVESUSDT', 'BTTUSDT', 'FETBTC', 'BATUSDT', 'XMRUSDT', \
				'IOSTUSDT', 'MATICBTC', 'ATOMUSDT', 'ALGOBTC', 'ALGOUSDT', 'DUSKBTC', \
				'TOMOBTC', 'XTZBTC', 'HBARBTC', 'HBARUSDT', 'FTTBTC', 'FTTUSDT', \
				'OGNBTC', 'OGNUSDT', 'BEARUSDT', 'ETHBULLUSDT', 'ETHBEARUSDT', \
				'WRXBTC', 'WRXUSDT', 'LTOBTC', 'EOSBEARUSDT', 'XRPBULLUSDT', \
				'XRPBEARUSDT', 'AIONUSDT', 'COTIBTC']
				
				bot, symbol_datas_dict = prog.CreateBot(
					strategy_name='ma_crossover',
					trade_allocation=0.001, 
					symbols=symbols)
				bot_symbol_datas.append((bot, symbol_datas_dict))

			else:
				bot_symbol_datas = prog.GetAllBotsFromDb()

			prog.StartExecution(bot_symbol_datas)
		
		i = input("Execute or Quit? (e or q)")
		
if __name__ == "__main__":
	Main()
