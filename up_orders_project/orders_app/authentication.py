from django.contrib.auth.models import User
from tastypie.authentication import Authentication
from tastypie.http import HttpBadRequest
import jwt
from tastypie.exceptions import ImmediateHttpResponse

class JWTAuthentication(Authentication):
    def _get_token_from_header(self, request):
        """Extracts token from request header"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        return auth_header
    
    def is_authenticated(self, request, **kwargs):
        """Checks if the user who requested is authenticated"""
        token = self._get_token_from_header(request=request)
        if not token:
            raise ImmediateHttpResponse(response=HttpBadRequest('Token is required.'))
        try:
            decoded_payload = jwt.decode(
                jwt=token,
                key="hakuna matata",
                algorithms="HS256"
            )
            user = User.objects.get(pk=decoded_payload['id'])
            if user:
                request.user = user
                return True
            else:
                return False
        except Exception as e:
            return False
        
    def get_identifier(self, request):
        return self._get_token_from_header(request=request) or "anonymous"
