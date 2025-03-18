import pandas as pd
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from langdetect import detect, DetectorFactory
from datetime import date ,datetime
from flair.data import Sentence
from flair.nn import Classifier
import json
from bson import ObjectId
from dotenv import load_dotenv
DetectorFactory.seed = 0

load_dotenv() # load Connection String


# Construct MongoDB URI dynamically
MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_CREDENTIALS')}"
MONGO_DBNAME = os.getenv("MONGO_DBNAME")

# Check if the URI is valid before connecting
if not os.getenv('MONGO_CREDENTIALS'):
    print("MongoDB credentials missing. Please update your .env file.")
else:
    try:
        # Establish MongoDB connection
        client = MongoClient(MONGO_URI)
        db = client[os.getenv("MONGO_DBNAME")]  # Get the database
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

# Create a new client and connect to the server
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[MONGO_DBNAME]
collection = db["game"]
data = list(collection.find())
# Convert to JSON and save to file
# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO 8601 string
        return super().default(obj)
with open("reviews.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4, cls=JSONEncoder)

print("Collection exported successfully!")
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

print(os.getcwd())
directory = os.getcwd() + "/game_review/data/"
folders = os.listdir(directory)
tagger = Classifier.load('sentiment')
result = []
i = 0
# for folder in folders:
#     if folder.__contains__("DS") or folder.__contains__("clean"):
#         continue
#     for file in os.listdir(f"{directory}{folder}"):
#         if file.__contains__("metacritic"):
#             continue
#         try:
#             df = pd.read_csv(f"{directory}{folder}/{file}")   
#             release_date = date.today()
#             match file.split("_")[-1].split('.')[0]:
#                 case "Death Stranding":
#                     release_date = datetime(2019,11,8)         
#                 case "Detroit_Become Human":
#                     release_date = datetime(2018,5,25)           
#                 case "God of War Ragnarok":
#                     release_date = datetime(2022,11,9)              
#                 case "Red Dead Redemption 2":
#                     release_date = datetime(2018,10,26)                     
#                 case "The Last of Us Part I":
#                     release_date = datetime(2013,6,14)                 
#                 case "The Last of Us Part II":
#                     release_date = datetime(2020,6,19)                 
#                 case "Indiana Jones and the Great Circle":
#                     release_date = datetime(2024,12,9)                  
#                 case "Stray":
#                     release_date = datetime(2022,7,19)                  
#                 case "Cyberpunk 2077":
#                     release_date = datetime(2020,12,10)                    
#                 case "Inside":
#                     release_date = datetime(2016,7,7)                  
#                 case "It Takes Two":
#                     release_date = datetime(2021,3,25)                    
#                 case "Limbo":
#                     release_date = datetime(2010,7,21)                      
#                 case "Little Nightmares":
#                     release_date = datetime(2017,4,28)                       
#                 case "Baldur's Gate 3":
#                     release_date = datetime(2023,8,3)                     
#                 case "Elden Ring":
#                     release_date = datetime(2022,2,25)                     
#                 case "Overwatch 2":
#                     release_date = datetime(2022,10,4)                      
#                 case "Age of Empires IV":
#                     release_date = datetime(2021,10,28)                   
#                 case "Total War_Warhammer III":
#                     release_date = datetime(2022,2,17)                  
#                 case _:
#                     continue
#             for index, row in df.iterrows():           
#                 try: 
#                     if file.__contains__("reddittttt"):
#                         lang = detect(row["Comment"])
#                         if lang != 'en':
#                             continue
#                         # make a sentence
#                         sentence = Sentence(row["Comment"])

#                         tagger.predict(sentence)

                        
                        
#                         date = pd.to_datetime(row["Comment Date"], errors="coerce").to_pydatetime()
#                         data = {"platform": file.split("_")[0],"game_title": file.split("_")[-1].split('.')[0] ,"review": row["Comment"], "insertion_data":date, "released_date" : release_date, "tag": sentence.tag,"score":sentence.score}
#                         collection.insert_one(data)
#                         #print(data)
#                         result.append(data)
#                         i = i + 1   
                       
#                     if file.__contains__("steam"):
#                         lang = detect(row["Review"])
#                         if lang != 'en':
#                             continue
#                         sentence = Sentence(row["Review"])

#                         tagger.predict(sentence)
                        
#                         date = pd.to_datetime(row["Date"], errors="coerce").to_pydatetime()
#                         data = {"platform": file.split("_")[0],"game_title": file.split("_")[-1].split('.')[0] ,"review": row["Review"], "insertion_data":date, "released_date" : release_date, "tag": sentence.tag,"score":sentence.score}
#                         result.append(data)
#                         collection.insert_one(data)

#                         i = i + 1   
                        
                        
#                     if file.__contains__("youtube"):
#                         lang = detect(row["Comment"])
#                         if lang != 'en':
#                             continue
#                         sentence = Sentence(row["Comment"])

#                         tagger.predict(sentence)

#                         date = pd.to_datetime(row["Date"], errors="coerce").to_pydatetime()
#                         data = {"platform": file.split("_")[0],"game_title": file.split("_")[-1].split('.')[0] ,"review": row["Comment"], "insertion_data":date, "released_date" : release_date, "tag": sentence.tag,"score":sentence.score}
#                         result.append(data)
#                         collection.insert_one(data)

#                         i = i + 1   
                    
#                     print(i)   
            
#                 except Exception as e:
#                     print(f"Error")
#         except Exception as e:
#                     print(f"Error")            

# print(len(result))        
        
# print(i)

