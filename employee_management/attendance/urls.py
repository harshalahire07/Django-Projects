from django.urls import path
from . import api, views

urlpatterns = [
    path('clock-in/', api.clock_in),
    path('clock-out/', api.clock_out),
    path('history/<int:employee_id>/', api.get_attendance),
    path('view/', views.attendance_index),
]

