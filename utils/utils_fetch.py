import objects
import json
import requests
import utils_data

def get_api_key(text='API/key.txt'):

    with open(text) as file:
        key = file.read()

    return key

def get_data_bitstamp_symbols_now(
    step = objects.GAP_EPOCH,
    symbols = objects.BITSTAMP_SYMBOLS,
    limit = objects.PERIOD+1
    ):

    '''
    Return a dictionary with the current prices and average prices
    for the last limit-1 periods for all symbols
    '''

    all_data = {symbol: get_data_bitstamp(step=step, crypto_symbol=symbol, limit=limit) for symbol in symbols}
    data_dic = utils_data.make_data_dic_bitstamp(all_data)
    try:
        time = list(data_dic.keys())[-1]
    except IndexError as e:
        print(data_dic)
        raise e

    current_prices = {symbol: float(data_dic[time][symbol]['close']) for symbol in symbols}
    #avg_prices = {symbol: utils_data.avg_price_symbol_periods(data_dic, symbol, limit-1, time) for symbol in symbols}
    past_prices = {symbol: utils_data.past_price_symbol_periods(data_dic, symbol, limit-1, time) for symbol in symbols}

    return current_prices, past_prices

def get_data_bitstamp(
    step,
    crypto_symbol,
    start = None,
    limit = objects.PERIOD+1):

    '''
    gets OLHC data from Bitstamp
    '''

    request_url = objects.URL_BITSTAMP.format(crypto_symbol)
    parameters = {
        'step': step,
        'limit': limit
        }
    if start:
        parameters['start'] = start

    response = requests.get(request_url, params=parameters)
    data = json.loads(response.text)['data']['ohlc']

    return data