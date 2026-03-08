from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('payment-dashboard/', views.payment_dashboard, name='payment_dashboard'),
    path('start-recording/', views.start_recording, name='start_recording'),
    path('recording-room/', views.recording_room, name='recording_room'),
    path('api/meeting-status/', views.meeting_status_api, name='meeting_status_api'),
    path('api/leave-meeting/', views.leave_meeting_api, name='leave_meeting_api'),
    path('api/next-script/', views.next_script_api, name='next_script_api'),
    path('api/done-script/', views.done_script_api, name='done_script_api'),
]
