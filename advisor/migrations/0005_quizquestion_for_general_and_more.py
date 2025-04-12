# Generated by Django 5.1.7 on 2025-04-12 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advisor', '0004_githubprofile_remove_userprofile_experience_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizquestion',
            name='for_general',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='for_job_seekers',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='for_students',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='for_teachers',
            field=models.BooleanField(default=False),
        ),
    ]
