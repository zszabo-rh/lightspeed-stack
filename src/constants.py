"""Constants used in business logic."""

UNABLE_TO_PROCESS_RESPONSE = "Unable to process this request"

# Supported attachment types
ATTACHMENT_TYPES = frozenset(
    {
        "alert",
        "api object",
        "configuration",
        "error message",
        "event",
        "log",
        "stack trace",
    }
)

# Supported attachment content types
ATTACHMENT_CONTENT_TYPES = frozenset(
    {"text/plain", "application/json", "application/yaml", "application/xml"}
)

# Default system prompt used only when no other system prompt is specified in
# configuration file nor in the query request
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant"

# Data collector constants
DATA_COLLECTOR_COLLECTION_INTERVAL = 7200  # 2 hours in seconds
DATA_COLLECTOR_CONNECTION_TIMEOUT = 30
DATA_COLLECTOR_RETRY_INTERVAL = 300  # 5 minutes in seconds
