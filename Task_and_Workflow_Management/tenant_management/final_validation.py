import requests
import time
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api"

# Helper to log
def log(msg, status="INFO", color="\033[94m"):
    reset = "\033[0m"
    print(f"{color}[{status}]{reset} {msg}")

def fail(msg):
    log(msg, "FAIL", "\033[91m")
    sys.exit(1)

def check(test_name, condition, error_msg):
    if not condition:
        fail(f"{test_name} - {error_msg}")
    log(f"Passed: {test_name}", "OK", "\033[92m")

# Test users
ADMIN_CREDS = { "email": f"admin_{uuid.uuid4().hex[:8]}@test.com", "password": "TestPass123!" }
MEMBER_CREDS = { "email": f"member_{uuid.uuid4().hex[:8]}@test.com", "password": "TestPass123!" }
MEMBER2_CREDS = { "email": f"member2_{uuid.uuid4().hex[:8]}@test.com", "password": "TestPass123!" }
MALICIOUS_CREDS = { "email": f"malicious_{uuid.uuid4().hex[:8]}@test.com", "password": "TestPass123!" }

# Sessions
admin_client = requests.Session()
member_client = requests.Session()
member2_client = requests.Session()
malicious_client = requests.Session()

# --------------------------------------------
# A. Registration & Login
# --------------------------------------------
log("Starting Registration & Login Tests...")

for creds in [ADMIN_CREDS, MEMBER_CREDS, MEMBER2_CREDS, MALICIOUS_CREDS]:
    r = requests.post(f"{BASE_URL}/accounts/register/", json=creds)
    check(f"Register {creds['email']}", r.status_code == 201, f"Failed: {r.status_code} {r.text}")

def login(client, creds):
    r = client.post(f"{BASE_URL}/accounts/login/", json=creds)
    check(f"Login {creds['email']}", r.status_code == 200, f"Failed: {r.status_code} {r.text}")
    token = r.json()["access"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return r.json()

admin_info = login(admin_client, ADMIN_CREDS)
member_info = login(member_client, MEMBER_CREDS)
member2_info = login(member2_client, MEMBER2_CREDS)
malicious_info = login(malicious_client, MALICIOUS_CREDS)

# Generate a fake JWT
fake_client = requests.Session()
fake_client.headers.update({"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"})
r = fake_client.get(f"{BASE_URL}/organizations/mine/")
check("Invalid Token check", r.status_code == 401, "Should return 401 for invalid JWT.")

# --------------------------------------------
# B. Organization Flow
# --------------------------------------------
log("\nStarting Organization Flow Tests...")

# Admin creates org
r = admin_client.post(f"{BASE_URL}/organizations/create/", json={"name": f"Org Admin {uuid.uuid4().hex[:6]}"})
check("Admin Create Org", r.status_code == 201, f"Failed: {r.status_code} {r.text}")
org_id = r.json()["id"]


# Member tries to create org
r = member_client.post(f"{BASE_URL}/organizations/create/", json={"name": f"Member Org {uuid.uuid4().hex[:6]}"})
check("Member Create Org", r.status_code == 201, f"Members CAN create organizations (they become Admin of their own org).")
member_org_id = r.json()["id"]

# Member tries viewing Admin's org
r = member_client.get(f"{BASE_URL}/projects/{org_id}/list/")
check("Member view unauthorized org", r.status_code in [403, 404], f"Should fail, got: {r.status_code}")

# Admin invites/adds Member to Admin's org
# Need member UUID
import base64
import json
def get_user_id(token):
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    return json.loads(base64.b64decode(payload))["user_id"]

member_user_id = get_user_id(member_info["access"])
member2_user_id = get_user_id(member2_info["access"])

r = admin_client.post(f"{BASE_URL}/organizations/{org_id}/add_member/", json={"email": MEMBER_CREDS["email"], "role": 1})
check("Admin adds member", r.status_code in [200, 201], f"Failed: {r.status_code} {r.text}")

r = admin_client.post(f"{BASE_URL}/organizations/{org_id}/add_member/", json={"email": MEMBER2_CREDS["email"], "role": 1})

# Role escalation (Member tries to escalate themselves)
r = member_client.post(f"{BASE_URL}/organizations/{org_id}/permission-requests/", json={"requested_role": 3, "requested_action": "Need access", "start_time": "2030-01-01T00:00:00Z", "end_time": "2030-01-02T00:00:00Z"})
check("Member requests escalation", r.status_code == 201, f"Escalation request failed: {r.status_code} {r.text}")

# --------------------------------------------
# C. Team Flow
# --------------------------------------------
log("\nStarting Team Flow Tests...")

r = admin_client.post(f"{BASE_URL}/organizations/{org_id}/teams/", json={"name": "Backend Team"})
check("Admin Create Team", r.status_code == 201, f"Failed: {r.status_code} {r.text}")
team_id = r.json()["id"]

r = member_client.post(f"{BASE_URL}/organizations/{org_id}/teams/", json={"name": "Hacker Team"})
check("Member Create Team", r.status_code == 403, f"Member should fail creating team, got {r.status_code}")

# Assign member to team
r = admin_client.put(f"{BASE_URL}/organizations/{org_id}/members/{member_user_id}/assign_team/", json={"team_id": team_id})
check("Admin assigns team to member", r.status_code == 200, f"Failed: {r.status_code} {r.text}")

# --------------------------------------------
# D. Project Flow
# --------------------------------------------
log("\nStarting Project Flow Tests...")

r = admin_client.post(f"{BASE_URL}/projects/{org_id}/create/", json={"name": "Alpha Project", "description": "Desc"})
check("Admin Create Project", r.status_code == 201, f"Failed: {r.status_code} {r.text}")
project_id = r.json()["id"]

# Member tries to create project
r = member_client.post(f"{BASE_URL}/projects/{org_id}/create/", json={"name": "Hacker Project"})
check("Member Create Project", r.status_code == 403, f"Member should fail creating project, got {r.status_code}")

# --------------------------------------------
# E. Task Flow
# --------------------------------------------
log("\nStarting Task Flow Tests...")

r = admin_client.post(f"{BASE_URL}/tasks/{org_id}/{project_id}/create/", json={"title": "Task 1", "description": "Do this"})
check("Admin Create Task", r.status_code == 201, f"Failed: {r.status_code} {r.text}")
task1_id = r.json()["id"]

r = member_client.post(f"{BASE_URL}/tasks/{org_id}/{project_id}/create/", json={"title": "Task Hacker"})
check("Member Create Task", r.status_code == 403, "Member should not create tasks")

# Admin Assign Task
r = admin_client.post(f"{BASE_URL}/tasks/{org_id}/{task1_id}/assign/", json={"assigned_to": member_user_id})
check("Admin Assign Task", r.status_code == 200, f"Failed: {r.status_code} {r.text}")

# Admin create another task and assign to member2
r = admin_client.post(f"{BASE_URL}/tasks/{org_id}/{project_id}/create/", json={"title": "Task 2"})
task2_id = r.json()["id"]
r = admin_client.post(f"{BASE_URL}/tasks/{org_id}/{task2_id}/assign/", json={"assigned_to": member2_user_id})

# Member View Tasks
r = member_client.get(f"{BASE_URL}/tasks/{org_id}/{project_id}/list/")
check("Member View Tasks", r.status_code == 200, "Should view tasks")
tasks = r.json()
# Task visibility: depends on RBAC. Member should only see assigned tasks, but currently view returns what they are allowed to see.
# In the tasks list endpoint, let's verify if they can update status
r = member_client.patch(f"{BASE_URL}/tasks/{task1_id}/update-status/", json={"status": "DONE"})
check("Member updates own task", r.status_code == 200, f"Failed: {r.status_code} {r.text}")

r = member_client.patch(f"{BASE_URL}/tasks/{task2_id}/update-status/", json={"status": "DONE"})
check("Member updates others task", r.status_code in [403, 404], f"Should fail, got: {r.status_code}")

# --------------------------------------------
# F. Audit Logs & Edge Cases
# --------------------------------------------
log("\nVerifying Audit Logs & URLs...")

r = admin_client.get(f"{BASE_URL}/audit/{org_id}/logs/")
check("Admin views audit logs", r.status_code == 200, f"Failed: {r.status_code} {r.text}")
audit_data = r.json()
# verify contains project logic
action_types = [a["action"] for a in audit_data]
check("Audit logs contain activity", "PROJECT_CREATED" in action_types or "TASK_ASSIGNED" in action_types or "ORG_CREATED" in action_types, "Missing audit actions")

r = member_client.get(f"{BASE_URL}/audit/{org_id}/logs/")
check("Member views audit logs", r.status_code == 403, "Members should not view logs.")

# URL manipulation: Malicious user tries to edit project in org_id
r = malicious_client.post(f"{BASE_URL}/projects/{org_id}/create/", json={"name": "Hack"})
check("Malicious user create cross-org", r.status_code == 403, f"Got: {r.status_code}")

# URL manipulation: Admin tries to patch task from member_org_id (foreign org)
r = admin_client.patch(f"{BASE_URL}/tasks/{task1_id}/update-status/", json={"status": "DONE"})
# updating task1_id should succeed as admin is owner ... wait, malicious user trying to patch task1_id
r = malicious_client.patch(f"{BASE_URL}/tasks/{task1_id}/update-status/", json={"status": "DONE"})
check("Malicious task patch", r.status_code in [403, 404], f"Got: {r.status_code}")

# Duplicate team
r = admin_client.post(f"{BASE_URL}/organizations/{org_id}/teams/", json={"name": "Backend Team"})
check("Duplicate team name", r.status_code == 400, "Should return 400 for duplicate team name")


# --------------------------------------------
# G. Stress Test
# --------------------------------------------
log("\nStress Test Quick Check...")
r = admin_client.post(f"{BASE_URL}/projects/{org_id}/create/", json={"name": "Stress Project"})
stress_proj_id = r.json()["id"]

start = time.time()
for i in range(50):
    r = admin_client.post(f"{BASE_URL}/tasks/{org_id}/{stress_proj_id}/create/", json={"title": f"Task {i}"})
    if r.status_code != 201:
        fail(f"Task creation failed at {i}: {r.status_code}")
log(f"Created 50 tasks in {time.time() - start:.2f} seconds", "OK", "\033[92m")

r = admin_client.get(f"{BASE_URL}/tasks/{org_id}/{stress_proj_id}/list/")
check("Load 50 tasks", r.status_code == 200, "Failed to load tasks")
log("All Validation Passed Successfully!", "SUCCESS", "\033[92m\033[1m")

