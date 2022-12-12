import json

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

def main():

    recipe_data = read_json('recipe_data.json')

    try:
        categories = read_json('food_categories.json')
    except:
        categories = {'Bakery': [],
                    'Canned Goods': [],
                    'Dairy': [],
                    'Dry Goods': [],
                    'Produce': [],
                    'Meat': [],
                    'Frozen': [],
                    'Sauces Oils Vinegars': [],
                    'Spices': [],
                    'Junk': []}


    for recipe, data in recipe_data.items():
        for ingredient in data['ingredients']:
            new_ingredient = True
            for category, value in categories.items():
                if ingredient in value:
                    new_ingredient = False
                    break
            if new_ingredient == True:
                if any(substring in ingredient for substring in ['divided', 'sliced', 'or', 'minced', 'taste', '1','2','3','4','5','6','7','8','9','10', 'optional', 'shredded', 'grated', 'chopped', 'cooked', 'uncooked', 'bunch', 'pinch', 'medium', 'small', 'med', 'packed', 'drained', 'large', 'diced']):
                    categories['Junk'].append(ingredient)
                elif 'frozen' in ingredient:
                    categories['Frozen'].append(ingredient)
                else:
                    print(f'New ingredient: {ingredient}. Would you like to add this to a category? ', end='')
                    if answer() == True:
                        while True:
                                print(f'Please specify the category: ', end = '')
                                cat = input().title()
                                if cat in categories:
                                    categories[cat].append(ingredient)
                                    break
                    else:
                        categories['Junk'].append(ingredient)
            write_json('food_categories.json', categories)





    print('sup\nsup\nsup')



if __name__ == '__main__':
    main()