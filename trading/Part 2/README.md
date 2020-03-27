# Algo Trading in Python
## Part 2: EXCHANGE INTERFACE & FINDING SIGNALS
###### Writing an interface allowing us to interact with Binance & checking all pairs for signals

This folder contains the source code for this [video](https://youtu.be/NTcZGzWBwAQ).

## Description

In this video we're building upon our original python program. 

We're creating a new class Binance.py, an interface for interacting with the [Binance API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md) (getting all trading symbols, getting data for a particular symbol, placing orders, cancelling orders and getting information about orders on our account).

Then we're updating the original TradingModel.py to use the newly created Binance class as a data source, and we're rewriting the original MA strategy and coding another strategy which uses the Bollinger Bands.

Finally, we're writing a loop that goes through all the symbols that are currently trading on Binance and see whether either of our strategies is being fulfilled, on any trading symbol, at this moment. If it does, we'll plot the chart of that trading pair/symnbol.

Note: We're not using some of the functions within the Binance interface in this video, in particular those that have anything to do with orders on our account. This video was more about expanding the code such that we can easily add new features to our trading bot. Placing of Orders on the account will come in the next video.

## Requirements

Create a [Binance Account](https://www.binance.com/?ref=10961872) (10% OFF for trading fees)

## Contact 

Do you have a strategy that you want to implement in an algorithm?
Send me an email: hello@tudorbarbulescu.com
