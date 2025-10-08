from django import forms
from .models import SurveyResponse, Neighborhood, PreferredCuisine, ActivityLevel, SocialContext
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SurveyResponseForm(forms.ModelForm):
    preferred_cuisine = forms.ModelChoiceField(
        queryset=PreferredCuisine.objects.all(),
        label="Preferred Cuisine",
        empty_label="Select a cuisine",
        required=True
    )

    activity_level = forms.ModelChoiceField(
        queryset=ActivityLevel.objects.all(),
        label="Activity Level",
        empty_label="Select activity level",
        required=True
    )

    stay_location = forms.ModelChoiceField(
        queryset=Neighborhood.objects.all(),
        label="Where are you staying?",
        empty_label="Select a neighborhood",
        required=True
    )

    activity_window_start = forms.TimeField(
        required=True,
        label="Start time of daily activity window",
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'})
    )

    activity_window_end = forms.TimeField(
        required=True,
        label="End time of daily activity window",
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'})
    )

    budget = forms.DecimalField(
        required=True,
        label="Trip Budget",
        min_value=0,
        widget=forms.NumberInput(attrs={"placeholder": "Enter your budget (e.g., 500.00)"})
    )

    social_context = forms.ModelChoiceField(
        queryset=SocialContext.objects.all(),
        empty_label="Select social context",
        required=True
    )

    dislikes = forms.CharField(
        required=False,  # optional
        label="What would you like to avoid?",
        widget=forms.Textarea(attrs={
            "placeholder": "e.g., long walks, spicy food, crowded places",
            "rows": 3
        })
    )

    class Meta:
        model = SurveyResponse
        fields = [
            'stay_length',
            'stay_location',
            'preferred_cuisine',
            'activity_level',
            'activity_window_start',
            'activity_window_end',
            'budget',
            'social_context',
            'dislikes'
        ]

def clean_stay_length(self):
    stay_length = self.cleaned_data.get('stay_length')
    if stay_length is None or stay_length < 1:
        raise forms.ValidationError("Stay length must be at least 1 day.")
    return stay_length



class FullSurveyForm(SurveyResponseForm):
    trip_title = forms.CharField(
        required=True,
        label="Trip Title",
        widget=forms.TextInput(attrs={"placeholder": "My Trip"})
    )

    radius = forms.IntegerField(
        required=True,
        label="Radius from stay location (miles)",
        min_value=0,
        widget=forms.NumberInput(attrs={"placeholder": "5"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip_title'].required = True
        self.fields['radius'].required = True


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    
class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
