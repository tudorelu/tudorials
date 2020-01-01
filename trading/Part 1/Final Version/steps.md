## Tutorial Steps:

### Explain:

		Today we'll talk about Algorithmic Trading of crypto-currencies using Python!!

Using data from the Binance API, a technical analysis library for python called pyti for our trading strategies and Plot.ly to plot everything, we'll start creating a Binance trading bot. 

Note that the principles discussed here are also applicable to regular stocks.

Let's get started

#### CANDLESTICKS

The price of a stock/coin can simply be represented as a line, moving up and down as time goes by. If we take a portion of that line (that represents say 1 hour), we can see what the price was at the beginning and at the end of it. We can also see the highest and the lowest points that the price has reached during that period.

A candlestick is simply a visual representation of that information. If the candlestick is green, then during that period the price went up. If it's red, then it went down.

#### MOVING AVERAGES

In technical analysis, moving averages are used as a way to filter out the noise caused by fluctuations in the price of an asset. It is simply the mean of all prices of an asset (stock/coin) over a period of time.

For example, a 10 day moving average will add up the closing prices of a coin over the last 10 days and divide by 10.


#### What's a Candlestick 


##### (Showing an image of candlestick)
	- Holds information about the Open, High, Low and Close Price of a coin/stock over a time interval (1hr) 
	- Red means that Close is lower than Open (over the last interval we're going down)
	- Green means that Close is higher than Open (going up over last interval)

#### What are Moving Averages (MAs)
##### (Show image of chart with MAs)
	- Due to the fluctiations in price, it's hard to identif thends in the shorter term 
	- Moving averages aggregate the price of the coin/stock over a period of time to give us a smoother line
	- Combining moving average with price 

#### Potential strategy
	- Big difference between price and MA (over 4%)
	- MAs cross over + big change in price since last interval (over 4%) = buy or sell signal

### Code:

#### Binance
	- Show Documantation
	- Write Code
	- Use functions for TI

#### Plot.ly
 - Write code

#### Main
 - Run for 4 different pairs
