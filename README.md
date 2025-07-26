# Ansible Collection - ivorynomad.onepassword

[![Ansible Galaxy](https://img.shields.io/badge/galaxy-ivorynomad.onepassword-blue.svg)](https://galaxy.ansible.com/ivorynomad/onepassword)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/IvoryNomad/ansible-onepassword/workflows/CI/badge.svg)](https://github.com/IvoryNomad/ansible-onepassword/actions)
[![codecov](https://codecov.io/gh/IvoryNomad/ansible-onepassword/branch/main/graph/badge.svg)](https://codecov.io/gh/IvoryNomad/ansible-onepassword)

An Ansible collection providing lookup plugins for seamless 1Password CLI integration. Securely retrieve secrets from your 1Password vaults directly in your Ansible playbooks and roles.

## Features

- **Secure secret retrieval** from 1Password vaults
- **Service Account and Connect authentication** support
- **Flexible secret reference syntax** using 1Password's standard format
- **Comprehensive error handling** with clear error messages
- **Type-safe implementation** with full Python typing support

## Requirements

- **Python 3.9+**
- **Ansible 2.13.9+**
- **1Password CLI** (`op`) installed and accessible in PATH
- **Valid 1Password authentication** (Service Account token or Connect credentials)

## Installation

### Step 1: Install the Collection

```bash
ansible-galaxy collection install ivorynomad.onepassword
```

### Step 2: Install Python Dependencies

Install the required Python dependency in the same environment as Ansible:

```bash
pip install op-python>=0.1.0
```

**Important:** If Ansible is installed in a virtual environment, ensure that environment is activated before installing both the collection and the Python dependency.

### Alternative: Install from requirements.txt

After installing the collection, you can install dependencies from the collection's requirements file:

```bash
# Find your collections path (usually ~/.ansible/collections/)
pip install -r ~/.ansible/collections/ansible_collections/ivorynomad/onepassword/requirements.txt
```

### Virtual Environment Notes

If you're using a virtual environment for Ansible:
- Activate your venv before running both `ansible-galaxy` and `pip install` commands
- Verify you're using the correct `ansible-galaxy` command (some systems have multiple installations)
- Check your installation with: `ansible-galaxy collection list | grep onepassword`

## Authentication

Configure authentication using one of the following methods:

### Option 1: Service Account Token

```bash
export OP_SERVICE_ACCOUNT_TOKEN="ops_your_service_account_token"
```

### Option 2: 1Password Connect

```bash
export OP_CONNECT_HOST="https://your-connect-server.com"
export OP_CONNECT_TOKEN="your_connect_token"
```

### Option 3: Environment File

Create a `.env` file in your project directory:

```env
# Service Account Authentication
OP_SERVICE_ACCOUNT_TOKEN=ops_your_service_account_token

# OR Connect Authentication
# OP_CONNECT_HOST=https://your-connect-server.com
# OP_CONNECT_TOKEN=your_connect_token
```

## Usage

### Basic Secret Retrieval

Retrieve a password from 1Password:

```yaml
- name: Get database password
  debug:
    var: lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password')
```

### Using in Variables

```yaml
- name: Configure application
  template:
    src: app.conf.j2
    dest: /etc/app/app.conf
  vars:
    db_password: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password') }}"
    api_key: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/API/credential') }}"
```

### Multiple Secrets

```yaml
- name: Deploy application with secrets
  docker_container:
    name: myapp
    image: myapp:latest
    env:
      DATABASE_PASSWORD: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password') }}"
      REDIS_PASSWORD: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Redis/password') }}"
      SECRET_KEY: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Django/secret_key') }}"
```

### Conditional Secret Retrieval

```yaml
- name: Get secrets based on environment
  set_fact:
    db_password: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://' + environment + '/Database/password') }}"
  vars:
    environment: "{{ 'Production' if ansible_hostname.startswith('prod') else 'Staging' }}"
```

### Using with Ansible Vault Fallback

```yaml
- name: Get API key with fallback
  set_fact:
    api_key: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/API/key') | default(vault_api_key) }}"
```

## Secret Reference Format

Use 1Password's standard secret reference syntax:

```
op://[vault]/[item]/[field]
```

**Examples:**
- `op://Production/Database/password` - Password field from Database item in Production vault
- `op://Personal/GitHub/username` - Username field from GitHub item in Personal vault
- `op://Shared/API/token` - Token field from API item in Shared vault

## Error Handling

The lookup plugin provides clear error messages for common issues:

```yaml
- name: Handle missing secrets gracefully
  set_fact:
    secret_value: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/MissingItem/password') | default('default_value') }}"
```

If a secret doesn't exist and no default is provided, the task will fail with a descriptive error message.

## Advanced Configuration

### Custom 1Password CLI Path

If your `op` CLI is installed in a non-standard location, set the path:

```yaml
- name: Get secret with custom op path
  debug:
    var: lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password', op_path='/usr/local/bin/op')
```

### Environment File Support

Enable `.env` file loading:

```yaml
- name: Get secret with .env support
  debug:
    var: lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password', use_dotenv=true)
```

## Best Practices

### 1. Use Specific Vault Names

```yaml
# Good - explicit vault
password: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password') }}"

# Avoid - relies on default vault
password: "{{ lookup('ivorynomad.onepassword.onepassword', 'Database/password') }}"
```

### 2. Group Related Secrets

Organize secrets logically in 1Password:
- `Production/Database` - All database credentials
- `Production/API` - All API keys and tokens
- `Staging/Database` - Staging environment database credentials

### 3. Use Descriptive Field Names

```yaml
# Clear field names in 1Password
db_host: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/hostname') }}"
db_port: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/port') }}"
db_user: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/username') }}"
db_pass: "{{ lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password') }}"
```

### 4. Handle Errors Gracefully

```yaml
- name: Set database password with fallback
  set_fact:
    database_password: "{{ 
      lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password') 
      | default(lookup('env', 'FALLBACK_DB_PASSWORD')) 
      | default('') 
    }}"

- name: Fail if no password available
  fail:
    msg: "Database password not found in 1Password or environment variables"
  when: database_password == ''
```

## Collection Contents

### Lookup Plugins

- **`onepassword`** - Retrieve secrets from 1Password vaults using secret references

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Unable to authenticate with 1Password
```
- Verify your Service Account token or Connect credentials are correct
- Ensure environment variables are properly set
- Check that the 1Password CLI (`op`) is installed and accessible

**2. Secret Not Found**
```
Error: Secret not found: op://Production/Database/password
```
- Verify the vault, item, and field names are correct
- Check that you have access to the specified vault
- Ensure the item exists in 1Password

**3. CLI Path Issues**
```
Error: op command not found
```
- Install the 1Password CLI: https://developer.1password.com/docs/cli/get-started/
- Ensure `op` is in your PATH or specify the path using `op_path` parameter

**4. Python Environment Mismatch**
```
ModuleNotFoundError: No module named 'op_python'
```
- Ensure `op-python` is installed in the same Python environment as Ansible
- If using a virtual environment, verify it's activated and install dependencies there
- Check with: `python -c "import op_python; print('op-python found')"`

### Debug Mode

Enable verbose output for troubleshooting:

```yaml
- name: Debug 1Password lookup
  debug:
    var: lookup('ivorynomad.onepassword.onepassword', 'op://Production/Database/password')
  environment:
    OP_DEBUG: "true"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- **GitHub Issues**: [https://github.com/IvoryNomad/ansible-onepassword/issues](https://github.com/IvoryNomad/ansible-onepassword/issues)
- **Documentation**: [https://github.com/IvoryNomad/ansible-onepassword](https://github.com/IvoryNomad/ansible-onepassword)

## Related Projects

- **[op-python](https://github.com/IvoryNomad/op-python)** - The underlying Python library for 1Password CLI integration
- **[1Password CLI](https://developer.1password.com/docs/cli/)** - Official 1Password command-line tool

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- Basic 1Password secret lookup functionality
- Service Account and Connect authentication support
- Comprehensive error handling and documentation
