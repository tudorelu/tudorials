# Automatic trading signals using python
This folder contains the source code for this [video](COMING SOON).

## Description
In this programming video we're writing a python program that gets price data (of coins, but works wth stocks too), computes some technical indicators (moving average), plots it. TradingModel.py does all of this plus has a strategy that allows you to automatically buy the coin whenever the difference between the price and a moving average is more than 3% - which is also backtested.

Using the [binance API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md), we'll download the data.
Using the [pyti library](https://pypi.org/project/pyti/) we'll calculate two moving averages for the price 
and using [plotly](https://plot.ly/python/getting-started/) we'll display the data in a nice candlestick plot. 

At the end, we'll test our program in a funky little demo.

## Requirements

#### Software
Have [python 3](https://www.python.org/downloads/) and [pip](https://stackoverflow.com/a/6587528/4468246) installed. 

Install [pyti](https://pypi.org/project/pyti/).
``` pip install pyti ```

Install [plotly](https://plot.ly/python/getting-started/).
``` pip install plotly ```

## Documentation
[Binance API](https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md)

[pyti](https://pypi.org/project/pyti/)

[pyplot](https://plot.ly/python/getting-started/)

## Credits

##### Music

Intro & Outro: Kalimba - Ninja we Ninja

Bob Marley - Sun is Shining

Shlohmo - Ghosts, part 2