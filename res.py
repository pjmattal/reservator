import requests
import datetime
import time
import csv
import configparser
import json

headers = {
    'authorization': 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
}


def login(config):
    data = {
        'email': config['username'],
        'password': config['password']
    }
    response = requests.post('https://api.resy.com/3/auth/password',
                             headers=headers, data=data)
    res_data = response.json()
    config['auth_token'] = res_data['token']
    config['payment_method_id'] = str(res_data['payment_method_id'])


def find_table(config):
    # convert datetime to string
    params = (
        ('x-resy-auth-token', config['auth_token']),
        ('day', config['date']),
        ('lat', '0'),
        ('long', '0'),
        ('party_size', config['guests']),
        ('venue_id', config['venue_id']),
    )
    response = requests.get('https://api.resy.com/4/find', headers=headers,
                            params=params)
    data = response.json()
    results = data['results']
    if len(results['venues']) > 0:
        open_slots = results['venues'][0]['slots']
        if len(open_slots) > 0:
            available_times = [(k['date']['start'],
                                datetime.datetime.strptime(k['date']['start'],
                                                           "%Y-%m-%d %H:%M:00").hour)
                               for k in open_slots]
            closest_time = \
            min(available_times, key=lambda x: abs(x[1] - config.getint('time')))[0]

            best_table = \
            [k for k in open_slots if k['date']['start'] == closest_time][0]

            return best_table


def make_reservation(config):
    # convert datetime to string
    params = (
        ('x-resy-auth-token', config['auth_token']),
        ('config_id', config['config_id']),
        ('day', config['date']),
        ('party_size', config['guests']),
    )
    details_request = requests.get('https://api.resy.com/3/details',
                                   headers=headers, params=params)
    details = details_request.json()
    book_token = details['book_token']['value']
    headers['x-resy-auth-token'] = config['auth_token']
    data = {
        'book_token': book_token,
        'source_id': 'resy.com-venue-details'
    }

    response = requests.post('https://api.resy.com/3/book', headers=headers,
                             data=data).json()
    print(response)
    if 'reservation_id' in response:
        print(f'reservation {response["reservation_id"]} made at {datetime.datetime.now()}')
        return True
    else:
        print(f'failed to make reservation: {response}')
        return False


def try_table(config):
    best_table = find_table(config)
    if best_table is not None:
        hour = datetime.datetime.strptime(best_table['date']['start'],
                                          "%Y-%m-%d %H:%M:00").hour
        if hour == config.getint('time'):
            config['config_id'] = best_table['config']['token']
            if make_reservation(config):
                return True
    return False


if __name__ == '__main__':
    cp = configparser.ConfigParser()
    cp.read('requests.config')
    config = cp['reservator']

    with open('venues.json') as f:
        venues = json.load(f)

    login(config)
    config['venue_id'] = str(venues[config['venue']])

    reserved = False
    while reserved == False:
        try:
            reserved = try_table(config)
            if not reserved:
                time.sleep(60 * 15)
        except KeyboardInterrupt:
            exit(-1)
        except Exception as e:
            # raise(e)
            print(f'Exeception {e}')
