"""
Imports from CSV and alphabetizes the data.json file.

TODO: import from Google sheets CSV.
"""
import csv
import json
import os
import re
import sys
import urllib.request


def parse_username(username: str):
    """
    Parses URLs and usernames into a consistent format for paypal, venmo, cashapp.
    """
    # Strip trailing slashes and user symbols, then take part after last slash.
    return username.strip(" /").split("/")[-1].strip("@$")

if "--download" in str(sys.argv):
    print("Downloading latest data from Google Sheets")
    url = "https://docs.google.com/spreadsheets/d/1EPQ4uAyxqMYW8dEPVfduenf48ItutJkJxIXOsFdHXpE/gviz/tq?tqx=out:csv&sheet=Form+Responses+1"
    urllib.request.urlretrieve(url, "raw.csv")
else:
    print("Use the `--download` flag to download the latest data")

# Load the current data file.
path = os.path.join("site", "data", "data.json")
data = []
with open(path, "r", encoding="utf-8") as jfile:
    data = json.loads(jfile.read())

# Load the CSV form responses.
responses = []
with open("raw.csv", "r", encoding="utf-8") as csvfile:
    rdr = csv.reader(csvfile)

    # Loop through rows
    rownum = 0
    for row in rdr:
        rownum += 1
        # Skip first row of titles.
        if rownum == 1:
            continue

        # Loop through columns
        record = {
            "name": "",
            "place": "",
            "paypal": "",
            "venmo": "",
            "cashapp": "",
            "last4": ""
        }
        colnum = 0
        for col in row:
            colnum += 1
            # Skip first column with date
            if colnum == 1:
                continue
            if colnum == 2:
                record["name"] = col.strip()
                # Strip leading "The" from place names.
                if record["name"].lower().startswith("the "):
                    record["name"] = re.sub(r"^[Tt]he ", "", record["name"])
            if colnum == 3:
                record["place"] = col.strip()
            if colnum == 4:
                record["paypal"] = parse_username(col)
            if colnum == 5:
                record["venmo"] = parse_username(col)
            if colnum == 6:
                record["last4"] = col.strip()
            if colnum == 7:
                record["cashapp"] = parse_username(col)

        # Add parsed response to the list.
        responses.append(record)

# Get list of existing workers.
existing_workers = []
for place in data:
    for worker in place["workers"]:
        existing_workers.append(worker)

# Next, cross reference existing data and only add new names.)
for person in responses:
    person_exists = False
    for worker in existing_workers:
        if person["name"].lower() == worker["name"].lower():
            person_exists = True
            break

    # If person does not already exist, add them to the appropriate place.
    if not person_exists:
        place_exists = False
        pix = -1
        for place in data:
            pix += 1
            if place["name"].lower() == person["place"].lower():
                place_exists = True
                # Add this worker.
                data[pix]["workers"].append({
                    "name": person["name"],
                    "paypal": person["paypal"],
                    "venmo": person["venmo"],
                    "cashapp": person["cashapp"],
                    "last4": person["last4"],
                })

        # Add this new place and worker.
        if not place_exists:
            data.append({
                "name": person["place"],
                "website": "",
                "note": "",
                "workers": [{
                    "name": person["name"],
                    "paypal": person["paypal"],
                    "venmo": person["venmo"],
                    "cashapp": person["cashapp"],
                    "last4": person["last4"],
                }]
            })

# Alphabetize the places.
data = sorted(data, key=lambda x: x["name"])

# Alphabetize the workers in each place.
for i in range(0, len(data)):
    data[i]["workers"] = sorted(data[i]["workers"], key=lambda x: x["name"])

# Write the file back.
with open(path, "w") as jfile:
    jfile.write(json.dumps(data, indent=2))

print(f"Written to {path}")
