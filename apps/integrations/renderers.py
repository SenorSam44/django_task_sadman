from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"]

        if response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {"data": data, "errors": [], "meta": None}

        return super().render(envelope, accepted_media_type, renderer_context)
