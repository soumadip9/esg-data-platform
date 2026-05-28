from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tenants.models import PlantCode, Tenant


class Command(BaseCommand):
    help = "Seed demo tenant, plant codes, and analyst user"

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(
            slug="acme-corp",
            defaults={"name": "Acme Corporation"},
        )
        self.stdout.write(f"Tenant: {tenant.name}")

        plants = [
            ("1000", "Acme HQ — Frankfurt", "DE"),
            ("2000", "Acme Plant — Munich", "DE"),
            ("3000", "Acme US — Chicago", "US"),
            ("UK01", "Acme UK — London", "GB"),
        ]
        for code, name, country in plants:
            PlantCode.objects.get_or_create(
                tenant=tenant, code=code, defaults={"name": name, "country": country}
            )

        user, created = User.objects.get_or_create(
            username="analyst",
            defaults={
                "email": "analyst@acme.example",
                "first_name": "Jordan",
                "last_name": "Lee",
                "tenant": tenant,
                "role": User.Role.ANALYST,
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created analyst / demo1234"))
        else:
            self.stdout.write("Analyst user already exists")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@acme.example",
                "is_staff": True,
                "is_superuser": True,
                "tenant": tenant,
                "role": User.Role.ADMIN,
            },
        )
        if created:
            admin_user.set_password("admin1234")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin / admin1234"))
