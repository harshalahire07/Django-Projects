from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('create/', views.employee_create, name='employee_create'),
    path('<int:id>/update/', views.employee_update, name='employee_update'),
    path('<int:id>/delete/', views.employee_delete, name='employee_delete'),
    path('<int:id>/', views.employee_detail, name='employee_detail'),
]
