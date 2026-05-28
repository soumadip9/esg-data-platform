from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tenants.models import PlantCode, Tenant


def seed_tenant(slug, name, plants, analyst_username, analyst_email, analyst_first, analyst_last):
    tenant, _ = Tenant.objects.get_or_create(slug=slug, defaults={"name": name})
    for code, plant_name, country in plants:
        PlantCode.objects.get_or_create(
            tenant=tenant, code=code, defaults={"name": plant_name, "country": country}
        )
    user, created = User.objects.get_or_create(
        username=analyst_username,
        defaults={
            "email": analyst_email,
            "first_name": analyst_first,
            "last_name": analyst_last,
            "tenant": tenant,
            "role": User.Role.ANALYST,
        },
    )
    if created:
        user.set_password("demo1234")
        user.save()
    return tenant, user, created


class Command(BaseCommand):
    help = "Seed demo tenants, plant codes, and analyst users"

    def handle(self, *args, **options):
        acme, analyst, created = seed_tenant(
            slug="acme-corp",
            name="Acme Corporation",
            plants=[
                ("1000", "Acme HQ — Frankfurt", "DE"),
                ("2000", "Acme Plant — Munich", "DE"),
                ("3000", "Acme US — Chicago", "US"),
                ("UK01", "Acme UK — London", "GB"),
            ],
            analyst_username="analyst",
            analyst_email="analyst@acme.example",
            analyst_first="Jordan",
            analyst_last="Lee",
        )
        self.stdout.write(f"Tenant: {acme.name}")
        if created:
            self.stdout.write(self.style.SUCCESS("Created analyst / demo1234 (Acme)"))
        else:
            self.stdout.write("Analyst user already exists (Acme)")

        globex, analyst2, created2 = seed_tenant(
            slug="globex-ind",
            name="Globex Industries",
            plants=[
                ("G100", "Globex HQ — Singapore", "SG"),
                ("G200", "Globex Plant — Mumbai", "IN"),
            ],
            analyst_username="analyst2",
            analyst_email="analyst@globex.example",
            analyst_first="Priya",
            analyst_last="Sharma",
        )
        self.stdout.write(f"Tenant: {globex.name}")
        if created2:
            self.stdout.write(self.style.SUCCESS("Created analyst2 / demo1234 (Globex)"))
        else:
            self.stdout.write("Analyst2 user already exists (Globex)")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@acme.example",
                "is_staff": True,
                "is_superuser": True,
                "tenant": acme,
                "role": User.Role.ADMIN,
            },
        )
        if created:
            admin_user.set_password("admin1234")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin / admin1234"))
