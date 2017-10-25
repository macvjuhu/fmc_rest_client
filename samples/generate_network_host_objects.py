#!/bin/env python3
import getopt
import logging
import re
import sys
from datetime import datetime

from fmc_rest_client import FMCRestClient
from fmc_rest_client import ResourceException
from fmc_rest_client.resources import *

logging.basicConfig(level=logging.INFO)

action='create'

def usage():
    print('script -s <fmc server url> -u <username> -p <password> -n <object_count> [-p <obj_prefix>')

def parse_args(argv):
    fmc_server_url = None
    username = None
    password = None
    object_count = None
    object_name_prefix = 'NWHostObject_'
    try:
        opts, args = getopt.getopt(argv,'hu:p:s:n:f:a:', ['file='])
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
            object_count = int(arg)
        elif opt == '-f':
            object_name_prefix = arg
        #elif opt == '-a':
            #action=arg
            #if action != 'create' || action !='delete' :
                #print('Invalid action :' , action)
                #usage()
                #sys.exit(2)
        else:
            pass
    if not (object_count and fmc_server_url and username and password) :
        usage()
        sys.exit(2)
    return username, password, fmc_server_url, object_count, object_name_prefix
                         
"""
    Increment the last index number of string , ex: obj_1 to obj_2
                                                    obj_2 to obj_3
"""
def increment_str_last_index(s):
    s=re.sub(r'\d+(?=[^\d]*$)', lambda m: str(int(m.group())+1).zfill(len(m.group())), s)
    return s

def ipRange(start_ip, end_ip):
   #print("\n Inside iprange() def ")
   start = list(map(int, start_ip.split(".")))
   end = list(map(int, end_ip.split(".")))
   temp = start
   ip_range = [] 
   ip_range.append(start_ip)
   while temp != end:
      start[3] += 1
      for i in (3, 2, 1):
         if temp[i] == 256:
            temp[i] = 0
            temp[i-1] += 1
      ip_range.append(".".join(map(str, temp))) 
   return ip_range         

def ipRangeByCount(start_ip, total_ip):
   start = list(map(int, start_ip.split(".")))
   temp = start
   ip_range = [] 
   ip_range.append(start_ip)
   i = 0
   while i < total_ip:
      ip_range.append(".".join(map(str, temp)))
      start[3] += 1
      for j in (3, 2, 1):
         if temp[j] == 256:
            temp[j] = 0
            temp[j-1] += 1
      i += 1
   return ip_range         
        
def create_range_objects(rest_client, nwObjCount, nwObjName, first_nwObjvalue, last_nwObjvalue=None):
    if last_nwObjvalue:
        iprange = ipRange(first_nwObjvalue, last_nwObjvalue)
    else:
        iprange = ipRangeByCount(first_nwObjvalue, nwObjCount)
    for i in range(1, nwObjCount+1):
        key=nwObjName+str(i)
        ip_index=i%len(iprange)
        print('Creating object {} = {}'.format(key, iprange[ip_index]))
        value=str(iprange[ip_index])
        if rest_client:
            try:           
                rest_client.create(Host(key,value))
            except ResourceException as e:
                if ResourceException.NAME_EXISTS == e.code:
                    print('Object already exists in FMC\n')


if __name__ == "__main__":
    start_time = datetime.now().replace(microsecond=0)
    username, password, fmc_server_url, object_count, object_name_prefix = parse_args(sys.argv[1:])
    print('Connecting to FMC {} ...'.format(fmc_server_url))
    rest_client = FMCRestClient(fmc_server_url, username, password)
    print('Connected Successfully')
    print("Objects to be created:", object_count)
    create_range_objects(rest_client, object_count, object_name_prefix, "10.10.10.1")
    end_time = datetime.now().replace(microsecond=0)
    print("Script completed in {}s.".format(str(end_time - start_time)))
