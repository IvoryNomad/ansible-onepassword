# File: TESTING.md
# Testing Guide for ansible-onepassword

This guide explains how to run tests for the `ivorynomad.onepassword` Ansible collection.

## Test Structure Overview

```
tests/
├── unit/                          # Python unit tests
│   ├── conftest.py               # Test configuration
│   └── plugins/lookup/
│       └── test_onepassword.py   # Main unit tests
├── integration/                   # Ansible integration tests
│   ├── targets/lookup_onepassword/
│   │   ├── tasks/main.yml        # Integration test tasks
│   │   └── aliases               # Test metadata
│   └── ansible.cfg               # Integration test config
└── requirements.txt               # Test dependencies
```

## Quick Start

### 1. Set Up Testing Environment

```bash
# Clone your repository
git clone https://github.com/IvoryNomad/ansible-onepassword.git
cd ansible-onepassword

# Create a virtual environment (recommended)
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install test dependencies
pip install -r tests/requirements.txt
```

### 2. Run All Tests

```bash
# Simple test runner (makes script executable first)
chmod +x test.sh
./test.sh
```

## Individual Test Types

### Unit Tests (Python)

Test the plugin logic without external dependencies:

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run unit tests
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=plugins --cov-report=term-missing

# Run specific test
pytest tests/unit/plugins/lookup/test_onepassword.py::TestOnePasswordLookup::test_successful_secret_lookup -v
```

### Integration Tests (Ansible)

Test the plugin within Ansible's framework:

```bash
# Run integration tests
ansible-test integration --docker -v lookup_onepassword

# Run with specific Python version
ansible-test integration --docker -v lookup_onepassword --python 3.10
```

### Sanity Tests (Code Quality)

Ansible's built-in code quality checks:

```bash
# Run all sanity tests
ansible-test sanity --docker -v

# Run specific sanity test
ansible-test sanity --test validate-modules --docker -v
```

### Linting and Formatting

```bash
# Python formatting
black --check plugins/ tests/
black plugins/ tests/  # Fix formatting

# Python linting
flake8 plugins/ tests/ --max-line-length=88

# YAML linting
yamllint .

# Ansible linting
ansible-lint
```

## GitHub Actions CI/CD

The repository includes a comprehensive GitHub Actions workflow (`.github/workflows/ci.yml`) that runs:

### 🔍 **Sanity Tests**
- Code quality checks
- Syntax validation
- Import validation
- Multiple Python versions (3.9-3.12)

### 🧪 **Unit Tests**
- Mock-based testing
- Coverage reporting
- Matrix testing (Python 3.9-3.12 × Ansible 2.13-2.15)

### 🔗 **Integration Tests**
- Real Ansible execution
- Error handling validation
- Plugin loading verification

### 📦 **Build & Validation**
- Collection building
- Installation testing
- Smoke tests

### 🎨 **Linting & Style**
- Black formatting
- flake8 linting
- YAML validation
- Ansible linting

### 🛡️ **Security Scanning**
- Dependency vulnerability checks
- Code security analysis

## Local Development Workflow

### 1. Make Changes
Edit your plugin code in `plugins/lookup/onepassword.py`

### 2. Run Tests Locally
```bash
# Quick unit tests during development
pytest tests/unit/plugins/lookup/test_onepassword.py -v

# Full test suite before committing
./test.sh
```

### 3. Fix Issues
```bash
# Format code
black plugins/ tests/

# Fix linting issues
flake8 plugins/ tests/ --max-line-length=88
```

### 4. Commit and Push
```bash
git add .
git commit -m "feat: add new functionality"
git push origin your-branch
```

The GitHub Actions workflow will automatically run all tests on your push/PR.

## Test Configuration

### pytest Configuration
- Uses `conftest.py` to set up the Ansible collection namespace
- Includes coverage reporting
- Supports test discovery

### Ansible Test Configuration  
- `tests/integration/ansible.cfg` configures Ansible for testing
- `aliases` file controls when/how tests run
- Uses Docker containers for isolated testing

### CI Matrix Testing
- **Python versions**: 3.9, 3.10, 3.11, 3.12
- **Ansible versions**: 2.13.9+, 2.14.0+, 2.15.0+
- **Operating systems**: Ubuntu (with Docker)

## Writing New Tests

### Adding Unit Tests

```python
# tests/unit/plugins/lookup/test_onepassword.py
def test_new_functionality(self, lookup_plugin, mock_op_client):
    """Test description."""
    # Setup mock
    mock_op_client.some_method.return_value = "expected_result"
    
    # Test
    result = lookup_plugin.run(['test_input'], variables={}, **{})
    
    # Assert
    assert result == ["expected_result"]
```

### Adding Integration Tests

```yaml
# tests/integration/targets/lookup_onepassword/tasks/main.yml
- name: Test new scenario
  set_fact:
    test_result: "{{ lookup('ivorynomad.onepassword.onepassword', 'test_input') }}"
  register: test_output
  ignore_errors: true

- name: Verify test result
  assert:
    that:
      - condition_to_check
    fail_msg: "Descriptive error message"
```

## Troubleshooting Tests

### Common Issues

**1. Import Errors**
```bash
# Ensure Python path is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**2. Ansible Collection Not Found**
```bash
# Check collection installation
ansible-galaxy collection list | grep onepassword
```

**3. Docker Issues with ansible-test**
```bash
# Ensure Docker is running
docker info

# Try without Docker (less isolated)
ansible-test integration -v lookup_onepassword
```

**4. Permission Issues**
```bash
# Make test script executable
chmod +x test.sh
```
