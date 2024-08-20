from tastypie.resources import ModelResource
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.authentication import Authentication
from tastypie.http import HttpBadRequest, HttpCreated, HttpNotFound, HttpUnauthorized
from tastypie.http import HttpApplicationError, HttpForbidden
from tastypie.models import ApiKey
from django.conf.urls import url
import jwt
from datetime import datetime, timedelta
import pytz
from tastypie.exceptions import ImmediateHttpResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from orders_app.models import CustomUser, Store, Item
from orders_app.mixins import CustomUserMixin

class JWTAuthentication(Authentication):
    def _get_token_from_header(self, request):
        """Extracts token from request header"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)
        return auth_header
    
    def is_authenticated(self, request, **kwargs):
        """Checks if the user who requested is authenticated"""
        print("===authentication===")
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

class RoleBasedAuthorization(Authorization):
    def __init__(self, required_role):
        self.required_role = required_role

    def is_authorized(self, request):
        print("===authorization===")
        username = request.user
        custom_user = CustomUser.objects.get(user__username=username)
        print(custom_user.role)
        return custom_user.role == self.required_role
    
    def create_detail(self, object_list, bundle):
        if not self.is_authorized(bundle.request):
            raise Unauthorized("You do not have permission.")
        return True
    
    def read_list(self, object_list, bundle):
        if not self.is_authorized(bundle.request):
            raise Unauthorized("You do not have permission.")
        return True
    
    def read_detail(self, object_list, bundle):
        if not self.is_authorized(bundle.request):
            raise Unauthorized("You do not have permission.")
        return True
    
    def update_detail(self, object_list, bundle):
        if not self.is_authorized(bundle.request):
            raise Unauthorized("You do not have permission.")
        return True
    
    def delete_detail(self, object_list, bundle):
        if not self.is_authorized(bundle.request):
            raise Unauthorized("You do not have permission.")
        return True

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        allowed_methods = ['get', 'post', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'username': ['exact']
        }

    def prepend_urls(self):
        return [
            url(r'^user/signup/$', self.wrap_view('signup'), name='user_signup'),
            url(r'^user/login/$', self.wrap_view('login'), name='user_login'),
        ]
    
    def generate_token(self, user_id, role):
        IST = pytz.timezone('Asia/Kolkata')
        return jwt.encode(
            payload={
                'id': user_id,
                'role': role,
                'exp': datetime.now(IST) + timedelta(days=30),
                'iat': datetime.now(IST)
            },
            key="hakuna matata",
            algorithm='HS256'
        )
    
    def signup(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        data = self.deserialize(
            request, request.body, format=request.META.get('content_type', 'application/json')
        )

        username = data['username']
        password = data['password']
        role = data['role']
        email = data['email']

        if User.objects.filter(username=username).exists():
            raise ImmediateHttpResponse(response=HttpBadRequest("Username already exists"))
        
        try:
            validate_email(email)
        except ValidationError:
            raise ImmediateHttpResponse(response=HttpBadRequest("Email is not valid."))

        user = User(username=username, password=password, email=email)
        user.set_password(password)
        user.save()

        custom_user = CustomUser.objects.create(
            user=user,
            name=username,
            role=role
        )
        token = self.generate_token(user_id=user.id, role=custom_user.role)
        return self.create_response(
            request,
            {
                'success': True,
                'access_token': token
            },
            response_class=HttpCreated
        )
    
    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        data = self.deserialize(
            request, request.body, format=request.META.get('content_type', 'application/json')
        )

        username = data['username']
        password = data['password']

        existing_user = authenticate(username=username, password=password)
        if not existing_user:
            raise ImmediateHttpResponse(response=HttpNotFound("User not found."))
        
        custom_user = CustomUser.objects.get(user__username=username)
        token = self.generate_token(user_id=existing_user.id, role=custom_user.role)

        return self.create_response(
            request,
            {
                'success': True,
                'access_token': token
            },
            status=200
        )

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
    
class StoreResource(ModelResource, CustomUserMixin):
    # merchant = fields.ForeignKey(CustomUser, 'merchant')

    class Meta:
        queryset = Store.objects.all()
        resource_name = 'store'
        allowed_methods = ['get', 'post', 'put', 'delete']
        list_allowed_methods = ['get']
        authentication = JWTAuthentication()
        authorization = Authorization()
        include_resource_uri = False
        limit = 20
        filtering = {
            'merchant': ['exact'],
            'name': ['exact', 'icontains']
        }
        excludes = ['merchant']

    def prepend_urls(self):
        return [
            url(r"^store/create/$", self.wrap_view('create_store'), name='create_store'),
            url(r"^store/get/many/$", self.wrap_view('get_stores'), name='get_stores'),
            url(r"^store/get/(?P<pk>.*?)/$", self.wrap_view('get_store_detail'), name='get_store_detail'),
            url(r"^store/(?P<pk>.*?)/update/$", self.wrap_view('update_store'), name='update_store'),
            url(r"^store/(?P<pk>.*?)/delete/$", self.wrap_view('delete_store'), name='delete_store'),
        ]
    
    def create_store(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        
        data = self.deserialize(
            request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
        )
        custom_user = CustomUser.objects.get(user__username=request.user)
        name = data['name']
        address = data['address']
        merchant = custom_user

        store = Store.objects.create(
            name=name,
            address=address,
            merchant=merchant
        )

        bundle = self.build_bundle(obj=store, request=request)
        bundle = self.full_dehydrate(bundle)
        
        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=201
        )
    
    def get_stores(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        stores = Store.objects.all()
        bundles = [self.build_bundle(obj=store, request=request) for store in stores]
        bundles = [self.full_dehydrate(bundle) for bundle in bundles]

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundles
            },
            status=200
        )
    
    def get_store_detail(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        pk = kwargs.get('pk', None)

        try:
            store = Store.objects.get(pk=pk)
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))
        
        bundle = self.build_bundle(obj=store, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def update_store(self, request, **kwargs):
        self.method_check(request, ['patch'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        pk = kwargs.get('pk', None)
        data = self.deserialize(
            request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
        )
        name = data['name']
        address = data['address']

        try:
            store = Store.objects.get(pk=pk, merchant__user__username=request.user)
            # if store.merchant.user.username != request.user:
            #     return self.create_response(
            #         request,
            #         {
            #             'success': False,
            #             'error_msg': "You are not authroized to perform this action."
            #         }
            #     )
            store.name = name
            store.address = address
            store.save()
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))

        bundle = self.build_bundle(obj=store, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def delete_store(self, request, **kwargs):
        self.method_check(request, ['delete'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        
        pk = kwargs.get('pk', None)

        try:
            store = Store.objects.get(pk=pk, merchant__user__username=request.user)
            store.delete()
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))
        except:
            raise ImmediateHttpResponse(response=HttpApplicationError("Could not delete."))
        

        return self.create_response(
            request,
            {
                'success': True
            },
            status=202
        )

class ItemResource(ModelResource, CustomUserMixin):
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        queryset = Item.objects.all()
        resource_name = 'item'
        allowed_methods = ['get', 'post', 'put', 'delete']
        list_allowed_methods = ['get']
        authentication = JWTAuthentication()
        authorization = Authorization()
        include_resource_uri = False
        limit = 20
        filtering = {
            'store': ['exact'],
            'name': ['exact', 'icontains']
        }
        excludes = ['store']

    def prepend_urls(self):
        return [
            url(r"^item/create/$", self.wrap_view('create_item'), name='create_item'),
            url(r"^item/get/many/$", self.wrap_view('get_items'), name='get_items'),
            url(r"^item/get/(?P<pk>.*?)/$", self.wrap_view('get_item_detail'), name='get_item_detail'),
            url(r"^item/(?P<pk>.*?)/update/$", self.wrap_view('update_item'), name='update_item'),
            url(r"^item/(?P<pk>.*?)/delete/$", self.wrap_view('delete_item'), name='delete_item'),
        ]
    
    def create_item(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        
        data = self.deserialize(
            request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
        )
        # custom_user = CustomUser.objects.get(user__username=request.user)
        name = data['name']
        category = data['category']
        price = data['price']
        store_id = data['store_id']

        try:
            store = Store.objects.get(pk=store_id, merchant__user__username=request.user)
            item = Item.objects.create(
                name=name,
                category=category,
                price=price,
                store=store
            )
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))

        bundle = self.build_bundle(obj=item, request=request)
        bundle = self.full_dehydrate(bundle)
        
        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=201
        )
    
    def get_items(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        items = Item.objects.all()
        bundles = [self.build_bundle(obj=item, request=request) for item in items]
        bundles = [self.full_dehydrate(bundle) for bundle in bundles]

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundles
            },
            status=200
        )
    
    def get_item_detail(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        pk = kwargs.get('pk', None)

        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Item not found."))
        
        bundle = self.build_bundle(obj=item, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def update_item(self, request, **kwargs):
        self.method_check(request, ['patch'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        pk = kwargs.get('pk', None)
        data = self.deserialize(
            request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
        )
        name = data['name']
        category = data['category']
        price = data['price']
        store_id = data['store_id']

        try:
            store = Store.objects.get(pk=store_id, merchant__user__username=request.user)
            item = Item.objects.get(pk=pk, store=store)
            # if store.merchant.user.username != request.user:
            #     return self.create_response(
            #         request,
            #         {
            #             'success': False,
            #             'error_msg': "You are not authroized to perform this action."
            #         }
            #     )
            item.name = name
            item.category = category
            item.price = price
            item.save()
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))
        except Item.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Item not found."))

        bundle = self.build_bundle(obj=item, request=request)
        bundle = self.full_dehydrate(bundle)

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    def delete_item(self, request, **kwargs):
        self.method_check(request, ['delete'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Merchant")
        if not authorization.is_authorized(request=request):
            return ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        
        pk = kwargs.get('pk', None)

        try:
            # store = Store.objects.get(pk=pk, merchant__user__username=request.user)
            item = Item.objects.get(pk=pk)
            item.delete()
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Store not found."))
        except:
            raise ImmediateHttpResponse(response=HttpApplicationError("Could not delete."))
        

        return self.create_response(
            request,
            {
                'success': True
            },
            status=202
        )

    
