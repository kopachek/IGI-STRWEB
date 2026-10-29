"""
Domain models for the confectionery shop (variant 24).

Relationship types used:
- OneToOneField: User <-> Client, User <-> Employee
- ForeignKey: Product -> Category, Order -> Client, etc.
- ManyToManyField: Employee <-> Client, Order <-> Product (through OrderItem)
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone

from shop.validators import validate_adult_age, validate_belarus_phone

from shop.upload import UploadPath

from shop.images import make_variants


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps (stored in UTC)."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ResponsiveImagesMixin(models.Model):
    """Creates smaller copies of the image fields listed in `responsive_fields` on save."""

    responsive_fields = ()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        pending = {}
        for fname in self.responsive_fields:
            f = getattr(self, fname)
            if f and not f._committed:  # a new upload
                f.file.seek(0)
                pending[fname] = f.file.read()
                f.file.seek(0)
        super().save(*args, **kwargs)
        for fname, data in pending.items():
            make_variants(getattr(self, fname), data)

class Banner(ResponsiveImagesMixin, TimeStampedModel):
    """Advertising banner on the home page."""

    responsive_fields = ('image',)
    title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=UploadPath('banners'))
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self) -> str:
        return self.title or f'Banner #{self.pk}'

class Manufacturer(ResponsiveImagesMixin, TimeStampedModel):
    """Sweet manufacturer / supplier firm."""

    responsive_fields = ('logo',)
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to=UploadPath('manufacturers'), blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class ProductCategory(ResponsiveImagesMixin, TimeStampedModel):
    """Type of confectionery product (cakes, candies, etc.)."""

    responsive_fields = ('image',)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=UploadPath('product_categories'), blank=True, null=True)

    class Meta:
        verbose_name_plural = 'product categories'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Product(ResponsiveImagesMixin, TimeStampedModel):
    """Confectionery item with price and unit of measurement."""

    class Unit(models.TextChoices):
        PIECES = 'pcs', 'Pieces'
        KILOGRAMS = 'kg', 'Kilograms'
        LITERS = 'l', 'Liters'

    responsive_fields = ('image',)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECES)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to=UploadPath('products'), blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.get_unit_display()})'

    @property
    def is_countable(self) -> bool:
        """True for items sold by the piece (whole quantities only)."""
        return self.unit == self.Unit.PIECES

    @property
    def qty_step(self) -> Decimal:
        return Decimal('1') if self.is_countable else Decimal('0.1')

    @property
    def qty_min(self) -> Decimal:
        return self.qty_step

    @property
    def qty_step_attr(self) -> str:
        """Value for the HTML `step` attribute."""
        return '1' if self.is_countable else 'any'


class ClientProfile(TimeStampedModel):
    """Customer profile linked one-to-one with Django User."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profile')
    phone = models.CharField(max_length=22, validators=[validate_belarus_phone])
    email = models.EmailField()
    birth_date = models.DateField(validators=[validate_adult_age])
    address = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username

    @property
    def age(self) -> int:
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


class EmployeeProfile(TimeStampedModel):
    """Commercial department employee."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    phone = models.CharField(max_length=22, validators=[validate_belarus_phone])
    birth_date = models.DateField(validators=[validate_adult_age])
    position = models.CharField(max_length=150, default='Sales manager')
    clients = models.ManyToManyField(ClientProfile, blank=True, related_name='assigned_employees')

    class Meta:
        ordering = ['user__last_name']

    def __str__(self) -> str:
        return f'{self.user.get_full_name() or self.user.username} ({self.position})'


class PickupPoint(TimeStampedModel):
    """Self-pickup location for orders."""

    name = models.CharField(max_length=150)
    address = models.CharField(max_length=300)
    phone = models.CharField(max_length=22, validators=[validate_belarus_phone])
    working_hours = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class PromoCode(TimeStampedModel):
    """Promotional code (active or archived)."""

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-is_active', 'code']

    def __str__(self) -> str:
        status = 'active' if self.is_active else 'archived'
        return f'{self.code} ({status})'

    @property
    def is_archived(self) -> bool:
        return not self.is_active

class Order(TimeStampedModel):
    """Sale record: client, dates, linked products via OrderItem."""

    client = models.ForeignKey(ClientProfile, on_delete=models.PROTECT, related_name='orders')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, null=True, blank=True)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    pickup_date = models.DateField()
    notes = models.TextField(blank=True)
    products = models.ManyToManyField(Product, through='OrderItem', related_name='orders')

    class Meta:
        ordering = ['-sale_date']

    def __str__(self) -> str:
        return f'Order #{self.pk} - {self.client}'

    @property
    def items_total(self) -> Decimal:
        total = self.items.aggregate(total=Sum(F('unit_price') * F('quantity')))['total']
        if total is None:
            return Decimal('0.00')
        return round(total, 2) or Decimal('0.00')


class OrderItem(models.Model):
    """Line item in an order (M2M through table)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.DecimalField(
        max_digits=8, decimal_places=3, default=Decimal('1'),
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = [['order', 'product']]

    def __str__(self) -> str:
        return f'{self.product.name} x{self.quantity}'

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


class Article(ResponsiveImagesMixin, TimeStampedModel):
    """News / blog article."""
    
    responsive_fields = ('image',)
    title = models.CharField(max_length=250)
    summary = models.CharField(max_length=300, help_text='One sentence summary.')
    body = models.TextField()
    image = models.ImageField(upload_to=UploadPath('articles'), blank=True, null=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-published_at']

    def __str__(self) -> str:
        return self.title


class CompanyInfo(TimeStampedModel):
    """About company page content."""

    title = models.CharField(max_length=200, default='About our confectionery')
    content = models.TextField()
    logo = models.ImageField(upload_to=UploadPath('company'), blank=True, null=True)

    def __str__(self) -> str:
        return self.title


class CompanyHistory(TimeStampedModel):
    """Company milestones by year (DB table for future UI)."""

    year = models.PositiveIntegerField()
    description = models.TextField()

    class Meta:
        ordering = ['year']
        verbose_name_plural = 'company history entries'

    def __str__(self) -> str:
        return str(self.year)


class FAQEntry(TimeStampedModel):
    """Glossary / frequently asked questions."""

    question = models.CharField(max_length=300)
    answer = models.TextField()
    published_at = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['-created_at']
        verbose_name = 'FAQ entry'
        verbose_name_plural = 'FAQ entries'

    def __str__(self) -> str:
        return self.question


class ContactPerson(ResponsiveImagesMixin, TimeStampedModel):
    """Staff shown on contacts page."""

    responsive_fields = ('photo',)
    full_name = models.CharField(max_length=150)
    role_description = models.CharField(max_length=250)
    phone = models.CharField(max_length=22, validators=[validate_belarus_phone])
    email = models.EmailField()
    photo = models.ImageField(upload_to=UploadPath('contacts'), blank=True, null=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self) -> str:
        return self.full_name


class Vacancy(TimeStampedModel):
    """Job opening."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    is_open = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'vacancies'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class Review(TimeStampedModel):
    """Customer review."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    author_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()
    review_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-review_date']

    def __str__(self) -> str:
        return f'{self.author_name} ({self.rating}/5)'
