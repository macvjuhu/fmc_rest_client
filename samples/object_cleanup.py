#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getopt
import sys
from _datetime import datetime

from fmc_rest_client import FMCRestClient
from fmc_rest_client.resources import *

logging.basicConfig(level=logging.INFO)

types_map = {
    'networks': [ NetworkGroup(), Host() , Network(), Range()],
    'ports': [PortObjectGroup(), Port(), ICMPV4Object(), ICMPV6Object() ],
    'ifobjects' : [ SecurityZone(), InterfaceGroup() ]
}

supported_types = ['AccessPolicy', 'FtdNatPolicy', 'NetworkGroup', 'Host' , 'Network', 'Range', 'SecurityZone', 'InterfaceGroup', 'PortObjectGroup', 'Port', 'ICMPV4Object', 'ICMPV6Object']

INCORRECT_TYPES_MSG = "Incorrect objects specified along with '-t' option. Pass the comma separated list of following - \n\t{}. " \
      "\nYou can also use - 'networks' for all network type objects, 'ports' for all port type objects.".format(
    supported_types)

fmc_server_url = None
username = None
password = None
obj_name_prefix = None
skip_read_only = False
obj_types = []

def usage():
    print('script -s <fmc server url> -u <username> -p <password> [-t <comma separated types>] [-x <object name prefix>] [--skip-readonly]')

def parse_args(argv):
    global fmc_server_url
    global username
    global password
    global obj_types
    global obj_name_prefix
    global skip_read_only

    try:
        opts, args = getopt.getopt(argv,'hu:p:s:t:x:', ['file=' , 'skip-readonly', '--types'])
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
            obj_types = process_types_arg(arg)
        elif opt  == '--skip-readonly':
            skip_read_only = True
        elif opt == '-x':
            obj_name_prefix = arg
        else:
            pass
    if len(obj_types) == 0:
        obj_types = get_object_list(supported_types)

    if password is None or username is None or fmc_server_url is None or len(obj_types)== 0:
        usage()
        sys.exit(2)

def process_types_arg(types):
    type_list = types.split(',')
    if len(type_list) == 0:
        print(INCORRECT_TYPES_MSG)
        sys.exit(2)
    return get_object_list(type_list)

def get_object_list(type_list):
    obj_list = []
    for t in type_list:
        if t in types_map:
            obj_list.extend(types_map[t])
        elif t in globals():
            obj_list.append(globals()[t]())
    if len(obj_list) == 0:
        print(INCORRECT_TYPES_MSG)
        sys.exit(2)
    print('Types selected for cleanup: {}'.format(list(map(lambda x: x.__class__.__name__, obj_list))))
    return obj_list


def delete_objects(rest_client, obj_types, skip_read_only=False, obj_name_prefix=None):
    failed_obj_dict = {}
    deleted_obj_list = []
    for obj_type in obj_types:
        resource_iterator = rest_client.list_iterator(obj_type)
        print('Found total {} objects at this point: {}'.format(type(obj_type).__name__, str(resource_iterator.total)))
        print('Deleting objects of type {}'.format(type(obj_type).__name__), end='')
        if obj_name_prefix:
            print(' starting name with {}'.format(obj_name_prefix), end='')
        print(' ...')
        for resource in resource_iterator:
            try:
                if not obj_name_prefix or obj_name_prefix in resource.name:
                    if skip_read_only and resource.metadata.readOnly.state:
                        #print (obj.__dict__)
                        print('\tSkipping delete for read only object {}'.format(resource.name))
                        continue
                    print('\tDeleting {} object {}'.format(type(resource).__name__, resource.name), end='')
                    delete_object(resource)
                    print(' \t\tdone.')
                    deleted_obj_list.append(resource)
            except Exception as e:
                failed_obj_dict[resource] = str(e)
    return failed_obj_dict, deleted_obj_list


def delete_object(resource):
    """
    Deletes an object, for interface group and security zone, it first unlink interfaces.
    """
    if type(resource) == SecurityZone or type(resource) == InterfaceGroup:
        resource.interfaces = []
        rest_client.update(resource)
    rest_client.remove(resource)

'''
print the std output both to terminal as well as to File
'''
def write_line_to_file(text, fh, do_print=True):
    _write_to_file(text, fh, do_print)

def _write_to_file(text, fh,do_print=True):
    if do_print:
        print(text)
    fh.write(text + '\n')

'''
    create report
'''
def write_report(report_filename, failed_obj_dict, deleted_obj_list, dump_deleted_obj=True):
    deleted_dump = 'DeletedObjectsDump-{}.json'.format(datetime.now().strftime('%Y%m%d%H%M%S'))
    with open(report_filename, 'w') as fh, open(deleted_dump,'w') as dh:
        if len(deleted_obj_list) > 0:
            write_line_to_file('-' * 120, fh)
            msg='Total number of deleted objects: '+str(len(deleted_obj_list))
            write_line_to_file(msg, fh)
            write_line_to_file('List of deleted object names:', fh)
            write_line_to_file('-' * 120, fh)
            if dump_deleted_obj:
                write_line_to_file('{\n\"items\": [', dh, do_print=False)
            for obj in deleted_obj_list:
                write_line_to_file('\t' + obj.name, fh)
                if dump_deleted_obj:
                    write_line_to_file(obj.json() + ',', dh,do_print=False)
            if dump_deleted_obj:
                write_line_to_file('\n]}', dh, do_print=False)
            write_line_to_file('-' * 120, fh)
        if len(failed_obj_dict)>0:
            write_line_to_file('-' * 120, fh)
            msg='Total number of object failed to delete: ' + str(len(failed_obj_dict))
            write_line_to_file(msg, fh)
            write_line_to_file('Failed objects list:', fh)
            write_line_to_file('-' * 120, fh)
            for resource,reason in failed_obj_dict.items():
                resource = '{}: {}'.format(type(resource).__name__, resource.name)
                reason = '\tReason for failure: ' + reason
                write_line_to_file(resource, fh)
                write_line_to_file(reason, fh)
            write_line_to_file('-'*120, fh)

    
                     
if __name__ == '__main__':
    start_time = datetime.now().replace(microsecond=0)
    parse_args(sys.argv[1:])
    print('Connecting to FMC {} ...'.format(fmc_server_url))
    rest_client = FMCRestClient(fmc_server_url, username, password)
    print('Connected Successfully')
    report_file = 'ObjectCleanupReport.txt'
    result = delete_objects(rest_client, obj_types, skip_read_only, obj_name_prefix)
    write_report(report_file, result[0], result[1])
    end_time = datetime.now().replace(microsecond=0)
    print("Script completed in {}s.".format(str(end_time - start_time)))
