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

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant"
