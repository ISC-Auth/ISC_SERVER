from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^applications/$', views.applications, name='applications'),
    url(r'^applications/add/$', views.add_applications, name='add_applications'),
    url(r'^get_applications', views.get_applications, name='get_applications'),
    url(r'^applications/detail/$', views.app_detail , name='app_detail'),
    url(r'^applications/delete',views.delete_applications, name='delete_applications'),
    url(r'^users/$', views.users, name='users'),
    url(r'^users/add/$', views.add_users, name='add_users'),
    url(r'^get_users', views.get_users, name='get_users'),
    url(r'^users/detail/$', views.users_detail , name='users_detail'),
    url(r'^users/delete',views.delete_user, name= 'delete_users'),
    url(r'^groups/$', views.groups, name='groups'),
    url(r'^groups/add/$', views.add_groups, name='add_groups'),
    url(r'^get_groups', views.get_groups, name='get_groups'),
    url(r'^groups/detail/$', views.groups_detail , name='groups_detail'),
    url(r'^groups/delete',views.delete_groups, name= 'delete_groups'),
]