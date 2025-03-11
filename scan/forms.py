from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class DietPlanForm(forms.Form):
    GOAL_CHOICES = (
        ('loss', 'Weight Loss'),
        ('gain', 'Muscle Gain'),
        ('maintain', 'Maintenance'),
    )
    goal = forms.ChoiceField(
        choices=GOAL_CHOICES,
        widget=forms.RadioSelect,
        label="Select Your Goal"
    )


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'weight', 'height', 'activity_level', 'goal']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
        }


class BMIBMRForm(forms.Form):
    weight = forms.FloatField(
        label="Weight (kg)", 
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    height = forms.FloatField(
        label="Height (cm)", 
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    age = forms.IntegerField(
        label="Age (years)", 
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    ACTIVITY_LEVEL_CHOICES = (
        (1.2, 'Sedentary (little or no exercise)'),
        (1.375, 'Lightly active (light exercise/sports 1-3 days/week)'),
        (1.55, 'Moderately active (moderate exercise/sports 3-5 days/week)'),
        (1.725, 'Very active (hard exercise/sports 6-7 days a week)'),
        (1.9, 'Extra active (very hard exercise/physical job & exercise 2x/day)'),
    )
    activity_level = forms.ChoiceField(
        choices=ACTIVITY_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FoodSearchForm(forms.Form):
    food_item = forms.CharField(
        label="Search for a food",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter food name (e.g., apple, chicken)'
        })
    )