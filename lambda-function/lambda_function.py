from __future__ import print_function
import boto3
import requests
import json

print('Loading function')


def lambda_handler(event, context):
    '''Provide an event that contains the following keys:

      - operation: one of the operations in the operations dict below
      - tableName: required for operations that interact with DynamoDB
      - payload: a parameter to pass to the operation being performed
    '''
    print("Received event: " + json.dumps(event, indent=2))
    
    # request user data from web api
    apiURL = '<YOUR API URL>'
    headers = {'Content-Type' : 'application/json'}
    r = requests.post(apiURL, json=json.dumps(event), headers=headers, hooks=dict(response=print_response))

def print_response(r, *args, **kwargs):
  print(r.status_code)
  print(r.json())
  