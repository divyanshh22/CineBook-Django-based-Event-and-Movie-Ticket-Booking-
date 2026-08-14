from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """Return a consistent JSON error shape for every API error.

    Success/error responses are standardised as:
        { "detail": "human readable message" }

    Validation errors keep DRF's field-keyed shape:
        { "field_name": ["message", ...] }
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    data = response.data
    if isinstance(data, dict) and "detail" not in data and "non_field_errors" not in data:
        # Already field-keyed validation data; leave as-is but ensure it is a dict
        return response

    response.data = {"detail": data}
    return response
