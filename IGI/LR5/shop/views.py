import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.db import transaction
from django.utils.dateparse import parse_date


from django.views.decorators.http import require_POST
from shop.decorators import client_required, employee_required
from shop.forms import (
    CheckoutForm,
    CustomerRegistrationForm,
    OrderCRUDForm,
    ProductCRUDForm,
    ProductFilterForm,
    ReviewForm,
    ArticleCRUDForm, 
    CategoryCRUDForm, 
    CompanyInfoCRUDForm, 
    ContactPersonCRUDForm,
    FAQEntryCRUDForm, 
    PromoCodeCRUDForm, 
    ReviewCRUDForm, 
    VacancyCRUDForm,
    PickupPointCRUDForm,
)
from shop.models import (
    Article,
    ClientProfile,
    CompanyHistory,
    CompanyInfo,
    ContactPerson,
    EmployeeProfile,
    FAQEntry,
    Order,
    OrderItem,
    PickupPoint,
    Product,
    ProductCategory,
    PromoCode,
    Review,
    Vacancy,
    Banner,
    Manufacturer,
)
from shop.cart import Cart, cart_total, clean_quantity, quantity_hint
from shop.services import fetch_public_holiday
from shop.utils import (
    build_category_chart_base64,
    format_date_dd_mm_yyyy,
    format_datetime_dd_mm_yyyy,
    sales_statistics,
)

logger = logging.getLogger('shop')


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class ShopLoginView(LoginView):
    template_name = 'shop/login.html'


class ShopLogoutView(LogoutView):
    next_page = 'home'

def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info('New customer registered: %s', user.username)
            messages.success(request, 'Registration successful.')
            return redirect('home')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})

def home(request):
    return render(request, 'shop/home.html', {
        'company': CompanyInfo.objects.first(),
        'banners': Banner.objects.filter(is_active=True),
        'latest_article': Article.objects.filter(is_published=True).first(),
        'partners': Manufacturer.objects.all(),
    })

def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category', 'manufacturer'), pk=pk)
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'can_buy': hasattr(request.user, 'client_profile') and product.is_available,
    })

def about(request):
    info = CompanyInfo.objects.first()
    history = CompanyHistory.objects.all()
    return render(request, 'shop/about.html', {'info': info, 'history': history})

def news_list(request):
    articles = Article.objects.filter(is_published=True)
    return render(request, 'shop/news.html', {'articles': articles})

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, is_published=True)
    return render(request, 'shop/article_detail.html', {'article': article})

def faq_list(request):
    entries = FAQEntry.objects.all()
    return render(
        request,
        'shop/faq.html',
        {
            'entries': entries,
            'dates_local': {e.pk: format_datetime_dd_mm_yyyy(e.created_at) for e in entries},
        },
    )


def contacts(request):
    people = ContactPerson.objects.all()
    return render(request, 'shop/contacts.html', {'people': people})


def privacy(request):
    return render(request, 'shop/privacy.html')


def vacancies(request):
    items = Vacancy.objects.filter(is_open=True)
    return render(request, 'shop/vacancies.html', {'vacancies': items})


def reviews_list(request):
    reviews = Review.objects.all()[:10]
    return render(request, 'shop/reviews.html', {'reviews': reviews})


@login_required
def review_create(request):
    profile = getattr(request.user, 'client_profile', None)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.author_name = request.user.get_full_name() or request.user.username
            review.save()
            logger.info('Review created by %s', request.user)
            messages.success(request, 'Thank you for your review!')
            return redirect('reviews')
    else:
        form = ReviewForm()
    return render(request, 'shop/review_form.html', {'form': form})


def promos(request):
    active = PromoCode.objects.filter(is_active=True)
    archived = PromoCode.objects.filter(is_active=False)
    return render(
        request,
        'shop/promos.html',
        {'active_promos': active, 'archived_promos': archived},
    )


def category_list(request):
    categories = ProductCategory.objects.prefetch_related('products')
    return render(request, 'shop/categories.html', {'categories': categories})


def product_list(request):
    form = ProductFilterForm(request.GET or None)
    products = Product.objects.filter(is_available=True).select_related('category', 'manufacturer')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            products = products.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q)
            )
        min_p = form.cleaned_data.get('min_price')
        max_p = form.cleaned_data.get('max_price')
        if min_p is not None:
            products = products.filter(price__gte=min_p)
        if max_p is not None:
            products = products.filter(price__lte=max_p)
        category = form.cleaned_data.get('category')
        if category:
            products = products.filter(category=category)
        sort = form.cleaned_data.get('sort') or 'name'
        products = products.order_by(sort)
    else:
        products = products.order_by('name')

    return render(
        request,
        'shop/products.html',
        {'products': products, 'filter_form': form, 'categories': ProductCategory.objects.all()},
    )


@login_required
def pickup_points(request):
    points = PickupPoint.objects.all()
    return render(request, 'shop/pickup_points.html', {'points': points})


@client_required
def purchase_history(request):
    orders = Order.objects.filter(client=request.user.client_profile).prefetch_related('items__product')
    return render(
        request,
        'shop/purchase_history.html',
        {
            'orders': orders,
            'dates': {o.pk: format_date_dd_mm_yyyy(o.sale_date) for o in orders},
        },
    )

@client_required
def cart_detail(request):
    items = Cart(request).items()
    return render(request, 'shop/cart.html', {'items': items, 'total': cart_total(items)})


@client_required
@require_POST
def cart_add(request):
    product = get_object_or_404(Product, pk=_to_int(request.POST.get('product_id')), is_available=True)
    qty = clean_quantity(product, request.POST.get('quantity'))
    if qty is None:
        messages.error(request, quantity_hint(product))
        return redirect('product_detail', pk=product.pk)
    Cart(request).add(product, qty)
    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart')


@client_required
@require_POST
def cart_change(request, pk, action):
    product = get_object_or_404(Product, pk=pk)
    Cart(request).change(product, 1 if action == 'inc' else -1)
    return redirect('cart')


@client_required
@require_POST
def cart_remove(request, pk):
    Cart(request).remove(pk)
    return redirect('cart')


@client_required
def checkout(request):
    """Payment page: turns the cart into an Order."""
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.info(request, 'Your cart is empty.')
        return redirect('cart')

    errors = []
    posted = request.POST if request.method == 'POST' else {}

    if request.method == 'POST':
        try:
            pickup_date = parse_date(posted.get('pickup_date', ''))
        except ValueError:
            pickup_date = None
        if not pickup_date or pickup_date < timezone.localdate():
            errors.append('Choose a pickup date (today or later).')

        point_id = _to_int(posted.get('pickup_point'))
        pickup = PickupPoint.objects.filter(pk=point_id).first() if point_id else None

        promo = None
        code = posted.get('promo_code', '').strip()
        if code:
            today = timezone.localdate()
            promo = (PromoCode.objects
                     .filter(code__iexact=code, is_active=True, valid_from__lte=today)
                     .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
                     .first())
            if promo is None:
                errors.append('Promo code is invalid or expired.')

        if not errors:
            factor = (Decimal(100) - promo.discount_percent) / Decimal(100) if promo else Decimal(1)
            with transaction.atomic():
                order = Order.objects.create(
                    client=request.user.client_profile,
                    pickup_point=pickup,
                    promo_code=promo,
                    pickup_date=pickup_date,
                )
                for it in items:
                    # 0.01 floor: OrderItem.save() treats a falsy price as "use product price"
                    price = max((it['product'].price * factor).quantize(Decimal('0.01')), Decimal('0.01'))
                    OrderItem.objects.create(
                        order=order, product=it['product'],
                        quantity=it['quantity'], unit_price=price,
                    )
            cart.clear()
            messages.success(request, f'Paid. Order #{order.pk}, total {order.items_total} BYN.')
            return redirect('purchase_history')

    return render(request, 'shop/checkout.html', {
        'items': items,
        'total': cart_total(items),
        'points': PickupPoint.objects.all(),
        'errors': errors,
        'posted': posted,
        'today': timezone.localdate(),
    })


@employee_required
def employee_dashboard(request):
    employee = request.user.employee_profile
    clients = employee.clients.all()
    orders = Order.objects.filter(Q(employee=employee) | Q(client__in=clients)).distinct()
    return render(
        request,
        'shop/employee_dashboard.html',
        {'employee': employee, 'clients': clients, 'orders': orders},
    )

@employee_required
def statistics_page(request):
    stats = sales_statistics()
    chart_category = build_category_chart_base64()
    return render(
        request,
        'shop/statistics.html',
        {
            'stats': stats,
            'chart_category': chart_category
        },
    )

class TitleMixin:
    title = ''
    delete_url_name = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.title
        if self.delete_url_name and getattr(self, 'object', None):
            ctx['delete_url'] = reverse(self.delete_url_name, kwargs={'pk': self.object.pk})
        return ctx

class ProductCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create product'
        return ctx


class ProductUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit product'
        ctx['product'] = self.object
        return ctx


class ProductDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('product_list')


class OrderCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Order
    form_class = OrderCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('statistics')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create order'
        return ctx


class OrderUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Order
    form_class = OrderCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('statistics')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Update order'
        return ctx

class OrderDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Order
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('statistics')

# --- News ---
class ArticleCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = Article
    form_class = ArticleCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('news')
    title = 'Add article'


class ArticleUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = Article
    form_class = ArticleCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('news')
    title = 'Edit article'
    delete_url_name = 'article_delete'


class ArticleDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Article
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('news')


# --- FAQ ---
class FAQCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = FAQEntry
    form_class = FAQEntryCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('faq')
    title = 'Add FAQ entry'


class FAQUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = FAQEntry
    form_class = FAQEntryCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('faq')
    title = 'Edit FAQ entry'
    delete_url_name = 'faq_delete'


class FAQDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = FAQEntry
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('faq')


# --- Contacts ---
class ContactCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = ContactPerson
    form_class = ContactPersonCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('contacts')
    title = 'Add contact'


class ContactUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = ContactPerson
    form_class = ContactPersonCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('contacts')
    title = 'Edit contact'
    delete_url_name = 'contact_delete'


class ContactDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = ContactPerson
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('contacts')


# --- Vacancies ---
class VacancyCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = Vacancy
    form_class = VacancyCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('vacancies')
    title = 'Add vacancy'


class VacancyUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = Vacancy
    form_class = VacancyCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('vacancies')
    title = 'Edit vacancy'
    delete_url_name = 'vacancy_delete'


class VacancyDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Vacancy
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('vacancies')


# --- Reviews (clients add them via review_create) ---
class ReviewUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = Review
    form_class = ReviewCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('reviews')
    title = 'Edit review'
    delete_url_name = 'review_delete'


class ReviewDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Review
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('reviews')


# --- Promo codes ---
class PromoCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = PromoCode
    form_class = PromoCodeCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('promos')
    title = 'Add promo code'


class PromoUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = PromoCode
    form_class = PromoCodeCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('promos')
    title = 'Edit promo code'
    delete_url_name = 'promo_delete'


class PromoDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = PromoCode
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('promos')


# --- Categories ---
class CategoryCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = ProductCategory
    form_class = CategoryCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('categories')
    title = 'Add category'


class CategoryUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = ProductCategory
    form_class = CategoryCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('categories')
    title = 'Edit category'
    delete_url_name = 'category_delete'


class CategoryDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('categories')

    def form_valid(self, form):
        # Product.category uses PROTECT: deleting a non-empty category would give a 500
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, 'Cannot delete: this category still has products.')
            return redirect(self.success_url)


# --- About company ---
class CompanyInfoCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = CompanyInfo
    form_class = CompanyInfoCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('about')
    title = 'Add company info'


class CompanyInfoUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = CompanyInfo
    form_class = CompanyInfoCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('about')
    title = 'Edit company info'

class PickupPointCreateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, CreateView):
    model = PickupPoint
    form_class = PickupPointCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('pickup_points')
    title = 'Add pickup point'


class PickupPointUpdateView(LoginRequiredMixin, StaffRequiredMixin, TitleMixin, UpdateView):
    model = PickupPoint
    form_class = PickupPointCRUDForm
    template_name = 'shop/crud_form.html'
    success_url = reverse_lazy('pickup_points')
    title = 'Edit pickup point'
    delete_url_name = 'pickup_delete'


class PickupPointDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = PickupPoint
    template_name = 'shop/confirm_delete.html'
    success_url = reverse_lazy('pickup_points')
