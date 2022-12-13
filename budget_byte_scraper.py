from bs4 import BeautifulSoup
import requests
import json
import csv
from fractions import Fraction
import re
from fpdf import FPDF

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

def collect_keywords(soup):
    '''
    Searches BeautifulSoup data to try and determine keywords & articles.

    Parameters:
        soup: BeautifulSoup parsed data

    Returns:
        keywords (list): list containing ingredient keywords
        articles (list): list containing ingredient articles
    '''
    script_data = json.loads(soup.find('script', class_ = 'yoast-schema-graph').text)['@graph'][0]
    keywords = script_data['keywords']
    articles = script_data['articleSection']

    # Need to fix one article and remove unwanted/vague articles
    unwanted = ['Recipes', 'Fall Recipes', 'Quick Recipes', 'Sauce Recipes', 'Comfort Food Recipes', 'Side Dish Recipes', 'Budget Friendly Meal Prep', 'Globally Inspired Recipes', 'Main Dish Recipes', 'Vegetarian Meal Prep Recipes', 'Winter Recipes', 'SNAP Challenge', 'Quick Pasta Recipes', 'Bowl Meals', 'No-Cook Recipes', 'Spring Recipes', 'Summer Recipes', 'Appetizer Recipes', 'Holiday Recipes']
    for i, article in enumerate(articles[:]):
        if article == 'Bean &amp; Grain Recipes':
            articles.remove('Bean &amp; Grain Recipes')
            articles.append('Bean & Grain Recipes')
        elif article in unwanted:
            articles.remove(article)
        elif 'under' in article.lower():
            articles.remove(article)

    return keywords, articles

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
    name = soup.find('h1', class_ = 'entry-title').text.lower()

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
    keywords, articles = collect_keywords(soup)

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

def clean_recipes(recipes):
    '''
    Removes recipes that are missing data

    Parameters:
        recipes (dict): Dictionary of all the recipes

    Returns:
        recipes (dict): Dictionary of all the recipes with bad recipes removed
    '''
    clean_recipes = {recipe_name:recipe_data for recipe_name,recipe_data in recipes.items()
                     if len(recipe_data['ingredients']) > 0 and len(recipe_data['instructions']) > 0}

    return clean_recipes

def keywords_counter(recipes):
    '''
    Counts the number of times each keyword and article appears

    Paramters:
        recipes (dict): Dictinoary from recipes based on keywords and articles

    Returns:
        keywords_articles (dict): Dictionary containing count of every keyword & article
    '''
    keywords_articles = {}
    for recipe in recipes.values():
        for keyword in recipe['keywords']:
            if keyword not in keywords_articles:
                keywords_articles[keyword] = 1
            else:
                keywords_articles[keyword] += 1
        for article in recipe['article']:
            if article not in keywords_articles:
                keywords_articles[article] = 1
            else:
                keywords_articles[article] += 1

    return keywords_articles

def keywords_queuer(keywords_articles):
    '''
    Builds queue of keywords & articles from most to least frequently used

    Parameters:
        keywords_artiles (dict): Dictionary containing count of every keyword & article

    Returns:
        keywords_queue (list): Queue of keywords & articles from most to least frequent
    '''

    keywords_queue = list(keywords_articles.items())
    keywords_queue.sort(key=lambda x: x[1], reverse=True)
    keywords_queue = [keyword[0] for keyword in keywords_queue]
    return keywords_queue

def answer():
    '''Asks user for answer until yes/no is entered

    Asks for user's answer. Does simple formatting of string to provide some leeway.
    If answer cannot be determined, asks user to enter new answer.

    Parameters:
        None

    Returns:
        bool: returns True if answer is 'yes' and False if answer is 'no'
    '''

    yes_list = ['yes', 'yep','yeah','yea','y','aye','surely','for sure','of course','definitely','certainly','absolutely','affirmative','you bet', 'you betcha', 'yes sir', 'yes ma\'am']
    no_list = ['no','nope','nay', 'nan','never','n','noway', 'no way','absolutely not', 'of course nort', 'certainly not', 'negative', 'not a chance']

    yesno = input().strip().lower()
    if yesno in yes_list:
        return True
    elif yesno in no_list:
        return False
    else:
        print(f'Please respond with \'yes\' or \'no\': ',end = '')
        return answer()

def recipe_tree(recipes):
    '''
    Builds a tree data structure from recipes based on keywords and articles

    Parameters:
        recipes (dict): Dictionary of all recipes

    Returns:
        tree: Tree data structure
    '''

    # First get dictionary containing every keyword and article & count of how often they appear
    keywords_articles = keywords_counter(recipes)

    # Build queue of keywords to use from most to to least frequent words
    keywords_queue = keywords_queuer(keywords_articles)

    # Build recipe dictionaries which have and don't have most frequent keyword
    contains_keyword = {}
    missing_keyword = {}
    for name, recipe in recipes.items():
        if keywords_queue[0] in recipe['keywords']:
            recipe['keywords'].remove(keywords_queue[0])
            contains_keyword[name] = recipe
        elif keywords_queue[0] in recipe['article']:
            recipe['article'].remove(keywords_queue[0])
            contains_keyword[name] = recipe
        else:
            missing_keyword[name] = recipe

    # Only want to narrow down recipes to <= 10 to give broader list of recommendations
    if len(contains_keyword) <= 10:
        contains_branch = ([recipe for recipe in contains_keyword], None, None)
    else:
        contains_branch = recipe_tree(contains_keyword)

    if len(missing_keyword) <= 10:
        missing_branch = ([recipe for recipe in missing_keyword], None, None)
    else:
        missing_branch = recipe_tree(missing_keyword)

    tree = (keywords_queue[0], contains_branch, missing_branch)
    return tree

def saveTree(tree, treeFile):
    '''Saves tree to TreeFile using desired format

    Accepts TreeFile file handle to allow program to work recursively.
    Writes tree to file in following format:
        Internal node
        'question text here'
        Leaf
        'answer1 text here'
        Leaf
        'answer2 text here'
        ...

    Parameters:
        tree (tuple): The 20 Questions tree tuple that is to be saved to a file
        TreeFile (file handle): File handle we are writing to

    Returns:
        None
    '''
    if (tree[1] == None) and (tree[2] == None): #If tree node is answer/leaf
        print('Leaf', file = treeFile)
        print(tree[0], file = treeFile)
    else: #If tree node is question/internal
        print('Internal Node', file = treeFile)
        print(tree[0], file = treeFile)
        saveTree(tree[1], treeFile)
        saveTree(tree[2], treeFile)

def saveTreeWrap(tree, treeFile):
    '''Opens and closes file for saveTree function

    Parameters:
        tree (tuple): The 20 Questions tree tuple that is to be saved to a file
        TreeFile (file handle): File handle we are writing to

    Returns:
        None
    '''
    treeFile = open(treeFile, 'w')
    saveTree(tree, treeFile)
    treeFile.close()

def loadTree(treeFile):
    '''Loads tree from treeFile

    Accepts TreeFile file handle to allow program to work recursively.
    Reads tree from file with the following format:
        Internal node
        'question text here'
        Leaf
        'answer1 text here'
        Leaf
        'answer2 text here'
        ...

    Parameters:
        TreeFile (file handle): File handle we are reading from

    Returns:
        tree (tuple): tree read from file
    '''
    line = treeFile.readline().strip()
    if line == 'Internal Node':
        question = treeFile.readline().strip()
        node1 = loadTree(treeFile)
        node2 = loadTree(treeFile)
        return (question, node1, node2)
    else: #line == 'Leaf'
        return (treeFile.readline().strip(), None, None)

def loadTreeWrap(treeFile):
    '''Opens and closes file for loadTree function

    Parameters:
        tree (tuple): The 20 Questions tree tuple that is to be saved to a file
        TreeFile (file handle): File handle we are writing to

    Returns:
        tree (tuple): tree read fromfile
    '''
    treeFile = open(treeFile, 'w')
    loadTree(treeFile)
    treeFile.close()

def printNames(names):
    '''
    Prints recipe names in a user-friendly way.

    Parameters:
        names (list): list with recipes names data

    Returns:
        None
    '''
    for number, name in enumerate(names):
        print(number+1, name)

def printPlan(meals):
    '''
    Prints key information about the meal plan that has built so far.

    Parameters:
        meals (dict): Dictionary containing recipes to be added to the meal plan

    Returns:
        None
    '''
    meal_list = []
    for meal, data in meals.items():
        cost = data['cost']['recipe']
        meal_list.append([meal, f'${cost}', data['servings']])

    for title in ['Recipe', 'Cost', 'Servings']:
        print('{0:<40}'.format(title), end='')

    print()
    for meal in meal_list:
        for item in meal:
            print('{0:<40}'.format(item), end='')
        print()

def simplePlay(tree):
    '''Accepts a tree & helps user find recipe they are interested in

    Recursive function that asks a series of questions to a user before
    recommending the user a recipe.

    Parameters:
        tree (tuple): tree tuple that is either a question (internal) or answer (leaf) node.

    Returns:
        meal (str): Returns meal name if one is selected or None if the user wants to start over
    '''
    print(f'We will go through a list of ingredients and articles related to the recipes. If you want recipes with these ingredients, answer yes. Similarly, answer no if you are not interested in these ingredients or recipe types.')
    if (tree[1] == None) and (tree[2] == None): #If tree node is answer/leaf
        length = len(tree[0])
        while True:
            print(f'Type a number 1-{length} to select the recipe you want to add, or type “try again” to start over: ')
            printNames(tree[0])
            response = input().strip().lower()
            if response in [str(x) for x in range(1, length + 1)]:
                return tree[0][int(response)-1]
            elif response == 'try again':
                return None
            else:
                print(f'Type a number 1-{length} to select the recipe you want to add, or type “try again” to start over: ', end ='')
    else: #Tree node is question/internal
        print(f'Would you like {tree[0]}?')
        if answer() == True:
            return simplePlay(tree[1])
        else:
            return simplePlay(tree[2])

def initialize_data():
    '''Prepares all of the data for the program

    Collects URLs if necessary, collects recipe data if necessary, makes tree
    data structure if necessary

    Parameters:
        None

    Returns:
        recipe_data (dict): Dictionary of all recipes
        tree (tuple): Tree data structure for recipe recommendations
    '''
    try: # Check cache for recipe data
        recipe_data = read_json('recipe_data.json')
    except: # Scrape new recipe data
        try: # Check cache for recipe URLs
            recipe_urls = read_csv('recipe_urls.csv')[0]
        except: # Crawl for new recipe URLs
            recipe_urls = recipe_crawler()
            write_csv('recipe_urls.csv', list(recipe_urls))
        recipe_data = {}
        for recipe_url in recipe_urls:
            recipe_temp = recipe_scraper(recipe_url)
            recipe_temp['url'] = recipe_url
            recipe_name = recipe_temp.pop('name')
            recipe_data[recipe_name] = recipe_temp
        recipe_data = clean_recipes(recipe_data)
        write_json('recipe_data.json', recipe_data)

    try:
        tree = loadTreeWrap('recipeTree.txt')
    except:
        tree = recipe_tree(recipe_data)
        saveTreeWrap(tree, 'recipeTree.txt')

    return recipe_data, tree

def meal_plan_builder(recipe_data, tree):
    '''Takes user input to build a meal plan

    Parameters:
        recipe_data (dict): Dictionary of all recipes
        tree (tuple): Tree data structure for recipe recommendations

    Returns:
        meals (dict): Dictionary containing recipes added to the meal plan
    '''
    # Initialize variables
    meals = {}
    finished = False
    manual = ['man', 'manual', 'manually']
    recommend = ['rec', 'recommend', 'recommendation', 'recommendations', 'recommended']

    #Print Welcome message
    print(f'Hi and welcome to the Meal Planner! Let\'s get started by adding a recipe to your meal plan!', end = ' ')

    # Begin meal plan loop
    while finished == False:
        while True:
            print(f'Would you like to add a meal manually or do you want some recommendations?')
            method = input().lower().strip()
            if method in manual or method in recommend:
                break
            else:
                print(f'Please answer with either \'manual\' or \'recommend\' when prompted.', end = ' ')
        if method in manual:
            while True:
                print(f'What is the name of the meal you would like to add?')
                meal = input().lower().strip()
                if meal in recipe_data:
                    meals[meal] = recipe_data[meal]
                    print(f'Great! {meal.title()} has been added to your meal plan! Here is your meal plan so far: ')
                    printPlan(meals)
                    break
                else:
                    print(f'It seems like that recipe isn\'t available. Try something else.')

        elif method in recommend:
            while True:
                meal = simplePlay(tree)
                if meal != None:
                    meals[meal] = recipe_data[meal]
                    print(f'Great! {meal.title()} has been added to your meal plan! Here is your meal plan so far: ')
                    printPlan(meals)
                    break

        print(f'Type \'finished\' if you are done with your meal plan, otherwise enter anything else to continue.')
        response = input().lower().strip()
        if response == 'finished':
            finished = True

    return meals

def grocery_list(recipes):
    '''Builds a grocery list for provided recipes

    Goes through each recipe to determine amount and category of each
    ingredient that is needed. Determines category of each ingredient.

    Parameters:
        recipes (list): List of recipe dictionaries

    Returns:
        grocery_list (dict): Categorized ingredients with quantities needed
    '''
    grocery_list = []
    # groery_list = [['rice', 1, 'cup'], ['apple, 2, 'oz'], ['flour', 2, 'oz']]
    for recipe in recipes.values():
        for ingredient, data in recipe['ingredients'].items():
            temp = [ingredient, data['amount'], data['unit']]
            new_grocery = True
            for i, grocery in enumerate(grocery_list):
                if grocery[0] == temp[0] and grocery[2] == temp[2]:
                    grocery_list[i][1] += temp[1]
                    new_grocery = False
                    break
            if new_grocery == True:
                grocery_list.append(temp)

    grocery_list.sort(key=lambda x: x[0]) # Alphabetical sort
    return grocery_list

class PDF(FPDF):
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def recipe_title(self, recipe_name):
        # Arial Bold Italic 32
        self.set_font('Arial', 'BI', 36)
        # Title
        self.multi_cell(0, 12, f'{recipe_name.title()}', 0, 'C')
        # Line break
        self.ln(4)

    def recipe_grocery(self, groceries):
        # Arial Bold Italic 32
        self.set_font('Arial', 'BIU', 36)
        # Title
        self.multi_cell(0, 12, f'GROCERY LIST', 0, 'C')
        # Line break
        self.ln(4)
        # Arial Bold Italic Underlined 10
        y_orig = self.get_y()
        x_orig = self.get_x()
        x_pos = self.get_x()
        self.set_font('Arial', '', 10)
        columns = 1
        # Print each ingredient
        for i, grocery in enumerate(groceries):
            self.set_x(x_pos)
            # Arial Bold 10
            if grocery[1] == None and grocery[2] == None:
                self.multi_cell(0, 7, f'{grocery[0]}', 0)
            elif grocery[1] == None:
                self.multi_cell(0, 7, f'{grocery[2]} {grocery[0]}', 0)
            elif grocery[2] == None:
                self.multi_cell(0, 7, f'{grocery[1]} {grocery[0]}', 0)
            else:
                self.multi_cell(0, 7, f'{grocery[1]} {grocery[2]} {grocery[0]}', 0)
            y_temp = self.get_y()
            if y_temp >= 260:
                columns += 1
                if columns > 3:
                    self.add_page()
                    x_pos = x_orig
                    self.set_xy(x_orig, y_orig)
                else:
                    x_pos += 50
                    self.set_y(y_orig)

    def recipe_info(self, recipe_data):
        # Arial Bold 12
        self.set_font('Arial', 'B', 12)
        # self.cell(0, 20, 'Servings   Prep Time   Cook Time   Total Time', 'TB', 1, 'C')
        self.cell(0, 5, f"{'Servings':30s} {'Prep Time':30s} {'Cook Time':30s} {'Total Time'}", 'T', 1, 'C')
        servings = str(recipe_data['servings'])
        prep_time = f"{recipe_data['time']['prep_hours']} hours {recipe_data['time']['prep_mins']} mins"
        cook_time = f"{recipe_data['time']['cook_hours']} hours {recipe_data['time']['cook_mins']} mins"
        total_time = f"{recipe_data['time']['total_hours']} hours {recipe_data['time']['total_mins']} mins"
        # Arial 12
        self.set_font('Arial', '', 12)
        self.cell(0, 5, f"{'':18s} {servings:25s} {prep_time:29s} {cook_time:28s} {total_time}", 'B', 1, 'L')
        self.cell(0,5, '', 0, 1)

    def recipe_ingredients(self, recipe_data):
        # Arial Bold Italic Underlined 10
        self.set_font('Arial', 'BIU', 10)
        self.cell(0, 5, f'INGREDIENTS', 0, 1)
        # Arial Bold 10
        self.set_font('Arial', 'B', 10)
        # Print each ingredient on left side of page
        for ingredient, data in recipe_data['ingredients'].items():
            if data['unit'] == None and data['amount'] == None:
                self.multi_cell(60, 4, f'{ingredient}', 0, 1)
            elif data['unit'] == None:
                self.multi_cell(60, 4, f'{data["amount"]} {ingredient}', 0, 1)
            elif data['amount'] == None:
                self.multi_cell(60, 4, f'{data["unit"]} {ingredient}', 0, 1)
            else:
                self.multi_cell(60, 4, f'{data["amount"]} {data["unit"]} {ingredient}', 0, 1)

            self.cell(0,4, '', 0, 1)

    def recipe_instructions(self, recipe_data, y_top):
        # Arial Bold Italic Underlined 10
        self.set_xy(65, y_top)
        self.set_font('Arial', 'BIU', 10)
        self.cell(0, 5, f'INSTRUCTIONS', 0, 1)
        self.set_x(65)
        # Print each ingredient on left side of page
        for i, instruction in enumerate(recipe_data['instructions']):
            # Arial Bold 10
            self.set_font('Arial', 'B', 10)
            self.multi_cell(0, 7, f'{i+1}. ', 0)
            y_temp = self.get_y()
            self.set_xy(70,y_temp-7)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 7, f'{instruction}', 0)
            y_temp = self.get_y()
            self.set_xy(65, y_temp+3)


def main():

    # Get recipe data & tree data strucutre
    recipe_data, tree = initialize_data()

    # # Build a meal plan
    meals = meal_plan_builder(recipe_data, tree)

    # Determine groceries needed
    groceries = grocery_list(meals)

    # Build PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    # Grocery PDF page should add here
    # pdf.recipe_title('GROCERY LIST')
    pdf.recipe_grocery(groceries)
    pdf.add_page()
    # Loop Begins here for each Recipe
    for i, (meal, recipe) in enumerate(meals.items()):
        pdf.recipe_title(meal)
        pdf.recipe_info(recipe)
        y_top = pdf.get_y()
        pdf.recipe_ingredients(recipe)
        pdf.recipe_instructions(recipe, y_top)
        if i != len(meals)-1:
            pdf.add_page()

    pdf.output('meal_plan.pdf','F')
    print('Your meal plan has been saved!')

if __name__ == '__main__':
    main()