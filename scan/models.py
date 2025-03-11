from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    activity_level = models.CharField(max_length=50, choices=[
        ('sedentary', 'Sedentary'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('very_active', 'Very Active'),
    ], null=True, blank=True)
    goal = models.CharField(max_length=50, choices=[
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('maintenance', 'Maintenance'),
    ], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    
    def calculate_bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight:
            height_m = self.height / 100  # converting cm to meters
            return round(self.weight / (height_m ** 2), 2)
        return None


class NutritionSearch(models.Model):
    """Model to store user nutrition searches for history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    food_item = models.CharField(max_length=100)
    search_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.food_item} - {self.search_date}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when User is created/updated"""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()