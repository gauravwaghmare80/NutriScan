from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile management
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Nutrition features
    path('nutrition/search/', views.get_nutrition, name='get_nutrition'),
    path('bmi-bmr/', views.bmi_bmr_calculator, name='bmi_bmr_calculator'),
    path('diet-plan/', views.personalized_diet_plan, name='personalized_diet_plan'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

]