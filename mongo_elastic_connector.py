import pandas as pd
import pymongo
from pymongo import MongoClient
import requests
import csv
import json
from elasticsearch import helpers
from pymongo import MongoClient
import time
from elasticsearch import Elasticsearch
import glob
import os

def read_from_folder(client,location):
    all_files = glob.glob(location)
    for file in all_files:
        df = pd.read_csv(file)
        json_list = json.loads(df.to_json(orient = 'records'))
        db_name = file.split('/')[2].split('.')[0].lower()
        db = client[db_name]
        collection = db[db_name]
        collection.insert_many(json_list)
        df = None

def _connect_mongo(host, port, username, password, db):
    """ A util for making a connection to mongo """

    if username and password:
        mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db)
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)


    return conn[db]


def read_mongo(db, collection, config,query={}, no_id=True):
    """ Read from Mongo and Store into DataFrame """
    if config['mongo_settings']['username']=="":
        username=None
        password=None

    # Connect to MongoDB
    db = _connect_mongo(host=config['mongo_settings']['host'], port=int(config['mongo_settings']['port']), username=config['mongo_settings']['username'], password=config['mongo_settings']['password'], db=db)

    # Make a query to the specific DB and Collection
    cursor = db[collection].find(query)

    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df

def get_config():

    config_file = os.path.join(os.getcwd(), 'config.json')
    if os.path.exists(config_file):
        with open('config.json', 'r') as f:
            config = json.load(f)

    else:
        error_message = 'config.json is either missing from working directory {} or is not a valid json'.format(os.getcwd())

        raise Exception(error_message)
    return config



def index_to_elasticsearch(es,config,all_dbs):
    elastic_settings = config['elastic_settings']
    start_time = time.time()
    for db in all_dbs:
        print("Reading: ",db)
        df = read_mongo(db,db,config)
        if '_index' not in df.columns:# will fail
            df["_index"] = index_name

        if '_type' not in df.columns:
            df["_type"] = "_doc"
        keep_arr = config['result_keys'] #This comes from columns of the CSV file. Keep wanted. 
        df_new = df[keep_arr]
        dicts = df_new.to_dict(orient='records')
        print("Indexing: ",db)
        es.indices.create(db,body=elastic_settings,ignore=400,)
        helpers.bulk(es,dicts)
        df,df_new,dicts = None,None,None
    print("Total indexing time is :",time.time() - start_time)

def main():
    session = requests.Session()
    session.trust_env = False
    print("Reading configuration...")
    config = get_config()
    print("Connecting to MongoClient")
    client = MongoClient()
    print("Connected Successfully")
    read_from_folder(client,config['fs_src'])
    all_dbs = client.list_database_names()
    all_dbs.remove('admin')
    all_dbs.remove('config')
    all_dbs.remove('local')
    print("Indexing to elasticsearch cluster...")
    es = Elasticsearch()
    index_to_elasticsearch(es,config,all_dbs)
    print("Connector worked successfully!") 


if __name__=="__main__":
    main()


