# Algo Trading in Python
## Part 5: KEEP THE BOT RUNNING 
###### State persistance & Order management

This folder contains the source code for this [video](https://youtu.be/Cr7nQYl3iH8).

## Description

In this videos we are enabling the bot to run in the background and make trades without our intervention. We are updating Binance.py, creating a database that will hold information about the bot, its pairs and the orders it placed, adding a simple MA crossover strategy and adding the code that will keep the bot running in the background, checking all the pairs and placing entry orders if it identifies signals but also placing exit orders after those entry orders have been fulfilled.

## Requirements

Create a [Binance Account](https://www.binance.com/?ref=10961872)

#### Software Requirements

Same requirements as in the previous videos plus

``` pip install sqlite3 ``` for the database
``` pip install yaspin ``` yaspin for the loading animation & printing command line messages 

