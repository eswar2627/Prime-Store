from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path("export/orders/csv/", views.export_orders_csv, name="export_orders_csv"),
    path("export/orderitems/csv/", views.export_orderitems_csv, name="export_orderitems_csv"),
    path("export/orders/excel/", views.export_orders_excel, name="export_orders_excel"),
    path("export/orderitems/excel/", views.export_orderitems_excel, name="export_orderitems_excel"),
]