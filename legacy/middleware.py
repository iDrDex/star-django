import json, base64

class Web2PyUser(object):
    def process_request(self, request):
        request.user_data = {}

        encoded = request.COOKIES.get('stargeo_user')
        if encoded:
            # Fix base64 alignment
            encoded += '=' * ((-len(encoded)) % 4)
            try:
                request.user_data = json.loads(base64.b64decode(encoded))
            except (TypeError, ValueError):
                pass

