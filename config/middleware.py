class NoCacheHTMLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.headers.get("Content-Type", "").startswith("text/html"):
            response["Cache-Control"] = "no-cache, must-revalidate"
        return response
