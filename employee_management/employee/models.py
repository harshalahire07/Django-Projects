from django.db import models

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100,null=False,blank=False)
    def __str__(self):
        return self.name
class Role(models.Model):
    name = models.CharField(max_length=100,null=False,blank=False)
    def __str__(self):
        return self.name
class Employee(models.Model):
    first_name = models.CharField(max_length=100,null=False,blank=False)
    last_name = models.CharField(max_length=100,null=False,blank=False)
    email = models.EmailField(max_length=100,null=False,blank=False)
    phone = models.IntegerField(null=False,blank=False)
    address = models.CharField(max_length=100,null=False,blank=False)
    department = models.ForeignKey(Department,on_delete=models.CASCADE)
    role = models.ForeignKey(Role,on_delete=models.CASCADE)
    def __str__(self):
        return self.first_name + " " + self.last_name
