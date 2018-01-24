import json
import logging
import time
from datetime import datetime
from fmc_rest_client.core.base_resources import json_dump
import requests
# Disable  InsecureRequestWarning: Unverified HTTPS request is being made.
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# logger = logging.getLogger(__name__)
logger = logging.getLogger('FMC_REST_CLIENT')

NAME_EXISTS_ERROR = ['already exists',
                     'conflicts with predefined name on device',
                     'Duplicate Name']
INVALID_NAME_ERROR = ['Invalid Object Name']

TOO_MANY_REQUESTS = 'Too Many Requests'

class ResourceException(Exception):
    GENERIC = 'generic'
    READ_ONLY = 'read-only'
    NAME_EXISTS = 'name-exists'
    INVALID_OBJECT_NAME = 'invalid-object-name'
    AUTH_FAILED = 'auth-failed'
    TOO_MANY_REQUESTS = 'too-many-requests'


    def __init__(self, code, message=None):
        self.code = code
        self.message = message

class RESTListIterator:
    """

    """
    def __init__(self, resource, rest_client):
        self.current_index = 0
        self.offset = 0
        self.resource = resource
        self.rest_client = rest_client
        self.list_cache, paging = rest_client._list(resource)
        self.total = paging['count']
        self.page_size = paging['limit']

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self.current_index < self.total:
            cache_size = len(self.list_cache)
            logger.debug('Fetching item number {} out of {}'.format(self.current_index, self.total))
            logger.debug('Current offset {} and Cache size {}'.format(self.offset, cache_size))
            if self.current_index == self.offset + cache_size:
                #fetch next page if we are done reading cached page
                self.offset = self.current_index
                logger.debug('Fetching page starting at offset {}'.format(self.offset))
                self.list_cache, paging = self.rest_client._list(self.resource, self.offset)
                if paging['count'] != self.total:
                    logger.warning("Resource size changed on server")
                self.total = paging['count']
                if self.current_index > self.total:
                    logger.warning("Resource size got reduced than current iteration")
                    raise StopIteration("Resource size got reduced.")
            resource = self.list_cache[self.current_index - self.offset]
            self.current_index += 1
            return resource
        else:
            raise StopIteration()

class FMCRawRestClient(object):
    def __init__(self, server, username=None, password=None, auth_token=None, domain='default'):
        self.server = server
        self.username = username
        self.password = password
        self.auth_token = auth_token
        self.reauth_count = 0
        if domain is None:
            domain = 'default'
        self.domain = domain
        if not self.auth_token:
            self.auth_token = self.get_auth_token()

    def get_auth_token(self):
        api_auth_path = "/api/fmc_platform/v1/auth/generatetoken"
        auth_url = self.server + api_auth_path
        try:
            # Download SSL certificates from your FMC first and provide its path for verification.
            # r = requests.post(auth_url, headers=headers, auth=requests.auth.HTTPBasicAuth(username,password), verify='/path/to/ssl_certificate/')
            headers = {'Content-Type': 'application/json'}
            logger.debug('Connecting to %s', auth_url)
            response = requests.post(auth_url, headers=headers,
                                     auth=requests.auth.HTTPBasicAuth(self.username, self.password), verify=False)
            auth_headers = response.headers
            auth_token = auth_headers.get('X-auth-access-token', default=None)
            if auth_token is None:
                logger.error('auth_token not found.')
                raise ResourceException(ResourceException.AUTH_FAILED)
            else:
                logger.debug('Got auth_token - ' + auth_token)
            return auth_token
        except ResourceException as e:
            raise e
        except Exception as err:
            # logger.debug('Error in generating auth token --> '+str(err))
            raise Exception('Error in generating auth token --> ' + str(err))

    def _validate_rest_call_params(self, method, url_path, post_data):
        if not method.upper() in ['POST', 'PUT', 'DELETE', 'GET', 'LIST']:
            raise Exception('Unsupported method: ' + method)
        if not str == type(url_path):
            raise Exception('URL path type is ' + type(url_path).__name__ + ' while string expected.')
        if post_data and not str == type(post_data):
            raise Exception('Post data type is ' + type(post_data).__name__ + ' while string expected.')

    def rest_call(self, method, url_path, post_data=None, offset=0, expanded=False):
        start_time = datetime.now().replace(microsecond=0)
        end_time = start_time
        try:
            self._validate_rest_call_params(method, url_path, post_data)
            variables = {'DOMAIN': self.domain}
            url = self.server + url_path.format(**variables)
            if url[-1] == '/':
                url = url[:-1]
            logger.debug('REST Call: [' + method.upper() + '] ' + url + '?offset=' + str(offset))
            # print(headers)
            reauth_retry_count = 3
            request_retry_count = 5
            while True:
                try:
                    headers = {'Content-Type': 'application/json', 'X-auth-access-token': self.auth_token}
                    status_code, response_json =  self._rest_call(method, url, post_data, headers, offset, expanded)
                    return response_json
                except ResourceException as e:
                    if e.code == ResourceException.AUTH_FAILED and reauth_retry_count > 0:
                        #we may get auth-failed when calling get_auth_token as well, that's why this retry loop
                        while True:
                            try:
                                reauth_retry_count -= 1
                                logger.debug('Retrying re-auth, retry left {}.'.format(reauth_retry_count))
                                self.auth_token = self.get_auth_token()
                                break # break inner loop for get_auth_token
                            except ResourceException as e:
                                if e.code == ResourceException.AUTH_FAILED and reauth_retry_count > 0:
                                    continue
                                else:
                                    raise e
                    elif e.code == ResourceException.TOO_MANY_REQUESTS and request_retry_count > 0:
                        request_retry_count -= 1
                        time.sleep(5)
                    else:
                        raise e
        except Exception as e:
            logger.error('REST called failed: ' + str(e))
            raise e
        finally:
            end_time = datetime.now().replace(microsecond=0)
            logger.debug('REST call completed in ' + str(end_time - start_time))

    def _rest_call(self, method, url, post_data, headers, offset=0, expanded=False):
        response = None
        data = None
        try:
            response = self._http_request(method, url, post_data, headers, offset, expanded)
            if response is not None:
                status_code = response.status_code
                data = response.text
                # print('Status code is: ' + str(status_code))
                if status_code == 200 or status_code == 201 or status_code == 202:
                    # print(method + ' was successful...')
                    response_json = json.loads(data)
                    # print(json.dumps(json_resp,sort_keys=True,indent=4, separators=(',', ': ')))
                    return status_code, response_json
                elif status_code == 401:
                    logger.debug('Re-authenticating ...')
                    raise ResourceException(ResourceException.AUTH_FAILED)
                        #self._rest_call(method, url, post_data, headers, offset, expanded)
                elif status_code == 404 and method == 'list':  # today REST API returns 404 when the list is empty
                    return [], 0
                elif status_code == 405 and (method == 'create' or method == 'post'):
                    raise ResourceException(ResourceException.READ_ONLY)
                elif status_code == 400 and (method == 'create' or method == 'post'):
                    response_json = json.loads(data)
                    desc = response_json['error']['messages'][0]['description']

                    for error in NAME_EXISTS_ERROR:
                        if error in desc:
                            raise ResourceException(ResourceException.NAME_EXISTS)
                    for error in INVALID_NAME_ERROR:
                        if error in desc:
                            raise ResourceException(ResourceException.INVALID_OBJECT_NAME)
                    raise ResourceException(ResourceException.GENERIC, desc)
                elif (status_code == 429) and (method == 'create' or method == 'post'):
                    response_json = json.loads(data)
                    reason_phrase = response_json['reasonPhrase']
                    raise ResourceException(ResourceException.TOO_MANY_REQUESTS, reason_phrase)
                else:
                    args = {'method': method.upper(), 'url': response.url, 'status_code': response.status_code,
                             'response': response.text}
                    msg = '[{method}] {url}\n\tHTTP Error:{status_code}, Response Data: {response}'.format(**args)
                    raise ResourceException(ResourceException.GENERIC, msg)
                    # response.raise_for_status()
                    # print ('Error occurred in --> ' + response)
        except requests.exceptions.HTTPError as err:
            logger.error('Error in connection --> ' + str(err))
            raise Exception(str(err))
        except ValueError as e:
            logger.error('Error with response ' + str(data))
            raise e
        finally:
            if response: response.close()

    def _http_request(self, method, url, post_data, headers, offset=0, expanded=False):
        response = None
        try:
            if method in ['post', 'create']:
                logger.debug('post payload:' + post_data)
                response = requests.post(url, data=post_data, headers=headers, verify=False)
            elif method in ['put']:
                logger.debug('put payload ' + post_data)
                response = requests.put(url, data=post_data, headers=headers, verify=False)
            elif method == 'get':
                response = requests.get(url, headers=headers, verify=False)
            elif method == 'delete':
                response = requests.delete(url, headers=headers, verify=False)
            elif method == 'list':
                params = {'limit': 4000, 'offset': offset, 'expanded': expanded}
                response = requests.get(url, headers=headers, params=params, verify=False)
            else:
                raise Exception('Unknown method ' + method)
        except Exception as e:
            raise e
        return response

    """
        The following json structure is retruned from FMC in case of list call
        {
            "items": [ <resource1>, ... ],
            "paging": {
                "offset": 0,
                "limit": 25,
                "count": 162,
                "next": [...],
                "pages": 7
            }
        }
    
    """
    def _list(self, resource, offset=None, limit=None):
        url_path = resource.get_api_path()
        json_resp = self.rest_call('list', url_path, offset=offset, expanded=True)
        objs = []
        # print(json_resp['items'])
        if 'items' in json_resp:
            for json_obj in json_resp['items']:
                obj = resource.__class__(json_obj['name'])
                obj.json_load(json_obj)
                objs.append(obj)
                # print(objs)
        paging = {}
        if 'paging' in json_resp:
            paging['pages'] = int(json_resp['paging']['pages'])
            paging['offset'] = int(json_resp['paging']['offset'])
            paging['count'] = int(json_resp['paging']['count'])
            paging['limit'] = int(json_resp['paging']['limit'])
        return objs, paging

    ######## Raw HTTP calls ###########
    ## these uses the raw payload which is json ##
    def get(self, url_path):
        # To be implemented
        return self.rest_call('get', url_path)

    def post(self, url_path, data):
        return self.rest_call('post', url_path, data)

    def put(self, url_path, data):
        return self.rest_call('put', url_path, data)

    def delete(self, url_path):
        return self.rest_call('delete', url_path)


class FMCBaseRestClient(FMCRawRestClient):
    def __init__(self, server, username=None, password=None, auth_token=None, domain='default'):
        super(FMCBaseRestClient, self).__init__(server, username, password, auth_token, domain)

    def _single_create(self, resource):
        url_path = resource.get_api_path()
        post_data = resource.json(pretty=False)
        json_resp = self.post(url_path, post_data)
        resource.json_load(json_resp)
        return resource

    def _bulk_create(self, resources, bulk_limit=1000):
        url_path = resources[0].get_api_path() + '?bulk=true'
        bulk_resources = resources
        if len(resources) > bulk_limit:
            bulk_resources = resources[:bulk_limit]
        post_data = json_dump(bulk_resources, pretty=False)
        json_resp = self.post(url_path, post_data)
        #print('Bulk response ' + str(json_resp))
        new_resources = []
        for item in json_resp['items']:
            resource = resources[0].__class__()
            resource.json_load(item)
            new_resources.append(resource)
        if len(resources) > bulk_limit:
            tmp_resources = self._bulk_create(resources[bulk_limit:])
            new_resources.extend(tmp_resources)
        return new_resources

    def create(self, resource, bulk_limit=1000):
        if isinstance(resource, list) and len(resource) > 0:
            response_resources = None
            if 'POST' in resource[0].__class__.bulk_operations:
                response_resources = self._bulk_create(resource, bulk_limit)
            else:
                response_resources = []
                for item in resource:
                    item = self._single_create(item)
                    response_resources.append(item)
            return response_resources
        else:
            if isinstance(resource, list):
                resource = resource[0]
            return self._single_create(resource)

    def load(self, resource):
        url_path = resource.get_api_path()
        if resource.id:
            url_path += '/' + str(resource.id)
            json_resp = self.get(url_path)
            resource.json_load(json_resp)
            return resource
        else:
            return self.list(resource)

    def get(self, resource):
        if isinstance(resource, str):
            return super().get(resource)
        else:
            return self.load(resource)

    def update(self, resource):
        url_path = resource.get_api_path()
        if resource.id:
            url_path += '/' + str(resource.id)
        post_data = resource.json(pretty=False)
        json_resp = self.put(url_path, post_data)
        resource.json_load(json_resp)
        return resource

    def remove(self, resource):
        url_path = resource.get_api_path()
        if resource.id:
            url_path += '/' + str(resource.id)
        json_resp = self.delete(url_path)
        return json_resp

    def delete(self, resource):
        if isinstance(resource, str):
            return super().delete(resource)
        else:
            return self.remove(resource)

    def list(self, resource, offset=0, limit=0):
        """

        :param resource:
        :param offset:
        :param limit: if 0 then all the records are returned
        :return:
        """
        objs = []
        result = self._list(resource, offset=offset)
        objs.extend(result[0])

        pages = result[1]['pages'] - 1  # we already read one page
        while pages > 0:
            offset += len(result[0])
            logger.debug('pages ' + str(pages))
            logger.debug('offset ' + str(offset) + ' len(objs) ' + str(len(objs)))
            result = self._list(resource, offset=offset)
            pages -= 1
            objs.extend(result[0])
        #FIXME: Need to fetch based on limit
        if limit > 0:
            objs = objs[0:limit]
        return objs


class FMCRestClient(FMCBaseRestClient):
    def __init__(self, server, username=None, password=None, auth_token=None, domain='default'):
        super(FMCRestClient, self).__init__(server, username, password, auth_token, domain)

    def list_iterator(self, resource):
        return RESTListIterator(resource, self)