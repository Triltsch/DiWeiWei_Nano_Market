# 09 — Teststrategie & Qualitätsicherung

---

## 1. Test Pyramid

```
                         △
                        ╱ ╲
                       ╱ E2E ╲        5-10%
                      ╱       ╲
                     ╱─────────╲
                    ╱ Integration╲     15-20%
                   ╱             ╲
                  ╱───────────────╲
                 ╱     Unit        ╲   70-80%
                ╱                   ╲
               ╱─────────────────────╲
```

**Zielquoten (MVP):**
- Unit Tests: 80%+ Code Coverage
- Integration Tests: 20+ Critical Flows
- E2E Tests: 10+ User Journeys
- Performance Tests: Baseline established
- Security Tests: OWASP Top 10 checked

---

## 2. Unit Testing

### 2.1 Scope

```python
# Tested (Unit Level):
- Service layer business logic
- Repository queries (mocked DB)
- JWT token generation/validation
- Password hashing/verification
- Input validation functions
- Utility functions / Helpers
```

### 2.2 Tools

- **Framework:** pytest
- **Mocking:** unittest.mock
- **Fixtures:** pytest fixtures + factories
- **Assertions:** pytest + assert-awesome-python

### 2.3 Example Test

```python
import pytest
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserRegister

class TestUserRegistration:
    """Test suite for user registration."""
    
    @pytest.fixture
    def auth_service(self):
        """Provide AuthService instance."""
        return AuthService(db_repo=MockUserRepository())
    
    def test_registration_success(self, auth_service):
        """
        Test: User registration with valid inputs succeeds.
        Expected: User created, email verified link sent.
        """
        # Arrange
        user_data = UserRegister(
            email="jan@example.com",
            username="jan_doe",
            password="SecureP@ss123"
        )
        
        # Act
        result = auth_service.register(user_data)
        
        # Assert
        assert result.success is True
        assert result.user.email == "jan@example.com"
        assert result.verification_link_sent is True
    
    def test_registration_duplicate_email(self, auth_service):
        """
        Test: Duplicate email registration fails.
        Expected: ValidationError with clear message.
        """
        # Arrange
        existing_user = UserRegister(
            email="existing@example.com",
            username="user1",
            password="Pass@123"
        )
        auth_service.register(existing_user)
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            auth_service.register(existing_user)
        assert "Email already exists" in str(exc_info.value)
    
    def test_password_strength_validation(self, auth_service):
        """
        Test: Weak password rejected.
        Expected: ValidationError.
        """
        weak_passwords = [
            "short",          # Too short
            "noupppercase123", # No uppercase
            "NoDigits",       # No digit
            "NoSpecial123",   # No special char
        ]
        
        for weak_pw in weak_passwords:
            user_data = UserRegister(
                email=f"user{hash(weak_pw)}@example.com",
                username=f"user_{hash(weak_pw)}",
                password=weak_pw
            )
            
            with pytest.raises(ValidationError):
                auth_service.register(user_data)
```

**Target:** Every service method has ≥2 test cases (happy path + error path)

---

## 3. Integration Testing

### 3.1 Scope

```
- API route → Service → Repository → Mock DB
- Correct status codes (200, 400, 401, 403, 409, 500)
- Request/Response serialization
- Error handling & validation chains
```

### 3.2 Example Integration Test

```python
@pytest.mark.asyncio
class TestNanoUploadAPI:
    """Integration tests for Nano upload endpoint."""
    
    @pytest.fixture
    async def client(self):
        """Provide test client."""
        app = create_app_for_testing()
        async with TestClient(app) as client:
            yield client
    
    async def test_upload_nano_success(self, client, auth_token, valid_nano_zip):
        """
        Test: Creator uploads Nano via API.
        Expected: 201 Created with nano_id.
        """
        # Arrange
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {"file": ("test.zip", valid_nano_zip, "application/zip")}
        data = {
            "title": "Excel Basics",
            "duration_minutes": "45",
            "competency_level": "1",
            "category": "Business Skills"
        }
        
        # Act
        response = await client.post(
            "/api/v1/nanos",
            files=files,
            data=data,
            headers=headers
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["id"]
        assert response.json()["data"]["status"] == "draft"
    
    async def test_upload_unauthorized(self, client, valid_nano_zip):
        """
        Test: Unauthenticated user cannot upload.
        Expected: 401 Unauthorized.
        """
        response = await client.post(
            "/api/v1/nanos",
            files={"file": ("test.zip", valid_nano_zip)},
            data={"title": "Test"}
        )
        
        assert response.status_code == 401
```

**Test DB:** SQLite in-memory für Tests (schnell, isoliert)

---

## 4. End-to-End (E2E) Testing

### 4.1 Scope

```
- Full user journeys (from login to download)
- Browser automation / API sequences
- Data persistence across requests
```

### 4.2 Tools

- **Selenium** or **Playwright** (browser automation)
- **Cypress** (modern, developer-friendly)

### 4.3 Example E2E Test

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
async def test_creator_journey():
    """
    E2E: Creator registers, uploads Nano, sees it published.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 1. Register
        await page.goto("http://localhost:3000/register")
        await page.fill('input[name="email"]', "creator@test.com")
        await page.fill('input[name="password"]', "SecurePass123!")
        await page.click('button[type="submit"]')
        await page.wait_for_navigation()
        assert "Check your email" in await page.content()
        
        # 2. Verify email (simulated)
        verification_link = await get_verification_link_from_fixture()
        await page.goto(verification_link)
        
        # 3. Login
        await page.goto("http://localhost:3000/login")
        await page.fill('input[name="email"]', "creator@test.com")
        await page.fill('input[name="password"]', "SecurePass123!")
        await page.click('button[type="submit"]')
        await page.wait_for_navigation()
        assert "/dashboard" in page.url
        
        # 4. Upload Nano
        await page.goto("http://localhost:3000/upload")
        await page.set_input_files('input[type="file"]', "fixtures/valid.zip")
        await page.fill('input[name="title"]', "Excel Basics")
        await page.select_option('select[name="level"]', "1")
        await page.click('button[name="upload"]')
        
        # 5. Wait for moderation  
        await asyncio.sleep(2)  # Simulate moderation
        
        # 6. Verify published
        await page.goto("http://localhost:3000/my-nanos")
        assert "Excel Basics" in await page.content()
        
        await browser.close()
```

**Test-Umgebung:** Staging environment (mit echten Services, nicht mocked)

---

## 5. Performance Testing

### 5.1 Ziele

```
Homepage Load: <2s (3G)
Search Results: <500ms (p95)
Chat/Message Send: <1s
Upload: Depends on file size (show progress)
```

### 5.2 Load Testing (Locust)

```python
from locust import HttpUser, task, between

class Scenario(HttpUser):
    """Simulated user behavior."""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login once."""
        self.token = self.login()
    
    @task(10)
    def search_nanos(self):
        """Search (most common action)."""
        self.client.get(
            "/api/v1/search?q=excel&limit=20",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(5)
    def view_nano(self):
        """View detail."""
        self.client.get(
            "/api/v1/nanos/abc-123",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def rate_nano(self):
        """Rate nano."""
        self.client.post(
            "/api/v1/nanos/abc-123/ratings",
            json={"score": 5, "comment": "Great!"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

# Run: locust -f locustfile.py --host=http://localhost:8000
```

**Results Analysis:**
```
Target: 1000 concurrent users, 95th percentile <1s
If fails → Identify bottleneck:
  - DB query too slow → Add index / cache
  - API response too large → Paginate / compress
  - Infrastructure too small → Scale up
```

---

## 6. Security Testing

### 6.1 OWASP Top 10 Checklist

| Vulnerability | Test | Tool / Method |
|---------------|------|---------------|
| **Injection** | SQL Injection | `" OR "1"="1` in search |
| | Command Injection | Test file upload |
| **Broken Auth** | Weak password | Test regex enforcement |
| | JWT forgery | Modify token, retry |
| **Sensitive Data** | PII logging | Grep logs for email/phone |
| **Entity  Expansion** | XXE (XML) | Upload malicious XML |
| **BROKEN ACCESS** | IDOR | Fetch `/api/users/other_id` |
| **XSS** | Stored XSS | Comment with `<script>` |
| **CSRF** | Token validation | POST without CSRF token |
| **LOG/MONITORING** | Audit trail | Verify all actions logged |

### 6.2 Security Test Example

```python
@pytest.mark.security
def test_sql_injection_prevention():
    """
    Test: SQL injection in search field prevented.
    """
    malicious_query = '" OR "1"="1'
    response = requests.get(
        f'http://localhost:8000/api/v1/search?q={malicious_query}',
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should not return all nanos, should return 0 or sanitized results
    assert len(response.json()["data"]) <= 1

@pytest.mark.security
def test_xss_prevention():
    """
    Test: HTML injection in comments escaped.
    """
    xss_payload = "<script>alert('XSS')</script>"
    
    response = requests.post(
        "http://localhost:8000/api/v1/nanos/abc/comments",
        json={"text": xss_payload},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Retrieve comment
    get_response = requests.get(
        "http://localhost:8000/api/v1/nanos/abc/comments"
    )
    
    comment_text = get_response.json()["data"][0]["text"]
    # Should be escaped
    assert "<script>" not in comment_text
    assert "&lt;script&gt;" in comment_text
```

---

## 7. Accessibility Testing

### 7.1 Standards

- WCAG 2.1 Level AA

### 7.2 Tools

- axe-core (automated)
- NVDA screen reader (manual)
- Keyboard navigation testing

### 7.3 Checklist

- [ ] All images have alt text
- [ ] Keyboard-navigable (Tab/Shift+Tab)
- [ ] Color contrast ≥4.5:1
- [ ] Focus indicators visible
- [ ] Form labels associated with inputs
- [ ] Headings hierarchical (h1 → h2 → h3)

---

## 8. Usability Testing

### 8.1 Method

- Session recordings (FullStory, LogRocket)
- User feedback surveys
- A/B testing for UI variants

### 8.2 Metrics

- Task Completion Rate (>90% target)
- Time to Complete (e.g., <5 min for first upload)
- Error Rate (<5%)
- Satisfaction (NPS >50)

---

## 9. Continuous Integration / Continuous Deployment (CI/CD)

### 9.1 Pipeline (GitHub Actions)

```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Lint
        run: |
          pip install flake8 black isort
          black --check app/
          flake8 app/ --max-line-length=100
  
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: pass
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          pip install -r requirements.txt
          pytest --cov=app/ --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: SAST (SonarQube)
        run: sonar-scanner
  
  deploy:
    needs: [lint, test, security]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Staging
        run: ./scripts/deploy-staging.sh
      - name: E2E Tests on Staging
        run: pytest tests/e2e/
      - name: Deploy to Production
        run: ./scripts/deploy-prod.sh
```

---

## 10. Qualitäts-Gating (Quality Gates)

**Blockiers für Go-Live:**
- [ ] Code Coverage ≥80%
- [ ] All Critical Bugs fixed
- [ ] Security audit passed
- [ ] Performance SLA met
- [ ] DSGVO compliance verified
- [ ] 3 days stable in production (staging)

---

## Referenzen

- [08 — Backlog & Roadmap](./08_backlog_roadmap.md) (User Stories)
- [06 — Security & Compliance](./06_security_compliance.md) (Security Tests)
