import json

from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand, call_command
from django_tenants.utils import schema_context
from psycopg2 import connect, sql
from tenant_users.permissions.models import UserTenantPermissions
from tenant_users.tenants.tasks import provision_tenant
from tenant_users.tenants.utils import create_public_tenant

from pulse import settings
from tenants.models import User


class Command(BaseCommand):
    help = "Creates a public tenant and two demo tenants"
    tenants_data_file = "tenants/data/tenants.json"

    root_user = None
    public_tenant = None

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        # Load the tenant data from the JSON file
        self.tenants_data = []
        with open(self.tenants_data_file, "r") as file:
            self.tenants_data = json.load(file)

    def handle(self, *args, **kwargs):
        self.drop_and_recreate_db()
        call_command("migrate_schemas", "--shared", "--noinput")
        self.stdout.write(
            self.style.SUCCESS("Database recreated & migrated successfully.")
        )

        self.create_public_tenant()
        self.create_private_tenants()

        self.stdout.write(
            self.style.SUCCESS("Yay, database has been populated successfully.")
        )

    def drop_and_recreate_db(self):
        db = settings.DATABASES["default"]
        db_name = db["NAME"]

        # Create a connection to the database
        conn = connect(
            dbname="postgres",
            user=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=db["PORT"],
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Terminate all connections to the database except the current one
        cur.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s
              AND pid <> pg_backend_pid();
            """,
            [db_name],
        )

        # Drop the database if it exists and create a new one
        cur.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
        )
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

        cur.close()
        conn.close()

    def create_public_tenant(self):
        self.stdout.write("Creating the public tenant...")
        public_tenant_data = self.tenants_data[0]

        # Create the public tenant and the root user
        public_tenant, _, root_user = create_public_tenant(
            domain_url=settings.BASE_DOMAIN,
            tenant_extra_data={"slug": public_tenant_data["subdomain"]},
            owner_email=public_tenant_data["owner"]["email"],
            is_superuser=True,
            is_staff=True,
            **{
                "password": public_tenant_data["owner"]["password"],
                "is_verified": True,
            },
        )
        self.public_tenant = public_tenant
        self.root_user = root_user

        self.stdout.write(
            self.style.SUCCESS(
                f"Public tenant ('{public_tenant.schema_name}') has been successfully created."
            )
        )

    def create_private_tenants(self):
        private_tenant_data = self.tenants_data[1:]

        for tenant_data in private_tenant_data:
            self.stdout.write(f"Creating tenant {tenant_data['schema_name']}...")

            # Create the tenant owner
            tenant_owner = User.objects.create_user(
                email=tenant_data["owner"]["email"],
                password=tenant_data["owner"]["password"],
            )
            tenant_owner.is_verified = True
            tenant_owner.save()

            # Create the tenant
            tenant, _ = provision_tenant(
                tenant_name=tenant_data["name"],
                tenant_slug=tenant_data["subdomain"],
                schema_name=tenant_data["schema_name"],
                owner=tenant_owner,
                is_superuser=False,
                is_staff=True,
            )

            with schema_context(tenant.schema_name):
                # Create a tenant-specific Device Manager group
                device_manager_group = Group.objects.create(name="Device Manager")
                device_manager_group.permissions.add(
                    Permission.objects.get(codename="add_device"),
                    Permission.objects.get(codename="change_device"),
                    Permission.objects.get(codename="delete_device"),
                    Permission.objects.get(codename="view_device"),
                )

                # Create a tenant-specific User and Group Manager group
                user_manager_group = Group.objects.create(name="User and Group Manager")
                user_manager_group.permissions.add(
                    Permission.objects.get(codename="add_group"),
                    Permission.objects.get(codename="change_group"),
                    Permission.objects.get(codename="delete_group"),
                    Permission.objects.get(codename="view_group"),
                )

                # Link the user to the tenant and assign the tenant-specific group
                user_permissions = UserTenantPermissions.objects.filter(
                    profile=tenant_owner
                ).first()
                user_permissions.groups.add(device_manager_group)
                user_permissions.groups.add(user_manager_group)
                user_permissions.save()

            # Add the root user to the tenant
            tenant.add_user(
                self.root_user,
                is_superuser=True,
                is_staff=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Tenant '{tenant.schema_name}' has been successfully created."
                )
            )
