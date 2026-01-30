from django.test import TestCase, Client
from django.urls import reverse
from .models import Employee, Department, Role
import json

class EmployeeApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="IT")
        self.role = Role.objects.create(name="Developer")
        self.employee = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone=1234567890,
            address="123 Street",
            department=self.dept,
            role=self.role
        )
        self.list_url = reverse('api_employee_list')
        self.detail_url = reverse('api_employee_detail', args=[self.employee.id])

    def test_get_employee_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['first_name'], "John")

    def test_create_employee(self):
        payload = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'phone': 9876543210,
            'address': '456 Avenue',
            'department': self.dept.id,
            'role': self.role.id
        }
        response = self.client.post(
            self.list_url,
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Employee.objects.count(), 2)

    def test_get_employee_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.employee.id)

    def test_update_employee(self):
        payload = {
            'first_name': 'Johnny',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': 1234567890,
            'address': '123 Street',
            'department': self.dept.id,
            'role': self.role.id
        }
        response = self.client.put(
            self.detail_url,
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, 'Johnny')

    def test_delete_employee(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Employee.objects.count(), 0)
