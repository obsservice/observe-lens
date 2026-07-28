from enum import StrEnum


class KnowledgeBaseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class DocumentType(StrEnum):
    GUIDE = "GUIDE"
    SOP = "SOP"
    CASE = "CASE"
    REFERENCE = "REFERENCE"
    OTHER = "OTHER"


class DocumentSourceType(StrEnum):
    UPLOAD = "UPLOAD"
    URL = "URL"
    API = "API"


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    REINDEXING = "REINDEXING"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class IndexTaskType(StrEnum):
    INDEX = "INDEX"
    REINDEX = "REINDEX"
    DELETE = "DELETE"


class IndexTaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class RetrievalFeedbackType(StrEnum):
    RELEVANT = "RELEVANT"
    IRRELEVANT = "IRRELEVANT"
    OUTDATED = "OUTDATED"
