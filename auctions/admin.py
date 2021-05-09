from django.contrib import admin
from .models import User, Category, ListingProduct, BidRecord, Comment, BidIncrement

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "image")
    list_display_links = ("category", )


class ListingProductAdmin(admin.ModelAdmin):
    list_display = ("id", "short_product_name", "category", "listed_by", "registerd_at", "is_closed")
    list_display_links = ("short_product_name",) 


class BidRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "short_product", "max_price", "registerd_at")
    list_display_links = ("short_product", )


class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "short_comment")
    list_display_links = ("short_comment", )


class UserAdmin(admin.ModelAdmin):
    filter_horizontal = ('watchlist', )


class BidIncrementAdmin(admin.ModelAdmin):
    list_display = ("id", "min_price", "max_price", "increment")
    list_display_links = ("min_price", "max_price")


admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ListingProduct, ListingProductAdmin)
admin.site.register(BidRecord, BidRecordAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(BidIncrement, BidIncrementAdmin)
