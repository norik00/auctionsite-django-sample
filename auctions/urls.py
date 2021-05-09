from django.urls import path

from . import views

# app_name = "auctions"

urlpatterns = [
    path("", views.index, name="index"),
    path("create", views.create, name="create"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("cagtegory", views.categories, name="categories"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("mylisting", views.my_listing, name="mylisting"),
    path("comment/<int:listing_id>", views.create_comment, name="comment"),
    path("watchlist/<int:listing_id>", views.update_watchlist, name="update_watchlist"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register")
]
