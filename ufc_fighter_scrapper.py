import string

from bs4 import BeautifulSoup
from typing import List
from database import store_many
import requests


def get_fighter_record(doc) -> List:
    """ Scrape the html document for the fighter's record

    :param doc: the html document of a fighter and their record
    :return: array containing the fight record of a fighter
    """
    fights = doc.find_all("tr", {
        "class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"})
    result = []
    for f in fights:
        fight = {}
        fight_info = f.find_all("p", {"class": "b-fight-details__table-text"})

        fight["outcome"] = fight_info[0].i.text.capitalize()
        fight["opponent"] = fight_info[2].text.strip()
        fight["method"] = fight_info[13].text.strip()
        fight["round"] = int(fight_info[15].text.strip())
        fight["time"] = fight_info[16].text.strip()
        result.append(fight)
    return result


def feet_inches_to_cm(height: string):
    # Parse all numbers from our string
    parsed_height = int(''.join(list(filter(str.isdigit, height))))
    # Inches will start off as a single digit unless we find another digit to add onto it
    inches = parsed_height % 10
    # Pop the inches off
    parsed_height = parsed_height // 10
    # If we still have inches leftover (our feet should be less than 10)
    while parsed_height > 10:
        # Shift our inches over a decimal place and add our extra inch height
        inches = (inches * 10) + (parsed_height % 10)
        parsed_height = parsed_height // 10
    # Unit conversion to cm
    return (parsed_height * 30.48) + (inches * 2.54)


def get_fighter_physical(doc):
    physical_stats = doc.find("div", {"class": "b-list__info-box b-list__info-box_style_small-width js-guide"})
    physical_stats = physical_stats.find_all("li")
    height = feet_inches_to_cm(physical_stats[0].contents[2].text.strip())
    weight = physical_stats[1].contents[2].text.strip()
    print(height)
    return ""


def scrape_fighter(fighter_url: str):
    """ Scrape a fighter for their first name, last name, and fight record

    :param fighter_url: webpage of a fighter from ufcstats.com
    :return: object that contains the first name, last name, and fight record
    """
    fighter = {}
    res = requests.get(fighter_url)
    doc = BeautifulSoup(res.text, "html.parser")
    name = doc.find("span", {"class": "b-content__title-highlight"}).text
    fighter["name"] = name.strip()
    fighter["record"] = get_fighter_record(doc)
    fighter["physical"] = get_fighter_physical(doc)
    return fighter


def get_fighter_urls() -> List[str]:
    """ Get every URL for every fighter on ufcstats.com

    :return: an array containing every fighter's url
    """
    result = []
    # ufcstats.com has every fighter organized by last name, and each page is seperated by the letter of an alphabet
    alphabetic_urls = []
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    for letter in alphabet:
        page = "http://ufcstats.com/statistics/fighters?char=" + letter + "&page=all"
        alphabetic_urls.append(page)

    for url in alphabetic_urls:
        res = requests.get(url)
        doc = BeautifulSoup(res.text, "html.parser")
        fighter_rows = doc.find_all("tr", {"class": "b-statistics__table-row"})
        # Get each row that contains a fighter's url
        for fighter_row in fighter_rows:
            if fighter_row is not None and fighter_row.a is not None:
                result.append(fighter_row.a["href"])
    return result


def scrape_all_fighters():
    urls = get_fighter_urls()
    fighters = []
    for url in urls:
        fighters.append(scrape_fighter(url))
    return fighters


if __name__ == "__main__":
    debug = 1
    if debug:
        print(scrape_fighter("http://ufcstats.com/fighter-details/b50a426a33da0012"))
    else:
        all_fighters = scrape_all_fighters()
        # Would it be better to just use our server for scraping purposes? decoupling?
        store_many(all_fighters, "fighters")
