from django.shortcuts import render

def messages_page(request):
    return render(request, 'chat/messages.html')