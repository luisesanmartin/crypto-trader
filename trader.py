import uuid
import sys
sys.path.insert(1, './utils')
import utils_fetch as fetch_utils
import utils_trade as trading_utils
import utils_data
from datetime import datetime
import time
import objects
import requests

def main():

	# Globals and variables
	symbols = objects.BITSTAMP_SYMBOLS
	amount = objects.AMOUNT
	fee_rate = objects.FEE_RATE
	buy_rate = objects.BUY_RATE
	sell_rate = objects.SELL_RATE
	cut_loss_rate = objects.CUT_LOSS_RATE
	periods = objects.PERIOD
	time_gap = objects.GAP_EPOCH
	max_errors = objects.MAX_CONTINUED_ERRORS
	max_loss = objects.MAX_CONTINUED_LOSS
	max_buy_order_open_periods = objects.MAX_BUY_ORDER_OPEN_PERIODS
	
	# Variables for tracking results
	hold = 0
	profits_total = 0
	periods_run = 0
	continued_errors = 0
	total_errors = 0
	continued_loss = 0
	buy_order_periods_open = 0

	# Others
	sender, to, key = trading_utils.email_credentials()

	while True:

		if continued_errors > max_errors:
			print("\nWe're getting to many errors. Going to sleep for now...")
			time.sleep(900)
			continued_errors = 0

		if continued_loss >= max_loss:
			line1 = f"\nWe've had {continued_loss} continued sells with loss"
			print(line1)
			line2 = "We're stopping code execution to prevent more losses"
			print(line2)
			subject = f'Trader bot - Stopping execution'
			message = f'{line1}\n{line2}'
			trading_utils.send_email(message, subject, sender, to, key)
			raise RuntimeError(line2)

		minutes, seconds = utils_data.minute_seconds_now()

		if (minutes+1) % (time_gap/60) == 0 and seconds == 3:
			time_now = utils_data.time_in_string(datetime.now())
			time_now_epoch = int(time.time()) - 30
			print(f"\nIt's {time_now}")
			
			# Trader in action
			if hold == 0:

				print('Currently not holding...')

				# Data
				try:
					data = fetch_utils.get_data_bitstamp_symbols_now(end=time_now_epoch)
					continued_errors = 0
				except Exception as e:
					print('Collecting the data failed...')
					print(e)
					continued_errors += 1
					total_errors += 1
					continue

				current_prices = data[0]
				past_prices = data[1]

				for symbol in past_prices.keys():

					current_price = current_prices[symbol]
					past_price = past_prices[symbol]
					
					if (buy_rate < 0 and current_price < past_price * (1+buy_rate)) or \
					   (buy_rate > 0 and current_price > past_price * (1+buy_rate)):

						print(f'Valley detected in {symbol}!')
						if symbol == 'pepeusd' or symbol == 'xdcusd':
							crypto_quantity = round(amount / current_price, 1)
						elif symbol == 'dotusd' or symbol == 'dogeusd':
							crypto_quantity = round(amount / current_price, 2)
						elif symbol == 'suiusd':
							crypto_quantity = round(amount / current_price, 4)
						elif symbol == 'solusd':
							crypto_quantity = round(amount / current_price, 5)
						else:
							crypto_quantity = round(amount / current_price, 8)
						client_order_id = str(uuid.uuid4())
						buy_order = trading_utils.bs_buy_limit_order(amount=crypto_quantity,
																 price=current_price,
																 market_symbol=symbol,
																 client_order_id=client_order_id)
						buy_order = buy_order.json()
						try:
							price_buy = float(buy_order['price'])
						except KeyError:
							print(buy_order)
							subject = 'Trader bot - Trader stopped'
							message = f'See buy order below:\n{buy_order}'
							trading_utils.send_email(message, subject, sender, to, key)
							raise KeyError
						amount_spent = float(crypto_quantity) * price_buy
						fee = amount_spent * fee_rate
						profits_total -= fee
						line1 = f'Sent a limit order to buy {crypto_quantity} for ${round(amount_spent, 2)}'
						print(line1)
						line2 = f'Purchase price: {price_buy}'
						print(line2)
						line3 = f'Client order ID: {client_order_id}'
						print(line3)
						hold = 1
						filled_buy_order = False
						subject = f'Trader bot - Valley detected for {symbol}'
						message = f'Valley detected!\n{line1}\n{line2}\n{line3}'
						#trading_utils.send_email(message, subject, sender, to, key)

						break

					else:
						print(f'No valley detected for {symbol}, not buying')
						pass
			
			elif hold == 1 and not filled_buy_order:

				print('Checking order status...')
				print(f'Client order ID: {client_order_id}')

				order_status = trading_utils.bs_check_order_status(client_order_id)
				order_status = order_status.json()
				status = order_status['status']

				if status == 'Finished':
					print('Buy order was filled!')
					filled_buy_order = True
				
				if status == 'Open' and buy_order_periods_open < max_buy_order_open_periods:
					print('Buy order is still open...')
					buy_order_periods_open += 1
					print(f"It's been open for {buy_order_periods_open} periods")
				
				if status == 'Open' and buy_order_periods_open >= max_buy_order_open_periods:
					print('Buy order has been open for too long. Cancelling order...')
					cancel_response = trading_utils.bs_cancel_order(client_order_id)
					print('Order canceled')
					buy_order_periods_open = 0
					hold = 0
	
			elif hold == 1 and filled_buy_order:
				print(f'Currently holding {symbol}...')

				# Data
				try:
					data = fetch_utils.get_data_bitstamp_symbols_now(symbols=[symbol])
					current_price = data[0][symbol]
					continued_errors = 0
				except Exception as e:
					print('Collecting the data failed...')
					print(e)
					continued_errors += 1
					total_errors += 1
					continue

				# We only sell if current price is higher than the
				# last buy price by the amount in "margin"
				price_with_margin = price_buy * (1 + sell_rate)
				take_profits = current_price > price_with_margin
				stop_loss = current_price < price_buy * (1+cut_loss_rate)
				
				if take_profits or stop_loss:

					sell_order = trading_utils.bs_sell_limit_order(amount=crypto_quantity,
																price=current_price,
																market_symbol=symbol)
					sell_order = sell_order.json()
					hold = 0
					try:
						amount_sold = float(crypto_quantity) * float(sell_order['price'])
					except KeyError:
						print(sell_order)
						subject = 'Trader bot - Sell order failed'
						message = f'See sell order below:\n{sell_order}'
						trading_utils.send_email(message, subject, sender, to, key)
						print('Sell order failed...')
						continue
					fee = amount_sold * fee_rate
					profits_total -= fee
					profits = amount_sold - amount_spent
					profits_total += profits
					amount = amount_sold
					line1 = 'Sent a limit order to sell '+str(crypto_quantity)+' for $'+str(round(amount_sold, 2))
					print(line1)
					line2 = 'Sell price: ${}'.format(sell_order['price'])
					print(line2)
					line3 = 'Profits with this operation (without fee): $'+str(round(profits, 2))
					print(line3)
					subject = f'Trader bot - Sell order for {symbol}'
					message = f'{line1}\n{line2}\n{line3}'
					trading_utils.send_email(message, subject, sender, to, key)

					if stop_loss:
						continued_loss += 1
					else:
						continued_loss = 0

				else:
					print('Price is not yet higher than the desired margin')
					print('Last purchase price: ${}'.format(price_buy))
					print('Price with margin: ${}'.format(price_with_margin))
					print(f'Current price: ${current_price}')

			# Accuracy tracking:
			periods_run += 1
			print('Total periods: {}'.format(periods_run))
			print(f'Total errors : {total_errors}')
			print('Total profits: $'+str(round(profits_total, 2)))
			time.sleep(time_gap-20)

		time.sleep(0.5)

if __name__ == '__main__':
	main()