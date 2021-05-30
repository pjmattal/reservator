import requests
import datetime
import time
import csv
import configparser
import json
headers = {
    'authorization': 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
    'content-type': 'application/x-www-form-urlencoded',
}


def login(username, password):
    data = {
        'email': username,
        'password': password
    }

    response = requests.post('https://api.resy.com/3/auth/password',
                             headers=headers, data=data)
    d = response.json()
    return d['token']


def fetch_json(token, lat, long):
    params = (
        ('x-resy-auth-token', token),
        ('day', datetime.date.today().strftime('%Y-%m-%d')),
        ('lat', lat),
        ('long', long),
        ('party_size', '2'),
    )
    response = requests.get('https://api.resy.com/4/find', headers=headers,
                            params=params)
    data = response.json()
    results = data['results']
    venues = { v['venue']['name']: v['venue']['id']['resy'] for v in results['venues'] }
    with open('venues.json', 'w') as f:
        json.dump(venues, f, indent=4)


if __name__ == '__main__':
    cp = configparser.ConfigParser()
    cp.read('requests.config')
    config = cp['reservator']

    config['token'] = login(config['username'], config['password'])
    fetch_json(config['token'], config['lat'], config['long'])