import json
from django.core.management.base import BaseCommand
from profiles.models import Profile

class Command(BaseCommand):
    help = 'Seed profiles from JSON file without duplicates'

    def handle(self, *args, **options):
        with open('seed_profiles.json', 'r', encoding='utf-8') as f:
            content = f.read()
            # Try to parse as JSON
            data = json.loads(content)

        # If data is a dict, try to find a list inside it
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    data = value
                    break
            else:
                self.stdout.write(self.style.ERROR('No list found in JSON file'))
                return

        # Ensure data is a list
        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR('JSON file must contain a list of profiles'))
            return

        created = 0
        for item in data:
            obj, created_flag = Profile.objects.get_or_create(
                name=item['name'],
                defaults={
                    'gender': item['gender'],
                    'gender_probability': item['gender_probability'],
                    'age': item['age'],
                    'age_group': item['age_group'],
                    'country_id': item['country_id'],
                    'country_name': item['country_name'],
                    'country_probability': item['country_probability'],
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new profiles'))