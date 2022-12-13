<!-- ABOUT THE PROJECT -->

## UMICH SI507 Final Project: Meal Planner

This project was made for SI507. The purpose of this project is to allow users to automatically create meal plans similar to those available for purchase at https://shop.budgetbytes.com/. This was accomplished by scraping recipe data from throughout the Budget Bytes website. Users are then able to manually add meals to a meal plan, or get recommendations by navigating a tree data strucure containing recipe keywords.

### Built With

This section acknowledges with the key packages (not built-in) used to make this project.

* Beautiful Soup
* requests
* FPDF

<!-- GETTING STARTED -->
## Getting Started

To get started, all you need to do is run the program. If you do not have the recipe_urls.csv, recipe_data.json, or recipeTree.txt already in your directory, then the first run will take a long time to gather and prepare the data.

Once the data is ready, the program will ask if you want to add a meal manually or if you would like recommendations. If you choose manually, you will then have the option to add the name of the recipe. This is useful if you already know what you want or if you saw a recipe you were interested in on the Budget Bytes website. If you choose recommendation, the program will ask the user if they are interested in certain keywords related to the recipe. The responses to these questions let the program navigate a tree data structure containing recipes. Once the program has narrowed down the list of recipes, the user will be asked to select one or start over.

When the user is finished adding recipes to their meal plan, the program will save the meal plan to meal_plan.pdf.

