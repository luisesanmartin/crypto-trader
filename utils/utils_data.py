import objects
from datetime import datetime

def make_data_dic_bitstamp(data):

    '''
    Transforms the JSON datasets to a dictionary
    with period as key and symbol as second-level key
    '''

    times = [obs['timestamp'] for obs in data[objects.BITSTAMP_SYMBOLS[-1]]]
    symbols = objects.BITSTAMP_SYMBOLS

    data_dic = {}

    for i, time in enumerate(times):

        data_dic[int(time)] = {symbol: data[symbol][i] for symbol in symbols if time == data[symbol][i]['timestamp']}

    return data_dic

def past_price_symbol_periods(data_dic, symbol, periods, time, gap_epoch=objects.GAP_EPOCH):

    '''
    Returns the price of the symbol n "periods" before "time"
    '''

    past_time = time - (gap_epoch * periods)
    past_price = float(data_dic[past_time][symbol]['close'])

    return past_price

def avg_price_symbol_periods(data_dic, symbol, periods, time, gap_epoch=objects.GAP_EPOCH):

    '''
    Returns the average price of the symbol for the last n "periods" previous to "time"
    '''

    prices = []
    for i in range(1, periods+1):

        time_iteration = time - (gap_epoch * i)
        prices.append(float(data_dic[time_iteration][symbol]['close']))

    return sum(prices) / len(prices)

def time_in_string(time):

    '''
    Transforms a datetime to a time string
    '''

    isoformat = time.isoformat()

    if '.' in isoformat:
        return isoformat[:-7].split('.')[0]

    else:
        return isoformat
    
def minute_seconds_now():

    '''
    returns the miuntes and seconds of the current time
    '''

    now = datetime.now()

    return now.minute, now.second