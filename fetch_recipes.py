import json
from typing import Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup
import requests

HOME = 'https://iba-world.com/'
PAGES = ('iba-cocktails', 'contemporary-classics', 'new-era-drinks')
CATEGORIES = {'iba-official-cocktails': 'The Unforgettables',
              'cocktails': 'Contemporary Classics',
              'new-era-drinks': 'New Era Drinks'}
WORDS = ('INGREDIENTS', 'METHOD', 'GARNISH')
MY_ITERABLE = Iterable[Dict[str, str]]


def get_all_iba_cocktails_names_and_links(home: str = HOME, pages: Iterable[str] = PAGES) -> Dict[str, str]:
    """Return all official iba cocktails names and the urls
    of their respective pages on the official iba website."""
    cocktails = {}
    for page in pages:
        source = requests.get(f'{home}{page}').text
        soup = BeautifulSoup(source, 'lxml')
        div = soup.find('div', class_='blog_list_items')
        headers = div.find_all('h3')
        anchors = div.find_all('a', class_='btn-readmore')
        cocktails.update({h.text.title(): a['href']
                    for i, h in enumerate(headers)
                    for j, a in enumerate(anchors)
                    if i == j})
    return cocktails


def get_recipe(link: str, words_to_search: Iterable[str] = WORDS,
               category_translations: Dict[str, str] = CATEGORIES) -> Dict[str, str]:
    """Return a dictionary with the details and recipe from the given page."""
    source = requests.get(link).text
    soup = BeautifulSoup(source, 'lxml')
    div = soup.find('div', class_="col-sm-9")
    content: List[str] = [i.text.lstrip() for i in div.find_all('p') if i.text.lstrip()]
    if len(content) == 1:
        temp = content[0]
        for word in words_to_search:
            temp = temp.replace(word, '')
        content = temp.lstrip().split('\n\n')
    else:
        for i in range(len(content)):
            for word in words_to_search:
                content[i] = content[i].replace(word, '')
            if content[i].lstrip().startswith('NOTE'):
                content[i - 1] += ' ' + content[i]
                content[i] = ''
        content = [entry for entry in content if entry]
    recipe = {
        'name': div.find('h1').text.title(),
        'ingredients': content[0].lstrip().split('\n'),
        'prep': content[1].lstrip(),
        'garnish': content[2].lstrip(),
        'category': category_translations[link.split('/')[-3]],
        'img': div.find('img', class_='alignnone')['src'],
        'link': link,
    }
    if 'INGREDIENTS' in recipe['ingredients']:
        recipe['ingredients'].remove('INGREDIENTS')
    return recipe


def get_all_iba_cocktail_recipes() -> Tuple[Dict[str, str], ...]:
    """Return all recipe dictionaries of all official iba cocktails."""
    links = get_all_iba_cocktails_names_and_links()
    return tuple(get_recipe(link) for link in links.values())


def export_cocktails(cocktails_iter: MY_ITERABLE, path: Optional[str] = None) -> None:
    """Create a .json file containing all cocktails in the given iterable."""
    if path is None:
        path = 'Cocktails.json'
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(cocktails_iter))


if __name__ == "__main__":
    print('Fetching all cocktail recipes...')
    export_cocktails(get_all_iba_cocktail_recipes())
    print('Done')