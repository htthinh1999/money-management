import json


class BaseModel:
    def __init__(self, dict):
        self.__dict__ = dict

    def __str__(self):
        return json.dumps(self.__dict__)
