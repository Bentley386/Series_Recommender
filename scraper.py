import time
import threading
import configparser
import re
import storage
import urllib

from urllib.request import urlopen
from bs4 import BeautifulSoup as soup

class Scraper():
    
    def __init__(self):
        print("Initializing")
        self.running = False
        self.config = configparser.ConfigParser()
        self.config.read("scraper.ini")
        self.interval = int(self.config['DEFAULT']['Interval'])
        self.usersURL = self.config['MyAnimeList']['Users']
        self.profileURL = self.config['MyAnimeList']['Profile']
        self.numProcessed = int(self.config['MyAnimeList']['Processed'])
        self.storage = storage.Storage()
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.scrape)
        self.thread.start()
        print("Enter any key to terminate...")
        input()
        self.stop()
        
    def stop(self):
        self.running = False
        self.thread.join()
        self.save()
        print("Crawling stopped.")

    def save(self):
        self.storage.saveJSON()
        self.config['MyAnimeList']['Processed'] = str(self.numProcessed)
        with open("scraper.ini","w") as f:
            self.config.write(f)
        
        
    def scrape(self):
        print("Starting to scrape")
        while self.running:
            self.save()
            page = self.numProcessed // 24
            client = urlopen(self.usersURL+str(page*24))
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
        try:
            client = urlopen(self.profileURL+user+"?status=7")
        except urllib.error.HTTPError as e:
            print(f"Error found while processing {user}: {e}")
            return
        
        page_soup = soup(client.read(),"lxml")
        info = page_soup.find_all("table",{"class":"list-table"})
        client.close()
        
        rawratings = []
        rawseries = []
        assert len(info)<2,f"Something weird happened with {user}"
            
        if len(info) == 1:
            info = info[0]["data-items"]
            rawratings = re.findall('"score":[0-9]+,"',info)
            rawratings = [x[8:-2] for x in rawratings]
            rawseries = re.findall('"anime_title":.+?,"anime_num',info)
            rawseries = [x[14:-11] for x in rawseries]
            if len(rawseries) == 300:
                page=300
                more = self.processDynamic(user,page)
                while len(more)>2:
                    rawratings = rawratings + [x[8:-2] for x in re.findall('"score":[0-9]+,"',more)]
                    rawseries = rawseries + [x[14:-11] for x in re.findall('"anime_title":.+?,"anime_num',more)]
                    page+=300
                    more = self.processDynamic(user,page)

            
        else:
            allowed = ["-","1","2","3","4","5","6","7","8","9","0","10"]
            rawseries = [x.span.text for x in page_soup.findAll("a",{"class":"animetitle"})]
            rawratings = page_soup.findAll("span",{"class":"score-label"})
            rawratings = [x.text if (x.text != '-') else '0' for x in rawratings if x.text in allowed]
         
        ratings = [rawratings[i] for i in range(len(rawratings)) if rawratings[i] != '0']
        series = [rawseries[i] for i in range(len(rawratings)) if rawratings[i] != '0']
        self.storage.updateObject(user,ratings,series)
    
    def processDynamic(self,user,num):
            client = urlopen(self.profileURL+user+"/load.json?offset=" + str(num) + "&status=7")
            return client.read().decode("utf-8")
        
if __name__ == "__main__":
    s = Scraper()
    s.start()