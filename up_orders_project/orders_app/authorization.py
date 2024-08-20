from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from orders_app.models import CustomUser

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
