from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def toConnect():
    try:
        conn = MongoClient("mongodb://localhost:27017/UCARSDB")
        dbucars = conn["UCARSDB"]
        return dbucars
    except ConnectionFailure:
        print("Server not available!")
