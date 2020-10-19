import requests
import json

url = 'https://www.soronline.us/api/get.php'
myobj = {'api': 'ee6bd4a1-6e0b-475b-a4b0-4e18d4a66cb5'}

def scrape():
    x = requests.post(url, data = myobj).json()
    data = json.loads(x[0]['data'])
    
    openzones = []
    shouldWrite = False
    
    if "keeps" in data:
        shouldWrite = True
        for keep in data['keeps']:
            openzones.append(keep['name'])
    
    if "forts" in data:
        shouldWrite = True
        for fort in data['forts']:
            openzones.append(fort['name'])
    
    if "cities" in data:
        shouldWrite = True
        for city in data['cities']:
            openzones.append(city['name'])

    if "servmsg" in data:
        openzones.append(data['servmsg'])

    string = str(openzones)
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.replace("'", "")
    if shouldWrite == True:
        f = open("result.txt", "w")
        f.write(string)
        f.close()
    return string
