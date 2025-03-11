import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib.auth import login, authenticate, logout
from .models import UserProfile
from .forms import BMIBMRForm

def home(request):
    return render(request, 'scan/index.html')

# ✅ Fetch Nutrition Data from USDA API
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
            nutrients = {nutrient["nutrientName"]: nutrient["value"] for nutrient in food.get("foodNutrients", [])}

            return {
                'product_name': food.get("description", "Unknown"),
                'calories': nutrients.get("Energy", "N/A"),
                'proteins': nutrients.get("Protein", "N/A"),
                'carbohydrates': nutrients.get("Carbohydrate, by difference", "N/A"),
                'fats': nutrients.get("Total lipid (fat)", "N/A"),
                'image_url': ""  # Add actual image handling if needed
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching data from USDA API: {str(e)}"}

    return {"error": "No nutritional data found for this food"}

# ✅ Recommend Foods Based on User Profile
def recommend_foods(user_profile):
    """Suggests foods based on user dietary goals using USDA API."""
    goal = user_profile.goal if user_profile else "balanced_diet"
    food_suggestions = {
        "weight_loss": ["Broccoli", "Chicken Breast", "Oatmeal", "Almonds"],
        "muscle_gain": ["Eggs", "Salmon", "Quinoa", "Greek Yogurt"],
        "balanced_diet": ["Brown Rice", "Vegetables", "Lean Meat", "Nuts"]
    }

    recommendations = []
    suggested_items = food_suggestions.get(goal, ["Fruits", "Whole Grains", "Proteins"])

    for item in suggested_items:
        food_data = fetch_usda_nutrition(item)
        if "error" not in food_data:
            recommendations.append(food_data)

    return recommendations

# ✅ Main View Handling Nutrition & Recommendations
@login_required(login_url='/login/')
def get_nutrition(request):
    # try:
    #     user_profile = UserProfile.objects.get(user=request.user)
    # except UserProfile.DoesNotExist:
        # return render(request, 'scan/index.html', {'error': 'User profile not found'})

    # recommendations = recommend_foods(user_profile)

    if request.method == "GET":
        food_item = request.GET.get('food_item', '').strip()

        if not food_item:
            return render(request, 'scan/index.html', {'error': 'Please enter a food item'}) # 'recommendations': recommendations}

        if food_item.isdigit():  # Placeholder for packaged food handling
            nutrition_data = {"error": "Packaged food lookup is not implemented"}  # Implement get_packaged_food_nutrition if needed
        else:
            nutrition_data = fetch_usda_nutrition(food_item)

        if "error" in nutrition_data:
            return render(request, 'scan/index.html', {'error': nutrition_data["error"]}) # 'recommendations': recommendations}

        return render(request, 'scan/nutrition_result.html', {**nutrition_data}) # 'recommendations': recommendations}

    # return render(request, 'scan/index.html', {'recommendations': recommendations})

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")  # Redirect to dashboard or any other page
    else:
        form = UserRegisterForm()
    return render(request, "scan/register.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "scan/login.html", {"error": "Invalid username or password"})
    return render(request, "scan/login.html")

def user_logout(request):
    logout(request)
    return redirect("home")

def dashboard(request):
    return render(request, "scan/dashboard.html")


def bmi_bmr_calculator(request):
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
            
            result = {
                'bmi': round(bmi, 2),
                'bmr': round(bmr_adjusted, 2)
            }
    else:
        form = BMIBMRForm()
        
    return render(request, 'scan/bmi_bmr_calculator.html', {'form': form, 'result': result})
