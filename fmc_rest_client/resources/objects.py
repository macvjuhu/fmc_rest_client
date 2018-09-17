from fmc_rest_client.core.base_resources import *

class ObjectGroupResource(ObjectResource):
    def __init__(self, name=None, objects=None, id=None):
        super().__init__(name, id)
        if objects is None:
            objects = []
        self.objects = objects

class SecurityZone(ObjectResource):
    def __init__(self, name=None, interface_mode=None, desc=None):
        super().__init__(name)
        self.interfaceMode = interface_mode
        self.description = desc
        self.interfaces = []


class InterfaceGroup(SecurityZone):
    def __init__(self, name=None, interface_mode=None, desc=None):
        super().__init__(name, interface_mode, )
        self.interfaceMode = interface_mode
        self.description = desc
        self.interfaces = []


class Network(ObjectResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, value=None):
        super().__init__(name)
        self.value = value


class Host(ObjectResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, value=None):
        super().__init__(name)
        self.value = value


class Range(ObjectResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, value=None):
        super().__init__(name)
        self.value = value


class NetworkGroup(ObjectGroupResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, objects=None):
        super().__init__(name, objects)


class Port(ObjectResource):
    def __init__(self, name=None, protocol=None, desc=None):
        super().__init__(name)
        self.protocol = protocol
        self.description = desc


class ProtocolPortObject(Port):
    bulk_operations = ['POST']
    def __init__(self, name=None, protocol='tcp', port='1-65535', desc=None):
        super().__init__(name, protocol, desc)
        self.port = port


class ICMPPortObject(Port):
    def __init__(self, name=None, protocol=None, type=None, code=None, desc=None):
        super().__init__(name, protocol, desc)
        self.icmpType = type
        self.code = code

    @staticmethod
    def json_ignore_attrs():
        return ['protocol']


class ICMPV4Object(ICMPPortObject):
    bulk_operations = ['POST']
    def __init__(self, name=None, type=None, code=None, desc=None):
        super().__init__(name, 'icmpv4', type, code, desc)


class ICMPV6Object(ICMPPortObject):
    bulk_operations = ['POST']
    def __init__(self, name=None, type=None, code=None, desc=None):
        super().__init__(name, 'icmpv6', type, code, desc)


class PortObjectGroup(ObjectGroupResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, objects=None, desc=None):
        super().__init__(name, objects)
        self.description = desc

        
class Url(ObjectResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, url=None, desc=None):
        super().__init__(name)
        self.url = url
        self.description = desc

        
class UrlGroup(ObjectGroupResource):
    bulk_operations = ['POST']
    def __init__(self, name=None, objects=None, literals=None, desc=None):
        super().__init__(name)
        self.objects = objects
        self.literals = literals
        self.description = desc
        

class SecurityGroupTag(ObjectResource):
    def __init__(self, name=None, tag=None, desc=None):
        super().__init__(name)
        self.tag = tag
        self.description = desc

class VariableSet(ObjectResource):
    def __init__(self, name=None):
        super().__init__(name)
