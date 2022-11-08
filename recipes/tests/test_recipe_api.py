from unittest.mock import patch

from django.urls import reverse
from recipes.tests.teste_recipe_base import RecipeMixin
from rest_framework import test


class RecipeAPIv2TestMixin(RecipeMixin):
    def get_recipe_list_reverse_url(self, reverse_result=None):
        api_url = reverse_result or reverse('recipes:recipe-api-list')
        return api_url

    def get_recipe_api_list(self, reverse_result=None):
        api_url = self.get_recipe_list_reverse_url(reverse_result)
        response = self.client.get(api_url)
        return response

    def get_auth_data(self, username='user', password='password'):
        userdata = {
            'username': username,
            'password': password
        }
        user = self.make_author(username=userdata.get('username'),
                                password=userdata.get('password')
                                )
        response = self.client.post(
            reverse('recipes:token_obtain_pair'),
            data={**userdata}
        )
        return {
            'jwt_access_token': response.data.get('access'),
            'jwt_refresh_token': response.data.get('refresh'),
            'user': user
        }

    def get_recipe_raw_data(self):
        return {
            'title': 'This is the title',
            'description': 'This is the description',
            'preparation_time': 1,
            'preparation_time_unit': 'Minutes',
            'servings': '1',
            'servings_unit': 'Person',
            'preparation_steps': 'This is the preparation steps.'
        }


class RecipeAPIv2Test(test.APITestCase, RecipeAPIv2TestMixin):
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

    @patch('recipes.views.api.RecipeAPIV2Pagination.page_size', new=10)
    def test_recipe_api_list_loads_recipes_by_category_id(self):
        category_wanted = self.make_category(name='WANTED_CATEGORY')
        category_not_wanted = self.make_category(name='WANTED_NOT_CATEGORY')

        recipes = self.criar_recipes_em_lote(quantidade=10)

        for recipe in recipes:
            recipe.category = category_wanted
            recipe.save()
        recipes[0].category = category_not_wanted
        recipes[0].save()

        api_url = reverse('recipes:recipe-api-list') + \
            f'?category_id={category_wanted.id}'
        response = self.get_recipe_api_list(api_url)

        self.assertEqual(
            len(response.data.get('results')),
            9
        )

    def test_recipe_api_list_user_must_send_jwt_token_to_create_recipe(self):
        api_list = self.get_recipe_list_reverse_url()
        response = self.client.post(api_list)
        self.assertEqual(
            response.status_code,
            401
        )

    def test_recipe_api_list_logged_user_can_create_a_recipe(self):
        recipe_raw_data = self.get_recipe_raw_data()
        auth_data = self.get_auth_data()
        jwt_access_token = auth_data.get('jwt_access_token')

        response = self.client.post(
            self.get_recipe_list_reverse_url(),
            data=recipe_raw_data,
            HTTP_AUTHORIZATION=f'Bearer {jwt_access_token}'
        )
        self.assertEqual(
            response.status_code,
            201
        )

    def test_recipe_api_list_logged_user_can_update_a_recipe(self):
        # Arrange
        recipe = self.make_recipe()
        access_data = self.get_auth_data()
        jwt_access_token = access_data.get('jwt_access_token')
        author = access_data.get('user')
        recipe.author = author
        recipe.save()

        wanted_new_title = f'The new title updated by {author.username}'

        # Action
        response = self.client.patch(
            reverse('recipes:recipe-api-detail', args=(recipe.id,)),
            data={
                'title': wanted_new_title
            },
            HTTP_AUTHORIZATION=f'Bearer {jwt_access_token}'
        )

        # Assertion
        self.assertEqual(
            response.data.get('title'),
            wanted_new_title
        )

    def test_recipe_api_list_logged_user_cant_update_a_recipe_owned_by_another_user(self):  # noqa
        # Arrange
        recipe = self.make_recipe()
        access_data = self.get_auth_data()

        # Actual owner of the recipe
        author = access_data.get('user')
        recipe.author = author
        recipe.save()

        # This user cannot update the recipe because it is owned by another
        # user
        another_user = self.get_auth_data(username='cant_update')

        # Action
        response = self.client.patch(
            reverse('recipes:recipe-api-detail', args=(recipe.id,)),
            data={},
            HTTP_AUTHORIZATION=f"Bearer {another_user.get('jwt_access_token')}"
        )

        # Assertion
        self.assertEqual(
            response.status_code,
            403
        )
