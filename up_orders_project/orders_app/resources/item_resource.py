from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.http import HttpNotFound, HttpUnauthorized
from tastypie.http import HttpApplicationError
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse

from orders_app.models import CustomUser, Store, Item
from orders_app.mixins import CustomUserMixin
from orders_app.authentication import JWTAuthentication
from orders_app.authorization import RoleBasedAuthorization
from orders_app.resources.store_resource import StoreResource

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

    
