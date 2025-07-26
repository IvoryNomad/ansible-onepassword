# File: test.sh
# Simple test runner script for local development

set -e

echo "🧪 Running tests for ansible-onepassword collection..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "galaxy.yml" ]]; then
    print_error "Please run this script from the collection root directory"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not detected. Consider using a venv."
fi

# Check if plugin file exists
if [[ ! -f "plugins/lookup/onepassword.py" ]]; then
    print_error "Plugin file plugins/lookup/onepassword.py not found!"
    exit 1
fi

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r tests/requirements.txt

# Verify Python imports work
print_status "Verifying Python imports..."
if not python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'plugins'))

try:
    from lookup.onepassword import LookupModule
    print('✓ Plugin import successful')
except ImportError as e:
    print(f'✗ Plugin import failed: {e}')
    sys.exit(1)

try:
    import op_python
    print('✓ op-python dependency available')
except ImportError as e:
    print(f'✗ op-python not available: {e}')
    sys.exit(1)

try:
    import ansible.errors
    print('✓ Ansible core available')
except ImportError as e:
    print(f'✗ Ansible core not available: {e}')
    sys.exit(1)
"; then
    print_error "Import verification failed. Check error messages above."
    exit 1
fi

# Run linting
print_status "Running linting checks..."
if command -v black &> /dev/null; then
    echo "  - Running Black formatter check..."
    black --check plugins/ tests/ || {
        print_warning "Black formatting issues found. Run 'black plugins/ tests/' to fix."
    }
else
    print_warning "Black not installed. Install with: pip install black"
fi

if command -v pylint &> /dev/null; then
    echo "  - Running pylint ..."
    pylint plugins/ tests/ || {
        print_warning "pylint issues found."
    }
else
    print_warning "pylint not installed. Install with: pip install pylint"
fi

# Run unit tests
print_status "Running unit tests..."
PWD_PATH=$(pwd)
PLUGINS_PATH="$PWD_PATH/plugins"
export PYTHONPATH="${PYTHONPATH}:${PWD_PATH}:${PLUGINS_PATH}"

# Run tests with verbose output to help diagnose issues
pytest tests/unit/ -v --tb=short --capture=no || {
    print_error "Unit tests failed. Check the output above for details."
    echo ""
    echo "Debug information:"
    echo "  Python path: $PYTHONPATH"
    echo "  Working directory: $(pwd)"
    echo "  Plugin file exists: $(test -f plugins/lookup/onepassword.py && echo 'Yes' || echo 'No')"
    echo ""
    exit 1
}

# Run with coverage if the tests pass
print_status "Running unit tests with coverage..."
pytest tests/unit/ -v --cov=plugins --cov-report=term-missing || {
    print_warning "Coverage run had issues, but basic tests passed."
}

# Run ansible-test sanity (if available)
if command -v ansible-test &> /dev/null; then
    print_status "Running ansible-test sanity checks..."
    
    # Check if Docker/Podman is available
    if command -v docker &> /dev/null || command -v podman &> /dev/null; then
        print_status "Container runtime detected, running in containers..."
        # Create a temporary collections structure for ansible-test
        TEMP_COLLECTIONS_DIR
        TEMP_COLLECTIONS_DIR=$(mktemp -d)
        COLLECTION_DIR="$TEMP_COLLECTIONS_DIR/ansible_collections/ivorynomad/onepassword"
        
        # Copy collection to temporary location
        mkdir -p "$COLLECTION_DIR"
        cp -r ./* "$COLLECTION_DIR/" 2>/dev/null || true
        
        cd "$COLLECTION_DIR"
        ansible-test sanity --docker -v plugins/lookup/onepassword.py || {
            print_warning "Some sanity checks failed. Review the output above."
        }
        
        cd - > /dev/null
        rm -rf "$TEMP_COLLECTIONS_DIR"
        
        print_status "Running integration tests..."
        # Similar setup for integration tests
        TEMP_COLLECTIONS_DIR=$(mktemp -d)
        COLLECTION_DIR="$TEMP_COLLECTIONS_DIR/ansible_collections/ivorynomad/onepassword"
        mkdir -p "$COLLECTION_DIR"
        cp -r ./* "$COLLECTION_DIR/" 2>/dev/null || true
        
        cd "$COLLECTION_DIR"
        ansible-test integration --docker -v lookup_onepassword || {
            print_warning "Integration tests had issues. This might be expected without real 1Password setup."
        }
        
        cd - > /dev/null
        rm -rf "$TEMP_COLLECTIONS_DIR"
    else
        print_warning "No container runtime (Docker/Podman) detected."
        print_warning "Running ansible-test without containers (less isolated but still useful)..."
        
        # Try running without Docker
        ansible-test sanity -v plugins/lookup/onepassword.py || {
            print_warning "Sanity checks had issues. This might be due to missing container runtime."
        }
        
        ansible-test integration -v lookup_onepassword || {
            print_warning "Integration tests had issues. This might be due to missing container runtime or 1Password setup."
        }
    fi
else
    print_warning "ansible-test not available. Install ansible-core for full testing."
fi

# Build collection
print_status "Building collection..."
ansible-galaxy collection build --force

# Verify the built collection
if ls ivorynomad-onepassword-*.tar.gz 1> /dev/null 2>&1; then
    print_status "✅ Collection built successfully!"
    echo "Built: $(ls ivorynomad-onepassword-*.tar.gz)"
else
    print_error "Collection build failed!"
    exit 1
fi

print_status "✅ Test run completed!"
echo ""
echo "To install the built collection locally:"
echo "  ansible-galaxy collection install ivorynomad-onepassword-*.tar.gz --force"
echo ""
echo "To run individual test types:"
echo "  pytest tests/unit/                    # Unit tests only"
echo "  ansible-test sanity                   # Sanity checks only"
echo "  ansible-test integration lookup_onepassword  # Integration tests only"
echo ""
echo "To fix formatting:"
echo "  black plugins/ tests/                 # Auto-format Python code"
