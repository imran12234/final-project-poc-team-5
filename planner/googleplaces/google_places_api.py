import requests
import json
import os

with open("planner/openaistuff/activity-list.json", "r") as f:
    activity_list = json.loads(f.read())

def enhance_activity_list():
    """
    Returns a dictionary of the first index from a list of places from the search query.
    """
    api_key = os.getenv("PLACES_API_KEY")

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours,places.location,places.priceLevel,places.websiteUri,places.types,places.photos"
    }

    for neighborhood in activity_list['neighborhoods']:
        """
        "neighborhoods": [
            {}, <---- neighborhood
        ]
        """
        for neighborhood_name, neighborhood_details in neighborhood.items():
            """
            "neighborhoods": [
                {
                    "neighborhood_name": {} <-- neighborhood_details
                },
            ]
            """
            for restaurant in neighborhood_details['restaurants']:
                """
                "neighborhoods": [
                    {
                        "neighborhood_name": {
                            "restaurants": [
                                {}, <---- restaurant
                            ]
                        },
                    },
                ]
                """
                for restaurant_name, restaurant_details in restaurant.items():
                    """
                    "neighborhoods": [
                        {
                            "neighborhood_name": {
                                "restaurants": [
                                    {
                                        "restaurant_name": {} <-- restaurant_details
                                    },
                                ]
                            },
                        },
                    ]
                    """
                    payload = {
                        "textQuery": f"{restaurant_name} in {neighborhood_name} Chicago"
                    }

                    # print(f"QUERIED BY PLACES: {restaurant_details['queried_by_places']}")
                    if restaurant_details['queried_by_places'] == False:
                        print(f"Updating {restaurant_name}")
                        response = requests.post(url, headers=headers, json=payload)
                        data = response.json()
                        first_location = data['places'][0]
                        restaurant_details['queried_by_places'] = True
                        if 'types' in first_location:
                            restaurant_details['tags'] = first_location['types']
                        if 'rating' in first_location:
                            restaurant_details['rating'] = first_location['rating']
                        if 'websiteUri' in first_location:
                            restaurant_details['websiteUri'] = first_location['websiteUri']
                        if 'priceLevel' in first_location:
                            restaurant_details['priceLevel'] = first_location['priceLevel']
                        if 'text' in first_location['displayName']:
                            restaurant_details['displayName'] = first_location['displayName']['text']
                        if 'formattedAddress' in first_location:
                            restaurant_details['address'] = first_location['formattedAddress']
                        if 'location' in first_location:
                            if 'latitude' in first_location['location']:
                                restaurant_details['location']['latitude'] = first_location['location']['latitude']
                            if 'longitude' in first_location['location']:
                                restaurant_details['location']['longitude'] = first_location['location']['longitude']
                        if 'currentOpeningHours' in first_location:
                            if 'weekdayDescriptions' in first_location['currentOpeningHours']:
                                restaurant_details['weekdayDescriptions'] = first_location['currentOpeningHours']['weekdayDescriptions']
                        if 'photos' in first_location:
                            restaurant_details['photo_name'] = first_location['photos'][0]['name']

            for attraction in neighborhood_details['attractions']:
                """
                "neighborhoods": [
                    {
                        "neighborhood_name": {
                            "attractions": [
                                {}, <---- attraction
                            ]
                        },
                    },
                ]
                """
                for attraction_name, attraction_details in attraction.items():
                    """
                    "neighborhoods": [
                        {
                            "neighborhood_name": {
                                "attractions": [
                                    {
                                        "attraction_name": {} <-- attraction_details
                                    },
                                ]
                            },
                        },
                    ]
                    """
                    payload = {
                        "textQuery": f"{attraction_name} in {neighborhood_name} Chicago"
                    }

                    # print(f"QUERIED BY PLACES: {attraction_details['queried_by_places']}")
                    if attraction_details['queried_by_places'] == False:
                        print(f"Updating {attraction_name}")   
                        response = requests.post(url, headers=headers, json=payload)
                        data = response.json()
                        first_location = data['places'][0]
                        attraction_details['queried_by_places'] = True
                        if 'types' in first_location:
                            attraction_details['tags'] = first_location['types']
                        if 'rating' in first_location:
                            attraction_details['rating'] = first_location['rating']
                        if 'websiteUri' in first_location:
                            attraction_details['websiteUri'] = first_location['websiteUri']
                        if 'priceLevel' in first_location:
                            attraction_details['priceLevel'] = first_location['priceLevel']
                        if 'text' in first_location['displayName']:
                            attraction_details['displayName'] = first_location['displayName']['text']
                        if 'formattedAddress' in first_location:
                            attraction_details['address'] = first_location['formattedAddress']
                        if 'location' in first_location:
                            if 'latitude' in first_location['location']:
                                attraction_details['location']['latitude'] = first_location['location']['latitude']
                            if 'longitude' in first_location['location']:
                                attraction_details['location']['longitude'] = first_location['location']['longitude']
                        if 'currentOpeningHours' in first_location:
                            if 'weekdayDescriptions' in first_location['currentOpeningHours']:
                                attraction_details['weekdayDescriptions'] = first_location['currentOpeningHours']['weekdayDescriptions']
                        if 'photos' in first_location:
                            attraction_details['photo_name'] = first_location['photos'][0]['name']
            
            with open("planner/openaistuff/activity-list.json", "w") as f:
                json.dump(activity_list, f, indent=4)

def get_image(image_name):
    """
    Returns the url of the image
    """
    api_key = os.getenv("PLACES_API_KEY")

    url = f"https://places.googleapis.com/v1/{image_name}/media?maxHeightPx=400&key={api_key}"

    return url
enhance_activity_list()