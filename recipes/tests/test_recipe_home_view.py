from unittest import skip
from unittest.mock import patch

from django.urls import resolve, reverse
from recipes import views
from utils.pagination import RECIPES_PER_PAGE

from .teste_recipe_base import RecipeTestBase


class RecipeHomeViewTest(RecipeTestBase):

    def test_recipe_home_view_function_is_correct(self):
        view = resolve(reverse('recipes:home'))
        self.assertIs(view.func, views.home)

    def test_recipe_home_view_return_status_code_200_OK(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertEqual(response.status_code, 200)

    def test_recipe_home_view_loads_correct_template(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertTemplateUsed(response, 'recipes/pages/home.html')

    @skip('WIP')
    def test_recipe_home_template_shows_no_recipes_found_if_no_recipes(self):
        response = self.client.get(reverse('recipes:home'))
        self.assertIn(
            'No recipes found here :( .',
            response.content.decode('utf-8')
        )

    def test_recipe_home_template_loads_recipes(self):
        self.make_recipe()
        response = self.client.get(reverse('recipes:home'))
        content = response.content.decode('utf-8')
        response_context_recipes = response.context['recipes']

        self.assertIn('Recipe Title', content)
        self.assertEqual(len(response_context_recipes), 1)

    def test_recipe_home_template_dont_load_recipe_not_published(self):
        self.make_recipe(is_published=False)

        response = self.client.get(reverse('recipes:home'))

        self.assertIn(
            'No recipes found here :( .',
            response.content.decode('utf-8')
        )

    def test_if_has_not_pagination_when_less_than_minimum_recipes_per_page(
        self
    ):
        # Se ao ter menos que o mínimo de receitas, não terá paginação
        for i in range(RECIPES_PER_PAGE):
            response = self.client.get(reverse('recipes:home'))
            conteudo = response.content.decode('utf-8')

            self.assertNotIn('pagination-content', conteudo)

            self.make_recipe(
                slug=f'receita-teste-{i}',
                author_data={'username': f'usuario{i}'}
            )

    def test_if_has_pagination_when_have_more_than_recipes_per_page(
        self
    ):
        self.criar_recipes_em_lote(RECIPES_PER_PAGE + 1)

        response = self.client.get(reverse('recipes:home'))
        conteudo = response.content.decode('utf-8')
        self.assertIn('pagination-content', conteudo)

    def test_if_current_page_is_correct(self):
        QTD_PAGINAS = 5
        self.criar_recipes_em_lote(RECIPES_PER_PAGE * QTD_PAGINAS)

        response = self.client.get(
            reverse('recipes:home') + f'?page={QTD_PAGINAS}')
        conteudo = response.context['pagination_range']['current_page']

        self.assertEqual(conteudo, QTD_PAGINAS)

    def test_if_show_first_page_when_current_page_is_incorrect(self):
        QTD_PAGINAS = 2
        self.criar_recipes_em_lote(RECIPES_PER_PAGE * QTD_PAGINAS)

        response = self.client.get(
            reverse('recipes:home') + '?page=B')
        conteudo = response.context['pagination_range']['current_page']

        self.assertEqual(1, conteudo)

    def test_recipe_home_is_paginated(self):
        for i in range(9):
            kwargs = {
                "author_data":  {
                    "username": f'u{i}'
                },
                "slug":         f'r{i}'
            }
            self.make_recipe(**kwargs)

        with patch('recipes.views.RECIPES_PER_PAGE', new=3):
            response = self.client.get(reverse('recipes:home'))
            recipes = response.context['recipes']
            paginator = recipes.paginator

            self.assertEqual(paginator.num_pages, 3)
            self.assertEqual(len(paginator.get_page(1)), 3)
            self.assertEqual(len(paginator.get_page(2)), 3)
            self.assertEqual(len(paginator.get_page(3)), 3)
