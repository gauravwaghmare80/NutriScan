from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home, get_nutrition, register, dashboard, user_logout, user_login
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('get-nutrition/', get_nutrition, name='get_nutrition'),
    path('register/', register, name='register'),
    path('login/', user_login , name='login'),
    path('logout/', user_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
]


urlpattern2 = [
    # path('', views.home, name='home'),
    path('bmi-bmr/', views.bmi_bmr_calculator, name='bmi_bmr_calculator'),
]

urlpatterns += urlpattern2
