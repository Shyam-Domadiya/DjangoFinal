from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tweets/', views.tweet_List, name='tweet_list'),
    path('create/', views.tweet_Create, name='tweet_create'),
    path('<int:tweet_id>/delete', views.Tweet_Delete, name='tweet_delete'),
    path('<int:tweet_id>/edit', views.Tweet_Edit, name='tweet_edit'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
]