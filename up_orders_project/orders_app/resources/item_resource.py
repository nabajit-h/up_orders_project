from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.http import HttpNotFound, HttpUnauthorized
from tastypie.http import HttpApplicationError
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse

from orders_app.models import Store, Item, CustomUser, StoreItem
from orders_app.authentication import JWTAuthentication
from orders_app.authorization import RoleBasedAuthorization
from orders_app.resources.store_resource import StoreResource
from orders_app.resources.custom_user_resource import CustomUserResource

class ItemResource(ModelResource):
    merchant = fields.ForeignKey(CustomUserResource, 'merchant')

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
            'name': ALL,
            'category': ALL,
            'price': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'store': ALL_WITH_RELATIONS,
            'merchant': ALL_WITH_RELATIONS
        }
        limit = 20

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

        try:
            name = data['name']
            description = data['description']
            category = data['category']
            price = data['price']
            store_id = data['store_id']

            custom_user = CustomUser.objects.get(user=request.user)
            store = Store.objects.get(pk=store_id, merchant=custom_user)

            item = Item.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                merchant=custom_user
            )

            StoreItem.objects.create(
                store=store,
                item=item,
                count=20
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

        filters = {}

        for key, value in request.GET.items():
            if key in self.Meta.filtering:
                filters[key] = value

        items = Item.objects.filter(**filters)
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

        try:
            custom_user = CustomUser.objects.get(user=request.user)
            item = Item.objects.get(pk=pk, merchant=custom_user)

            if 'name' in data:
                item.name = data['name']
            if 'description' in data:
                item.description = data['description']
            if 'category' in data:
                item.category = data['category']
            if 'price' in data:
                item.name = data['price']

            item.save()
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
            raise ImmediateHttpResponse(
                response=HttpUnauthorized("You are unauthorized to perform this action.")
            )
        
        pk = kwargs.get('pk', None)

        try:
            custom_user = CustomUser.objects.get(user=request.user)
            item = Item.objects.get(pk=pk, merchant=custom_user)
            item.delete()
        except Item.DoesNotExist:
            raise ImmediateHttpResponse(response=HttpNotFound("Item not found."))
        except:
            raise ImmediateHttpResponse(response=HttpApplicationError("Could not delete."))
        

        return self.create_response(
            request,
            {
                'success': True
            },
            status=202
        )
    

    
