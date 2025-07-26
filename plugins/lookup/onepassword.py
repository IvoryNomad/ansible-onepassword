# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Just kidding, we're not really using GPLv3 - but ansible sanity checks are not totally sane
# Copyright (c) 2025 IvoryNomad
# SPDX-License-Identifier: MIT

"""
1Password lookup plugin using IvoryNomad/op-python OpClient class
"""

# flake8: noqa
DOCUMENTATION = """
    name: onepassword
    author: Nathan Eric Norman (@IvoryNomad)
    version_added: "1.0.0"
    short_description: fetch secrets from 1Password using op-python
    description:
        - This lookup returns values from 1Password items using the IvoryNomad/op-python OpClient class
        - Requires the op-python library and 1Password CLI to be installed and authenticated
        - Supports both Service Account tokens and 1Password Connect authentication
    options:
        _terms:
            description:
                - 1Password item name, UUID, or secret reference
                - Can be item name/UUID or full secret reference like "op://vault/item/field"
            required: True
        vault:
            description: vault name or UUID (optional if using secret reference syntax)
            required: False
        field:
            description: specific field to retrieve from the item (defaults to 'password')
            required: False
            default: 'password'
        use_dotenv:
            description: enable loading environment variables from .env file
            required: False
            default: False
        dotenv_path:
            description: path to .env file
            required: False
            default: '.env'
        op_path:
            description: path to op CLI executable
            required: False
            default: 'op'
    notes:
        - Authentication via OP_SERVICE_ACCOUNT_TOKEN or OP_CONNECT_HOST/OP_CONNECT_TOKEN environment variables
        - Supports secret references like "op://vault/item/field" or item lookups by name
    requirements:
        - op-python library
        - 1Password CLI (op) installed and authenticated
"""
# flake8: enable

EXAMPLES = """
# Get password field from an item by name
- name: Get database password
  debug:
    var: "{{ lookup('onepassword', 'database-credentials', vault='Production') }}"

# Get specific field from an item
- name: Get username from item
  debug:
    var: "{{ lookup('onepassword', 'database-credentials', vault='Production', field='username') }}"

# Use secret reference syntax (recommended)
- name: Get secret using reference
  debug:
    var: "{{ lookup('onepassword', 'op://Production/database-credentials/password') }}"

# Get API key using secret reference
- name: Get API key
  debug:
    var: "{{ lookup('onepassword', 'op://Production/api-keys/api_key') }}"

# Multiple secrets at once
- name: Get multiple secrets
  vars:
    db_pass: "{{ lookup('onepassword', 'op://Production/database-credentials/password') }}"
    api_key: "{{ lookup('onepassword', 'op://Production/api-keys/key') }}"
"""

RETURN = """
_raw:
    description: The value of the specified field from the 1Password item
    type: string
"""

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError, AnsibleLookupError
from ansible.utils.display import Display
from typing import Any, Optional, Dict

try:
    from op_python import OpClient, OnePasswordError

    HAS_OP_PYTHON = True
except ImportError:
    HAS_OP_PYTHON = False
    OpClient = None
    OnePasswordError = None

display = Display()


class LookupModule(LookupBase):

    def __init__(self, loader=None, templar=None, **kwargs):
        super().__init__(loader, templar, **kwargs)
        self._op_client = None

    def _get_client(self, **kwargs):
        """Get or create OpClient instance with specified options"""
        if not HAS_OP_PYTHON:
            raise AnsibleError(
                " ".join(
                    [
                        "The op-python library is required for this lookup plugin.",
                        "Install with: pip install op-python",
                    ]
                )
            )

        if self._op_client is None:
            client_options = {
                "op_path": kwargs.get("op_path", "op"),
                "use_dotenv": kwargs.get("use_dotenv", False),
                "dotenv_path": kwargs.get("dotenv_path", ".env"),
                "dotenv_override": kwargs.get("dotenv_override", False),
            }

            try:
                self._op_client = OpClient(**client_options)
            except OnePasswordError as e:
                raise AnsibleError(f"Failed to initialize 1Password client: {e}")

        return self._op_client

    def run(self, terms, variables=None, **kwargs):
        """Main lookup method"""
        ret = []

        # Handle empty terms early - no need to initialize client
        if not terms:
            return ret

        # Get client options from kwargs
        vault = kwargs.get("vault")
        field = kwargs.get("field", "password")

        # Get OpClient instance
        op = self._get_client(**kwargs)

        for term in terms:
            try:
                # Check if term is a secret reference (starts with op://)
                if term.startswith("op://"):
                    # Use secret reference syntax
                    display.vvv(
                        f"onepassword lookup: getting secret reference '{term}'"
                    )
                    value = op.get_secret(term)
                else:
                    # Traditional item + field lookup
                    display.vvv(
                        f"onepassword lookup: getting item '{term}' field '{field}' from vault '{vault}'"
                    )

                    # Get the complete item
                    item = op.get_item(term, vault=vault)

                    # Extract the requested field
                    value = self._extract_field_from_item(item, field)

                if value is None:
                    raise AnsibleLookupError(
                        f"Field '{field}' not found in item '{term}'"
                    )

                ret.append(value)

            except OnePasswordError as e:
                raise AnsibleLookupError(
                    f"Failed to retrieve 1Password item '{term}': {e}"
                )
            except Exception as e:
                raise AnsibleLookupError(f"Unexpected error retrieving '{term}': {e}")

        return ret

    def _extract_field_from_item(
        self, item: Dict[str, Any], field_name: str
    ) -> Optional[str]:
        """Extract a specific field value from a 1Password item"""

        # Handle different item structures that might be returned
        if "fields" in item:
            # Look through the fields array
            for field in item["fields"]:
                # Check various possible field identification methods
                if (
                    field.get("label", "").lower() == field_name.lower()
                    or field.get("id", "").lower() == field_name.lower()
                    or field.get("type", "").lower() == field_name.lower()
                ):
                    return field.get("value")

        # For common field names, try direct access
        common_fields = {
            "password": ["password", "passwd", "pass"],
            "username": ["username", "user", "login"],
            "email": ["email", "e-mail"],
            "url": ["url", "website", "link"],
            "notes": ["notes", "note"],
        }

        # Try direct field access in item
        for field_variant in common_fields.get(field_name.lower(), [field_name]):
            if field_variant in item:
                return item[field_variant]

        # If it's a simple field request for password and item has a 'password' key
        if field_name.lower() == "password" and "password" in item:
            return item["password"]

        return None
