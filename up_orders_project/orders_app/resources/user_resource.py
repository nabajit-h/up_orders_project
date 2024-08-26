from tastypie.resources import ModelResource
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication
from tastypie.http import HttpBadRequest, HttpCreated, HttpNotFound
from django.conf.urls import url
import jwt
from datetime import datetime, timedelta
import pytz
from tastypie.exceptions import ImmediateHttpResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from orders_app.models import CustomUser

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
        first_name = data['first_name']
        last_name = data['last_name']
        password = data['password']
        role = data['role']
        email = data['email']

        if User.objects.filter(username=username).exists():
            raise ImmediateHttpResponse(response=HttpBadRequest("Username already exists"))
        
        try:
            validate_email(email)
        except ValidationError:
            raise ImmediateHttpResponse(response=HttpBadRequest("Email is not valid."))

        user = User(
            username=username, 
            password=password, 
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()

        custom_user = CustomUser.objects.create(
            user=user,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
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
