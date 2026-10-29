"""Django admin customization with filters and inlines."""

from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html

from shop.models import (
    Article,
    ClientProfile,
    CompanyHistory,
    CompanyInfo,
    ContactPerson,
    EmployeeProfile,
    FAQEntry,
    Manufacturer,
    Order,
    OrderItem,
    PickupPoint,
    Product,
    ProductCategory,
    PromoCode,
    Review,
    Vacancy,
    Banner,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('line_total_display',)

    @admin.display(description='Line total')
    def line_total_display(self, obj):
        if obj.pk:
            return obj.line_total
        return '—'


admin.site.register(Order)
admin.site.register(Product)
admin.site.register(ProductCategory)
admin.site.register(ClientProfile)
admin.site.register(EmployeeProfile)
admin.site.register(Manufacturer)
admin.site.register(PromoCode)
admin.site.register(PickupPoint)
admin.site.register(Article)
admin.site.register(Review)

admin.site.register(CompanyInfo)
admin.site.register(CompanyHistory)
admin.site.register(FAQEntry)
admin.site.register(ContactPerson)
admin.site.register(Vacancy)
admin.site.register(Banner)
