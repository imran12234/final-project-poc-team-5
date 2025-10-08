from openai import OpenAI
from .nearby_locations import nearby_places
from ..googleplaces.google_places_api import enhance_activity_list
import json
import os

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def build_prompt(user_preferences, activity_list):
    return f"""
YOU MUST FOLLOW THESE RULES:

1. ONLY use the activities/restaurants I’ve provided. DO NOT create your own entries.
2. If there aren't enough activities or restaurants, just recommend fewer, NEVER make up new ones.
3. The final output MUST follow this JSON format:

{{
    "itinerary": [
        {{
            "neighborhood": "Lincoln Park",
            "name": "Lincoln Park Zoo",
            "explanation": "Detailed and creative why this is a good fit for me",
            "day": 1,
            "order": 2,
            "category": "activity",
        }},
        ...
    ]
    "recommendations": [
        {{
            "neighborhood": "Lincoln Park",
            "name": "Lincoln Park Zoo",
            "explanation": "Detailed and creative why this is a good fit for me",
            "category": "activity",
        }},
        ...
    ],
}}
4. For each day in the itinerary, you MUST include 4 things to do. At least 2 of those MUST BE AN ACTIVITY, and at least 1 of those MUST BE A RESTAURANT
5. Put all remaining activities and restaurants not used in the itinerary into the recommendations list.
6. Do not repeat any item in both itinerary and recommendations.
7. For each item, include: name, neighborhood, category (restaurant/activity), latitude, longitude, and a brief explanation.
8. If you run out of valid activities, leave that day incomplete. DO NOT substitute with extra restaurants.

Now here is the list of available places and user preferences:
Activity list:
{activity_list}

User Preferences:
{user_preferences}

REMEMBER: DO NOT make up anything not already provided. Use only what's in the list above.
FORMAT STRICTLY AS SHOWN ABOVE. Do not change field names, do not add or omit fields.
"""

def activity_recommendation(user_preferences, location, radius_miles):

    activity_list = json.dumps(nearby_places(location, radius_miles))
    # print(f"Activity list sent to GPT: {activity_list}")
    prompt = build_prompt(user_preferences, activity_list)
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a JSON-only response generator. Use `null` for missing values (not `None`). Do not include any commentary outside the JSON object."},
        {"role": "user", "content": prompt}
    ])

    try:
        parsed = json.loads(response.choices[0].message.content)
        print(f"[DEBUG] Parsed list:\n{json.dumps(parsed, indent=4)}")
        return parsed
    except json.JSONDecodeError:
        print("[ERROR] Could not parse GPT response as JSON.")
        print("[RAW RESPONSE]", response.choices[0].message.content)
        return None 

def get_recommendations(stay_length, location, favorite_cuisine, activity_level, budget, social_context, dislikes, radius_miles):
    """
    Returns a dictionary
    ```
    {
        "itinerary": [
            {
                "neighborhood": "Lincoln Park",
                "name": "Lincoln Park Zoo",
                "explanation": "A relaxing outdoor option that fits the user's interest in nature",
                "day": 1,
                "order": 2,
                "category": "activity"
            },
        ]
        "recommendations": [
            {
                "neighborhood": "Lincoln Park",
                "name": "Lincoln Park Zoo",
                "explanation": "A relaxing outdoor option that fits the user's interest in nature",
                "category": "activity"
            },
        ],
    }
    ```
    """

    # return { #UNCOMMENT THIS WHOLE RETURN STATEMENT TO MOCK AN OPEN AI API CALL
    #     "itinerary": [
    #         {
    #             "neighborhood": "Uptown",
    #             "name": "Montrose Dog Beach",
    #             "explanation": "Given your preference of not liking crowded places, Montrose Dog Beach can provide a nice escape to relax and enjoy some time alone.",
    #             "day": "1",
    #             "order": "1",
    #             "category": "activity",
    #         },
    #         {
    #             "neighborhood": "Uptown",
    #             "name": "Sun Wah BBQ",
    #             "explanation": "Considering your preferences for Chinese cuisine and a moderate budget, Sun Wah BBQ offers a variety of Chinese dishes at a reasonable price.",
    #             "day": "1",
    #             "order": "2",
    #             "category": "restaurant",
    #             "latitude": 41.9739608,
    #             "longitude": -87.6595962
    #         },
    #         {
    #             "neighborhood": "Uptown",
    #             "name": "Honeymoon Cafe",
    #             "explanation": "This restaurant also offers Chinese cuisine and is budget-friendly. With its relaxed atmosphere, it can be a good fit for you.",
    #             "day": "1",
    #             "order": "3",
    #             "category": "restaurant",
    #             "latitude": 41.973345200000004,
    #             "longitude": -87.65939639999999
    #         },
    #     ],
    #     "recommendations": [
    #         {
    #             "neighborhood": "Uptown",
    #             "name": "Immm Thai",
    #             "explanation": "rec 1",
    #             "category": "restaurant"
    #         },
    #         {
    #             "neighborhood": "Uptown",
    #             "name": "First Sip Cafe",
    #             "explanation": "rec 2",
    #             "category": "activity"
    #         },
    #     ]
    # }

    user_input = f"""
- Staying for {stay_length} days
- Staying in the neighborhood {location}
- Favorite cuisine is {favorite_cuisine}
- Activity level of user is {activity_level}
- Budget of user is {budget}
- Social Context of user is {social_context}
- General dislikes of user is {dislikes}
"""

    result = activity_recommendation(user_input, location, radius_miles)

    if result is None:
        raise ValueError("GPT response could not be parsed as JSON.")

    # print(result)

    # print(json.dumps(result, indent=4))
    return result

# get_recommendations(6, "River North", "Chinese", "High", "$$", "family", "messy activities")
