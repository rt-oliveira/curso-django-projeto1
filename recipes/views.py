from django.db.models import F, Q, Value
from django.db.models.aggregates import Avg, Count, Max, Min, Sum
from django.db.models.functions import Concat
from django.forms.models import model_to_dict
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView
from tag.models import Tag
from utils.pagination import RECIPES_PER_PAGE, make_pagination

from recipes.models import Recipe


class RecipeListViewBase(ListView):
    model = Recipe
    context_object_name = 'recipes'
    paginate_by = None
    ordering = ['-id']

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()
        qs = qs.filter(
            is_published=True
        )
        qs = qs.select_related('author', 'category')
        qs = qs.prefetch_related('tags', 'author__profile')

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        page_obj, pagination_range = make_pagination(
            self.request, ctx.get(self.context_object_name), RECIPES_PER_PAGE)

        html_language = translation.get_language()

        ctx.update({
            'recipes': page_obj,
            'pagination_range': pagination_range,
            'html_language': html_language
        })

        return ctx


class RecipeListViewHome(RecipeListViewBase):
    template_name = 'recipes/pages/home.html'


class RecipeListViewHomeApi(RecipeListViewBase):
    template_name = 'recipes/pages/home.html'

    def render_to_response(self, context, **response_kwargs):
        recipe_obj = self.get_context_data()['recipes']
        recipes = recipe_obj.object_list.values()

        return JsonResponse(
            list(recipes),
            safe=False
        )


class RecipeListViewCategory(RecipeListViewBase):
    template_name = 'recipes/pages/category.html'

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        qs = qs.filter(
            category__id=self.kwargs.get('category_id'),
            is_published=True
        )

        if not qs:
            raise Http404()

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        category_translation = _('Category')
        category_name = ctx.get('recipes')[0].category.name

        ctx.update({
            'title': f'{category_name} - {category_translation} | '
        })

        return ctx


class RecipeListViewSearch(RecipeListViewBase):
    template_name = 'recipes/pages/search.html'

    def get_queryset(self, *args, **kwargs):
        search_term = self.request.GET.get('q', '')

        if not search_term:
            raise Http404()

        qs = super().get_queryset(*args, **kwargs)

        qs = qs.filter(
            Q(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            ),
            is_published=True
        )

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        search_term = self.request.GET.get('q', '')

        ctx.update({
            'page_title': f'Search for "{search_term}" |',
            'search_term': search_term,
            'additional_url_query': f'&q={search_term}'
        })

        return ctx


class RecipeDetail(DetailView):
    model = Recipe
    context_object_name = 'recipe'
    template_name = 'recipes/pages/recipe-view.html'

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.filter(is_published=True)

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'is_detail_page': True})

        return ctx


class RecipeDetailApi(RecipeDetail):

    def render_to_response(self, context, **response_kwargs):
        recipe = self.get_context_data()['recipe']
        recipe_dict = model_to_dict(recipe)

        recipe_dict['created_at'] = str(recipe.created_at)
        recipe_dict['updated_at'] = str(recipe.updated_at)

        if recipe_dict.get('cover'):
            recipe_dict['cover'] = self.request.build_absolute_uri() + \
                recipe_dict['cover'].url[1:]
        else:
            recipe_dict['cover'] = ''

        del recipe_dict['is_published']
        del recipe_dict['preparation_steps_is_html']

        return JsonResponse(
            recipe_dict,
            safe=False
        )


def theory(request, *args, **kwargs):
    recipes = Recipe.objects.get_published().annotate(
        author_full_name=Concat(F('author__first_name'),
                                Value(' '),
                                F('author__last_name'),
                                Value(' ('),
                                F('author__username'),
                                Value(')'))
    )[:5]
    dados_recipes = recipes.aggregate(
        qtd=Count('id'),
        max_id=Max('id'),
        min_id=Min('id'),
        avg_id=Avg('id'),
        soma_id=Sum('id')
    )

    context = {
        'recipes': recipes,
        'dados_recipes': dados_recipes
    }

    return render(
        request,
        'recipes/pages/theory.html',
        context=context
    )


class RecipeListViewTag(RecipeListViewBase):
    template_name = 'recipes/pages/tag.html'

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        qs = qs.filter(
            tags__slug=self.kwargs.get('slug', '')
        )

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        page_title = Tag.objects.filter(
            slug=self.kwargs.get('slug', '')).first()

        if not page_title:
            page_title = 'No recipes found'

        page_title = f'{page_title} - Tag |'

        ctx.update({
            'page_title': page_title
        })

        return ctx
