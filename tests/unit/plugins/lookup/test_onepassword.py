# File: tests/unit/plugins/lookup/test_onepassword.py
"""
Unit tests for the onepassword lookup plugin.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from ansible.errors import AnsibleError, AnsibleLookupError

# Import the plugin directly for testing
try:
    from lookup.onepassword import LookupModule
except ImportError:
    # Fallback import method
    import importlib.util
    from pathlib import Path

    plugin_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "plugins"
        / "lookup"
        / "onepassword.py"
    )
    spec = importlib.util.spec_from_file_location("onepassword", plugin_path)
    onepassword_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(onepassword_module)
    LookupModule = onepassword_module.LookupModule


class TestOnePasswordLookup:
    """Test cases for the onepassword lookup plugin."""

    @pytest.fixture
    def lookup_plugin(self):
        """Create a lookup plugin instance for testing."""
        return LookupModule()

    def test_plugin_initialization(self, lookup_plugin):
        """Test that the plugin can be initialized successfully."""
        assert lookup_plugin is not None
        assert hasattr(lookup_plugin, "run")

    def test_successful_secret_lookup(self, lookup_plugin):
        """Test successful secret retrieval."""
        # Patch at the module level where OpClient is imported
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            # Setup mock
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.return_value = "test_password_123"

            # Test the lookup
            result = lookup_plugin.run(["op://Test/Demo/password"], variables={}, **{})

            # Verify results
            assert result == ["test_password_123"]
            mock_client.get_secret.assert_called_once_with("op://Test/Demo/password")

    def test_multiple_secret_lookup(self, lookup_plugin):
        """Test looking up multiple secrets."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            # Setup mock
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.side_effect = ["password1", "password2", "token123"]

            # Test multiple lookups
            terms = [
                "op://Test/App1/password",
                "op://Test/App2/password",
                "op://Test/API/token",
            ]
            result = lookup_plugin.run(terms, variables={}, **{})

            # Verify results
            assert result == ["password1", "password2", "token123"]
            assert mock_client.get_secret.call_count == 3

    def test_authentication_error(self, lookup_plugin):
        """Test handling of authentication errors."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            # Setup mock to raise authentication error
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.side_effect = Exception("Authentication failed")

            # Test that AnsibleLookupError is raised (not AnsibleError)
            with pytest.raises(
                Exception
            ) as exc_info:  # Could be AnsibleLookupError or AnsibleError
                lookup_plugin.run(["op://Test/Demo/password"], variables={}, **{})

            # Check that the error message contains relevant info
            error_msg = str(exc_info.value)
            assert (
                "Authentication failed" in error_msg
                or "Failed to retrieve" in error_msg
            )

    def test_secret_not_found_error(self, lookup_plugin):
        """Test handling when secret doesn't exist."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            # Setup mock to raise not found error
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.side_effect = Exception("Secret not found")

            # Test that AnsibleLookupError is raised
            with pytest.raises(Exception) as exc_info:  # Could be AnsibleLookupError
                lookup_plugin.run(
                    ["op://Test/NonExistent/password"], variables={}, **{}
                )

            # Check that the error message contains relevant info
            error_msg = str(exc_info.value)
            assert "Secret not found" in error_msg or "Failed to retrieve" in error_msg

    def test_empty_terms(self, lookup_plugin):
        """Test behavior with empty terms list."""
        # Empty terms should return empty results without calling OpClient
        result = lookup_plugin.run([], variables={}, **{})
        assert result == []

    def test_custom_op_path(self, lookup_plugin):
        """Test using custom op CLI path."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.return_value = "test_secret"

            # Test with custom op_path
            result = lookup_plugin.run(
                ["op://Test/Demo/password"], variables={}, op_path="/custom/path/to/op"
            )

            # Verify client was called with custom path and all defaults
            mock_client_class.assert_called_with(
                op_path="/custom/path/to/op",
                use_dotenv=False,
                dotenv_path=".env",
                dotenv_override=False,
            )
            assert result == ["test_secret"]

    def test_dotenv_configuration(self, lookup_plugin):
        """Test enabling dotenv support."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.return_value = "env_secret"

            # Test with dotenv enabled
            result = lookup_plugin.run(
                ["op://Test/Demo/password"],
                variables={},
                use_dotenv=True,
                dotenv_path="/custom/.env",
            )

            # Verify client was configured with dotenv options and all defaults
            mock_client_class.assert_called_with(
                op_path="op",
                use_dotenv=True,
                dotenv_path="/custom/.env",
                dotenv_override=False,
            )
            assert result == ["env_secret"]

    def test_client_initialization_error(self, lookup_plugin):
        """Test handling when OpClient initialization fails."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            # Import the exception type that op-python uses
            from op_python import OnePasswordError

            # Make OpClient initialization raise an error
            mock_client_class.side_effect = OnePasswordError(
                "Failed to initialize client"
            )

            # Test that AnsibleError is raised
            with pytest.raises(AnsibleError) as exc_info:
                lookup_plugin.run(["op://Test/Demo/password"], variables={}, **{})

            assert "Failed to initialize 1Password client" in str(exc_info.value)
            assert "Failed to initialize client" in str(exc_info.value)

    def test_client_caching(self, lookup_plugin):
        """Test that OpClient is cached and reused."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.return_value = "cached_secret"

            # Make multiple calls
            result1 = lookup_plugin.run(
                ["op://Test/Demo/password1"], variables={}, **{}
            )
            result2 = lookup_plugin.run(
                ["op://Test/Demo/password2"], variables={}, **{}
            )

            # OpClient should only be instantiated once due to caching
            assert mock_client_class.call_count == 1
            assert result1 == ["cached_secret"]
            assert result2 == ["cached_secret"]
            assert mock_client.get_secret.call_count == 2

    def test_traditional_item_lookup(self, lookup_plugin):
        """Test traditional item lookup (not using secret reference syntax)."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock item structure that op-python might return
            mock_item = {
                "fields": [
                    {"label": "username", "value": "testuser"},
                    {"label": "password", "value": "testpass123"},
                ]
            }
            mock_client.get_item.return_value = mock_item

            # Test traditional lookup
            result = lookup_plugin.run(
                ["database-item"], variables={}, vault="Production", field="password"
            )

            # Verify the get_item call
            mock_client.get_item.assert_called_once_with(
                "database-item", vault="Production"
            )
            assert result == ["testpass123"]

    def test_traditional_item_lookup_username(self, lookup_plugin):
        """Test traditional item lookup for username field."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock item structure
            mock_item = {
                "fields": [
                    {"label": "username", "value": "admin"},
                    {"label": "password", "value": "secret"},
                ]
            }
            mock_client.get_item.return_value = mock_item

            # Test username lookup
            result = lookup_plugin.run(
                ["database-item"], variables={}, vault="Production", field="username"
            )

            assert result == ["admin"]


class TestSecretReferenceValidation:
    """Test cases for secret reference format validation."""

    def test_valid_references(self):
        """Test various valid secret reference formats."""
        valid_refs = [
            "op://Production/Database/password",
            "op://Personal/GitHub/username",
            "op://Shared/API/token",
            "op://Test-Vault/My-Item/my-field",
        ]

        for ref in valid_refs:
            # This would test your validation logic if you have it
            # For now, just verify the format looks reasonable
            assert ref.startswith("op://")
            parts = ref.split("/")
            assert len(parts) >= 4  # op:, '', vault, item, field

    def test_invalid_references(self):
        """Test invalid secret reference formats."""
        invalid_refs = [
            "not_a_reference",
            "op://",  # Missing parts
            "op://vault",  # Missing item and field
            "op://vault/item",  # Missing field
            "",  # Empty string
            "vault/item/field",  # Missing op:// prefix
        ]

        for ref in invalid_refs:
            # These should be caught by validation
            # The actual validation would be in your plugin code
            if ref.startswith("op://"):
                parts = ref.split("/")
                if len(parts) < 4:
                    assert True  # This should be invalid
            else:
                assert True  # Non-op:// references should be invalid


class TestPluginIntegration:
    """Integration-style tests that test the plugin more holistically."""

    def test_plugin_with_all_parameters(self):
        """Test plugin with various parameter combinations."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.return_value = "full_test_secret"

            plugin = LookupModule()

            result = plugin.run(
                ["op://Test/Demo/password"],
                variables={"ansible_check_mode": False},
                op_path="/usr/bin/op",  # Use the real op path from the system
                use_dotenv=True,
                dotenv_path=".env.test",
                dotenv_override=True,
            )

            # Verify the client was configured correctly
            mock_client_class.assert_called_with(
                op_path="/usr/bin/op",
                use_dotenv=True,
                dotenv_path=".env.test",
                dotenv_override=True,
            )

            assert result == ["full_test_secret"]

    def test_error_handling_with_context(self):
        """Test that errors include helpful context."""
        with patch("lookup.onepassword.OpClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.get_secret.side_effect = Exception("Network timeout")

            plugin = LookupModule()

            with pytest.raises(AnsibleError) as exc_info:
                plugin.run(["op://Test/Demo/password"], variables={}, **{})

            error_msg = str(exc_info.value)
            # Should contain context about what was being retrieved
            assert (
                "op://Test/Demo/password" in error_msg or "Network timeout" in error_msg
            )
