#! /usr/bin/python3
import requests


def get_sto_news():
    response = requests.get(
        'https://api.arcgames.com/v1.0/games/sto/news?tag=*&limit=10&offset=0&field[]=images.img_microsite_thumbnail&field[]=platforms',
        headers={'DNT' : '1'}).json()
    return response['news']
