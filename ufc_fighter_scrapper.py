from datetime import datetime

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


def get_all_digits(to_parse):
    """
    Strip given string down to just digits.
    :param to_parse: String containing digits
    :return: Integer values contained in the string, if none returns 0.
    """
    # Check if we have a valid input
    if to_parse.strip() == "--":
        return 0
    return int(''.join(list(filter(str.isdigit, to_parse))))


def imperial_to_metric(height: int):
    """
    Converts our height from imperial to metric.
    :param height to be converted
    :return: Height in cm, 0.0 if no height available.
    """
    # Inches will start off as a single digit unless we find another digit to add onto it
    inches = height % 10
    # Pop the inches off
    height = height // 10
    # If we still have inches leftover (our feet should be less than 10)
    while height > 10:
        # Shift our inches over a decimal place and add our extra inch height
        inches = (inches * 10) + (height % 10)
        height = height // 10
    # Unit conversion to cm
    return (height * 30.48) + (inches * 2.54)


def parse_birthday(birthday: str) -> int:
    """
    Converts the birthday string scraped from document to a time object which is then subtracted by the current date.
    This gives us the age of the fighter at the time of the scraping
    :param birthday: string representation of the fighters birthday.
    :return: Age of the fighter, if not available returns 0.
    """
    # Invalid Input
    if birthday.strip() == "--":
        return 0

    unparsed_birthday = birthday.strip().removeprefix("DOB:").strip()
    age = datetime.today() - datetime.strptime(unparsed_birthday, "%b %d, %Y")
    # Convert days to age
    return int(age.days * 0.00273973)


def get_fighter_physical(doc):
    """ Scrape the fighter's physical features: height, weight, reach, and age

    :param doc: Document object containing the HTML with the attributes needed
    :return: Object containing the height, weight, reach, and age. If not available returns 0.

    """
    physical_stats = doc.find("div", {"class": "b-list__info-box b-list__info-box_style_small-width js-guide"})
    physical_stats = physical_stats.find_all("li")

    unparsed_height = physical_stats[0].contents[2].text
    parsed_height = get_all_digits(unparsed_height)
    height = imperial_to_metric(parsed_height)

    unparsed_weight = physical_stats[1].contents[2].text
    weight = get_all_digits(unparsed_weight)
    reach = get_all_digits(physical_stats[2].contents[2])
    age = parse_birthday(physical_stats[4].contents[2])
    return {"height": height, "weight": weight, "reach": reach, "age": age}


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
    fighter["physical"] = get_fighter_physical(doc)
    fighter["record"] = get_fighter_record(doc)
    print(fighter)
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
        print(scrape_fighter("http://ufcstats.com/fighter-details/b361180739bed4b0"))
    else:
        all_fighters = scrape_all_fighters()
        # Would it be better to just use our server for scraping purposes? decoupling?
        store_many(all_fighters, "fighters")
