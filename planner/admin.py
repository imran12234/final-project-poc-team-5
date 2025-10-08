from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Neighborhood)
admin.site.register(Category)
admin.site.register(ActivityLevel)
admin.site.register(PreferredCuisine)
admin.site.register(Itinerary)
admin.site.register(ItineraryActivity)
admin.site.register(SurveyResponse)
admin.site.register(FavoriteItinerary)
admin.site.register(SocialContext)
