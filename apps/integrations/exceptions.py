from rest_framework.views import exception_handler


def envelope_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    errors = []
    if isinstance(response.data, dict):
        for key, value in response.data.items():
            if isinstance(value, list):
                for msg in value:
                    errors.append({"message": str(msg)})
            else:
                errors.append({"message": str(value)})
    else:
        errors.append({"message": str(response.data)})

    response.data = {"data": None, "errors": errors, "meta": None}
    return response
