from django.urls import path
from . import views, api

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    
    path('api/employees/', api.EmployeeListApi, name='api_employee_list'),
    path('api/employees/<int:id>/', api.EmployeeDetailApi, name='api_employee_detail'),
]
