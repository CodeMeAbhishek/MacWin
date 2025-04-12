from django.db import models

# Create your models here.
class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    skills = models.TextField()  # comma-separated
    experience = models.PositiveIntegerField(default=0)  # years

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

    def __str__(self):
        return f"Question for {self.user_email} - {self.question_text[:50]}"


class QuizAnswer(models.Model):
    user_email = models.EmailField()
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user_email} - {self.answer_text[:50]}"