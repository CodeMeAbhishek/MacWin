from django.core.management.base import BaseCommand
from advisor.models import JobMarketData

class Command(BaseCommand):
    help = 'Loads dummy job market data'

    def handle(self, *args, **kwargs):
        JobMarketData.objects.all().delete()
        jobs = [
            {'role': 'Frontend Developer', 'required_skills': 'HTML,CSS,JavaScript', 'average_salary': 60000, 'demand_level': 'High'},
            {'role': 'Backend Developer', 'required_skills': 'Python,Django', 'average_salary': 70000, 'demand_level': 'Medium'},
            {'role': 'Data Analyst', 'required_skills': 'Python,Excel,SQL', 'average_salary': 65000, 'demand_level': 'High'},
            {'role': 'DevOps Engineer', 'required_skills': 'Linux,Docker,AWS', 'average_salary': 85000, 'demand_level': 'Low'},
        ]

        for job in jobs:
            JobMarketData.objects.create(**job)

        self.stdout.write(self.style.SUCCESS('✅ Dummy job data loaded successfully!'))
