# mongo-elasticsearch-connector
This repository  connects  mongodb with elasticsearch. It inserts multiples csv files from local directory to mongodb collections first, then it 
indexes all these collections to elasticsearch. A template of elasticsearch settings currently exists in `config.json` but changes can be made to it.

##### USAGE:  
```python mongo_elastic_connector.py```  

Change the `fs_src` and `result_keys` in `config.json` according to the need.
`fs_src` is the source location of the csv files
`result_keys` are the column names that needs to be indexed into elasticsearch.
