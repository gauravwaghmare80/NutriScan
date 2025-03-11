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