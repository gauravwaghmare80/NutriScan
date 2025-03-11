{% comment %} forms.py {% endcomment %}
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


{% comment %} models.py {% endcomment %}
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



{% comment %} views.py {% endcomment %}
import requests
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse

from .forms import UserRegisterForm, UserProfileForm, BMIBMRForm, DietPlanForm, FoodSearchForm
from .models import UserProfile, NutritionSearch


def home(request):
    return render(request, 'scan/index.html')


def fetch_usda_nutrition(food_name):
    """Fetches nutrition details from USDA API for a given food name."""
    api_key = getattr(settings, "USDA_API_KEY", None)
    if not api_key:
        return {"error": "USDA API Key is missing in settings"}

    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "foods" in data and data["foods"]:
            food = data["foods"][0]
            nutrients = {}
            
            # Extract nutrients in a more robust way
            for nutrient in food.get("foodNutrients", []):
                nutrient_name = nutrient.get("nutrientName")
                if nutrient_name:
                    nutrients[nutrient_name] = nutrient.get("value", "N/A")

            # Get specific nutrients with fallbacks
            return {
                'product_name': food.get("description", "Unknown"),
                'calories': nutrients.get("Energy", "N/A"),
                'proteins': nutrients.get("Protein", "N/A"),
                'carbohydrates': nutrients.get("Carbohydrate, by difference", "N/A"),
                'fats': nutrients.get("Total lipid (fat)", "N/A"),
                'fiber': nutrients.get("Fiber, total dietary", "N/A"),
                'sugars': nutrients.get("Sugars, total including NLEA", "N/A"),
                'sodium': nutrients.get("Sodium, Na", "N/A"),
                'potassium': nutrients.get("Potassium, K", "N/A"),
                'image_url': ""  # Placeholder for image
            }
        return {"error": "No nutritional data found for this food"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching data from USDA API: {str(e)}"}


def recommend_foods(user_profile):
    """Suggests foods based on user dietary goals using USDA API."""
    goal = user_profile.goal if user_profile else "maintenance"
    
    food_suggestions = {
        "weight_loss": ["Broccoli", "Chicken Breast", "Oatmeal", "Almonds", "Greek Yogurt"],
        "muscle_gain": ["Eggs", "Salmon", "Quinoa", "Greek Yogurt", "Sweet Potato", "Lean Beef"],
        "maintenance": ["Brown Rice", "Avocado", "Chicken", "Mixed Vegetables", "Nuts", "Fruits"]
    }

    # Map from model choices to dictionary keys
    goal_mapping = {
        "weight_loss": "weight_loss",
        "muscle_gain": "muscle_gain",
        "maintenance": "maintenance"
    }
    
    mapped_goal = goal_mapping.get(goal, "maintenance")
    suggested_items = food_suggestions.get(mapped_goal, ["Fruits", "Whole Grains", "Proteins"])

    recommendations = []
    for item in suggested_items[:3]:  # Limit to 3 items to avoid API rate limits
        food_data = fetch_usda_nutrition(item)
        if "error" not in food_data:
            recommendations.append(food_data)

    return recommendations


@login_required(login_url='/login/')
def get_nutrition(request):
    """View for handling nutrition data search and display"""
    form = FoodSearchForm()
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        recommendations = recommend_foods(user_profile)
    except UserProfile.DoesNotExist:
        recommendations = []
        messages.warning(request, "Please complete your profile to get personalized recommendations")

    if request.method == "GET" and 'food_item' in request.GET:
        form = FoodSearchForm(request.GET)
        if form.is_valid():
            food_item = form.cleaned_data['food_item']
            
            # Save search to history
            NutritionSearch.objects.create(
                user=request.user,
                food_item=food_item
            )
            
            nutrition_data = fetch_usda_nutrition(food_item)
            
            if "error" in nutrition_data:
                messages.error(request, nutrition_data["error"])
                return render(request, 'scan/nutrition_search.html', {
                    'form': form,
                    'recommendations': recommendations
                })
            
            return render(request, 'scan/nutrition_result.html', {
                'nutrition_data': nutrition_data,
                'recommendations': recommendations
            })

    return render(request, 'scan/nutrition_search.html', {
        'form': form,
        'recommendations': recommendations
    })


def register(request):
    """Register a new user and create their profile"""
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            username = user_form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please complete your profile.')
            login(request, user)
            return redirect('edit_profile')
    else:
        user_form = UserRegisterForm()
    
    return render(request, "scan/register.html", {"user_form": user_form})


def user_login(request):
    """Handle user login"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_page = request.GET.get('next', 'dashboard')
            messages.success(request, f'Welcome back, {username}!')
            return redirect(next_page)
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "scan/login.html")


def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, "You have been logged out successfully!")
    return redirect("home")


@login_required
def dashboard(request):
    """User dashboard with profile summary and recent activities"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        bmi = profile.calculate_bmi()
    except UserProfile.DoesNotExist:
        profile = None
        bmi = None
    
    # Get recent nutrition searches
    recent_searches = NutritionSearch.objects.filter(
        user=request.user
    ).order_by('-search_date')[:5]
    
    context = {
        'profile': profile,
        'bmi': bmi,
        'recent_searches': recent_searches,
    }
    
    return render(request, "scan/dashboard.html", context)


@login_required
def edit_profile(request):
    """Edit user profile information"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'scan/edit_profile.html', {'form': form})


def bmi_bmr_calculator(request):
    """Calculate BMI and BMR based on form inputs"""
    result = {}
    if request.method == 'POST':
        form = BMIBMRForm(request.POST)
        if form.is_valid():
            weight = form.cleaned_data['weight']
            height = form.cleaned_data['height']
            age = form.cleaned_data['age']
            gender = form.cleaned_data['gender']
            activity_factor = float(form.cleaned_data['activity_level'])
            
            # BMI Calculation: weight (kg) / (height in m)^2
            height_m = height / 100  # converting cm to meters
            bmi = weight / (height_m ** 2)
            
            # BMR Calculation using the Harris-Benedict Equation
            if gender == 'male':
                bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
            
            # Adjusting BMR with the activity level
            bmr_adjusted = bmr * activity_factor
            
            # Calculate daily calorie needs for different goals
            calories_maintenance = round(bmr_adjusted)
            calories_loss = round(bmr_adjusted * 0.8)  # 20% deficit
            calories_gain = round(bmr_adjusted * 1.15)  # 15% surplus
            
            # Determine BMI category
            bmi_category = "Unknown"
            if bmi < 18.5:
                bmi_category = "Underweight"
            elif 18.5 <= bmi < 25:
                bmi_category = "Normal weight"
            elif 25 <= bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obesity"
            
            result = {
                'bmi': round(bmi, 2),
                'bmi_category': bmi_category,
                'bmr': round(bmr, 2),
                'bmr_adjusted': round(bmr_adjusted, 2),
                'calories_maintenance': calories_maintenance,
                'calories_loss': calories_loss,
                'calories_gain': calories_gain
            }
            
            # If user is logged in, optionally update their profile
            if request.user.is_authenticated and request.POST.get('update_profile'):
                try:
                    profile = UserProfile.objects.get(user=request.user)
                    profile.weight = weight
                    profile.height = height
                    profile.age = age
                    profile.save()
                    messages.success(request, "Your profile has been updated with these measurements.")
                except UserProfile.DoesNotExist:
                    pass
    else:
        # Pre-fill form with user data if available
        initial_data = {}
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                initial_data = {
                    'weight': profile.weight,
                    'height': profile.height,
                    'age': profile.age
                }
            except UserProfile.DoesNotExist:
                pass
        
        form = BMIBMRForm(initial=initial_data)
        
    return render(request, 'scan/bmi_bmr_calculator.html', {'form': form, 'result': result})


def personalized_diet_plan(request):
    """Generate a personalized diet plan based on user goals"""
    plan = None
    
    # If user is logged in, pre-select their goal from profile
    initial_goal = None
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            # Map from model choice to form choice
            goal_mapping = {
                "weight_loss": "loss",
                "muscle_gain": "gain",
                "maintenance": "maintain"
            }
            initial_goal = goal_mapping.get(profile.goal)
        except UserProfile.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data['goal']
            
            # Get BMR/calorie info if available from profile
            calorie_info = None
            if request.user.is_authenticated:
                try:
                    profile = UserProfile.objects.get(user=request.user)
                    if all([profile.weight, profile.height, profile.age]):
                        # Calculate BMR (simplified)
                        height_m = profile.height / 100
                        bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age)
                        # Assume moderate activity if not specified
                        activity_factor = 1.55
                        if profile.activity_level:
                            activity_mapping = {
                                'sedentary': 1.2,
                                'lightly_active': 1.375,
                                'moderately_active': 1.55,
                                'very_active': 1.725
                            }
                            activity_factor = activity_mapping.get(profile.activity_level, 1.55)
                        
                        bmr_adjusted = bmr * activity_factor
                        
                        if goal == 'loss':
                            calorie_target = round(bmr_adjusted * 0.8)
                        elif goal == 'gain':
                            calorie_target = round(bmr_adjusted * 1.15)
                        else:
                            calorie_target = round(bmr_adjusted)
                        
                        calorie_info = f"Your estimated daily calorie target: {calorie_target} calories"
                except UserProfile.DoesNotExist:
                    pass
            
            # Sample logic for diet plan suggestions - enhanced with more details
            if goal == 'loss':
                plan = {
                    'title': "Weight Loss Diet Plan",
                    'description': "Focus on a calorie deficit with nutrient-dense foods. Include lean proteins, vegetables, and whole grains.",
                    'calorie_info': calorie_info,
                    'principles': [
                        "Create a moderate calorie deficit (15-20% below maintenance)",
                        "Eat protein with every meal to preserve muscle mass",
                        "Focus on high-volume, low-calorie foods like vegetables",
                        "Stay hydrated - drink at least 8 glasses of water daily",
                        "Limit processed foods and added sugars"
                    ],
                    'meals': [
                        {
                            'name': "Breakfast",
                            'options': [
                                "Oatmeal with berries and a boiled egg",
                                "Greek yogurt with nuts and fruit",
                                "Vegetable omelette with whole grain toast"
                            ]
                        },
                        {
                            'name': "Lunch",
                            'options': [
                                "Grilled chicken salad with vinaigrette",
                                "Turkey and vegetable wrap",
                                "Lentil soup with side salad"
                            ]
                        },
                        {
                            'name': "Snack",
                            'options': [
                                "Greek yogurt with nuts",
                                "Apple slices with peanut butter",
                                "Vegetable sticks with hummus"
                            ]
                        },
                        {
                            'name': "Dinner",
                            'options': [
                                "Steamed fish with quinoa and mixed vegetables",
                                "Baked chicken with roasted vegetables",
                                "Tofu stir-fry with brown rice"
                            ]
                        }
                    ]
                }
            elif goal == 'gain':
                plan = {
                    'title': "Muscle Gain Diet Plan",
                    'description': "Increase protein intake and consume calorie surplus foods. Incorporate strength training friendly meals.",
                    'calorie_info': calorie_info,
                    'principles': [
                        "Eat in a moderate calorie surplus (10-20% above maintenance)",
                        "Consume 1.6-2.2g of protein per kg of bodyweight",
                        "Time your carbohydrates around workouts",
                        "Include healthy fats for hormone production",
                        "Eat frequently - 4-6 meals per day"
                    ],
                    'meals': [
                        {
                            'name': "Breakfast",
                            'options': [
                                "Eggs with whole-grain toast and avocado",
                                "Protein pancakes with banana and honey",
                                "Smoothie with protein powder, milk, banana, and peanut butter"
                            ]
                        },
                        {
                            'name': "Lunch",
                            'options': [
                                "Turkey sandwich with a side of sweet potatoes",
                                "Chicken and rice bowl with vegetables",
                                "Beef burrito with beans and cheese"
                            ]
                        },
                        {
                            'name': "Snack",
                            'options': [
                                "Protein smoothie with banana and peanut butter",
                                "Trail mix with dried fruits and nuts",
                                "Cottage cheese with pineapple"
                            ]
                        },
                        {
                            'name': "Dinner",
                            'options': [
                                "Lean steak with brown rice and broccoli",
                                "Salmon with quinoa and asparagus",
                                "Chicken pasta with olive oil and vegetables"
                            ]
                        }
                    ]
                }
            elif goal == 'maintain':
                plan = {
                    'title': "Maintenance Diet Plan",
                    'description': "Balance your calories with a mix of proteins, carbs, and fats. Focus on variety and moderation.",
                    'calorie_info': calorie_info,
                    'principles': [
                        "Eat at maintenance calories",
                        "Focus on whole, minimally processed foods",
                        "Ensure adequate protein intake (1.2-1.6g per kg bodyweight)",
                        "Include a variety of fruits and vegetables",
                        "Practice mindful eating"
                    ],
                    'meals': [
                        {
                            'name': "Breakfast",
                            'options': [
                                "Smoothie bowl with assorted fruits and granola",
                                "Whole grain toast with avocado and eggs",
                                "Overnight oats with nuts and berries"
                            ]
                        },
                        {
                            'name': "Lunch",
                            'options': [
                                "Mixed greens with tofu and a light dressing",
                                "Mediterranean bowl with falafel and hummus",
                                "Tuna salad sandwich on whole grain bread"
                            ]
                        },
                        {
                            'name': "Snack",
                            'options': [
                                "Mixed nuts and a piece of fruit",
                                "Yogurt with honey",
                                "Whole grain crackers with cheese"
                            ]
                        },
                        {
                            'name': "Dinner",
                            'options': [
                                "Baked salmon with wild rice and steamed vegetables",
                                "Chicken stir-fry with mixed vegetables",
                                "Vegetable curry with brown rice"
                            ]
                        }
                    ]
                }
    else:
        form = DietPlanForm(initial={'goal': initial_goal} if initial_goal else None)
        
    return render(request, 'scan/diet_plan.html', {'form': form, 'plan': plan})


{% comment %} urls.py {% endcomment %}

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile management
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Nutrition features
    path('nutrition/search/', views.get_nutrition, name='get_nutrition'),
    path('bmi-bmr/', views.bmi_bmr_calculator, name='bmi_bmr_calculator'),
    path('diet-plan/', views.personalized_diet_plan, name='personalized_diet_plan'),
]

{% comment %} admin.py {% endcomment %}

from django.contrib import admin
from .models import UserProfile, NutritionSearch

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'weight', 'height', 'goal', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('goal', 'activity_level')

class NutritionSearchAdmin(admin.ModelAdmin):
    list_display = ('food_item', 'user', 'search_date')
    search_fields = ('food_item', 'user__username')
    list_filter = ('search_date',)

# Register your models here.
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(NutritionSearch, NutritionSearchAdmin)

