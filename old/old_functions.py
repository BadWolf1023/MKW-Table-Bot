from typing import List
from bs4 import BeautifulSoup


def combine_soups(soups: List[BeautifulSoup]):
    last_soup = None
    for soup_num, soup in enumerate(soups):
        if soup_num == 0:
            last_soup = soup
        else:
            table_body = last_soup.find('table')
            table_body.append(soup.find('table'))

    while len(soups) > 0:
        del soups[0]

    return last_soup
