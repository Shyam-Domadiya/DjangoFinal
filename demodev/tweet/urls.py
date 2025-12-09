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
    path('users/', views.user_list, name='user_list'),
    path('follow/<int:user_id>/', views.send_follow_request, name='send_follow_request'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('follow-requests/', views.follow_requests, name='follow_requests'),
    path('accept-follow/<int:request_id>/', views.accept_follow_request, name='accept_follow_request'),
    path('reject-follow/<int:request_id>/', views.reject_follow_request, name='reject_follow_request'),
    path('tweet/<int:tweet_id>/', views.tweet_detail, name='tweet_detail'),
    path('tweet/<int:tweet_id>/comment/add/', views.add_comment_ajax, name='add_comment_ajax'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('tweet/<int:tweet_id>/like/', views.toggle_like, name='toggle_like'),
    path('tweet/<int:tweet_id>/likes/', views.tweet_likes, name='tweet_likes'),
]