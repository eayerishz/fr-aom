from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib import messages
from .forms import NewItemForm, EditItemForm
from .models import Category


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)



def items(request):
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', 0)
    categories = Category.objects.all()
    items = Item.objects.filter(is_sold=False)

    if category_id:
        items = items.filter(category_id=category_id)

    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    return render(request, 'item/items.html', {
        'items': items,
        'query': query,
        'categories': categories,
        'category_id': int(category_id)
    })



def detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    related_items = Item.objects.filter(category=item.category, is_sold=False).exclude(pk=pk)[:3]
    ratings = item.ratings.all()  # Get all ratings for the item

    return render(request, 'item/detail.html', {
        'item': item,
        'related_items': related_items,
        'ratings': ratings
    })



@login_required
def new(request):
    if request.method == 'POST':
        form = NewItemForm(request.POST, request.FILES)

        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = NewItemForm()

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'New item',
    })



@login_required
def edit(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = EditItemForm(request.POST, request.FILES, instance=item)

        if form.is_valid():
            form.save()

            return redirect('item:detail', pk=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Edit item',
    })


@superuser_required
@login_required
def delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    return redirect('core:index')


from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def rate_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    existing_rating = Rating.objects.filter(item=item, user=request.user).first()
    if existing_rating:
        return JsonResponse({"error": "You have already rated this item."}, status=400)

    if request.method == 'POST':
        data = request.POST
        rating_value = data.get('rating')
        comment = data.get('comment', '')

        if not rating_value or float(rating_value) < 1 or float(rating_value) > 5:
            return JsonResponse({"error": "Invalid rating value."}, status=400)

        Rating.objects.create(
            item=item,
            user=request.user,
            stars=float(rating_value),
            comment=comment
        )

        return JsonResponse({"message": "Rating submitted successfully."})

    return JsonResponse({"error": "Invalid request method."}, status=400)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Item


@login_required
def get_item_ratings(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user_rating = Rating.objects.filter(item=item, user=request.user).first()  # Get the user's existing rating


    ratings = Rating.objects.filter(item=item)
    ratings_data = [
        {
            'user': rating.user.username,
            'rating': rating.stars,
            'comment': rating.comment,
        }
        for rating in ratings
    ]

    if not ratings_data:
        return JsonResponse({"message": "No ratings found for this item."}, status=404)

    return JsonResponse({
        "ratings": ratings_data,
        "user_rating": {
            'rating': user_rating.stars if user_rating else None,
            'comment': user_rating.comment if user_rating else ''
        }
    }, status=200)


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Rating


def RateEdit(request, pk):
    rating = get_object_or_404(Rating, item_id=pk, user=request.user)

    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')

        rating.rating = rating_value
        rating.comment = comment
        rating.save()

        return JsonResponse({"message": "Rating updated successfully"})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def delete_rating(request, rating_id, item_id):
    rating = get_object_or_404(Rating, id=rating_id, item_id=item_id)

    if request.user == rating.user or request.user.is_superuser:
        rating.delete()
        messages.success(request, 'Rating deleted successfully.')
    else:
        messages.error(request, 'You do not have permission to delete this rating.')

    return redirect('item:detail', pk=item_id)
