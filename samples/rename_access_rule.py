#!/bin/env python3
import getopt
import sys

from fmc_rest_client import FMCRestClient
from fmc_rest_client.resources import *

fmc_server_url = None
username = None
password = None
policy_name = None

def usage():
    print('script -s <fmc server url> -u <username> -p <password> -n <ac policy name>')

def parse_args(argv):
    global fmc_server_url
    global username
    global password
    global policy_name
    try:
        opts, args = getopt.getopt(argv,'hu:p:s:n:', ['file='])
    except getopt.GetoptError as e:
        print(str(e))
        usage()
        sys.exit(2)
    server_provided = False
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt == '-u':
            username = arg
        elif opt == '-p':
            password = arg
        elif opt == '-s':
            fmc_server_url = arg
        elif opt == '-n':
            policy_name = arg
        else:
            pass
    if not username or not password or not fmc_server_url or not policy_name:
        usage()
        sys.exit(2)

def get_fmc_rest_client():
    global rest_client
    print('Connecting to FMC {} ...'.format(fmc_server_url))
    rest_client = FMCRestClient(fmc_server_url, username, password)
    print('Connected Successfully')
    return  rest_client

def get_policy_by_name(policyName, policyType):
    alist = rest_client.list(globals()[policyType]())
    for policy in alist:
        #print(policy.json())
        if policyName == policy.name:
            return policy

"""
    Parameters:
        resource_json: json dict
        attrs: list of attrs to be removed from json dict
"""
def _remove_attrs(resource_json, attrs):
    for attr in attrs:
        if attr in resource_json:
            resource_json.pop(attr, None)

def rename_resource(resource, new_name):
    url_path = resource.get_api_path()
    #print("url-path= ", url_path)
    if resource.id:
        url_path += '/' + str(resource.id)
    url_path +='/'
    resource_json = rest_client.get(url_path)
    
    #add comment and update the name
    resource_json['newComments'] = ['Previous name ' + resource_json['name']]
    resource_json['name'] = new_name
    
    #filter attrs not allowed by put/update operation
    resAttrs = ['metadata', 'links']
    resAttrs.append('commentHistoryList')
    _remove_attrs(resource_json, resAttrs)
    for value in ['sourcePorts', 'destinationPorts']:
        if value in resource_json:
            if 'objects' in resource_json[value]:
                for objRef in resource_json[value]['objects']:
                    _remove_attrs(objRef,['protocol']) 
    #update it
    resource_json = rest_client.put(url_path, json.dumps(resource_json))




if __name__ == "__main__":
    parse_args(sys.argv[1:])
    rest_client = get_fmc_rest_client()
    ac_policy = get_policy_by_name(policy_name, 'AccessPolicy')
    if not ac_policy:
        print('Access Policy {} not found.'.format(policy_name))
        exit(2)
    print(ac_policy.json())
    rules = rest_client.list(AccessRule(container=ac_policy))
    i = 0
    for rule in rules: 
        print(rule.json())
        i += 1
        new_name = 'my_rule-' + str(i)
        rule.container = ac_policy
        rename_resource(rule, new_name)
    print("Script completed.")
