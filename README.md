## FMC REST CLIENT
Easy to use REST Client for Firepower Management Center REST API

### Features
* Create object for FMC REST resources and perform CRUD operations
* Maintains REST connection with FMC
* Listing for a particular resource type supports fetching all results in single go
* Easy to add support for new resources or url endpoints

### Enhancements in future
* Support for bulk operations, leveraging FMC REST API where available or support in client
* Iterator for list operation
* Get by name

## How to use

### Using REST Client
Create FMCRestClient instance
```
fmc = FMCRestClient(fmc_server_url, username, password)
# create a resource instance
host1 = Host('host1', '1.1.1.1')
# create in FMC
host1 = fmc.create(host1)
# get all Host objects
hosts = fmc.list(Host())
for host in hosts:
    print(host.name)
    print(host.json())
# update value for host1
host1.value = '2.2.2.2'
fmc.update(host1)
# get host1 from FMC
host1 = fmc.load(host1)
print(host1.json())
# delete host1 from FMC
fmc.remove(host1)
```
### Adding a new FMC resource class
To add a new class representing FMC REST API resource, follow the below guideline
 * Class name should be singular name of the FMC REST resource or url endpoint.
 * The class should extend the appropriate base classes defined in 'fmc_rest_client.core.base_resources' module.
 * The member variables name should match the attribute names in json
 * Complex structure or nested attributes in json can be models as dictionary or another object of a class extending BaseContainedResource class.

#### Examples <br>
##### Resource having list attribute
For Network Group object we have following json -
```
{
  "id": "005056A9-0AC2-0ed3-0000-025769807771",
  "name": "nog1",
  "type": "NetworkGroup"
  "objects": {
      "type": "Range",
      "id": "005056A9-0AC2-0ed3-0000-025769808881",
      "name": "range1",
    }
  ],
  "literals": [
    {
      "type": "Network",
      "value": "1.2.3.0/24"
    }
  ]
}

```
A simple resource class for this can be like below -
```
class NetworkGroup(ObjectResource):
    def __init__(self, name=None, objects=None, literals=None):
        super().__init__(name)
        self.objects = objects
        self.literals = literals
```
Or a complex resource class can look like following -
```
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
```
##### Resource with complex structure
Refer AccessPolicy and AccessRule class examples in fmc_rest_client.resources module.
AccessPolicy uses a AccessPolicyDefaultAction for a nested structure for defaultAction field, while AccessRule
uses a dict for field sourceNetworks.

