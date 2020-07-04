from collections import OrderedDict
import csv
from datetime import datetime
import pickle
from os.path import isfile
from urllib.request import urlopen

from bs4 import BeautifulSoup


DATAFILE = ".tspdata.p"
TSP_URL = "https://www.tsp.gov/InvestmentFunds/FundPerformance/index.html"

STOCK_NAMES = [
    "TSPLInco", #0
    "TSPL2020", #1
    "TSPL2030", #2
    "TSPL2040", #3
    "TSPL2050", #4
    "TSPGFund", #5
    "TSPFFund", #6
    "TSPCFund", #7
    "TSPSFund", #8
    "TSPIFund", #9
]


def parse_csv(filename):
    """ Parses a Thrift Savings Plan output CSV file.
    """

    data = OrderedDict()

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:

            date = datetime.strptime(row['date'], "%Y-%m-%d")
            date = date.replace(hour=16)
            prices = [
                float(row[' L Income']),
                float(row[' L 2020']),
                float(row[' L 2030']),
                float(row[' L 2040']),
                float(row[' L 2050']),
                float(row[' G Fund']),
                float(row[' F Fund']),
                float(row[' C Fund']),
                float(row[' S Fund']),
                float(row[' I Fund'])
            ]

            data[date] = prices

    return OrderedDict(sorted(data.items(), key=lambda t: t[0], reverse=True))


def parse_tsp_site(url):
    """ Parses the Thrift Savings Plan web site table (at url) and
    returns an OrderedDict with dates as keys and prices as values
    in an array.
    """
    page = urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    table = soup.find(lambda tag: tag.name == 'table' and
                      tag.has_attr('class') and
                      'tspStandard' in tag.attrs['class'])

    data = OrderedDict()

    for row in table.findAll('tr'):
        # Get the date and skip if this is not a date row.
        date_row = row.find(lambda tag: tag.name == 'td' and
                            tag.has_attr('class') and
                            'leadingCell' in tag.attrs['class'])

        if date_row is None:
            continue

        date = datetime.strptime(date_row.contents[0], "%b %d, %Y")
        date = date.replace(hour=16)

        # Go through each cell and set the prices
        col_num = 0
        prices = [0] * 10
        for cell in row.findAll('td'):
            if cell.has_attr('class') and 'packed' in cell.attrs['class']:
                prices[col_num] = float(cell.contents[0].strip())
                col_num += 1

        data[date] = prices

    return OrderedDict(sorted(data.items(), key=lambda t: t[0], reverse=True))


def merge_data(*dict_args):
    """ Merges a set of dictionaries together by removing entires in subequent
    dictionaies that already exists in predecessors.
    """

    result = OrderedDict()

    for dictionary in dict_args:
        entires_to_remove = result.keys()

        for k in entires_to_remove:
            dictionary.pop(k, None)

        result.update(dictionary)

    return OrderedDict(sorted(result.items(),
                       key=lambda t: t[0],
                       reverse=True))


def print_beancount(data, desired=[4, 5, 6, 7, 8, 9], filename="auto_tsp.beancount"):
    """ Takes the output data with the desired columns and outputs them
    to a file ready for import to beancount.
    """

    with open(filename, "w") as fh:
        while data:
            date, prices = data.popitem()

            for idx, price in enumerate(prices):
                if idx not in desired:
                    continue

                line_new = '{:} price {:<15} {:>8} USD\n'.format(
                    date.strftime("%Y-%m-%d"),
                    STOCK_NAMES[idx].upper(),
                    price)

                fh.write(line_new)


if __name__ == '__main__':

    # Get the old data in, if necessary from a CSV.
    try:
        p_import = pickle.load(open(DATAFILE, "rb"))
    except (OSError, IOError) as e:
        if isfile("shareprices.csv"):
            p_import = parse_csv("shareprices.csv")

    # Now update the data from the web.
    web_data = parse_tsp_site(TSP_URL)

    # Merge the two datasets back together
    data = merge_data(web_data, p_import)

    # Save the output back to the pickle and beancount output file.
    pickle.dump(data, open(DATAFILE, "wb"))
    print_beancount(data)
