#! /usr/bin/python3
import requests
import json
import re


def get_xiv_news_items():
    """Method to get the news the topics from lodestone
    :return: a list of news topics
    :rtype: list"""
    response = requests.get(
        'https://eu.lodestonenews.com/news/updates',
        headers={'DNT' : '1'}, params={'locale' : 'eu'}).text

    json_blob = json.loads(response)
    patch_note_notices = []
    for item in json_blob:
        if "FINAL FANTASY XIV Updated" in item['title']:
            patch_note_notices.append(item)

    return patch_note_notices


def get_xiv_patch_notes_links(news_items):
    """Method to parse the lodestone topics and only get the ones that contains patch notes
    :param news_items: The list of topics from lodestone
    :return: a list of links to patch notes
    :rtype: list"""
    patch_notes_links = []
    for item in news_items:
        response = requests.get(
            item['url'],
            headers={'DNT': '1'}, params={'locale': 'eu'}).text
        links = re.findall(r'(https?://[^\s]+)', response)
        for link in links:
            if "sqex.to" in link:
                # Since they have a lot of crap in the parsed result we need to clean it
                patch_notes_links.append(link[:21])
    return patch_notes_links


def make_patch_object(links):
    """Method to make a list of json objects with title (version of patch note) and url to it.
    :param links: The list of links to patch notes pages
    :return: list of dictionary with title and url to patch notes
    :rtype: list"""
    list_of_objects = []
    for link in links:
        response = requests.get(
            link,
            headers={'DNT': '1'}, params={'locale': 'eu'}).text
        title = response[response.find('<title>') + 7: response.find('</title>')]
        list_of_objects.append({'title' : title, 'url' : link})
    return list_of_objects


news_items = get_xiv_news_items()
patch_note_links = get_xiv_patch_notes_links(news_items)
print(make_patch_object(patch_note_links))