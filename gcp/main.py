'''
Dummy function to test GCP functionality 
'''

import base64
import pandas as pd
from mod_1 import ts
from google.cloud import storage


def timenow(event, context):
    '''
    Function creates a csv file with timestamp
    
    Output:
        Returns a csv file
    '''
    
    print("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))
    
    #Import file
    df_test = pd.read_csv("data/dummy_file.csv")
    
    print("Test if import worked",type(df_test))
    
    d = ts()
    
    print("Test if ts worked", d)
    
    df = pd.DataFrame(data=d, index=range(1))

    df.to_csv("data/test_gcp.csv", index=False)
    
    print("Generated csv")
    
def upload_file(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

    