import os
import ast
import inspect
import importlib
from django.test import TestCase
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class ArchitectureGuardrailTests(TestCase):
    def get_all_view_modules(self):
        app_names = ['accounts', 'audit', 'organizations', 'projects', 'tasks', 'web']
        modules = []
        for app in app_names:
            try:
                mod = importlib.import_module(f"apps.{app}.views")
                modules.append((app, mod))
            except ImportError as e:
                print(f"Failed opening {app}: {e}")
                pass
        return modules

    def test_all_api_views_require_authentication(self):
        """Assert that every APIView subclass has IsAuthenticated in its permission_classes."""
        modules = self.get_all_view_modules()
        
        # Endpoints explicitly designed to bypass authentication (e.g., login mapping)
        exempt_views = ['RegisterAPIView', 'LoginAPIView', 'TokenRefreshView']

        for app_name, mod in modules:
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and issubclass(obj, APIView) and obj is not APIView:
                    if name in exempt_views:
                        continue
                        
                    perms = getattr(obj, 'permission_classes', [])
                    
                    found_auth = False
                    for p in perms:
                        if p == IsAuthenticated or (hasattr(p, '__name__') and p.__name__ == 'IsAuthenticated'):
                            found_auth = True
                            
                    self.assertTrue(
                        found_auth,
                        f"SECURITY FLAW: View '{name}' in app '{app_name}' is missing IsAuthenticated constraint in permission_classes!"
                    )

    def test_views_accessing_models_use_permission_service(self):
        """Assert that if a view module accesses models, it imports the RBAC service."""
        apps_dir = os.path.join(settings.BASE_DIR, 'apps')
        
        # Exempt apps that strictly do not deal with tenant-specific models (like bootstrap routing)
        exempt_apps = ['accounts', 'web']
        
        for root, dirs, files in os.walk(apps_dir):
            if 'views.py' in files:
                view_path = os.path.join(root, 'views.py')
                normalized_path = view_path.replace('\\', '/')
                
                if any(f"/apps/{app}/" in normalized_path for app in exempt_apps):
                    continue
                    
                with open(view_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                imports_rbac = False
                
                # Check heuristically if query bounds execute in this file
                has_model_query = '.objects.' in content
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if alias.name in ['enforce_organization_isolation', 'has_permission', 'rbac_service'] or 'rbac_service' in str(node.module):
                                imports_rbac = True
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'rbac_service' in alias.name:
                                imports_rbac = True
                                
                if has_model_query:
                    self.assertTrue(
                        imports_rbac,
                        f"CRITICAL ARCHITECTURAL FLAW: File {normalized_path} queries models (.objects.) but fails to import centralized RBAC Permission Service!"
                    )
