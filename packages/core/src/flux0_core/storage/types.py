from enum import Enum


class StorageType(Enum):
    NANODB = "nanodb"
    MONGODB = "mongodb"


class NanoDBStorageType(Enum):
    MEMORY = "nanodb_memory"
    JSON = "nanodb_json"
