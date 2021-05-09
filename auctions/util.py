import datetime

from django.db.models import Max
from pytz import timezone, utc

from .models import BidIncrement, BidRecord, ListingProduct


def get_max_bid(product_id):
    max_price = BidRecord.objects.filter(product_id=product_id) \
        .aggregate(Max("max_price"))["max_price__max"]
    
    if max_price:
        return max_price
    else:
        return 0


def get_increment(current_price):
    return BidIncrement.objects.get(
        min_price__lte=current_price, max_price__gt=current_price
    ).increment


def get_highest_bidder(product_id):
    max_bid = get_max_bid(product_id)
    try:
        bidder = BidRecord.objects.get(product_id=product_id, max_price=max_bid)
        return bidder.bidder
    except BidRecord.DoesNotExist:
        return None


def automatic_bid(current_price, price, product_id):
    increment = get_increment(current_price)
    max_bid = int(get_max_bid(product_id))

    if max_bid > current_price:
        next_current_price = price + increment if price + increment < max_bid else max_bid

        ListingProduct.objects.filter(id=product_id).update(
            current_price=next_current_price)
    else:
        diff = price - current_price
        
        if diff < increment:
            ListingProduct.objects.filter(id=product_id).update(
                current_price=price)
        else:
            ListingProduct.objects.filter(id=product_id).update(
                current_price=current_price+increment)


def update_is_closed():
    products = ListingProduct.objects.filter(is_closed=False)
    
    for product in products:
        if product.bid_period <= datetime.datetime.now(datetime.timezone.utc):
            product.is_closed = True
            product.save()

    return True
