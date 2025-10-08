# planner/urls.py
from django.urls import path
from . import views
from .views import *
from django.contrib.auth import views as auth_views

app_name = "planner"

urlpatterns = [
    path("survey/", views.survey_full_page, name="survey"),
    path('', views.dashboard, name='dashboard'),
    path('activity/', views.activity_page, name='activity'),
    path('summary/', views.summary_page, name='summary'),
    path('login/', login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_now, name='logout'),
    path('favorites/', views.favorites_page, name='favorites'),
    path('favorite_itinerary/<int:itinerary_id>/', views.favorite_itinerary, name='favorite_itinerary'),

    path('password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
]
