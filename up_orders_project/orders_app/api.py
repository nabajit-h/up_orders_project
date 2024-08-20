from tastypie.api import Api

from orders_app.resources import UserResource, CustomUserResource, StoreResource, ItemResource

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(CustomUserResource())
v1_api.register(StoreResource())
v1_api.register(ItemResource())