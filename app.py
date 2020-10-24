import json
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup
from flask import Flask, render_template, request
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


def get_recipe(link: str, words_to_search : Iterable[str] = WORDS,
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


def get_random_recipe(cocktails_iter: MY_ITERABLE) -> Dict[str, str]:
    """Return a random cocktail from the given iterable"""
    return random.choice(cocktails_iter) # type: ignore


def export_cocktails(cocktails_iter: MY_ITERABLE, path: Optional[str] =None) -> None:
    """Create a .json file containing all cocktails in the given iterable."""
    if path is None:
        path = 'Cocktails.json'
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(cocktails_iter))


def import_cocktails(path: Optional[str] = None) -> Any:
    """Return the contents of a .json file."""
    if path is None:
        path = 'Cocktails.json'
    with open(path, 'r', encoding='utf-8') as file:
        return json.loads(file.read())


def search_recipes_by_filters(cocktails_iter: MY_ITERABLE, ingredients: str,
                              category: str, cocktail_name: str) -> List[Dict[str, str]]:
    """Return a list of all cocktails in the given iterable that match the given criteria."""
    results = []
    if ingredients is None:
        ingredients = ''
    if category is None:
        category = ''
    if cocktail_name is None:
        cocktail_name = ''
    for cocktail in cocktails_iter:
        if (category.lower() in cocktail['category'].lower()
            and (cocktail_name.lower() in cocktail['name'].lower()
                 or cocktail['name'].lower() in cocktail_name.lower())
            and all(ingredient.lower() in ''.join(cocktail['ingredients']).lower()
                    for ingredient in ingredients.split(','))):
            results.append(cocktail)
    return results


def render_cocktail(path: str, cocktails_iter: MY_ITERABLE, results: Optional[MY_ITERABLE] = None,
                    cocktail: Optional[str] = None) -> str:
    """Render a template of a specific or a random cocktail."""
    if cocktail:
        recipe = find_recipe_by_name(cocktails_iter, cocktail)
        select = False
    else:
        recipe = get_random_recipe(cocktails_iter)
        select = True
    return render_template(path, name=recipe['name'],
                           ingredients=recipe['ingredients'], garnish=recipe['garnish'], prep=recipe['prep'],
                           category=recipe['category'], image=recipe['img'], results=results, select=select)


def find_recipe_by_name(cocktail_iter: MY_ITERABLE, cocktail_name: str) -> Dict[str, str]:
    """Return a cocktail dictionary matching `cocktail_name`
    from `cocktail_iter` or an empty recipe if not found"""
    for cocktail in cocktail_iter:
        if cocktail_name.lower() == cocktail['name'].lower():
            return cocktail
    return {'': ''}


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home() -> str:
    """Render a template based on the http request's headers."""
    ingredients = request.form.get('ingredients-search')
    category = request.form.get('category-select')
    cocktail_name = request.form.get('cocktail-name-search')
    recipe_select = request.form.get('recipe-select')
    results = request.form.getlist('search-results')
    displayed = request.form.get('displayed')
    if recipe_select:
        results = tuple(find_recipe_by_name(cocktails, result) for result in results)
        return render_cocktail('select.j2', results, results=results, cocktail=recipe_select)
    elif displayed:
        return render_cocktail('index.j2', cocktails, cocktail=displayed)
    elif not any((ingredients, category, cocktail_name)):
        return render_cocktail('index.j2', cocktails)
    else:
        results = search_recipes_by_filters(cocktails_iter=cocktails,
                                            ingredients=ingredients,  # type: ignore
                                            category=category,  # type: ignore
                                            cocktail_name=cocktail_name)  # type: ignore
        if len(results) == 0:
            return render_cocktail('no_result.j2', cocktails)
        else:
            return render_cocktail('select.j2', results, results=results)


if __name__ == "__main__":
    print('Fetching all cocktail recipes...')
    export_cocktails(get_all_iba_cocktail_recipes())
    cocktails = import_cocktails()
    print('Starting up server...')
    app.run(threaded=True, port=5000)