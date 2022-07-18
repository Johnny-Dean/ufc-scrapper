from bs4 import BeautifulSoup
from database import store_many
from typing import List
import requests


def scrape_event(url: str):
    """ Scrape an event for the title and the fights in the event

    :param url: URL of event to be scraped
    :return: object containing the title of the fights and an array containing every fight on the card
    """
    fight_card = {"org": "UFC", "title": "", "fights": [], }
    res = requests.get(url)
    doc = BeautifulSoup(res.text, "html.parser")
    # Title Scrape
    title = doc.find("span", {"class": "b-content__title-highlight"}).text.strip()
    if title.startswith("UFC Fight Night:"):
        fight_card["title"] = "Fight Night"
    else:
        fight_card["title"] = title[4:7]
    # Fights Scrape
    fights = doc.find_all("tr", {"class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"})
    for f in fights:

        fighters = f.find_all("a")
        fight = {"Red":fighters[0].text.strip(), "Blue": fighters[1].text.strip()}
        fight_card["fights"].append(fight)

    return fight_card


def get_event_urls() -> List[str]:
    """ Get every URL for each event on ufcstats.com/statistics/events/upcoming

    :return: array containing the urls of each UFC event
    """
    EVENTS_URL = "http://ufcstats.com/statistics/events/upcoming"
    res = requests.get(EVENTS_URL)
    doc = BeautifulSoup(res.text, "html.parser")
    events = doc.find_all("i", {"class": "b-statistics__table-content"})
    urls = []
    for e in events:
        if e.a:
            urls.append(e.a["href"])
    return urls


def scrape_all_events():
    event_urls = get_event_urls()
    events = []
    for event in event_urls:
        events.append(scrape_event(event))
    return events


# Do I make these a main function that runs in github actions?
if __name__ == "__main__":
    scraped_events = scrape_all_events()
    store_many(scraped_events, "events")
