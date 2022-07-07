from bs4 import BeautifulSoup
from typing import List, Tuple
from database import get_database
import requests


def split_name(name: str) -> Tuple[str, str]:
    """  Split up a fighter's name

    :param name: the name to split up.
    :return: a tuple containing the first and last name.
    """
    split_up_name = name.split()
    if len(split_up_name) == 1:
        return split_up_name[0], ""
    else:
        # Check if fighter has more than one last name.
        # ex: Silvana Gomez Juarez
        last_name = ""
        for last in split_up_name[1:]:
            last_name += last + " "

    return split_up_name[0], last_name.strip()


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

        fight["Outcome"] = fight_info[0].i.text
        fight["Opponent"] = fight_info[2].text.strip()
        fight["Method"] = fight_info[13].text.strip()
        fight["Round"] = fight_info[15].text.strip()
        fight["Time"] = fight_info[16].text.strip()

        result.append(fight)
    return result


def scrape_fighter(fighter_url: str):
    """ Scrape a fighter for their first name, last name, and fight record

    :param fighter_url: webpage of a fighter from ufcstats.com
    :return: object that contains the first name, last name, and fight record
    """
    fighter = {}
    res = requests.get(fighter_url)
    doc = BeautifulSoup(res.text, "html.parser")
    name = doc.find("span", {"class": "b-content__title-highlight"}).text
    fighter["First"], fighter["Last"] = split_name(name)
    fighter["Record"] = get_fighter_record(doc)
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


if __name__ == "__main__":
    urls = get_fighter_urls()
    fighters = []
    for url in urls:
        fighters.append(scrape_fighter(url))
    db = get_database()
    collection = db["fighters"]
    collection.drop()
    collection.insert_many(fighters)
