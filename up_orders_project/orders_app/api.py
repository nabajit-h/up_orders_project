from tastypie.api import Api

from orders_app.resources.user_resource import UserResource
from orders_app.resources.custom_user_resource import CustomUserResource
from orders_app.resources.store_resource import StoreResource
from orders_app.resources.item_resource import ItemResource
from orders_app.resources.order_resource import OrderResource

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(CustomUserResource())
v1_api.register(StoreResource())
v1_api.register(ItemResource())
v1_api.register(OrderResource())