from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegisterForm(forms.ModelForm):
    # username = forms.CharField(max_length=100)
    # email = forms.EmailField()
    # password = forms.PasswordInput(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'weight', 'height', 'activity_level', 'goal']

class BMIBMRForm(forms.Form):
    weight = forms.FloatField(label="Weight (kg)", min_value=0)
    height = forms.FloatField(label="Height (cm)", min_value=0)
    age = forms.IntegerField(label="Age (years)", min_value=0)
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    ACTIVITY_LEVEL_CHOICES = (
        (1.2, 'Sedentary (little or no exercise)'),
        (1.375, 'Lightly active (light exercise/sports 1-3 days/week)'),
        (1.55, 'Moderately active (moderate exercise/sports 3-5 days/week)'),
        (1.725, 'Very active (hard exercise/sports 6-7 days a week)'),
        (1.9, 'Extra active (very hard exercise/physical job & exercise 2x/day)'),
    )
    activity_level = forms.ChoiceField(choices=ACTIVITY_LEVEL_CHOICES)
