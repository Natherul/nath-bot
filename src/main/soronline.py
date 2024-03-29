import requests
import json

url = 'https://www.soronline.us/api/get.php'
myobj = {'api': 'ee6bd4a1-6e0b-475b-a4b0-4e18d4a66cb5'}


def scrape():
    """DEPRECATED! Scrapes the soronline API for updates
    :return: dictionary of open zones
    :rtype: dict"""
    x = requests.post(url, data = myob, timeout=10).json()
    data = json.loads(x[0]['data'])
    
    openzones = {}
    should_write = False
    string = ""
    
    if "keeps" in data:
        should_write = True
        for keep in data['keeps']:
            openzones[keep['pname']] = keep['name']
    
    if "forts" in data:
        should_write = True
        for fort in data['forts']:
            openzones[fort['pname']] = fort['name']
    
    if "cities" in data:
        should_write = True
        for city in data['cities']:
            openzones['City'] = city['name']

    if "servmsg" in data:
        openzones['Server'] = data['servmsg']

    # early city detection
    if "zonelocks" in data:
        destrocount = 0
        ordercount = 0
        for lock in data['zonelocks']:
            openzones[lock['name']] = "Locked by " + lock['owner']
            if lock['owner'] == "Destruction":
                destrocount = destrocount + 1
            elif lock['owner'] == "Order":
                ordercount = ordercount + 1
        if destrocount > 1 and "Altdorf" not in openzones:
            openzones['City'] = "Altdorf"
            should_write = True
        elif ordercount > 1 and "Inevitable City" not in openzones:
            openzones['City'] = "Inevitable City"
            should_write = True

    if len(openzones) > 0:
        string = str(openzones)
    if should_write == True:
        f = open("result.txt", "w")
        f.write(string)
        f.close()
    return openzones
