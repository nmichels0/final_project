from bs4 import BeautifulSoup
import requests
import json
import csv
from fractions import Fraction
import re

def read_csv(filepath, encoding='utf-8-sig'):
    """
    Reads a CSV file, parsing row values per the provided delimiter. Returns a list of lists,
    wherein each nested list represents a single row from the input file.

    Parameters:
        filepath (str): The location of the file to read
        encoding (str): name of encoding used to decode the file

    Returns:
        list: nested "row" lists
    """

    with open(filepath, 'r', encoding=encoding) as file_obj:
        data = []
        reader = csv.reader(file_obj)
        for row in reader:
            data.append(row)
        return data

def write_csv(filepath, data, headers=None, encoding='utf-8', newline=''):
    """
    Writes data to a target CSV file. Column headers are written as the first
    row of the CSV file if optional headers are specified.

    Parameters:
        filepath (str): path to target file (if file does not exist it will be created)
        data (list | tuple): sequence to be written to the target file
        headers (seq): optional header row list or tuple
        encoding (str): name of encoding used to encode the file
        newline (str): specifies replacement value for newline '\n'
                       or '\r\n' (Windows) character sequences

    Returns:
        None
    """

    with open(filepath, 'w', encoding=encoding, newline=newline) as file_obj:
        writer = csv.writer(file_obj)
        if headers:
            writer.writerow(headers)
            for row in data:
                writer.writerow(row)
        else:
            writer.writerow(data)

def read_json(filepath, encoding='utf-8'):
    """Reads a JSON file and convert it to a Python dictionary

    Parameters:
        filepath (str): a path to the JSON file
        encoding (str): name of encoding used to decode the file

    Returns:
        dict/list: dict or list representations of the decoded JSON document
    """
    with open(filepath, 'r', encoding=encoding) as file_obj:
        return json.load(file_obj)

def write_json(filepath, data, encoding='utf-8', indent=2):
    """Serializes object as JSON. Writes content to the provided filepath.

    Parameters:
        filepath (str): the path to the file

        data (dict)/(list): the data to be encoded as JSON and written to
        the file

        encoding (str): name of encoding used to encode the file

        indent (int): number of "pretty printed" indention spaces applied to
        encoded JSON

    Returns:
        None
    """

    with open(filepath, 'w', encoding=encoding) as file_obj:
        json.dump(data, file_obj, indent=indent)

def get_request(url, params=None):
    '''
    Initiates an HTTP GET request to the SWAPI service in order
    to return a representation of a resource. < params > is not included in the
    request if no params is passed to this function during the function call.
    Once a response is received, it is converted to a python dictionary.

    Parameters:
        url (str): a URL that specifies the resource.
        params (dict): an optional dictionary of querystring arguments.
        The default value is None.

    Returns:
        dict: dictionary representation of the decoded JSON.
    '''

    if params:
        return requests.get(url, params).json()
    else:
        return requests.get(url).json()

def recursion_crawler(url):
    '''
    Recursively crawls through recipe pages that have "Next Page" feature.

    Parameters:
        url (str): page to crawl

    Returns:
        recipe_urls (set): set of recipe urls
    '''

    # Step 1: Request & soup url
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, 'lxml')

    recipe_urls = set()
    articles = soup.find_all('article', class_ = 'post-summary post-summary--default')
    for article in articles:
        recipe_urls.update([article.contents[0]['href']])

    next_page = soup.find_all('li', class_ = 'pagination-next')
    if next_page:
        recipe_urls.update(recursion_crawler(next_page[0].contents[0].attrs['href']))

    return recipe_urls

def recipe_crawler():
    '''
    Crawls through the Budget Bytes website to determine all recipe URLs.

    Parameters:
        None

    Returns:
        recipe_urls (set): list of the recipe URLs on Budget Bytes
    '''
    # Step 0: Request recipes homepage and make soup
    html_text = requests.get('https://www.budgetbytes.com/recipes/').text
    soup = BeautifulSoup(html_text, 'lxml')

    # Step 1: Get all keyword catagories urls
    keyword_urls = set()
    articles = soup.find_all('article')
    for article in articles[1:]: # Ingredient keywords letters A-to-Z
        links = article.find_all('a', href=True)
        for link in links: # Each ingredient starting with current letter
            keyword_urls.update([link['href']])

    # Step 2: Get all recipe urls from each keyword  url
    recipe_urls = set()
    for keyword_url in keyword_urls:
        recipe_urls.update(recursion_crawler(keyword_url))

    return recipe_urls

def collect_costs(soup):
    '''
    Searches BeautifulSoup data to try and determine recipe & serving costs.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        recipe_cost (float): Cost of entire recipe
        serving_cost (float): Cost of single serving
    '''
    try:
        cost = soup.find ('span', class_ = 'cost-per').text.split(' / ')
        if len(cost)==2:
            recipe_cost = float(cost[0].split()[0][1:])
            serving_cost = float(cost[1].split()[0][1:])
        else:
            recipe_cost = float(cost[0].split()[0][1:])
            serving_cost = float(cost[0].split()[0][1:])
    except:
        recipe_cost = None
        serving_cost = None

    return recipe_cost, serving_cost

def collect_servings(soup, recipe_cost, serving_cost):
    '''
    Searches BeautifulSoup data to try and determine amount of servings recipe
    makes.

    Parameters:
        soup: BeautifulSoup parsed data
        recipe_cost (float): Cost of entire recipe
        serving_cost (float): Cost of single serving

    Returns:
        servings (int): Total servings made by recipe
    '''
    try:
        servings = int(soup.find('div', class_ = 'wprm-recipe-block-container wprm-recipe-block-container-separated wprm-block-text-normal wprm-recipe-servings-container').text.split()[1])
    except:
        try:
            servings = round(recipe_cost/serving_cost)
        except:
            servings = 1

    return servings

def collect_times(soup):
    '''
    Searches BeautifulSoup data to try and determine prep, cook, & total time.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        prep_hours (int): hours to prep recipe
        prep_mins (int): mins to prep recipe
        cook_hours (int): hours to cook recipe
        cook_mins (int): mins to cook recipe
        total_hours (int): Total hours to make recipe
        total_mins (int): total mins to make recipe
    '''
    # prep time
    try:
        prep_hours = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-hours wprm-recipe-prep_time wprm-recipe-prep_time-hours').text)
    except:
        prep_hours = 0
    try:
        prep_mins = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-prep_time wprm-recipe-prep_time-minutes').text)
    except:
        prep_mins = 0

    # cook time
    try:
        cook_hours = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-hours wprm-recipe-cook_time wprm-recipe-cook_time-hours').text)
    except:
        cook_hours = 0
    try:
        cook_mins = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-cook_time wprm-recipe-cook_time-minutes').text)
    except:
        cook_mins = 0

    # total time
    try:
        total_hours = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-hours wprm-recipe-total_time wprm-recipe-total_time-hours').text)
    except:
        total_hours = prep_hours + cook_hours
    try:
        total_mins = int(soup.find('span', class_ = 'wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-total_time wprm-recipe-total_time-minutes').text)
    except:
        total_mins = prep_mins + cook_mins

    return prep_hours, prep_mins, cook_hours, cook_mins, total_hours, total_mins

def clean_unit(ingredient_unit):
    '''
    Cleans ingredient unit data.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        unit (str): unit used for ingredient amount
    '''
    if ingredient_unit[-1] == '.':
        ingredient_unit = ingredient_unit[:-1]
    if ingredient_unit[-1] == 's':
        ingredient_unit = ingredient_unit[:-1]
    if ingredient_unit[-3:] == 'can':
        if ingredient_unit[-5] == '.':
            ingredient_unit = ingredient_unit[:-5] + ' can'
        if ingredient_unit[-7] != ' ':
            ingredient_unit = ingredient_unit[:-6] + ' oz can'

    return ingredient_unit

def clean_ingredient(ingredient_name):
    '''Cleans ingredient name data.

    Lots of common issues with ingredient name. Ex:
        Asterisks in middle or end of name 'mozzarella*'
        Parentheticals like '(optional)' or '(about # lbs)'

        ### Everything below this needs to be solved by creating common ingredient list ###
        Ending in ', sliced' or ', divided' or ', thinly sliced'
        salt, salt and pepper, salt & pepper, salt & pepper to taste, freshly cracked pepper, etc.
        Size adjectives like 'medium jalapeno' vs 'jalapeno'
        cheddar cheese vs. cheddar, grated/shredded/'' parmesan, etc.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        name (str): unit used for ingredient amount
    '''
    # Remove asterisks
    ingredient_name = re.sub(r'\*', '', ingredient_name)

    # Remove parentheticals
    ingredient_name = re.sub('\(.*?\)','',ingredient_name).strip()

    return ingredient_name

def collect_ingredients(soup):
    '''
    Searches BeautifulSoup data to try and determine ingredients.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        ingredients_dict (dict): dictionary containing ingredient information
    '''
    ingredients = soup.find_all('li', class_ = 'wprm-recipe-ingredient')
    ingredient_dict = {}
    for ingredient in ingredients:
        # Ingredient Amount
        try:
            ingredient_amount = ingredient.find('span', class_ = 'wprm-recipe-ingredient-amount').text.strip()
            try: # If amount is not fraction
                ingredient_amount = float(ingredient_amount)
            except: # If amount is fraction
                ingredient_amount = float(sum(Fraction(amount) for amount in ingredient_amount.split()))
        except:
            ingredient_amount = None

        # Ingredient Unit
        try:
            ingredient_unit = ingredient.find('span', class_ = 'wprm-recipe-ingredient-unit').text.lower().strip()
            ingredient_unit = clean_unit(ingredient_unit)
        except:
            ingredient_unit = None

        # Ingredient Name
        ingredient_name = ingredient.find('span', class_ = 'wprm-recipe-ingredient-name').text.lower().strip()
        ingredient_name = clean_ingredient(ingredient_name)

        # Ingredient Note
        try:
            ingredient_cost = ingredient.find('span', class_ = 'wprm-recipe-ingredient-notes wprm-recipe-ingredient-notes-normal').text.strip()
            ingredient_cost = float(re.sub(r'[^0-9.]', '', ingredient_cost))
        except:
            ingredient_cost = None

        # Put ingredient data in dict
        ingredient_dict[ingredient_name] = {'amount': ingredient_amount,
                                            'unit': ingredient_unit,
                                            'cost': ingredient_cost}
    return ingredient_dict

def collect_instructions(soup):
    '''
    Searches BeautifulSoup data to try and determine ingredients.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        ingredients_dict (dict): dictionary containing ingredient information
    '''
    instructions = soup.find_all('li', class_ = 'wprm-recipe-instruction')
    steps = []
    for instruction in instructions:
        try:
            steps.append(instruction.find('span').text.strip())
        except:
            steps.append(instruction.text.strip())

    return steps

def recipe_scraper(url):
    '''
    Initiates an HTTP GET request to the provided URL. Scrapes webpage for data
    related to recipe. Returns dictionary with recipe data.

    Parameters:
        url (str): a URL that specifies the resource.

    Returns:
        dict: dictionary representation of recipe data
    '''
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, 'lxml')

    # Collect name
    name = soup.find('h1', class_ = 'entry-title').text

    # Collect Costs
    recipe_cost, serving_cost = collect_costs(soup)

    # Collect servings
    servings = collect_servings(soup, recipe_cost, serving_cost)

    # Collect times
    prep_hours, prep_mins, cook_hours, cook_mins, total_hours, total_mins = collect_times(soup)

    # Collect ingredients
    ingredient_dict = collect_ingredients(soup)

    # Collect instructions
    steps = collect_instructions(soup)

    # Collect keywords & article sections
    script_data = json.loads(soup.find('script', class_ = 'yoast-schema-graph').text)['@graph'][0]
    keywords = script_data['keywords']
    articles = script_data['articleSection']

    return {'name': name,
            'cost': {'recipe': recipe_cost,
                      'serving': serving_cost},
            'servings': servings,
            'time': {'prep_hours': prep_hours,
                     'prep_mins': prep_mins,
                     'cook_hours': cook_hours,
                     'cook_mins': cook_mins,
                     'total_hours': total_hours,
                     'total_mins': total_mins},
            'ingredients': ingredient_dict,
            'instructions': steps,
            'keywords': keywords,
            'article': articles}



def main():

    try:
        recipe_urls = read_csv('recipe_urls.csv')[0]
    except:
        recipe_urls = recipe_crawler()
        write_csv('recipe_urls.csv', list(recipe_urls))

    try:
        recipe_data = read_json('recipe_data.json')
    except:
        recipe_data = {}
        for recipe_url in recipe_urls:
            recipe_temp = recipe_scraper(recipe_url)
            recipe_temp['url'] = recipe_url
            recipe_name = recipe_temp.pop('name')
            recipe_data[recipe_name] = recipe_temp

        write_json('recipe_data.json', recipe_data)

    print('sup\nsup\nsup')





if __name__ == '__main__':
    main()