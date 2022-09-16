#!/bin/env python3
import getopt
import logging
import re
import sys
import json
from datetime import datetime

from fmc_rest_client import FMCRestClient
from fmc_rest_client import ResourceException
from fmc_rest_client.resources import *

logging.basicConfig(level=logging.DEBUG)

obj_types = []
types_map = {
    'networks': [ NetworkGroup(), Host() , Network(), Range()],
    'ports': [PortObjectGroup(), Port(), ICMPV4Object(), ICMPV6Object() ]
}
supported_types = ['AccessPolicy', 'FtdNatPolicy', 'NetworkGroup', 'Host' , 'Network', 'Range', 'SecurityZone', 'InterfaceGroup', 'PortObjectGroup', 'Port', 'ICMPV4Object', 'ICMPV6Object']
def usage():
    print('script -s <fmc server url> -u <username> -p <password> -t <comma separated types> [-r <repeat-count>]')

def parse_args(argv):
    fmc_server_url = None
    username = None
    password = None
    auth_token = None
    object_types = []
    #whole operation will be repeated this many times
    repeat = 1

    try:
        opts, args = getopt.getopt(argv,'hu:p:s:t:r:', ['--types', 'auth='])
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
        elif opt == '-t' or opt == '--types':
            object_types = process_types_arg(arg)
        elif opt == '-r' or opt == '--repeat':
            repeat = int(arg)
        elif opt == '--auth':
            auth_token = arg
        else:
            usage()
            sys.exit(2)

    if (len(object_types) == 0 or fmc_server_url == None or ((username == None or password == None) and (auth_token ==None))):
        usage()
        sys.exit(2)
    return username, password, auth_token, fmc_server_url, object_types, repeat
                         
def process_types_arg(types):
    type_list = types.split(',')
    msg = "Incorrect objects specified along with '-t' option. Pass the comma separated list of following - \n\t{}. " \
          "\nYou can also use - 'networks' for all network type objects, 'ports' for all port type objects.".format(supported_types)
    if len(type_list) == 0:
        print(msg)
        sys.exit(2)
    obj_list = []

    for t in type_list:
        if t in types_map:
            obj_list.extend(types_map[t])
        elif t in globals():
            obj_list.append(globals()[t]())
    if len(obj_list) == 0:
        print(msg)
        sys.exit(2)
    print('Types selected for iteration: {}'.format(list(map(lambda x: x.__class__.__name__, obj_list))))
    return obj_list


if __name__ == "__main__":
    username, password, auth_token, fmc_server_url, object_types, repeat = parse_args(sys.argv[1:])
    start_time = datetime.now().replace(microsecond=0)
    print('Connecting to FMC {} ...'.format(fmc_server_url))
    rest_client = FMCRestClient(fmc_server_url, username, password, auth_token)
    end_time = datetime.now().replace(microsecond=0)
    print('Connected Successfully in {}s'.format(str(end_time - start_time)))
    start_time = datetime.now().replace(microsecond=0)
    for r in range(repeat):
        for obj_type in object_types:
            count = 0
            print('Iterating objects of type {} ...'.format(type(obj_type).__name__))
            for resource in rest_client.list_iterator(obj_type):
                print("Resource name " + resource.name)
                try:
                    obj = rest_client.load(resource)
                    print("Resource value " + obj.json())
                except Exception as ex:
                    print("Failed to get object  " + str(ex));
                count += 1
            print('Total {} objects of type {} iterated.'.format(count, type(obj_type).__name__))
    end_time = datetime.now().replace(microsecond=0)
    print('Script completed in {}s.'.format(str(end_time - start_time)))


