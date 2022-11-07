from unittest.mock import patch

from django.urls import reverse
from recipes.tests.teste_recipe_base import RecipeMixin
from rest_framework import test


class RecipeAPIv2Test(test.APITestCase, RecipeMixin):
    def get_recipe_api_list(self):
        api_url = reverse('recipes:recipe-api-list')
        response = self.client.get(api_url)
        return response

    def test_recipe_api_list_returns_status_code_200(self):
        response = self.get_recipe_api_list()

        self.assertEqual(
            response.status_code,
            200
        )

    @patch('recipes.views.api.RecipeAPIV2Pagination.page_size', new=7)
    def test_recipe_api_list_loads_correct_number_of_recipes(self):
        wanted_number_of_recipes = 9
        self.criar_recipes_em_lote(wanted_number_of_recipes)

        response = self.client.get(reverse('recipes:recipe-api-list'))
        qtd_of_loaded_recipes = len(response.data.get('results'))

        self.assertEqual(
            qtd_of_loaded_recipes,
            wanted_number_of_recipes
        )

    def test_recipe_api_list_do_not_shoe_not_published_recipes(self):
        recipes = self.criar_recipes_em_lote(quantidade=2)
        recipe_not_published = recipes[0]
        recipe_not_published.is_published = False
        recipe_not_published.save()

        response = self.get_recipe_api_list()
        self.assertEqual(
            len(response.data.get('results')),
            1
        )
