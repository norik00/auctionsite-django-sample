import datetime

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from pytz import timezone, utc

from . import util
from .models import (BidIncrement, BidRecord, Category, Comment,
                     ListingProduct, User)


def update_is_closed():
    products = ListingProduct.objects.filter(is_closed=False)
    
    for product in products:
        if product.bid_period <= datetime.datetime.now(datetime.timezone.utc):
            product.is_closed = True
            product.save()

    return True


class BidForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BidForm, self).__init__(*args, **kwargs)
        self.fields["price"].widget.attrs["class"] = "input-50"

    price = forms.IntegerField(label=False)


class CreateListingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateListingForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "normal"

    categories = Category.objects.all()
    
    product_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder":"Procut name"}
        ),
        max_length=50, 
    )
    detailed_description = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder":"Description"}
        ),
        max_length=1500,
    )
    start_price = forms.FloatField(
        widget=forms.NumberInput(
            attrs={"placeholder":"Start price"}
        )
    )
    bid_period = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local","placeholder":"Bed period"}
        )
    )
    image = forms.ImageField(label="Photo")
    category = forms.ModelChoiceField(
        queryset=categories,
        empty_label='Category'
    )
    
    class Meta:
        model = ListingProduct
        fields = ["product_name", "detailed_description", "start_price", "bid_period", "image", "category"]


def index(request):
    util.update_is_closed()

    d = {
        "page_title": "New Arrivals",
        "listings": ListingProduct.objects.filter(is_closed=False).order_by("-registerd_at")
    }

    if request.method == "GET":
        keyword = request.GET.get("keyword")
        category = request.GET.get("category")

        if keyword and category:
            d["listings"] = ListingProduct.objects.filter(
                product_name__contains=keyword,
                category__category__contains=category,
                is_closed=False
            ).order_by('-registerd_at')

            d["keyword"] = keyword
            d["category"] = category
            d["page_title"] = f'"{keyword}"'
        elif keyword:
            d["listings"] = ListingProduct.objects.filter(
                product_name__contains=keyword,
                is_closed=False
            ).order_by('-registerd_at')

            d["keyword"] = keyword
            d["page_title"] = f'"{keyword}"'
        elif category:
            d["listings"] = ListingProduct.objects.filter(
                category__category__contains=category,
                is_closed=False
            ).order_by('-registerd_at')
            
            d["page_title"] = f'"{category}"'
            d["category"] = category

    return render(request, "auctions/index.html", d)


def listing(request, listing_id):
    util.update_is_closed()

    user = request.user
    listing = ListingProduct.objects.get(id=listing_id)
    bids = listing.bidrecord_set
    
    highest_user = util.get_highest_bidder(listing_id)

    d = {
        "bid_form": BidForm(),
        "bid_count": bids.count(),
        "listing": listing,
        "bid_records": listing.bidrecord_set.all(),
        "comments":listing.comment_set.all().order_by("-registerd_at"),
        "is_highest":True if highest_user == request.user else False,
        "is_watch": True if listing.user_set.filter(id=user.id) else False,
        "increment": util.get_increment(listing.current_price)
    }

    if request.method == "POST":
        if "addBid" in request.POST:
            form = BidForm(request.POST)
            
            if form.is_valid():
                price = form.cleaned_data["price"]
                q = BidRecord(max_price=price, bidder=user, product=listing)

                max_bid_price = util.get_max_bid(listing.id)

                if max_bid_price == 0:
                    if listing.current_price > price:
                        form.add_error("price", f"Price must be greater than or equal to ${listing.start_price}.")
                        d["bid_form"] = form
                        return render(request, "auctions/listing.html", d)
                elif listing.current_price == price:
                    form.add_error("price", f"Price must be greater than or equal to ${price + 1}.")
                    d["bid_form"] = form
                    return render(request, "auctions/listing.html", d)
                elif max_bid_price == price:
                    form.add_error("price", f"${price} is the same to highest bid.")
                    d["bid_form"] = form
                    return render(request, "auctions/listing.html", d)

                util.automatic_bid(listing.current_price, price, listing.id)

                # Save BidRecord
                q.save()
                return redirect(reverse("listing", args=[listing_id]))
            else:
                d["bid_form"] = form
        elif "toClosed" in request.POST:
            listing.is_closed = True
            listing.save()
            return redirect(reverse("listing", args=[listing_id]))

    return render(request, "auctions/listing.html", d)


@login_required
def my_listing(request):
    d = {
        "page_title": "Mylisting",
        "listings": ListingProduct.objects.filter(listed_by=request.user).order_by("is_closed", "bid_period")
    }
    return render(request, "auctions/mylisting.html", d)


def categories(request):
    return render(request, "auctions/all_category.html", {
        "page_title": "Categories",
        "categories": Category.objects.all().order_by('id')
    })

@login_required
def watchlist(request):
    user = User.objects.get(id=request.user.id)
    watchlists = user.watchlist.all().order_by("is_closed", "bid_period")

    d = {
        "page_title": "Watchlist",
        "watchlists": watchlists
    }

    return render(request, "auctions/watchlist.html", d)


@login_required
def create(request):
    d = {
        "page_title": "Create Listing",
        "form": CreateListingForm()
    }

    if request.method == "POST":
        form = CreateListingForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.cleaned_data
            l = ListingProduct(
                listed_by=request.user,
                current_price=data["start_price"],
                **data
            )
            l.save()

            return redirect(reverse("listing", args=[l.id]))
        else:
            d["form"] = form
    
    return render(request, "auctions/create.html", d)


@login_required
def create_comment(request, listing_id):
    listing = ListingProduct.objects.get(id=listing_id)

    if request.method == "POST":
        comment = request.POST.get("comment")
        if comment:
            q = Comment(comment=comment, product=listing, contributor=request.user)
            q.save()

    return redirect(reverse("listing", args=[listing_id]))


@login_required
def update_watchlist(request, listing_id):
    listing = ListingProduct.objects.get(id=listing_id)

    if request.method == "POST":
        if "addWatch" in request.POST:
            request.user.watchlist.add(listing)
            return redirect(reverse("listing", args=[listing_id]))
        elif "removeWatch" in request.POST:
            request.user.watchlist.remove(listing)
            return redirect(reverse("listing", args=[listing_id]))
    
    return redirect(reverse("listing", args=[listing_id]))


def login_view(request):
    d = {
        "page_title": "Sign In"
    }

    if request.method == "POST":
        url = request.GET.get("next")
        print(url)
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return redirect(reverse("index"))
        else:
            d["message"] = "Invalid username and/or password."
            return render(request, "auctions/login.html", d)
    else:
        return render(request, "auctions/login.html", d)


def logout_view(request):
    logout(request)

    return redirect(reverse("index"))


def register(request):
    d = {
        "page_title": "Sign Up"
    }

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            d["message"] = "Passwords must match."

            return render(request, "auctions/register.html", d)

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            d["message"] = "Username already taken."

            return render(request, "auctions/register.html", d)
        login(request, user)

        return redirect(reverse("index"))
    else:
        return render(request, "auctions/register.html", d)
