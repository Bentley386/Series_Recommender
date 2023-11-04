import time
import configparser
import re
import storage
import urllib

from urllib.request import urlopen
from bs4 import BeautifulSoup as soup

class Scraper():
    
    def __init__(self):
        print("Initializing")
        self.config = configparser.ConfigParser()
        self.config.read("scraper.ini")
        self.interval = int(self.config['DEFAULT']['Interval'])
        self.usersURL = self.config['MyAnimeList']['Users']
        self.profileURL = self.config['MyAnimeList']['Profile']
        self.numProcessed = int(self.config['MyAnimeList']['Processed'])
        self.storage = storage.Storage()
        
    def save(self):
        self.storage.saveJSON()
        self.config['MyAnimeList']['Processed'] = str(self.numProcessed)
        with open("scraper.ini","w") as f:
            self.config.write(f)
        
        
    def start(self):
        print("Starting to scrape")
        while True:
            self.save()
            page = self.numProcessed // 24
            print(page)
            try:
                client = urlopen(self.usersURL+str(page*24))
            except Exception as e:
                print(self.usersURL+str(page*24))
                raise e
            self.processUsers(soup(client.read(),"lxml"))
            client.close()
            time.sleep(self.interval)
        
    def processUsers(self,page_soup):
        print("Starting to scrape on a new page")
        while True:
            time.sleep(self.interval)
            users = page_soup.findAll("div",{"class":"picSurround"})
            user = users[self.numProcessed % 24].a["href"][9:]
            self.processUser(user)
            self.numProcessed +=1
            if self.numProcessed % 24 == 0:
                break

    def processUser(self,user):
        ratings = []
        series = []
        page = 0
        while True:
            rawratings,rawnames = self.processDynamic(user,page)
            if (len(rawratings) != len(rawnames)):
                print(f"Something went wrong with user {user}")
                break
            ratings = ratings + rawratings
            series = series + rawnames
            if len(rawratings)<300:
                break
            page+=300
        
        series = [series[i] for i in range(len(ratings)) if ratings[i] != '0']            
        ratings = [ratings[i] for i in range(len(ratings)) if ratings[i] != '0']
        self.storage.updateObject(user,ratings,series)
    
    def processDynamic(self,user,num):
        try:
            client = urlopen(self.profileURL+user+"/load.json?offset=" + str(num) + "&status=7")
            resultingText = client.read().decode("utf-8")
            time.sleep(self.interval)
            client.close()
            ratings = [x[8:-2] for x in re.findall('"score":[0-9]+,"',resultingText)]
            names = [x[15:-18] for x in re.findall('"anime_title":.+?,"anime_title_eng',resultingText)]
            return [ratings,names]
        except urllib.error.HTTPError as e:
            print(f"Error found while processing {user}: {e}")
            return [[],[]]
        
        
if __name__ == "__main__":
    s = Scraper()
    s.start()