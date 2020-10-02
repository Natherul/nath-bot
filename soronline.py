import requests
import json

url = 'https://www.soronline.us/api/get.php'
myobj = {'api': 'ee6bd4a1-6e0b-475b-a4b0-4e18d4a66cb5'}

def scrape():
    x = requests.post(url, data = myobj).json()
    data = json.loads(x[0]['data'])
    
    openzones = []
    
    if "keeps" in data:
        for keep in data['keeps']:
            openzones.append(keep['name'])
    
    if "forts" in data:
        for fort in data['forts']:
            openzones.append(fort['name'])
    
    if "cities" in data:
        for city in data['cities']:
            openzones.append(city['name'])

    if "servmsg" in data:
        openzones.append(data['servmsg'])

    string = str(openzones)
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.replace("'", "")
    f = open("result.txt", "w")
    f.write(string)
    f.close()
    return string
