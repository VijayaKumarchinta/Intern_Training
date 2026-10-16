from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"

    @classmethod
    def values(cls):
        return {r.value for r in cls}

    @classmethod
    def is_valid(cls, value):
        return value in cls.values()
