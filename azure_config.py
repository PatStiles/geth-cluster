''' Helper functing used across the Azure scripts '''

import json
import os

AUTH_FILE_PATH = "./azure_credentials.json"

GROUP_NAME = "BasicRG"
NETWORK_NAME = "BasicNet"
SUBNET_NAME = "DpSubnet"

LOCATION = 'eastus'
IMAGE = "/subscriptions/94fe0430-bbed-43a0-800e-2bc712a8499f/resourceGroups/BasicRG/providers/Microsoft.Compute/galleries/images/images/datapods"
def load_azure_credentials():
    ''' Load the user's Azure credentials from disk '''

    conf = {}

    with open(AUTH_FILE_PATH, 'r', encoding='utf-8') as jfile:
        conf = json.load(jfile)
        for key, value in conf.items():
            os.environ["AZURE_"+key] = value
            conf[key] = value

    return conf
