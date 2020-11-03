import json
import configparser

class Storage():
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("storage.ini")
        self.seriesFile = self.config["MyAnimeList"]["Series"]
        self.listsFile = self.config["MyAnimeList"]["Lists"]
        self.seriesObject = self.loadJSON(self.seriesFile)
        self.listsObject = self.loadJSON(self.listsFile)
        
    def loadJSON(self,file):
        with open(file,"r") as f:
            res = json.load(f)
        return res
        
    def updateObject(self,user,ratings,series):
        
        if len(ratings)==0 or len(ratings)!=len(series):
            print(f"The lengths for {user} are suspicious.")
            return
        field = {}
        for i in range(len(ratings)):
            if (series[i] in self.seriesObject):
                field[self.seriesObject[series[i]]] = ratings[i]
            else:
                self.seriesObject["HashNum"] += 1
                self.seriesObject[series[i]] = self.seriesObject["HashNum"]
                field[self.seriesObject["HashNum"]] =  ratings[i]
                
        self.listsObject[user] = field
    
    def saveJSON(self):
        with open(self.seriesFile,"w") as f:
            json.dump(self.seriesObject,f)

        with open(self.listsFile,"w") as f:
            json.dump(self.listsObject,f)
    
    
    