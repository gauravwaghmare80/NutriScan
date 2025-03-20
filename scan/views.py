import requests
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.contrib.messages import get_messages
from .forms import UserRegisterForm, UserProfileForm, BMIBMRForm, DietPlanForm, FoodSearchForm
from .models import UserProfile, NutritionSearch


def home(request):
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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
                return render(request, 'scan/food_nutrition_search.html', {
                    'form': form,
                    'recommendations': recommendations
                })
            
            return render(request, 'scan/nutrition_result.html', {
                'nutrition_data': nutrition_data,
                'recommendations': recommendations
            })

    return render(request, 'scan/food_nutrition_search.html', {
        'form': form,
        'recommendations': recommendations
    })


def register(request):
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
    """Register a new user and create their profile"""
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        
        if user_form.is_valid():
            user = user_form.save()  # Django's UserCreationForm already handles password hashing
            
            # Automatically log in the user after successful registration
            login(request, user)

            messages.success(request, f'Account created successfully for {user.username}! Please complete your profile.')
            return redirect('edit_profile')  # Make sure 'edit_profile' exists in urls.py
        else:
            # Don't show a generic error - form errors will display automatically in the template
            pass
    else:
        user_form = UserRegisterForm()

    context = {
        "user_form": user_form
    }

    return render(request, "scan/register.html", context)


def user_login(request):
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
    """Handle user logout"""
    logout(request)
    messages.info(request, "You have been logged out successfully!")
    return redirect("home")


@login_required
def dashboard(request):
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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


from django.shortcuts import render
from django.contrib import messages
from .forms import BMIBMRForm
from .models import UserProfile

def bmi_bmr_calculator(request): 
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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
            
            # Convert height to meters
            height_m = height / 100  
            
            # BMI Calculation: weight (kg) / (height in m)^2
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

            # Calculate ideal weight range (BMI 18.5 - 24.9)
            ideal_weight_low = 18.5 * (height_m ** 2)
            ideal_weight_high = 24.9 * (height_m ** 2)

            # Determine weight difference
            weight_difference = 0
            if bmi < 18.5:  # Underweight
                weight_difference = round(ideal_weight_low - weight, 2)
            elif bmi >= 25:  # Overweight or Obese
                weight_difference = round(weight - ideal_weight_high, 2)

            # Prepare result dictionary
            result = {
                'bmi': round(bmi, 2),
                'bmi_category': bmi_category,
                'bmr': round(bmr, 2),
            }

            if bmi < 18.5:  # Underweight
                result['calories_gain'] = calories_gain
                result['weight_difference'] = weight_difference
            elif bmi >= 25:  # Overweight or Obese
                result['calories_loss'] = calories_loss
                result['weight_difference'] = weight_difference
            else:  # Normal weight
                result['calories_maintenance'] = calories_maintenance

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
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
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

def search(request):
    # Clear the messages
    storage = get_messages(request)
    for _ in storage:  # Iterating through to clear the messages
        pass  
    return render(request,'scan/food_nutrition_search.html')