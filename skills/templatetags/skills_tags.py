from django import template
from ..models import ClassTradeOffer

register = template.Library()

@register.simple_tag(takes_context=True)
def pending_trade_offers_count(context):
    """Get the count of pending trade offers for the current user"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 0
    return ClassTradeOffer.objects.filter(
        receiver=request.user,
        status=ClassTradeOffer.PENDING
    ).count()

