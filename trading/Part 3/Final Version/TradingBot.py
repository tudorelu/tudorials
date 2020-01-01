from StrategyEvaluator import StrategyEvaluator
from Strategies import Strategies

from Binance import Binance
from TradingModel import TradingModel

import json

from decimal import Decimal, getcontext

def BacktestStrategies(symbols=[], interval='4h', plot=False):

	trade_value = Decimal(100)

	strategy_evaluators = [
		StrategyEvaluator( strategy_function=Strategies.bollStrategy, strategy_settings={'indicators':['low_boll']}),
		StrategyEvaluator( strategy_function=Strategies.maStrategy, strategy_settings={'indicators':['slow_sma']})
	]

	coins_tested = 0

	for symbol in symbols:

		print(symbol)

		model = TradingModel(symbol=symbol, timeframe=interval)

		for evaluator in strategy_evaluators:
			resulting_balance = evaluator.backtest(
				model,
				starting_balance=trade_value
			)

			if resulting_balance != trade_value:
				print(evaluator.strategy.__name__ 
				+ ": starting balance: " + str(trade_value)
				+ ": resulting balance: " + str(round(resulting_balance, 2)))

				if plot:
					model.plotData(
						buy_signals = evaluator.results[model.symbol]['buy_times'],
						sell_signals = evaluator.results[model.symbol]['sell_times'],
						plot_title = evaluator.strategy.__name__+" on "+model.symbol,
						indicators = evaluator.settings['indicators'])
					
				evaluator.profits_list.append(resulting_balance - trade_value)
				evaluator.updateResult(trade_value, resulting_balance)
			
			coins_tested = coins_tested + 1

	for evaluator in strategy_evaluators:
		print("")
		evaluator.printResults()
	
def Main():
	exchange = Binance()
	symbols = exchange.GetTradingSymbols(quoteAssets=["BTC", "USDT"])

	BacktestStrategies(symbols=symbols, interval='5m', plot=True)

if __name__ == '__main__':
	Main()
