from django.utils.timezone import now
from datetime import timedelta, datetime, date
from .openaistuff.recommender_prompt import get_recommendations
from .googleplaces.google_places_api import get_image
from django.shortcuts import render, redirect, get_object_or_404
from datetime import time as dt_time
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import time as dt_time
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
import requests
import os
from .forms import FullSurveyForm
import json
from django.db.models import Prefetch
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm


def survey_page(request):
    if request.method == "POST":
        form = SurveyResponseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            response = form.save(commit=False)
            if request.user.is_authenticated:
                response.username = request.user
            response.save()
            request.session['survey_data'] = {
                "trip_title": data['trip_title'],
                "stay_length": data['stay_length'],
                "stay_location": data['stay_location'].name,
                "preferred_cuisine": data['preferred_cuisine'].name,
                "activity_level": data['activity_level'].name,
                "activity_duration_hours": data['activity_duration_hours'],
                "budget": str(data.get('budget', '')),
                "social_context": data['social_context'].name,
                "radius": data['radius'],
                "dislikes": data.get('dislikes', '')
            }
            return redirect("planner:activity")

# @login_required  #needs to be uncommented later
def dashboard(request):
    user = request.user
    if not request.user.is_authenticated:
        return redirect("planner:survey")
    if user.is_authenticated:
        user_display = user.first_name or user.username or "[User]"
    else:
        user_display = "[User]"

    # Pre-made trip templates
    premade_trips = [
        {
            "title": "Classic Chicago Experience",
            "duration": "3 Days",
            "description": "Perfect for first-timers! Explore iconic landmarks, deep-dish pizza, and stunning architecture.",
            "highlights": [
                "Millennium Park & Cloud Gate (The Bean)",
                "Navy Pier & Lakefront Trail",
                "Lou Malnati's Deep Dish Pizza",
                "Architecture River Cruise",
                "Museum of Science & Industry"
            ]
        },
        {
            "title": "Foodie's Paradise",
            "duration": "2 Days",
            "description": "A culinary journey through Chicago's diverse neighborhoods and award-winning restaurants.",
            "highlights": [
                "Chicago-style hot dogs at Portillo's",
                "Italian beef at Al's Beef",
                "Brunch in West Loop",
                "Chicago French Market",
                "Rooftop dining with skyline views"
            ]
        },
        {
            "title": "Art & Culture Tour",
            "duration": "2 Days",
            "description": "Immerse yourself in Chicago's world-class museums and vibrant arts scene.",
            "highlights": [
                "Art Institute of Chicago",
                "Chicago Theatre District",
                "Millennium Park concerts",
                "Museum Campus (Field, Shedd, Adler)",
                "Street art in Pilsen & Logan Square"
            ]
        }
    ]

    return render(request, "planner/dashboard.html", {
        "user_display": user_display,
        "premade_trips": premade_trips,
    })



def favorites_page(request):
    if request.user.is_authenticated:
        favorited_itinerary_ids = FavoriteItinerary.objects.filter(user=request.user).values_list('itinerary_id', flat=True)
        favorited_itineraries = Itinerary.objects.filter(id__in=favorited_itinerary_ids).prefetch_related(
            Prefetch(
                'itineraryactivity_set',
                queryset=ItineraryActivity.objects.order_by('day', 'order'),
                to_attr='ordered_activities'  # This lets you access .ordered_activities in the template
            )
        )
    else:
        favorited_itineraries = []  

    return render(request, 'planner/favorites.html', {
        'favorites': favorited_itineraries,
    })

def favorite_itinerary(request, itinerary_id):
    if request.method == 'POST':
        itinerary = get_object_or_404(Itinerary, id=itinerary_id)
        FavoriteItinerary.objects.get_or_create(user=request.user, itinerary=itinerary)
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)
    

def logout_now(request):
    logout(request)
    return redirect('planner:login')

def login_page(request):
    return render(request, "planner/login.html")

def landing_redirect(request):
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    else:
        return redirect("planner:survey")

def survey_full_page(request):
    session_key = 'survey_data'

    # ✅ Clear stale session data on GET
    if request.method == 'GET':
        for key in [
            "survey_data",
            "activity_index",
            "activity_recommendations",
            "restaurant_recommendations",
            "temp_activities",
            "current_itinerary"
        ]:
            request.session.pop(key, None)
        print("[DEBUG] Cleared session data at start")

    data = request.session.get(session_key, {})

    if request.method == 'POST':
        form = FullSurveyForm(request.POST)

        if form.is_valid():
            # ✅ Store cleaned data into session
            for key, val in form.cleaned_data.items():
                if hasattr(val, "pk") and hasattr(val, "name"):
                    data[key] = val.name
                elif isinstance(val, dt_time):
                    data[key] = val.strftime("%H:%M")
                elif isinstance(val, Decimal):
                    data[key] = float(val)  # convert Decimal to float
                else:
                    data[key] = val


            request.session[session_key] = data
            print("[SURVEY SUBMIT] Preferred Cuisine:", data.get("preferred_cuisine"))
            # print(f"[DEBUG] Session survey data now: {json.dumps(data, indent=4)}")

            # ✅ Save to model if authenticated
            if request.user.is_authenticated:
                model_data = data.copy()
                model_data["stay_location"] = Neighborhood.objects.get(name=data["stay_location"])
                model_data["preferred_cuisine"] = PreferredCuisine.objects.get(name=data["preferred_cuisine"])
                model_data["activity_level"] = ActivityLevel.objects.get(name=data["activity_level"])
                model_data["social_context"] = SocialContext.objects.get(name=data["social_context"])
                model_data["user"] = request.user
                # activity_duration_hours is already an integer, no conversion needed
                model_data.pop("trip_location", None)

                SurveyResponse.objects.create(**model_data)

            # Clean up partial recommendation data
            for key in [
                "activity_index",
                "activity_recommendations",
                "restaurant_recommendations",
                "temp_activities"
            ]:
                request.session.pop(key, None)

            return redirect("planner:activity")
        else:
            print("[DEBUG] Form errors:", form.errors.as_json())
    else:
        form = FullSurveyForm(initial=data)
    
    return render(request, "planner/survey.html", {
        "form": form
        
    })

def activity_page(request):
    print("original_activity_id:", request.POST.get("original_activity_id", "<not found>"))


    day = int(request.GET.get("day", 1))

    if request.method == "POST" and "original_activity_id" in request.POST:
        try:
            original_id = int(request.POST["original_activity_id"])
        except (ValueError, KeyError):
            messages.error(request, "Something went wrong. Please try again.")
            return redirect("planner:activity")

        replacement_name = request.POST["replacement_name"]
        replacement_description = request.POST["replacement_description"]
        replacement_neighborhood = request.POST["replacement_neighborhood"]
        replacement_latitude = request.POST["replacement_latitude"]
        replacement_longitude = request.POST["replacement_longitude"]
        replacement_category = request.POST["replacement_category"]
        replacement_photo_name = request.POST["replacement_photo_name"]
        replacement_address = request.POST["replacement_address"]

        activity = ItineraryActivity.objects.get(id=original_id)

        recommendations = request.session["recommendations"]
        recommendations.append({
            "name": activity.activity_name,
            "explanation": activity.activity_description,
            "neighborhood": activity.activity_neighborhood.name,
            "category": activity.category,
            "latitude": activity.latitude,
            "longitude": activity.longitude,
            "photo_name": activity.photo_name,
            "address": activity.address
        })

        new_recommendations_list = []
        for recommendation in recommendations:
            if recommendation["name"] == replacement_name:
                continue
            new_recommendations_list.append(recommendation)

        request.session["recommendations"] = new_recommendations_list

        
        
        neighborhood, _ = Neighborhood.objects.get_or_create(name=replacement_neighborhood)

        activity.activity_name = replacement_name
        activity.activity_description = replacement_description
        activity.activity_neighborhood = neighborhood
        activity.latitude = replacement_latitude
        activity.longitude = replacement_longitude
        activity.category = replacement_category
        activity.photo_name = replacement_photo_name
        activity.address = replacement_address
        activity.save()

        return redirect("planner:activity")


    activity_cards = []
    survey_data = request.session["survey_data"]

    if "current_itinerary" not in request.session:
        create_new_itinerary(request, survey_data["stay_length"]) # itinerary created, also don't need to use current_day, we'll change to pagination
        fetch_and_store_recommendations(survey_data, request) # still the same except I just removed activity_index
        current_itinerary = Itinerary.objects.get(id=request.session["current_itinerary"]) # get the itinerary with the id passed from other function
        make_activity_cards((request.session["itinerary"]), current_itinerary)
    else:
        current_itinerary = Itinerary.objects.get(id=request.session["current_itinerary"])
    activity_cards = get_activities(current_itinerary, day)

    # print(json.dumps(recommendations, indent=4))
    # return JsonResponse(survey_data, safe=False)
    return render(request, "planner/activity.html", {
        "activities": activity_cards,
        "recommendations": request.session["recommendations"],
        "day": day,
        "total_days": current_itinerary.total_duration
    })

def make_activity_cards(activities: list, current_itinerary):
    """
    Adds the activities to the database
    """
    print(f"Neighborhood: {json.dumps(activities, indent=4)}")
    for i in range(len(activities)):
        ItineraryActivity.objects.create(
            itinerary = current_itinerary,
            activity_name = activities[i]["name"],
            day = activities[i]["day"], # This will be given by ChatGPT
            activity_neighborhood = Neighborhood.objects.get(name=activities[i]["neighborhood"]),
            activity_description = activities[i]["explanation"],
            order = activities[i]["order"], # This will also be given by ChatGPT. This represents the order each activity will happen
            latitude = activities[i]["latitude"],
            longitude = activities[i]["longitude"],
            category = activities[i]["category"],
            photo_name = activities[i]["photo_name"],
            address = activities[i]["address"]
        )

def get_activities(current_itinerary, day):
    # print(f"***********IN GET_ACTIVITIES()")
    current_itinerary_activities = ItineraryActivity.objects.filter(itinerary=current_itinerary, day=day).order_by("order")
    activities = []

    for i in range(len(current_itinerary_activities)):
        activity = current_itinerary_activities[i]
        activities.append({
            "id": activity.id,
            "index": i,
            "neighborhood": activity.activity_neighborhood.name,
            "place": activity.activity_name,
            "description": activity.activity_description,
            "latitude": activity.latitude,
            "longitude": activity.longitude,
            "category": activity.category,
            "photo_name": activity.photo_name,
            "address": activity.address
    })

    # print(f"activity cards: {json.dumps(activities,indent=4)}")
    return activities

def create_new_itinerary(request, stay_length):

    itinerary = Itinerary.objects.create(
        name=request.session["survey_data"]["trip_title"],
        username=request.user if request.user.is_authenticated else None,
        total_duration=stay_length,
        current_day=1
    )

    request.session["current_itinerary"] = itinerary.id # store the current itinerary in the user's session so we can keep "building it"


def fetch_and_store_recommendations(data, request):
    # print("[DEBUG] Called fetch_and_store_recommendations()")
    result = get_recommendations(
        data["stay_length"],
        data["stay_location"],
        data["preferred_cuisine"],
        data["activity_level"],
        data["budget"],
        data["social_context"],
        data["dislikes"],
        1.0 #WILL GET FROM SURVEY. THIS IS THE RADIUS IN MILES. TODO: Seem to be getting issues with increasing the distance, which increases the amount of activities to send to gpt, which possibly increases response size which fails more.
    )

    # need to add back all the photo names into dict
    with open("planner/openaistuff/activity-list.json", "r") as f:
        activity_list = json.loads(f.read())

    
    # add the photo details to the recommendations/itinerary list
    for itinerary in result["itinerary"]:
        for neighborhood in activity_list["neighborhoods"]:
            for neighborhood_name, neighborhood_details in neighborhood.items():
                for restaurant in neighborhood_details["restaurants"]:
                    for restaurant_name, restaurant_details in restaurant.items():
                        if restaurant_name == itinerary["name"]:
                            itinerary["photo_name"] = restaurant_details["photo_name"]
                            itinerary["latitude"] = restaurant_details["location"]["latitude"]
                            itinerary["longitude"] = restaurant_details["location"]["longitude"]
                            itinerary["address"] = restaurant_details["address"]

                for attraction in neighborhood_details["attractions"]:
                    for attraction_name, attraction_details in attraction.items():
                        if attraction_name == itinerary["name"]:
                            itinerary["photo_name"] = attraction_details["photo_name"]
                            itinerary["latitude"] = attraction_details["location"]["latitude"]
                            itinerary["longitude"] = attraction_details["location"]["longitude"]
                            itinerary["address"] = attraction_details["address"]

    for recommendations in result["recommendations"]:
        for neighborhood in activity_list["neighborhoods"]:
            for neighborhood_name, neighborhood_details in neighborhood.items():
                for restaurant in neighborhood_details["restaurants"]:
                    for restaurant_name, restaurant_details in restaurant.items():
                        if restaurant_name == recommendations["name"]:
                            recommendations["photo_name"] = restaurant_details["photo_name"]
                            recommendations["latitude"] = restaurant_details["location"]["latitude"]
                            recommendations["longitude"] = restaurant_details["location"]["longitude"]
                            recommendations["address"] = restaurant_details["address"]

                for attraction in neighborhood_details["attractions"]:
                    for attraction_name, attraction_details in attraction.items():
                        if attraction_name == recommendations["name"]:
                            recommendations["photo_name"] = attraction_details["photo_name"]
                            recommendations["latitude"] = attraction_details["location"]["latitude"]
                            recommendations["longitude"] = attraction_details["longitude"]
                            recommendations["address"] = attraction_details["address"]

    print(f"[DEBUG] Photo URLs in itinerary:")
    for item in result["itinerary"]:
        print(f"  {item['name']}: {item.get('photo_name', 'NO PHOTO')}")

    request.session["itinerary"] = result["itinerary"]
    request.session["recommendations"] = result["recommendations"]
    
    # request.session["activity_index"] = 0

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        print("Trying to login with:", username, password)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('planner:dashboard')
        else:
            form.add_error(None, "Invalid credentials.")
    return render(request, 'planner/login.html', {'form': form})


@login_required
def summary_page(request):

    itineraries = Itinerary.objects.filter(username=request.user).order_by('id')
    itinerary = None
    activities = []

    itineraryID = request.GET.get('itinerary_id') or request.session.get("current_itinerary")

# @login_required
# def summary_page(request):
#     itineraries = Itinerary.objects.filter(username=request.user).order_by('id')
#     itinerary = None
#     activities = []
    
#     itineraryID = request.GET.get('itinerary_id')

    if itineraryID:
        try:
            itinerary = get_object_or_404(Itinerary, id=itineraryID)
        except Itinerary.DoesNotExist:
            itinerary = None

    if itinerary:
        activities = ItineraryActivity.objects.filter(itinerary=itinerary).order_by('day', 'order')
        activities_for_coords = []
        for i in range(len(activities)):
            activity = activities[i]
            activities_for_coords.append({
                "id": activity.id,
                "index": i,
                "neighborhood": activity.activity_neighborhood.name,
                "place": activity.activity_name,
                "description": activity.activity_description,
                "latitude": activity.latitude,
                "longitude": activity.longitude,
                "category": activity.category,
                "photo_name": activity.photo_name,
                "address": activity.address,
                "day": activity.day
        })
        # for activity in activities:
        #     start = datetime.combine(datetime.today(), activity.start_time)
        #     end = datetime.combine(datetime.today(), activity.end_time)
        #     if start > end:
        #         end += timedelta(days=1)
        #     duration = (end - start).seconds // 60
        #     activity.duration_minutes = duration


        # activities = ItineraryActivity.objects.filter(itinerary=itinerary).order_by('start_time')
        # for activity in activities:
        #     start = datetime.combine(datetime.today(), activity.start_time)
        #     end = datetime.combine(datetime.today(), activity.end_time)
        #     if start > end:
        #         end += timedelta(days=1)
        #     duration = (end - start).seconds // 60
        #     activity.duration_minutes = duration

    return render(request, "planner/summary.html", {
        'selected_itinerary': itinerary,
        'activities': activities,
        'itineraries': itineraries,
        'activities_for_coords': activities_for_coords
    })
    

def register(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful.")
            return redirect("planner:login")
    else:
        form = RegisterUserForm()
    return render(request, "planner/register.html", {"form": form})



class emailValidationForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user is associated with this email address.")
        return email

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset/form.html'
    success_url = reverse_lazy('password_reset_done')
    form_class = emailValidationForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'email'
        })
        return form
    def form_valid(self, form):
        print("Form is valid, attempting to send reset email...")
        return super().form_valid(form)
    
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset/confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'New password'})
        form.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})
        return form

def photo_proxy(request):
    """Proxy photo requests to Google Places API to avoid CORS and authentication issues"""
    photo_name = request.GET.get('photo_name', '')

    if not photo_name:
        return HttpResponse(status=400)

    api_key = os.getenv("PLACES_API_KEY")
    url = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=400&key={api_key}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return HttpResponse(response.content, content_type=response.headers.get('Content-Type', 'image/jpeg'))
        else:
            print(f"[ERROR] Failed to fetch photo: {response.status_code} - {response.text}")
            return HttpResponse(status=response.status_code)
    except Exception as e:
        print(f"[ERROR] Photo proxy exception: {str(e)}")
        return HttpResponse(status=500)

