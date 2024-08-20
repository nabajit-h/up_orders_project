from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.http import HttpNotFound, HttpUnauthorized
from tastypie.http import HttpApplicationError
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse

from orders_app.models import CustomUser, Store
from orders_app.mixins import CustomUserMixin
from orders_app.authentication import JWTAuthentication
from orders_app.authorization import RoleBasedAuthorization

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
