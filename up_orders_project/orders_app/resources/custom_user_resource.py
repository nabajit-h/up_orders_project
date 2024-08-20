from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.http import HttpNotFound
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse

from orders_app.models import CustomUser
from orders_app.resources.user_resource import UserResource
from orders_app.authentication import JWTAuthentication

class CustomUserResource(ModelResource):
    user = fields.OneToOneField(UserResource, 'user', full=True)

    class Meta:
        queryset = CustomUser.objects.all()
        resource_name = 'custom_user'
        allowed_methods = ['get', 'post', 'put', 'delete']
        list_allowed_methods = []
        authentication = JWTAuthentication()
        authorization = Authorization()
        include_resource_uri = False

    def prepend_urls(self):
        return [
            url(r'^custom_user/get/(?P<pk>.*?)/$', self.wrap_view('get_custom_user'), name='get_custom_user'),
        ]
    
    def get_custom_user(self, request, **kwargs):
        self.method_check(request, allowed=['get'])

        pk = kwargs.get('pk', None)

        try:
            custom_user = CustomUser.objects.get(user__id=pk)
        except CustomUser.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Custom user not found."))
        
        bundle = self.build_bundle(obj=custom_user, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            bundle,
            status=200
        )
    