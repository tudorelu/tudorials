import sqlite3
from decimal import Decimal

def adapt_decimal(d):
	return format(round(d, 14), 'f')

def convert_decimal(s):
	return Decimal(s)

class BotDatabase:

	def __init__(self, name:str):
		
		sqlite3.register_adapter(Decimal, adapt_decimal)
		sqlite3.register_converter("decimal", convert_decimal)
		self.name = name
		self.Initialise()
		
	def Initialise(self):
		''' Initialises the Database ''' 

		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		# Create tables
		c.execute('''CREATE TABLE IF NOT EXISTS bots (
			id text primary key, 
			name text, 
			strategy_name text, 
			interval text,  
			trade_allocation text, 
			profit_target text,
			test_run bool
			)''')

		c.execute('''CREATE TABLE IF NOT EXISTS pairs (
			id text primary key, 
			bot_id text, 
			symbol text, 
			is_active bool, 
			current_order_id text, 
			profit_loss text,
			FOREIGN KEY(current_order_id) REFERENCES orders(id),
    	FOREIGN KEY(bot_id) REFERENCES bots(id)
			)''')
		
		c.execute('''CREATE TABLE IF NOT EXISTS orders (
			id text primary key,
			bot_id text,
			symbol text,
			time text,
			price text,
			take_profit_price text,
			original_quantity text,
			executed_quantity text,
			status text,
			side text,
			is_entry_order bool, 
			is_closed bool, 
			closing_order_id text,
			FOREIGN KEY(bot_id) REFERENCES bots(id),
			FOREIGN KEY(closing_order_id) REFERENCES orders(id)
			)''')

		conn.commit()

	def SaveBot(self, bot):
		'''
		Adds a Bot to the Database

			id text primary key, 
			name text, 
			strategy_id text, 
			interval text, 
			order_type text, 
			trade_allocation text, 
			profit_target text, 
			test_run bool
		'''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		values = (
			bot['id'], 
			bot['name'], 
			bot['strategy_name'],
			bot['interval'], 
			bot['trade_allocation'],
			bot['profit_target'],
			bot['test_run'])
		c.execute('INSERT INTO bots VALUES (?, ?, ?, ?, ?, ?, ?)', values)
		conn.commit()
	
	def GetBot(self, id:str):
		''' Gets Bot details from Database '''

		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM bots WHERE id = ?', (id, ))
		details = c.fetchone()
		return details

	def GetAllBots(self):
		''' Gets Bot details from Database '''

		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM bots')
		details = c.fetchall()
		return details

	def UpdateBot(self, bot):
		''' Updates a Bot within the Database '''

		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()

		c.execute('Update bots ' + \
			'Set ' + \
			'name = ' + bot['name'] + ', ' + \
			'profit_target = ' + bot['profit_target'] + ', ' + \
			'Where id = ' + bot['id'])
		conn.commit()

	def SaveOrder(self, order):
		'''
		Saves an Order to the Database
		'''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		values = (
			order['id'],
			order['bot_id'],
			order['symbol'],
			order['time'],
			order['price'],
			order['take_profit_price'],
			order['original_quantity'],
			order['executed_quantity'],
			order['status'],
			order['side'],
			order['is_entry_order'],
			order['is_closed'],
			order['closing_order_id']
		)
		c.execute('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
		conn.commit()
	
	def GetOrder(self, id:str):
		''' Gets Bot details from Database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM orders WHERE id=?', (id, ))
		result = dict(c.fetchone())
		return result

	def UpdateOrder(self, order):
		''' Updates a Bot within the Database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()

		values = (
			order['take_profit_price'], 
			order['executed_quantity'],
			order['status'],
			order['is_closed'],
			order['closing_order_id'],
			order['id'])

		c.execute('Update orders ' + \
			'Set ' + \
			'take_profit_price = ?, '+ \
			'executed_quantity = ?, status = ?, ' + \
			'is_closed = ?, closing_order_id = ? ' + \
			'Where id = ?', values)
		conn.commit()

	def SavePair(self, pair):
		'''
		Saves a Pair to the Database
			id text primary key, 
			bot_id text, 
			symbol text, 
			is_active bool, 
			current_order_id text, 
			profit_loss text,
			FOREIGN KEY(current_order_id) REFERENCES orders(id),
    	FOREIGN KEY(bot_id) REFERENCES bots(id)
		'''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		values = (
			pair['id'],
			pair['bot_id'],
			pair['symbol'],
			pair['is_active'],
			pair['current_order_id'],
			pair['profit_loss'],
		)
		c.execute('INSERT INTO pairs VALUES (?, ?, ?, ?, ?, ?)', values)
		conn.commit()
	
	def GetPair(self, id:str):
		''' Gets Bot details from Database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM pairs WHERE id=?', (id, ))
		result = dict(c.fetchone())
		return result
	
	def UpdatePair(self, bot, symbol, pair):
		''' Updates a Bot within the Database '''
		values = 	(
			pair['is_active'], 
			pair['current_order_id'],
			pair['profit_loss'],
			symbol, 
			bot['id'])
			
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute("UPDATE pairs " + \
			"SET is_active = ?, current_order_id = ?, profit_loss = ? "+ \
			"WHERE symbol = ? and bot_id = ? ", values)
		conn.commit()

	def GetOpenOrdersOfBot(self, bot):
		''' Gets all the bots within a database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM orders Where bot_id = ? and closing_order_id = 0 and is_closed = False', (bot['id'],))
		
		orders = []
		result = [dict(row) for row in c.fetchall()]
		return result
		
	def GetActivePairsOfBot(self, bot):
		''' Gets all the bots within a database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM pairs Where bot_id = ? and is_active = True', (bot['id'],))
		result = [dict(row) for row in c.fetchall()]
		return result

	def GetAllPairsOfBot(self, bot):
		''' Gets all the bots within a database '''
		conn = sqlite3.connect(self.name, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT * FROM pairs Where bot_id = ?', (bot['id'],))
		result = [dict(row) for row in c.fetchall()]
		return result
