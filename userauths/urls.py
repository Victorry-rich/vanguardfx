from django.urls import path, include
from userauths import views

app_name = "userauths"

urlpatterns = [
    path('user/sign-up/', views.register_view, name= "sign-up"),
    path('user/sign-in/', views.login_view, name="sign-in"),
    path('get_user_data/', views.get_user_data, name='get_user_data'),
    path('get_total_deposit/', views.get_total_deposit, name='get_total_deposit'),
    path('trigger_daily_task/', views.trigger_daily_task, name='trigger_daily_task'),
    path('otp', views.otp_view, name="otp"),
    path('recover_password', views.recover_password, name="recover-password"),
    path('logout', views.logout_view, name="logout"),
    path('lockscreen', views.lock_screen_view, name='lockscreen'),
]

