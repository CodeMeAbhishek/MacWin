from django.db import models

# Create your models here.

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    skills = models.TextField()
    years_of_experience = models.IntegerField()
    age = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Individual', 'Individual'),
        ('Job-seeker', 'Job-seeker'),
    ], null=True, blank=True)
    quiz_answers = models.TextField(null=True, blank=True)  # Store quiz answers as JSON
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

class JobMarketData(models.Model):
    role = models.CharField(max_length=100)
    required_skills = models.TextField()
    average_salary = models.PositiveIntegerField()
    demand_level = models.CharField(max_length=50)

from django.db import models

class CareerAdviceHistory(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    skills = models.TextField()
    experience = models.PositiveIntegerField()
    advice = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Advice for {self.name} ({self.email}) at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class QuizQuestion(models.Model):
    user_email = models.EmailField()
    question_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    for_students = models.BooleanField(default=False)
    for_teachers = models.BooleanField(default=False)
    for_job_seekers = models.BooleanField(default=False)
    for_general = models.BooleanField(default=True)

    def __str__(self):
        return f"Question for {self.user_email} - {self.question_text[:50]}"


class QuizAnswer(models.Model):
    user_email = models.EmailField()
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user_email} - {self.answer_text[:50]}"
    
class GitHubProfile(models.Model):
    username = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    profile_url = models.URLField()
    bio = models.TextField(null=True, blank=True)
    repos_count = models.PositiveIntegerField(default=0)
    languages = models.TextField(null=True, blank=True)  # Comma-separated
    followers = models.PositiveIntegerField(default=0)
    matched_skills = models.TextField(null=True, blank=True)  # Matching skills with our user
    timestamp = models.DateTimeField(auto_now_add=True)
