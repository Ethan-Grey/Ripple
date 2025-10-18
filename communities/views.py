from django.shortcuts import render
from .models import Community

def communities_page(request):
    communities = Community.objects.select_related('skill').all().order_by('name')
    return render(request, 'communities/communities.html', {'communities': communities})