from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
import random
from .models import Quote

def get_random_quote():
    count = Quote.objects.aggregate(count=Count('id'))['count']
    if count > 0:
        random_index = random.randint(0, count - 1)
        return Quote.objects.all()[random_index]
    return None

def quote_list(request):
    quotes_list = Quote.objects.all()
    paginator = Paginator(quotes_list, 5)  # Show 5 quotes per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    random_quote = get_random_quote()
    
    context = {
        'page_obj': page_obj,
        'random_quote': random_quote,
    }
    
    return render(request, 'quotes/quote_list.html', context)

def random_quote(request):
    quote = get_random_quote()
    return render(request, 'quotes/random_quote.html', {'quote': quote})
