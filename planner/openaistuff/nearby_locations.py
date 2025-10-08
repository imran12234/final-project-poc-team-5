from geopy.distance import geodesic
import json

with open("planner/openaistuff/activity-list.json") as f:
    activity_list = json.load(f)


def nearby_places(target_neighborhood, radius_miles):
    target_coords = None
    nearby_distance = radius_miles # hardcoded, needs to be updated with the survey response

    for neighborhood in activity_list["neighborhoods"]:
        for neighborhood_name, neighborhood_details in neighborhood.items():
            if neighborhood_name == target_neighborhood:
                latitude = float(neighborhood_details["location"]["latitude"])
                longitude = float(neighborhood_details["location"]["longitude"])
                print(f"{neighborhood_name} longitude: {longitude}, latitude: {latitude}")
                target_coords = (latitude, longitude)

    nearby_places = []

    for neighborhood in activity_list["neighborhoods"]:
        for neighborhood_name, neighborhood_details in neighborhood.items():
            for restaurant in neighborhood_details['restaurants']:
                for restaurant_name, restaurant_details in restaurant.items():
                    place_coords = (
                        restaurant_details["location"]["latitude"],
                        restaurant_details["location"]["longitude"]
                    )
                    distance = geodesic(target_coords, place_coords).miles
                    if distance <= nearby_distance:
                        details = dict(restaurant_details)
                        details["category"] = "restaurant"
                        details["neighborhood"] = neighborhood_name
                        details.pop("photo_name")
                        details.pop("queried_by_places")
                        details.pop("address")
                        details.pop("location")
                        if "websiteUri" in details:
                            details.pop("websiteUri")
                        details.pop("displayName")
                        nearby_places.append(
                            {
                                f"{restaurant_name}": details
                            }
                        )
                        # nearby_places.append(
                        #     {
                        #         f"{restaurant_name}": restaurant_details
                        #     }
                        # )

            for attraction in neighborhood_details['attractions']:
                for attraction_name, attraction_details in attraction.items():
                    place_coords = (
                        attraction_details["location"]["latitude"],
                        attraction_details["location"]["longitude"]
                    )
                    distance = geodesic(target_coords, place_coords).miles
                    if distance <= nearby_distance:
                        details = dict(attraction_details)
                        details["category"] = "activity"
                        details["neighborhood"] = neighborhood_name
                        details.pop("photo_name")
                        details.pop("queried_by_places")
                        details.pop("address")
                        details.pop("location")
                        if "websiteUri" in details:
                            details.pop("websiteUri")
                        details.pop("displayName")
                        nearby_places.append(
                            {
                                f"{attraction_name}": details
                            }
                        )
                        # nearby_places.append(
                        #     {
                        #         f"{attraction_name}": attraction_details
                        #     }
                        # )

    # print(f"Places within 1.5 miles of {target_neighborhood}:")
    # for name in nearby_places:
    #     print(json.dumps(name, indent=4))

    # print(json.dumps(nearby_places, indent=4))
    return nearby_places
