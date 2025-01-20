from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('gccp_api_rest.urls'), name ='gcapi_rest.urls'),
]
