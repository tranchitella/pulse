from io import StringIO
from unittest.mock import MagicMock, Mock, patch

from django.core.management import call_command
from django.test import TestCase

from tenants.management.commands.populate_db import Command


class PopulateDBCommandTest(TestCase):
    def setUp(self):
        self.mock_tenants_data = [
            {
                "schema_name": "public",
                "subdomain": "",
                "name": "Public",
                "owner": {
                    "username": "admin@example.com",
                    "email": "admin@example.com",
                    "password": "admin123",
                },
            },
            {
                "schema_name": "tenant1",
                "subdomain": "tenant1",
                "name": "Tenant 1",
                "owner": {
                    "username": "owner1@example.com",
                    "email": "owner1@example.com",
                    "password": "password123",
                },
            },
        ]

    @patch("tenants.models.Tenant.objects.get")
    @patch("tenants.management.commands.populate_db.connect")
    @patch("tenants.management.commands.populate_db.call_command")
    @patch("tenants.management.commands.populate_db.create_public_tenant")
    @patch("tenants.management.commands.populate_db.provision_tenant")
    @patch("tenants.management.commands.populate_db.UserTenantPermissions.objects.filter")
    @patch("json.load")
    def test_command_executes_successfully(
        self,
        mock_json_load,
        mock_user_permissions_filter,
        mock_provision,
        mock_create_public,
        mock_call_command,
        mock_connect,
        mock_tenant_get,
    ):
        # Setup mocks
        mock_json_load.return_value = self.mock_tenants_data

        mock_public_tenant = Mock()
        mock_public_tenant.schema_name = "public"
        mock_root_user = Mock()
        mock_create_public.return_value = (mock_public_tenant, Mock(), mock_root_user)

        # Mock Tenant.objects.get to return public tenant
        mock_tenant_get.return_value = mock_public_tenant

        mock_private_tenant = Mock()
        mock_private_tenant.schema_name = "tenant1"
        mock_private_tenant.add_user = Mock()
        mock_provision.return_value = (mock_private_tenant, Mock())

        # Ensure UserTenantPermissions.objects.filter(...).first() returns an object
        mock_user_permissions = Mock()
        mock_user_permissions.groups = Mock()
        mock_user_permissions_filter.return_value.first.return_value = mock_user_permissions

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Execute command
        out = StringIO()
        call_command("populate_db", stdout=out)

        # Assertions
        mock_connect.assert_called_once()
        mock_call_command.assert_called_once_with(
            "migrate_schemas", "--shared", "--noinput"
        )
        mock_create_public.assert_called_once()
        self.assertIn("successfully", out.getvalue())

    @patch("tenants.management.commands.populate_db.connect")
    @patch("json.load")
    def test_drop_and_recreate_db(self, mock_json_load, mock_connect):
        mock_json_load.return_value = self.mock_tenants_data

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cmd = Command()
        cmd.drop_and_recreate_db()

        # Verify database connection was made
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()

        # Verify execute was called (terminate connections, drop, create)
        self.assertEqual(mock_cursor.execute.call_count, 3)
