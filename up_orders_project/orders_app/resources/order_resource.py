from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from django.conf.urls import url
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpUnauthorized, HttpNotFound
from tastypie import fields

from orders_app.models import Order, CustomUser, Store, Item, OrderItem
from orders_app.authentication import JWTAuthentication
from orders_app.authorization import RoleBasedAuthorization
from orders_app.resources.custom_user_resource import CustomUserResource
from orders_app.resources.store_resource import StoreResource
from orders_app.resources.item_resource import ItemResource
from orders_app.tasks import generate_order

class OrderResource(ModelResource):
    customer = fields.ForeignKey(CustomUserResource, 'customer')
    merchant = fields.ForeignKey(CustomUserResource, 'merchant')
    store = fields.ForeignKey(StoreResource, 'store')
    items = fields.ManyToManyField(ItemResource, 'items', full=True)

    class Meta:
        queryset = Order.objects.all()
        resource_name = 'order'
        allowed_methods = ['get', 'post', 'patch', 'delete']
        list_allowed_methods = ['get']
        authentication = JWTAuthentication()
        authorization = Authorization()
        include_resource_uri = False

    def prepend_urls(self):
        return [
            url(r"^order/create/$", self.wrap_view('create_order'), name='create_order'),
            url(r"^order/get/many/$", self.wrap_view('get_orders'), name='get_orders'),
            url(r"^order/get/(?P<pk>.*?)/$", self.wrap_view('get_order_detail'), name='get_order_detail'),
            # url(r"^order/(?P<pk>.*?)/update/$", self.wrap_view('update_order'), name='update_order'),
            url(r"^order/(?P<pk>.*?)/delete/$", self.wrap_view('delete_order'), name='delete_order'),
        ]
    
    def create_order(self, request, **kwargs):
        """
        It creates an Order made by a Customer. Allows only HTTP POST method.
        An Order will have a Customer, a Store and a list of Items.
        An Order will have items from a single Store only.
        """
        self.method_check(request, ['post'])
        self.is_authenticated(request)

        authorization = RoleBasedAuthorization("Customer")
        if not authorization.is_authorized(request):
            raise ImmediateHttpResponse(HttpUnauthorized("You are unauthorized to perform this action."))
        
        data = self.deserialize(
            request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
        )

        try:
            customer = CustomUser.objects.get(user=request.user)
            data['user_id'] = customer.id
            print(data)
            generate_order.delay(data)

            # order = Order.objects.create(
            #     customer=customer,
            #     merchant=store.merchant,
            #     store=store,
            #     bill_amount=bill_amount
            # )

            # order_items = []
            # for item in data['items']:
            #     item_obj = Item.objects.get(pk=item['id'])
            #     order_items.append(OrderItem(order=order, item=item_obj))

            # OrderItem.objects.bulk_create(order_items)

            # bundle = self.build_bundle(obj=order, request=request)
            # bundle = self.full_dehydrate(bundle)
            
        except Store.DoesNotExist:
            raise ImmediateHttpResponse(HttpNotFound("Store not found."))
        
        return self.create_response(
            request,
            {
                'success': True
            },
            status=201
        )
    
    def get_orders(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        try:
            filters = {}

            for key, value in request.GET.items():
                if key in self.Meta.filtering:
                    filters[key] = value

            orders = Order.objects.filter(**filters)
            
            bundles = [self.build_bundle(obj=order, request=request) for order in orders]
            bundles = [self.full_dehydrate(bundle) for bundle in bundles]

        except Order.DoesNotExist:
            raise ImmediateHttpResponse(HttpNotFound("Order not found."))

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundles
            },
            status=200
        )
    
    def get_order_detail(self, request, **kwargs):
        self.method_check(request, ['get'])
        self.is_authenticated(request)

        pk = kwargs.get('pk')

        try:
            order = Order.objects.get(pk=pk)
            
            bundle = self.build_bundle(obj=order, request=request)
            bundle = self.full_dehydrate(bundle)
        except Order.DoesNotExist:
            raise ImmediateHttpResponse(HttpNotFound("Order not found."))

        return self.create_response(
            request,
            {
                'success': True,
                'data': bundle
            },
            status=200
        )
    
    # def update_order(self, request, **kwargs):
    #     self.method_check(request, ['get'])
    #     self.is_authenticated(request)

    #     pk = kwargs.get('pk')

    #     data = self.deserialize(
    #         request, request.body, format=request.META.get("CONTENT_TYPE", "application/json")
    #     )

    #     try:
    #         order = Order.objects.get(pk=pk)
            
    #     except Order.DoesNotExist:
    #         raise ImmediateHttpResponse(HttpNotFound("Order not found."))

    #     return self.create_response(
    #         request,
    #         {
    #             'success': True
    #         },
    #         status=200
    #     )
    
    def delete_order(self, request, **kwargs):
        self.method_check(request, ['delete'])
        self.is_authenticated(request)

        pk = kwargs.get('pk')

        try:
            order = Order.objects.get(pk=pk)
            order.delete()
        except Order.DoesNotExist:
            raise ImmediateHttpResponse(HttpNotFound("Order not found."))

        return self.create_response(
            request,
            {
                'success': True
            },
            status=202
        )
