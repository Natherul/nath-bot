import requests
import json

url = 'https://www.soronline.us/api/get.php'
myobj = {'api': 'ee6bd4a1-6e0b-475b-a4b0-4e18d4a66cb5'}

def scrape():
    x = requests.post(url, data = myobj).json()
    data = json.loads(x[0]['data'])
    
    openzones = {}
    shouldWrite = False
    string = ""
    
    if "keeps" in data:
        shouldWrite = True
        for keep in data['keeps']:
            openzones[keep['pname']] = keep['name']
    
    if "forts" in data:
        shouldWrite = True
        for fort in data['forts']:
            openzones[fort['pname']] = fort['name']
    
    if "cities" in data:
        shouldWrite = True
        for city in data['cities']:
            openzones['City'] = city['name']

    if "servmsg" in data:
        openzones['Server'] = data['servmsg']

    #early city detection
    if "zonelocks" in data:
        destrocount = 0
        ordercount = 0
        for lock in data['zonelocks']:
            if lock['owner'] == "Destruction":
                destrocount = destrocount + 1
            elif lock['owner'] == "Order":
                ordercount = ordercount + 1
        if destrocount > 1 and "Altdorf" not in openzones:
            openzones['City'] = "Altdorf"
            shouldWrite = True
        elif ordercount > 1 and "Inevitable City" not in openzones:
            openzones['City'] = "Inevitable City"
            shouldWrite = True

    if len(openzones) > 0:
        string = str(openzones)
    if shouldWrite == True:
        f = open("result.txt", "w")
        f.write(string)
        f.close()
    return openzones
