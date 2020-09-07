import requests
import random
import os
import difflib
import cache
import threading

GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEYS").split(",")
OPENSECRETS_API_KEYS = os.getenv("OPENSECRETS_API_KEYS").split(",")


def get_representatives(zipcode, address):
    repdata = requests.get(
        "https://www.googleapis.com/civicinfo/v2/representatives",
        params={"address": f"{address} {zipcode}",
                "key": random.choice(GOOGLE_API_KEYS)},
    ).json()

    votedata = requests.get(
        "https://www.googleapis.com/civicinfo/v2/voterinfo",
        params={"address": f"{address} {zipcode}",
                "key": random.choice(GOOGLE_API_KEYS)},
    ).json()

    if "normalizedInput" not in repdata:
        return None

    for office in repdata["offices"]:
        for officialIndex in office["officialIndices"]:
            repdata["officials"][officialIndex]["office"] = office

    opensecrets_data = poll_opensecrets(repdata["normalizedInput"]["state"])
    for rep in list(filter(lambda k: "country" in k["office"]["levels"], repdata["officials"])):
            close_matches = difflib.get_close_matches(
                rep["name"], opensecrets_data.keys(), cutoff=.8)
            for match in close_matches:
                rep["opensecrets"] = opensecrets_data[match]

    if "contests" in votedata:
        for contest in votedata["contests"]:
            official_names = [
                official["name"].lower() for official in contest["candidates"]
            ]
            for rep in repdata["officials"]:
                if (
                    len(difflib.get_close_matches(
                        rep["name"].lower(), official_names))
                    > 0
                ):
                    rep["contest"] = contest
                    rep["election"] = {
                        "contest": contest, "full_data": votedata}

    for official in repdata["officials"]:
        official["party_color"] = "#808080"
        try:
            if "democra" in official["party"].lower():
                official["party_color"] = "#0000FF"
            if "republic" in official["party"].lower():
                official["party_color"] = "#FF0000"
            if "green" in official["party"].lower():
                official["party_color"] = "#00FF00"
            if "nonpartisan" in official["party"].lower():
                official["party_color"] = "#C0C0C0"
        except Exception as e:
            print(f"Couldn't process party color for official {official}: {e}")
            continue

    return {
        "representatives": repdata["officials"],
        "input": repdata["normalizedInput"],
    }


def poll_opensecrets(state: str, cache_only: bool = True):
    try:
        state = state.upper()
        if cache.get(f"opensecrets_{state}") is None:
            if cache_only:
                print(f"Loading state {state} in the background...")
                thread = threading.Thread(
                    target=lambda: poll_opensecrets(state, cache_only=False))
                thread.setDaemon(True)
                thread.start()
                return {}
            people_dict = {}
            ids = requests.get(
                "http://www.opensecrets.org/api/",
                params={
                    "method": "getLegislators",
                    "id": state,
                    "output": "json",
                    "apikey": random.choice(OPENSECRETS_API_KEYS),
                },
            ).json()["response"]

            if not isinstance(ids["legislator"], list):
                # Handle cases where there is only one legislator and the API compacts the response
                ids["legislator"] = [ids["legislator"]]

            for legislator in ids["legislator"]:
                try:
                    attributes = legislator["@attributes"]
                    cid = attributes["cid"]
                    name = attributes["firstlast"]
                    name_dict = {"name": name, "cid": cid}
                    secrets = requests.get(
                        "http://www.opensecrets.org/api/",
                        params={
                            "method": "candSummary",
                            "cid": cid,
                            "output": "json",
                            "apikey": random.choice(OPENSECRETS_API_KEYS),
                        },
                    ).json()["response"]["summary"]["@attributes"]

                    name_dict["secrets"] = secrets
                    people_dict[name] = name_dict
                except Exception as e:
                    print(
                        f"an error occured when trying to load {legislator}: {e}")
            print(f"Loaded opensecrets data for {state}!")
            cache.set(f"opensecrets_{state}", people_dict)

        return cache.get(f"opensecrets_{state}")
    except Exception as e:
        print(f"could not poll OpenSecrets: {e}")
        return {}

