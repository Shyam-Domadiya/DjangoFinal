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
    path('activate/<uidb64>/<token>/', views.activate_email, name='activate_email'),
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
    path('tweet/<int:tweet_id>/pin/', views.pin_tweet, name='pin_tweet'),
    path('tweet/<int:tweet_id>/unpin/', views.unpin_tweet, name='unpin_tweet'),
    path('ajax/refresh/', views.refresh_content, name='refresh_content'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('media/upload/', views.upload_media, name='upload_media'),
    path('media/<int:media_id>/delete/', views.delete_media, name='delete_media'),
    path('media/user/', views.get_user_media, name='get_user_media'),
    path('media/<int:media_id>/tweets/', views.get_media_tweets, name='get_media_tweets'),
    path('tweet/<int:tweet_id>/edit-history/', views.get_tweet_edit_history, name='get_tweet_edit_history'),
    path('search/', views.search, name='search'),
    path('draft/save/', views.save_draft, name='save_draft'),
    path('draft/get/', views.get_draft, name='get_draft'),
    path('draft/clear/', views.clear_draft, name='clear_draft'),
    path('draft/restore/', views.restore_draft, name='restore_draft'),
    path('scheduled-tweets/', views.get_scheduled_tweets, name='get_scheduled_tweets'),
    path('tweet/<int:tweet_id>/cancel-schedule/', views.cancel_scheduled_tweet, name='cancel_scheduled_tweet'),
    path('admin/publish-scheduled/', views.publish_scheduled_tweets_manual, name='publish_scheduled_tweets_manual'),
    
    # ========================================================================
    # PASSWORD RESET URLS - PRODUCTION GRADE WITH HTTPS SUPPORT
    # ========================================================================
    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
]