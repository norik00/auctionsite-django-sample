from .models import User, Category
from tzlocal import get_localzone

def constant_text(request):
    queryset = Category.objects.filter(id__range=(1,4))
    return {
        "tz": get_localzone(),
        "categories": queryset
    }