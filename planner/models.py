from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
# Create your models here.
class Neighborhood(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class ActivityLevel(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class PreferredCuisine(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class SocialContext(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Itinerary(models.Model): # Users have their own itineraries.
    name = models.CharField(max_length=255) # This will be AI Generated
    username = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # username = models.ForeignKey(User, on_delete=models.CASCADE)
    current_day = models.IntegerField(default=1)
    total_duration = models.IntegerField()

    def __str__(self):
        return f"{self.name}: {str(self.id)}"
    
class ItineraryActivity(models.Model):
    # username = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    activity_name = models.CharField(max_length=255)
    day = models.IntegerField(default=1)
    activity_neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE)
    activity_description = models.CharField(max_length=500)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()
    category = models.CharField(max_length=255)
    photo_name = models.CharField()
    address = models.CharField()
    # start_time = models.TimeField()
    # end_time = models.TimeField()
    def duration(self):
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        return end_dt - start_dt
    
    def __str__(self):
        return "Itinerary: " + str(self.itinerary.id)
    
class SurveyResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Optional for anonymous users

    trip_title = models.CharField(
        max_length=255,
        verbose_name="Trip Title",
        help_text="Give your trip a name",
        default="My Trip"
    )

    stay_length = models.IntegerField()

    stay_location = models.ForeignKey(
        'Neighborhood',
        on_delete=models.CASCADE,
        related_name='survey_stay_location'
    )

    preferred_cuisine = models.ForeignKey(
        'PreferredCuisine',
        on_delete=models.CASCADE
    )

    activity_level = models.ForeignKey(
        'ActivityLevel',
        on_delete=models.CASCADE
    )

    activity_window_start = models.TimeField()
    activity_window_end = models.TimeField()

    budget = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    social_context = models.ForeignKey(
        'SocialContext',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    radius = models.IntegerField(
        help_text="Radius in miles from stay location",
        default=1
    )

    dislikes = models.TextField(blank=True)

    def __str__(self):
        user_display = self.user.username if self.user else "Anonymous"
        return f"{user_display} - {self.stay_length} days in {self.stay_location.name}"


class FavoriteItinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    favorited_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'itinerary')  # prevent duplicate favorites

    def __str__(self):
        return f"{self.user.username} favorited {self.itinerary.name}"
