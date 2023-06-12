import requests
import pandas as pd
from time import sleep
import re
import json

# Pick the 2023 Year
LEAGUE_ID = 418 #418 is 2023, 404 is 2022
BASE_LEAGUE_URL = f"https://components.ifsc-climbing.org/results-api.php?api=season_leagues_calendar&league={LEAGUE_ID}"
CATEGORY_IDS = {
    "Lead Men" : 1,
    "Lead Women" : 5,
    "Boulder Men" : 3,
    "Boulder Women" : 7
}
CATEGORY_TYPES = {
    "Lead Men" : "Lead",
    "Lead Women" : "Lead",
    "Boulder Men" : "Boulder",
    "Boulder Women" : "Boulder"
}
BASE_EVENT_URL = "https://components.ifsc-climbing.org/results-api.php?api=overall_r_result_complete&event_id={event_id}&category_id={category_id}"
ATTEMPT_POINTS = -0.1
ZONE = 10
TOP = 15.1
PLACEMENT_POINTS = {
    1 : 25,
    2 : 15,
    3 : 10,
    4 : 8,
    5 : 6,
    6 : 4,
    7 : 2
}

# Get Events 
events = requests.get(BASE_LEAGUE_URL).json()["events"]
output = []

for event in events:

    event_name = event['event']
    event_id = event['event_id']
    print(event_name)
    for cat in CATEGORY_IDS:

        try:
            r = requests.get(BASE_EVENT_URL.format(event_id=event_id, category_id=CATEGORY_IDS[cat]))
            r.encoding = 'latin-1'
            
            r = json.loads(r.text)  
            print(f"Running: {cat}")

        except json.decoder.JSONDecodeError:
            print(f"Skipping {cat}")
            continue
        
        add_placements = False
        for i, cat_round in enumerate(r["category_rounds"]):
            if i + 1 == len(r["category_rounds"]) and cat_round["status"] == "finished":
                add_placements = True
            
        for rank in r['ranking']:
            name = f"{rank['lastname']} {rank['firstname']}"

            end_rank = rank['rank']

            for i, route in enumerate(rank["rounds"]):
                round_name = route["round_name"]

                if end_rank is not None and end_rank <= 7 and (i + 1) == len(rank["rounds"]) and add_placements:
                    print(f"Placement: {name}, {end_rank}")
                    placement_points = PLACEMENT_POINTS[end_rank]
                else:
                    placement_points = 0
                if "Lead" in cat :
                    for final_route in route["ascents"]:
                        output_dict = {}
                        output_dict["event_name"] = event_name
                        output_dict["event_id"] = event_id
                        output_dict["event_type"] = cat
                        output_dict["competitor_name"] = name 
                        output_dict["round"] = round_name
                        output_dict["score"] = final_route["score"].replace('+', '')
                        output_dict["route_name"] = final_route["route_name"]
                        output_dict["event_category"] = CATEGORY_TYPES[cat]
                        output_dict["final_output_score"] = 0 + placement_points
                        output_dict["num_routes"] = len(route["ascents"])
                        output_dict["placement"] = end_rank

                        output.append(output_dict)
                        
                else:
                    mult = 4 / len(route["ascents"])
                    output_dict = {}
                    output_dict["event_name"] = event_name
                    output_dict["event_id"] = event_id
                    output_dict["event_type"] = cat
                    output_dict["competitor_name"] = name 
                    output_dict["round"] = route["round_name"]
                    output_dict["score"] = route["score"]
                    output_dict["route_name"] = 'N/A'
                    output_dict["event_category"] = CATEGORY_TYPES[cat]
                    final_output_score_unadjusted = 0
                    for final_route in route["ascents"]:
                        ## Account for the DNS case (will default to 0 for the route)
                        if final_route["zone_tries"] is None and final_route["top_tries"] is None:
                            continue
                        elif  final_route["zone_tries"] == 0 or final_route["top_tries"] is None:
                            continue
                        elif  final_route["zone_tries"] is None or final_route["top_tries"] == 0:
                            continue
                        elif  final_route["zone_tries"] is None or final_route["top_tries"] is None:
                            print("Odd skipped")
                            continue

                        max_attempts = max(final_route["top_tries"], final_route["zone_tries"])

                        if final_route["top"] == True:
                            final_output_score_unadjusted += TOP
                        if final_route["zone"] == True:
                            final_output_score_unadjusted += ZONE
                        final_output_score_unadjusted += max_attempts * ATTEMPT_POINTS
            
                    ## To equalize points around 4
                    mult = 4 / len(route["ascents"])
                    output_dict["final_output_score"] = (final_output_score_unadjusted * mult) + placement_points
                    output_dict["num_routes"] = len(route["ascents"])
                    output_dict["placement"] = end_rank
                    output.append(output_dict)


pd.DataFrame(output).to_excel(f"IFSC_Route_{LEAGUE_ID}.xlsx")
