from fmc_rest_client.core.base_resources import *

"""
{
  "type": "AccessPolicy",
  "name": "AccessPolicy1",
  "description": "policy to test FMC implementation",
  "defaultAction": {
    "type": "AccessPolicyDefaultAction",
    "logBegin": "false",
    "logEnd": "false",
    "sendEventsToFMC": "false",
    "action": "3"
  }
}
"""
class AccessPolicy(PolicyResource):
    def __init__(self, name=None, default_action='TRUST', desc=None):
        super().__init__(name)
        self.name = name
        self.description = desc
        self.defaultAction = AccessPolicyDefaultAction(default_action)


class AccessPolicyDefaultAction(BaseContainedResource):
    def __init__(self, action='TRUST', log_begin=True, log_end=False):
        super()
        self.logBegin = log_begin
        self.logEnd = log_end
        self.sendEventsToFMC = False
        self.action = action

class AccessRuleMetadata(Metadata):
    def __init__(self, ruleIndex=-1, accessPolicy:ReferenceType=None, domain:ReferenceType=None, readOnly: ReadOnly=None):
        super().__init__(domain, readOnly)
        if accessPolicy:
            self.accessPolicy = accessPolicy
        else: #set so that json_load can find the type
            self.accessPolicy = ReferenceType(None)
        self.section = 'Mandatory'
        self.category = None
        self.ruleIndex = ruleIndex

    
"""
{
  "action": "ALLOW",
  "enabled": true,
  "type": "AccessRule",
  "name": "Rule1",
  "sendEventsToFMC": false,
  "logFiles": false,
  "logBegin": false,
  "logEnd": false,
  "variableSet": {
    "name": "Default Set",
    "id": "VariableSetUUID",
    "type": "VariableSet"
  }
}

"""
class AccessRule(ContainedPolicyResource):
    bulk_operations = ['POST']

    def __init__(self, name=None, container=None):
        super().__init__(name, container)
        self.name = name
        self.action = 'ALLOW' 
        self.sendEventsToFMC = False
        self.logBegin = False
        self.logEnd = False
        self.enabled = True
        self.newComments = []
        self.sourceZones = {'objects': [] }
        self.destinationZones = { 'objects': [] }
        self.sourceNetworks = { 'objects': [] , 'literals': [] }
        self.destinationNetworks = { 'objects': [], 'literals': [] }
        self.sourcePorts = { 'objects':  [] }
        self.destinationPorts = { 'objects': [] }
        self.metadata = AccessRuleMetadata()

    def json_load(self, json):
        super().json_load(json)
        if self.metadata.accessPolicy.id:
            self.container = AccessPolicy()
            self.container.id = self.metadata.accessPolicy.id

class IntrusionPolicy(PolicyResource):

    def __init__(self, name=None):
        super().__init__(name)
        self.name = name
