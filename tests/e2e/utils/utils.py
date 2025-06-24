"""Unsorted utility functions to be used from other sources and test step definitions."""

from typing import Any

import jsonschema


def validate_json(message: Any, schema: Any) -> None:
    """Check the JSON message with the given schema."""
    try:
        jsonschema.validate(
            instance=message,
            schema=schema,
        )

    except jsonschema.ValidationError as e:
        assert False, "The message doesn't fit the expected schema:" + str(e)

    except jsonschema.SchemaError as e:
        assert False, "The provided schema is faulty:" + str(e)
