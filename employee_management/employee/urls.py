"""
URL configuration for employee_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('remove_employee/', views.remove_employee, name='remove_employee'),
    path('remove_employee/<int:employee_id>/', views.remove_employee, name='remove_employee'),
    path('update_employee/', views.update_employee, name='update_employee'),
    path('update_employee/<int:employee_id>/', views.update_employee, name='update_employee'),
    path('view_all_employees/', views.view_all_employees, name='view_all_employees'),
]
