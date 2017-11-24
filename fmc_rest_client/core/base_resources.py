import inspect
import json
import logging

from fmc_rest_client.core.pluralize import pluralize

logger = logging.getLogger('FMC_REST_CLIENT')

class ObjectJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return self.default(obj.to_json())
        elif hasattr(obj, '__dict__'):
            d = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('__') and not (hasattr(obj, 'hide_in_json')
                                                     and obj.hide_in_json(key)) and value:
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


def json_dump(obj, pretty=True):
    indent = None
    sort_keys = False
    separators = (',', ': ')
    if pretty:
        indent = 2
        sort_keys = True
        separators = None
    return json.dumps(obj, cls=ObjectJSONEncoder, indent=indent, separators=separators, sort_keys=sort_keys)

class ReferenceType:
    """
    Class to represent reference in a Resource,
    Used for json encoding of references to keep only data required for reference
    """
    def __init__(self, obj):
        self.type = obj.type
        self.id = obj.id
        self.name = obj.name

class BaseResource:
    """
    Base Resource for all resources
    If this resource support bulk API add methods which support bulk operation in
    bulk_operations list. Use following operations - POST, PUT etc.

    """

    bulk_operations = []

    def __init__(self):
        self.type = self.__class__.__name__

    def json(self, pretty=True):
        """ dump the object in json """
        return json_dump(self, pretty)

    def json_load(self, json):
        """ load this object from json """
        pass

    @staticmethod
    def json_ignore_attrs():
        # We use unsupported* variables to indicate the original object is not completely supported.
        return ['unsupported', 'unsupportedText', 'metadata']

    def aggregatted_json_ignore_attrs(self):
        alist = []
        for cls in inspect.getmro(self.__class__):
            if 'json_ignore_attrs' in cls.__dict__:
                alist.extend(cls.json_ignore_attrs())
        return alist

    def hide_in_json(self, attr_name):
        alist = self.aggregatted_json_ignore_attrs()
        # print('Attribute to hide in ' + self.type + ' ' + str(list))
        # print('Attribute ' + attr_name + [' not found.', 'found'][attr_name in list])
        return attr_name in alist

class BaseContainedResource:
    """This is a resource which is used inside a resource but can never be referenced independently."""
    def __init__(self):
        super().__init__()

class BaseReferenceResource(BaseResource):
    """ All REST Resources or URL endpoints should extend from this or its specific sub class"""
    def __init__(self, id=None):
        super().__init__()
        self.id = id

    def _get_resource_suffix(self):
        return pluralize(self.type).lower()

    def _get_api_base(self):
        return '/api/fmc_config/v1/domain/{DOMAIN}'

class NamedResource(BaseReferenceResource):
    def __init__(self, name, id=None):
        super().__init__(id)
        self.name = name

    def json_load(self, json):
        # print('json to load ' + str(json))
        self.id = json['id']
        self.type = json['type']
        self.name = json['name']
        if 'metadata' in json:
            self.metadata = json['metadata']

class ObjectResource(NamedResource):
    def __init__(self, name, id=None):
        super().__init__(name, id)

    def get_api_path(self):
        return self._get_api_base() + '/object/' + self._get_resource_suffix()


class PolicyResource(NamedResource):
    def __init__(self, name, id=None):
        super().__init__(name, id)

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


