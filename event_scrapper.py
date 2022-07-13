from bs4 import BeautifulSoup
from database import get_database
from typing import List
import requests


def scrape_event(url: str):
    """ Scrape an event for the title and the fights in the event

    :param url: URL of event to be scraped
    :return: object containing the title of the fights and an array containing every fight on the card
    """
    fight_card = {"Title": "", "Fights": []}
    res = requests.get(url)
    doc = BeautifulSoup(res.text, "html.parser")
    title = doc.find("div", {"class": "field field--name-node-title field--type-ds field--label-hidden field__item"})
    fight_card["Title"] = title.text.strip()

    fights = doc.find_all("div", {"class": "c-listing-fight__content"})
    for f in fights:
        fighters = f.find_all("div", {"class": "c-listing-fight__detail-corner-name"})
        # Write this better
        first_fighter = fighters[0].text.strip()
        second_fighter = fighters[1].text.strip()
        fight_card["Fights"].append((first_fighter, second_fighter))

    # Fight Night we need to append the main fighters of the card to distinguish the fight nights
    main_event = fight_card["Fights"][0]
    fight_card["Title"] = fight_card["Title"] + ": " + main_event[0] + " vs " + main_event[1]
    return fight_card


def get_event_urls() -> List[str]:
    """ Get every URL for each event on ufc.com/events

    :return: array containing the urls of each UFC event that is on ufc.com/events
    """
    EVENTS_URL = "https://www.ufc.com/events"
    BASE_URL = "https://ufc.com"
    res = requests.get(EVENTS_URL)
    doc = BeautifulSoup(res.text, "html.parser")
    event_pages = doc.find_all("div", {"class": "c-card-event--result__logo"})
    urls = []

    for e in event_pages:
        urls.append(BASE_URL + e.a['href'])
    return urls


# Do I make these a main function that runs in github actions?
if __name__ == "__main__":
    event_urls = get_event_urls()
    events = []
    for event in event_urls:
        events.append(scrape_event(event))
    dbname = get_database()
    collection = dbname["events"]
    collection.drop()
    collection.insert_many(events)
