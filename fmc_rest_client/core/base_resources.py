import inspect
import json
import logging

from fmc_rest_client.core.pluralize import pluralize

logger = logging.getLogger('FMC_REST_CLIENT')

class ObjectJSONEncoder(json.JSONEncoder):
    def __init__(self, full_dump=False, *args, **kwargs):
        json.JSONEncoder.__init__(self, *args, **kwargs)
        self.full_dump = full_dump

    def hide_attr(self, obj, attr_name):
        if not self.full_dump and (hasattr(obj, 'hide_in_json')
                                    and obj.hide_in_json and obj.hide_in_json(attr_name)):
            return True
        return False

    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return self.default(obj.to_json())
        elif hasattr(obj, '__dict__'):
            d = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('__') and not self.hide_attr(obj, key) and value:
                    d[key] = convert_to_references(value)
            return d

        return obj

def convert_to_references(obj):
    """ recursively converts all BaseReferenceResource to ReferenceType"""
    if isinstance(obj, BaseReferenceResource):
        if hasattr(obj, 'id') and not obj.id:
            logger.warning('Id missing for object ' + str(obj.__dict__) + '.\nFMC may fail to resolve this reference.')
        converted_obj = ReferenceType(obj)
    elif isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, set):
        new_list = type(obj)()
        for item in obj:
            if isinstance(obj, set):
                new_list.add(convert_to_references(item))
            else:
                new_list.append(convert_to_references(item))
        converted_obj = new_list
    elif isinstance(obj, dict):
        new_dict = {}
        for key, converted_obj in obj.items():
            new_dict[key] = convert_to_references(converted_obj)
        converted_obj = new_dict
    elif obj and isinstance(obj, object) and hasattr(obj, '__dict__'):
        converted_obj = convert_to_references(obj.__dict__)
    else:
        converted_obj = obj
    return converted_obj

def json_dump(obj, pretty=True, full_dump=True):
    indent = None
    sort_keys = False
    separators = (',', ': ')
    if pretty:
        indent = 2
        sort_keys = True
        separators = None
    json_str = json.dumps(obj, cls=ObjectJSONEncoder, indent=indent,
                          separators=separators, sort_keys=sort_keys, full_dump=full_dump)
    return json_str

def is_reference_type(json):
    return isinstance(json, dict) and set(['id', 'type','name']).issubset(json.keys())

class BaseResource:
    """
    Base Resource for all resources
    """
    def json(self, pretty=True, full_dump=True):
        """
        Dumps the object in json format
        Set full_dump False to ignore the attribute which shouldn't be there for post or put requests
        Implement json_ignore_attrs, providing the list of attributes to be ignored when full_dump is False.
        """
        return json_dump(self, pretty, full_dump)

    def json_load(self, json):
        """ load this object from json """
        #print('json to load ' + str(json))
        for key in self.__dict__.keys():
            if key in json:
                if isinstance(getattr(self, key), BaseResource):
                    getattr(self, key).json_load(json[key])
                elif is_reference_type(json[key]):
                    ref = ReferenceType()
                    ref.json_load(json[key])
                    setattr(self, key, ref)
                else:
                    setattr(self, key, json[key])

    @staticmethod
    def json_ignore_attrs():
        """
        List of attributes to be ignored while serializing for post/put requests
        Added 'metadata' here for example, ideally it should be at the right Resource Subclass which defines this attribute
        """
        return ['metadata']

    def _aggregatted_json_ignore_attrs(self):
        alist = []
        for cls in inspect.getmro(self.__class__):
            if 'json_ignore_attrs' in cls.__dict__:
                alist.extend(cls.json_ignore_attrs())
        return alist

    def hide_in_json(self, attr_name):
        alist = self._aggregatted_json_ignore_attrs()
        # print('Attribute to hide in ' + self.type + ' ' + str(list))
        # print('Attribute ' + attr_name + [' not found.', 'found'][attr_name in list])
        return attr_name in alist

class BaseContainedResource(BaseResource):
    """
        This is a resource which is used inside a resource but can never be referenced independently.
        This is a marker base class at this point, to make it easy to identify this kind of resources
    """
    def __init__(self):
        super().__init__()

class BaseReferenceResource(BaseResource):
    """
    All REST Resources or URL endpoints should extend from this or its specific sub class
    If this resource support bulk API add methods which support bulk operation in
    bulk_operations list. Use following operations - POST, PUT etc.
    """
    bulk_operations = []

    def __init__(self, id=None):
        self.id = id
        self.type = self.__class__.__name__

    def _get_resource_suffix(self):
        return pluralize(self.type).lower()

    def _get_api_base(self):
        return '/api/fmc_config/v1/domain/{DOMAIN}'

    def get_api_path(self):
        """ The URL representing this REST Endpoint/Resource"""
        return self._get_api_base() + '/' + self._get_resource_suffix()

class NamedResource(BaseReferenceResource):
    def __init__(self, name, id=None):
        super().__init__(id)
        self.name = name


class ReferenceType(BaseContainedResource):
    """
    Class to represent reference in a Resource,
    Used for json encoding of references to keep only data required for reference
    """
    def __init__(self, obj=None):
        if obj and isinstance(obj, NamedResource):
            self.type = obj.type
            self.id = obj.id
            self.name = obj.name

    def json_load(self, json):
        for key in ['id' , 'name', 'type']:
            if key in json:
                setattr(self, key, json[key])

class ReadOnly(BaseContainedResource):
    def __init__(self, state=False, reason=None):
        self.state = state
        self.reason = reason

class Metadata(BaseContainedResource):
    def __init__(self, timestamp=0, domain: ReferenceType=None, readOnly:  ReadOnly=None):
        self.timestamp = timestamp
        self.domain = domain
        if readOnly:
            self.readOnly = readOnly
        else:
            self.readOnly = ReadOnly()


class ObjectResource(NamedResource):
    def __init__(self, name, id=None):
        super().__init__(name, id)
        self.metadata = Metadata()

    def get_api_path(self):
        """ The URL representing this REST Endpoint/Resource"""
        return self._get_api_base() + '/object/' + self._get_resource_suffix()


class PolicyResource(NamedResource):
    def __init__(self, name, id=None):
        super().__init__(name, id)
        self.metadata = Metadata()

    def get_api_path(self):
        return self._get_api_base() + '/policy/' + self._get_resource_suffix()


class ContainedPolicyResource(PolicyResource):
    def __init__(self, name, container, id = None):
        super().__init__(name, id)
        self.container = container

    def get_api_path(self):
        return self.container.get_api_path() + '/' + self.container.id + '/' + self._get_resource_suffix()

    @staticmethod
    def json_ignore_attrs():
        return ['container']

class Device(NamedResource):
    def __init__(self, name, id=None):
        super().__init__(name, id)
        self.metadata = Metadata()

    def get_api_path(self):
        return self._get_api_base() + '/devices/' + self._get_resource_suffix()
