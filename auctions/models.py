import datetime

from dateutil.tz import gettz
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max
from pytz import timezone, utc
from tzlocal import get_localzone


class User(AbstractUser):
    watchlist = models.ManyToManyField('ListingProduct')


class Category(models.Model):
    category = models.CharField(max_length=20)
    image = models.ImageField(null=True)

    def __str__(self):
        return f"{self.category}"

    
class BidIncrement(models.Model):
    min_price = models.IntegerField()
    max_price = models.IntegerField()
    increment = models.IntegerField()

    def __str__(self):
        return f"Bid increment {self.increment}"


class ListingProduct(models.Model):
    product_name = models.CharField(max_length=50)
    detailed_description = models.TextField(max_length=1500)
    start_price = models.IntegerField()
    bid_period = models.DateTimeField()
    current_price = models.IntegerField()
    image = models.ImageField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    listed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    registerd_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.short_product_name}({self.category}) by {self.listed_by}"

    @property
    def short_product_name(self):
        "Returns the first 20 character of product_name"
        return f"{self.product_name[:20]}..."


    @property
    def short_discription(self):
        "Returns the first 25 character of product_name"
        return f"{self.detailed_description[:100]}..."


    def save(self, *args, **kwargs):
        # Convert to UTC time
        self.bid_period = self.bid_period.replace(tzinfo=None).astimezone(utc)
        super().save(*args, **kwargs)


class BidRecord(models.Model):
    max_price = models.IntegerField()
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(ListingProduct, on_delete=models.CASCADE)
    registerd_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} price: {self.max_price}"


    @property
    def short_product(self):
        "Return the first 10 character of product"
        return f"{self.product.short_product_name}..."


class Comment(models.Model):
    comment = models.TextField(max_length=70)
    product = models.ForeignKey(ListingProduct, on_delete=models.CASCADE)
    contributor = models.ForeignKey(User, on_delete=models.CASCADE)
    registerd_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.comment[:10]} registerd by {self.contributor}"


    @property
    def short_comment(self):
        "Returns the first 10 character of comment"
        return f"{self.comment[:10]}..."
