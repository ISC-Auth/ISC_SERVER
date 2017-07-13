from django.conf.urls import url,include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^',include('isc_auth.urls')),
    url(r'^',include('users.urls')),
]
