from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.http import HttpNotFound
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse

from orders_app.models import User, CustomUser
from orders_app.resources.user_resource import UserResource
from orders_app.authentication import JWTAuthentication

class CustomUserResource(ModelResource):
    user = fields.OneToOneField(UserResource, 'user', full=True)

    class Meta:
        queryset = CustomUser.objects.all()
        resource_name = 'custom_user'
        allowed_methods = ['get', 'put', 'delete']
        list_allowed_methods = []
        authentication = JWTAuthentication()
        authorization = Authorization()
        include_resource_uri = False

    def prepend_urls(self):
        return [
            url(r'^custom_user/get/$', self.wrap_view('get_custom_user'), name='get_custom_user'),
            url(r'^custom_user/update/$', self.wrap_view('update_custom_user'), name='update_custom_user'),
            url(r'^custom_user/delete/$', self.wrap_view('delete_custom_user'), name='delete_custom_user'),
        ]
    
    def get_custom_user(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)

        try:
            custom_user = CustomUser.objects.get(user=request.user)
        except CustomUser.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Custom user not found."))
        
        bundle = self.build_bundle(obj=custom_user, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def update_custom_user(self, request, **kwargs):
        self.method_check(request, ['patch'])
        self.is_authenticated(request)

        data = self.deserialize(
            request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json')
        )

        try:
            user = User.objects.get(username=request.user.username)
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                user.email = data['email']
            user.save()
            custom_user = CustomUser.objects.get(user=request.user)
            if 'first_name' in data:
                custom_user.first_name = data['first_name']
            if 'last_name' in data:
                custom_user.last_name = data['last_name']
            custom_user.save()
        except User.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("User not found."))
        except CustomUser.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Custom user not found."))
        
        bundle = self.build_bundle(obj=custom_user, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def delete_custom_user(self, request, **kwargs):
        self.method_check(request, ['delete'])
        self.is_authenticated(request)

        try:
            user = User.objects.get(username=request.user.username)
            user.delete()
        except User.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("User not found."))
        except CustomUser.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Custom user not found."))
        
        return self.create_response(
            request,
            {
                'success': True
            },
            status=200
        )
        