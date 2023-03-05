#! /usr/bin/python3
import requests


def get_sto_news():
    """Method to get the news from arc"""
    response = requests.get(
        'https://api.arcgames.com/v1.0/games/sto/news?tag=*&limit=10&offset=0&field[]=images.img_microsite_thumbnail&field[]=platforms&platform=pc',
        headers={'DNT' : '1'}).json()['news']
    for news_entry in response:
        article_link = 'https://www.playstartrekonline.com/en/news/article/' + str(news_entry['id'])
        news_entry['article_link'] = article_link

    return response
