from enum import Enum, auto

class NodeType(Enum):
    SERVICE = "SERVICE"
    FILE = "FILE"
    FUNCTION = "FUNCTION"
    API_ENDPOINT = "API_ENDPOINT"
    DB_TABLE = "DB_TABLE"
    TEAM = "TEAM"
    CI_JOB = "CI_JOB"

class EdgeType(Enum):
    IMPORTS = "IMPORTS"            # File -> File / Module
    CALLS_FUNCTION = "CALLS_FUNCTION" # Function -> Function
    CALLS_API = "CALLS_API"        # Function -> API_ENDPOINT
    QUERIES = "QUERIES"            # Function -> DB_TABLE
    DEFINES = "DEFINES"            # File -> Function / API_ENDPOINT / DB_TABLE
    BELONGS_TO = "BELONGS_TO"      # Function -> File -> Service
    TESTS = "TESTS"                # File (Test) -> Function / Service
    OWNS = "OWNS"                  # Team -> Service
    COVERS = "COVERS"              # CI_JOB -> Service
