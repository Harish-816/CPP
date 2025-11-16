from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('crops/create/', views.crop_create_view, name='crop_create'),
    path('crops/<int:pk>/', views.crop_detail_view, name='crop_detail'),
    path('crops/<int:pk>/update/', views.crop_update_view, name='crop_update'),
    path('crops/<int:pk>/delete/', views.crop_delete_view, name='crop_delete'),
    path('crops/<int:pk>/analyze/', views.analyze_crop_view, name='crop_analyze'),
]
