import requests
from bs4 import BeautifulSoup
import re
import pprint
import os

WEBSITE_URL = "https://en.wikipedia.org/wiki/List_of_animal_names"


def get_animal_table(url):
    """
    gets animal table from wiki page using BeautifulSoup.
    :param url: url of wiki page
    :return: animals table soup object
    """
    response = requests.get(WEBSITE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.find_all("table", {"class": "wikitable sortable"})[1]


def get_animal_name(animal_name_column):
    """
    extracts animal name from table row.
    :param animal_name_column: all information regarding the animal from the table.
    :return: animal name cleaned from any unnecessary suffixes.
    """
    # gets animal_name and cleans all kind of redundant information like: '(list)', '[notes]', etc..
    name_pattern = re.compile(r'^[a-z /]+', re.IGNORECASE)  # regex for name of the animal.
    animal_name = name_pattern.match(animal_name_column.text).string
    animal_name_after_cleaning = \
        re.sub(r'((See.*)|(see.*)|(\(list\).*)|(Also see.*))|([\r\n])|(\[[\w\d ]+\])', "", animal_name)

    return re.sub(r'^\s*|\s*$|-*$', "", animal_name_after_cleaning)  # remove trailing whitespaces and dashes.


def get_list_of_collateral_adjective(collateral_adjective):
    """
    extracts all collateral_adjective from 5th column in the table.
    while cleaning those name from citation, remarks etc..
    and split the string based on the '<br/>' delimiter.
    :param collateral_adjective: 5th column in the table.
    :return: all collateral_adjective separated.
    """
    # regex to identify the content of the collateral_adjective column from table.
    collateral_adjective_pattern = re.compile(r'^<td>(.*)</td>$', re.IGNORECASE)
    collateral_adjective_match = collateral_adjective_pattern.search(str(collateral_adjective))

    if collateral_adjective_match:

        if len(collateral_adjective) > 0:   # Animals of known collateral adjective (not '?')

            # creating list of collateral_adjective which found in the 5th column.
            #   and separate them by '<br/>'.
            list_of_breeds = collateral_adjective_match.group(1).split('<br/>')
            list_of_collateral_adjective = []

            # cleaning each collateral_adjective from redundant information.
            for breed in list_of_breeds:
                breed = re.sub(r'<sup .*', "", breed)       # remove sup tag from each of them.
                breed = re.sub(r'<[= /\w"]+>', "", breed)   # remove remarks.
                breed = re.sub(r'^\s*|\s*$', "", breed)     # remove beginning and trainings whitespaces.
                list_of_collateral_adjective.append(breed)
            return list_of_collateral_adjective

    else:   # Animals with '?' in their collateral adjective:
        return ['?']


def get_animal_and_list_of_collateral_adjective_from_row(table_row):
    """
    extract needed information (animal name and list of all of its collateral_adjective) from row.
    :param table_row:
    :return: list - animal name and list of all of its collateral_adjective
    """
    if len(table_row) > 5:  # eliminate working on rows which are only for the letter place holder.
        animal_name = get_animal_name(table_row[0])
        collateral_adjective = get_list_of_collateral_adjective(table_row[5])
        return [animal_name, collateral_adjective]
    return None


def save_picture_of_animal(name_of_animal, animal_information):
    """
    download picture of the animal locally.
    :param name_of_animal:
    :param animal_information: 0th column of the table row.
    :return: absolute path to the picture which downloaded.
    """

    # extracting animal page in Wikipedia:
    soup = BeautifulSoup(str(animal_information), 'html.parser')
    animal_url = "https://en.wikipedia.org" + soup.find('a', href=True)['href']
    animal_wiki_page = requests.get(animal_url)

    # extracting animal picture url:
    soup = BeautifulSoup(animal_wiki_page.content, 'html.parser')
    animal_picture_url = 'https://' + soup.find(class_='image').find('img')['src'][2:]

    # download the picture:
    img_data = requests.get(animal_picture_url).content
    for name in name_of_animal.split('/'):  # if animal name have alternatives, will add each of them.
        pic_file_name_absolute_path = \
            os.getcwd() + '\\tmp\\' + name + animal_picture_url[animal_picture_url.rfind('.'):]
        #     [current_dir\tmp\]      [animal_name]                    .[picture_ext]

        with open(pic_file_name_absolute_path, 'wb') as pic_file:
            pic_file.write(img_data)

    return pic_file_name_absolute_path


def main():
    """
    driver function.
    :return:
    """
    # dictionaries for saving results.
    dictionary_of_all_collateral_adjective = {}
    list_of_pictures_files_with_local_paths = {}

    # scraping all rows from Wikipedia table.
    for row in get_animal_table(WEBSITE_URL).find_all('tr'):
        row_data = row.find_all('td')  # split row data based on column.

        name_and_list_of_collateral_adjective = get_animal_and_list_of_collateral_adjective_from_row(row_data)

        # eliminate working on row which is character placeholder.
        if name_and_list_of_collateral_adjective is not None:

            name = name_and_list_of_collateral_adjective[0]
            collateral_adjective_of_animal = name_and_list_of_collateral_adjective[1]

            # download picture of any animal while saving the local path in dictionary.
            # key-value -> animal_name-picture_file_path
            list_of_pictures_files_with_local_paths[name] = save_picture_of_animal(name, row_data[0])

            if collateral_adjective_of_animal is not None:
                for breed in collateral_adjective_of_animal:  # will add animal to each breed it belongs to.
                    if str(breed) not in dictionary_of_all_collateral_adjective:
                        dictionary_of_all_collateral_adjective[str(breed)] = []
                    for n in name.split('/'):  # add each animal name alternative to the dictionary.
                        dictionary_of_all_collateral_adjective[str(breed)].append(n)

    # saving dictionaries into files:
    with open('output.txt', 'wt') as result:
        pprint.pprint(dictionary_of_all_collateral_adjective, compact=True, indent=4, stream=result)
    with open('picture_list.txt', 'wt') as out:
        pprint.pprint(list_of_pictures_files_with_local_paths, compact=True, indent=4, stream=out)


def set_up():
    path = os.getcwd() + '\\tmp\\'
    os.mkdir(path)


if __name__ == "__main__":
    set_up()
    main()
