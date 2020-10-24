import json
import random
from typing import Any, Dict, Iterable, List, Optional

from flask import Flask, render_template, request

MY_ITERABLE = Iterable[Dict[str, str]]
app = Flask(__name__)


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


def get_random_recipe(cocktails_iter: MY_ITERABLE) -> Dict[str, str]:
    """Return a random cocktail from the given iterable"""
    return random.choice(cocktails_iter) # type: ignore


def find_recipe_by_name(cocktail_iter: MY_ITERABLE, cocktail_name: str) -> Dict[str, str]:
    """Return a cocktail dictionary matching `cocktail_name`
    from `cocktail_iter` or an empty recipe if not found"""
    for cocktail in cocktail_iter:
        if cocktail_name.lower() == cocktail['name'].lower():
            return cocktail
    return {'': ''}


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


@app.route('/', methods=['GET', 'POST'])
def home() -> str:
    cocktails = import_cocktails()
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
    app.run(threaded=True, port=5000)