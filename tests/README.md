# SentryIQ Test Suite

Comprehensive testing for the SentryIQ AI-powered cybersecurity platform.

## Test Structure

### Unit Tests (Isolated)
- `test_chain_detector.py` — CVE chain detection engine
- `test_prioritizer.py` — Vulnerability prioritization algorithm
- `test_risk_scoring.py` — Human risk scoring calculations
- `test_sandbox.py` — NemoClaw sandbox isolation & monitoring

### Integration Tests (API)
- `test_api_integration.py` — FastAPI endpoint integration
- `test_phishing_engine.py` — Phishing simulation workflows

### Fixtures & Setup
- `conftest.py` — Shared pytest fixtures, database setup, mock clients

## Running Tests

### Run all tests
```bash
cd backend
pip install -e ".[dev]"
pytest
```

### Run specific test file
```bash
pytest tests/test_chain_detector.py -v
```

### Run by marker
```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m asyncio           # Async tests only
```

### Run with coverage
```bash
pytest --cov=backend --cov-report=html
```

### Run in parallel
```bash
pytest -n auto              # Uses all CPU cores
```

### Watch mode (auto-run on file changes)
```bash
pytest-watch
```

## Test Coverage Goals

- **Phase 7**: Minimum 80% code coverage
- **Critical paths**: 100% coverage
  - Chain detection algorithm
  - Risk scoring calculations
  - Sandbox enforcement
  - API authentication

## Key Test Fixtures

### Database
```python
@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create async test database session."""
```

### NIM Client
```python
@pytest.fixture
def mock_nim_client() -> NIMClient:
    """Create mock NIM client for testing."""
```

### Sandbox
```python
@pytest_asyncio.fixture
async def test_sandbox() -> NemoclawSandbox:
    """Create test sandbox instance."""
```

### Sample Data
```python
@pytest.fixture
def sample_cve_data():
    """Sample CVE data for tests."""

@pytest.fixture
def sample_stack_data():
    """Sample SMB stack data for tests."""
```

## Test Markers

- `@pytest.mark.unit` — Fast, isolated tests
- `@pytest.mark.integration` — API and workflow tests
- `@pytest.mark.asyncio` — Async/await tests
- `@pytest.mark.sandbox` — Security sandbox tests

## Continuous Integration

GitHub Actions CI runs:
1. `pytest` — Full test suite
2. `pytest --cov` — Coverage report
3. `black --check` — Code formatting
4. `ruff check` — Linting
5. `mypy` — Type checking

## Adding New Tests

1. Create `test_module_name.py` in `/tests/`
2. Use fixtures from `conftest.py`
3. Add appropriate markers (`@pytest.mark.unit`, etc.)
4. Keep tests focused and isolated
5. Use descriptive names: `test_function_behavior_condition`

Example:
```python
@pytest.mark.unit
def test_calculate_risk_score_with_high_clicks(risk_scorer):
    """Test risk calculation when clicks are above threshold."""
    score, level, _ = risk_scorer.calculate_employee_risk(
        clicks=10,
        reports=0,
        critical_vuln_count=5,
        compliance_frameworks_count=0,
    )
    
    assert level == "HIGH"
    assert 60 <= score < 80
```

## Debugging Failed Tests

```bash
# Show all output (print statements)
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff

# Show local variables on failure
pytest -l
```

## Performance Notes

- Unit tests: ~100ms total
- Integration tests: ~500ms total
- Full suite: ~5 seconds on modern hardware
- Parallel execution: ~2 seconds with `-n auto`

## Test Data Schemas

### CVE Data
```python
{
    "cve_id": "CVE-2024-12345",
    "description": "Vulnerability description",
    "cvss_score": 9.5,
    "cwe_ids": ["CWE-79"],
    "affected_cpes": ["cpe:2.3:a:vendor:product:*:*:*:*:*:*:*:*"],
    "epss_score": 0.95,
    "is_kev": True,
}
```

### Stack Data
```python
{
    "org_name": "Test SMB Inc",
    "cpe_identifiers": ["cpe:2.3:a:microsoft:windows:11:*:*:*:*:*:*:*"],
    "internet_facing_cpes": ["cpe:2.3:a:microsoft:windows:11:*:*:*:*:*:*:*"],
    "compliance_frameworks": ["NDPA", "POPIA"],
}
```

## See Also

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
