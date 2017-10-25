from fmc_rest_client.core.base_resources import PolicyResource


class FtdNatPolicy(PolicyResource):
    def __init__(self, name=None, desc=None):
        super().__init__(name)
        self.name = name
        self.description = desc
