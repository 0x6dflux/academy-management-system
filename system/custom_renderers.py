from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """Adds `status` key in the `response.data` and places the original `response.data` in the `result/s`."""

    def render(
        self,
        data,
        accepted_media_type=None,
        renderer_context=None,
    ) -> bytes:
        # to understand the below line, look at `Response` class codes
        # there is a `rendered_content` property which sets the response object on a
        # dictionary called `context` with `response` key (line 62). this variable is
        # passed as an argument to the `.render()` method.
        response = renderer_context.get("response", None)  # type: ignore

        if isinstance(data, dict) and response is not None:
            data = {"status": response.status_code, "result": data}

        elif isinstance(data, list) and response is not None:
            data = {"status": response.status_code, "results": data}

        return super().render(data, accepted_media_type, renderer_context)
