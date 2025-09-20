import requests
import json
import os

api_url = "https://zenquotes.io/api/quotes/"

def fetch_and_save_quotes():
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    quotes = response.json()

    # break into sets of 5
    sets = [quotes[i:i+5] for i in range(0, len(quotes), 5)]

    # make output folder
    os.makedirs("quote_sets", exist_ok=True)

    for idx, quote_set in enumerate(sets, start=1):
        # prepare data as list of dicts
        formatted_set = [
            {"quote": q["q"], "author": q["a"]}
            for q in quote_set
        ]

        # save each set into its own JSON file
        filename = f"quote_sets/set_{idx}.json"
        with open(filename, "w") as f:
            json.dump(formatted_set, f, indent=4)

        print(f"Saved {filename}")

# fetch_and_save_quotes()
