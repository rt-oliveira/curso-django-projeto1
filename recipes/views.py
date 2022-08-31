from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
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

        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        page_obj, pagination_range = make_pagination(
            self.request, ctx.get(self.context_object_name), RECIPES_PER_PAGE)

        ctx.update({'recipes': page_obj, 'pagination_range': pagination_range})

        return ctx


class RecipeListViewHome(RecipeListViewBase):
    template_name = 'recipes/pages/home.html'


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
        category_name = ctx.get('recipes')[0].category.name
        ctx.update({
            'title':    f'{category_name} - Category | '
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
            'page_title':           f'Search for "{search_term}" |',
            'search_term':          search_term,
            'additional_url_query': f'&q={search_term}'
        })

        return ctx


def recipe(request, id):
    recipe = get_object_or_404(
        Recipe,
        pk=id,
        is_published=True
    )

    return render(request, 'recipes/pages/recipe-view.html', context={
        'recipe':           recipe,
        'is_detail_page':   True
    })
