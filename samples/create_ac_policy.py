#!/bin/env python3
import getopt
import sys

from fmc_rest_client import FMCRestClient
from fmc_rest_client.resources import *
import logging
logging.basicConfig(level=logging.INFO)

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
    global fmc
    print('Connecting to FMC {}@{} ...'.format(username, fmc_server_url))
    fmc = FMCRestClient(fmc_server_url, username, password)
    print('Connected Successfully')
    return fmc

class NetworkGroup(ObjectResource):
    def __init__(self, name=None, objects=None, literals=None):
        super().__init__(name)
        if objects == None:
            objects = []
        super().__setattr__('objects',objects)
        if literals == None:
            literals = []
        super().__setattr__('literals', literals)

    def __setattr__(self, name, value):
        if name in ['objects', 'literals']:
            raise Exception("You cannot set value for attribute {}. Its a list, operate on that, "
                            "e.g net_grp_obj.{}.append(host1)".format(name, name))
        else:
            super().__setattr__(name, value)

if __name__ == "__main__":
    parse_args(sys.argv[1:])
    fmc = get_fmc_rest_client()
    try:
        acp = AccessPolicy(policy_name)
        acp = fmc.create(acp)
        print('Created acp ' + acp.name)
        net1 = Host('host1', '1.1.1.1')
        #net1 = fmc.create(net1)
        net2 = Host('host2', '2.2.2.2')
        #net2 = fmc.create(net2)
        nets = fmc.create([net1, net2])
        net1 = nets[0]
        net2 = nets[1]
        rule1 = AccessRule('rule1', acp)
        rule1.action = 'ALLOW'
        rule1.sourceNetworks = { 'objects' : [ net1]}
        rule2 = AccessRule('rule2', acp)
        rule2.action = 'ALLOW'
        rule2.sourceNetworks = {'objects': [net1]}
        rule2.destinationNetworks = {'objects': [net2]}
        rules = [rule1, rule2]
        rules = fmc.create(rules)
        print(rules[1].json())
        # another network object
        # Add another source network in rule1
        #rule1.sourceNetworks['objects'].append(net2)
        #rule1 = fmc.update(rule1)


    finally:
        fmc.remove(acp)
        fmc.remove(net1)
        fmc.remove(net2)
        #pass


