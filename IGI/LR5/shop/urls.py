"""Shop URL patterns (includes regex routes)."""

from django.urls import path, re_path

from shop import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news'),
    path('news/<int:pk>/', views.article_detail, name='article_detail'),
    path('faq/', views.faq_list, name='faq'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy/', views.privacy, name='privacy'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('reviews/add/', views.review_create, name='review_add'),
    path('promos/', views.promos, name='promos'),
    path('categories/', views.category_list, name='categories'),
    path('products/', views.product_list, name='product_list'),
    path('statistics/', views.statistics_page, name='statistics'),
    path('login/', views.ShopLoginView.as_view(), name='login'),
    path('logout/', views.ShopLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('pickup/', views.pickup_points, name='pickup_points'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('checkout/', views.checkout, name='checkout'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    re_path(r'^products/(?P<pk>\d+)/edit/$', views.ProductUpdateView.as_view(), name='product_edit'),
    re_path(r'^products/(?P<pk>\d+)/delete/$', views.ProductDeleteView.as_view(), name='product_delete'),
    re_path(r'^products/new/$', views.ProductCreateView.as_view(), name='product_create'),
    
    re_path(r'^orders/(?P<pk>\d+)/edit/$', views.OrderUpdateView.as_view(), name='order_edit'),
    re_path(r'^orders/(?P<pk>\d+)/delete/$', views.OrderDeleteView.as_view(), name='order_delete'),
    re_path(r'^orders/new/$', views.OrderCreateView.as_view(), name='order_create'),
    re_path(r'^catalog/category-(?P<slug>[\w-]+)/$', views.category_list, name='category_by_slug'),
    
    re_path(r'^news/new/$', views.ArticleCreateView.as_view(), name='article_create'),
    re_path(r'^news/(?P<pk>\d+)/edit/$', views.ArticleUpdateView.as_view(), name='article_edit'),
    re_path(r'^news/(?P<pk>\d+)/delete/$', views.ArticleDeleteView.as_view(), name='article_delete'),

    re_path(r'^faq/new/$', views.FAQCreateView.as_view(), name='faq_create'),
    re_path(r'^faq/(?P<pk>\d+)/edit/$', views.FAQUpdateView.as_view(), name='faq_edit'),
    re_path(r'^faq/(?P<pk>\d+)/delete/$', views.FAQDeleteView.as_view(), name='faq_delete'),

    re_path(r'^contacts/new/$', views.ContactCreateView.as_view(), name='contact_create'),
    re_path(r'^contacts/(?P<pk>\d+)/edit/$', views.ContactUpdateView.as_view(), name='contact_edit'),
    re_path(r'^contacts/(?P<pk>\d+)/delete/$', views.ContactDeleteView.as_view(), name='contact_delete'),

    re_path(r'^vacancies/new/$', views.VacancyCreateView.as_view(), name='vacancy_create'),
    re_path(r'^vacancies/(?P<pk>\d+)/edit/$', views.VacancyUpdateView.as_view(), name='vacancy_edit'),
    re_path(r'^vacancies/(?P<pk>\d+)/delete/$', views.VacancyDeleteView.as_view(), name='vacancy_delete'),

    re_path(r'^reviews/(?P<pk>\d+)/edit/$', views.ReviewUpdateView.as_view(), name='review_edit'),
    re_path(r'^reviews/(?P<pk>\d+)/delete/$', views.ReviewDeleteView.as_view(), name='review_delete'),

    re_path(r'^promos/new/$', views.PromoCreateView.as_view(), name='promo_create'),
    re_path(r'^promos/(?P<pk>\d+)/edit/$', views.PromoUpdateView.as_view(), name='promo_edit'),
    re_path(r'^promos/(?P<pk>\d+)/delete/$', views.PromoDeleteView.as_view(), name='promo_delete'),

    re_path(r'^categories/new/$', views.CategoryCreateView.as_view(), name='category_create'),
    re_path(r'^categories/(?P<pk>\d+)/edit/$', views.CategoryUpdateView.as_view(), name='category_edit'),
    re_path(r'^categories/(?P<pk>\d+)/delete/$', views.CategoryDeleteView.as_view(), name='category_delete'),

    re_path(r'^about/new/$', views.CompanyInfoCreateView.as_view(), name='about_create'),
    re_path(r'^about/(?P<pk>\d+)/edit/$', views.CompanyInfoUpdateView.as_view(), name='about_edit'),
    re_path(r'^products/(?P<pk>\d+)/$', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    re_path(r'^cart/(?P<pk>\d+)/(?P<action>inc|dec)/$', views.cart_change, name='cart_change'),
    re_path(r'^cart/(?P<pk>\d+)/remove/$', views.cart_remove, name='cart_remove'),

    re_path(r'^pickup/new/$', views.PickupPointCreateView.as_view(), name='pickup_create'),
    re_path(r'^pickup/(?P<pk>\d+)/edit/$', views.PickupPointUpdateView.as_view(), name='pickup_edit'),
    re_path(r'^pickup/(?P<pk>\d+)/delete/$', views.PickupPointDeleteView.as_view(), name='pickup_delete'),
]
