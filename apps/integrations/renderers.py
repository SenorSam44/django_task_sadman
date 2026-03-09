from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """
    Wraps all non-paginated responses in {data, errors, meta}.
    Paginated responses are already wrapped by EnvelopePagination and pass through unchanged.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # Let the exception handler's envelope pass through untouched
        if response is not None and response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        # Paginated responses are already in envelope form — don't double-wrap
        if (
            isinstance(data, dict)
            and "data" in data
            and "meta" in data
            and "errors" in data
        ):
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {"data": data, "errors": [], "meta": None}
        return super().render(envelope, accepted_media_type, renderer_context)
