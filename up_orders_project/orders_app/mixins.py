from orders_app.models import User, CustomUser

class CustomUserMixin:
    def get_custom_user(self, username):
        user = User.objects.get(username=username)
        custom_user = CustomUser.objects.get(user=user)
        return custom_user