
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Productos
    path("productos/", views.lista_productos, name="productos"),
    path("productos/nuevo/", views.crear_producto, name="crear_producto"),
    path("productos/editar/<int:pk>/", views.editar_producto, name="editar_producto"),
    path("productos/eliminar/<int:pk>/", views.eliminar_producto, name="eliminar_producto"),

    # Categorías
    path("categorias/", views.lista_categorias, name="categorias"),
    path("categorias/nueva/", views.crear_categoria, name="crear_categoria"),
    path("categorias/editar/<int:pk>/", views.editar_categoria, name="editar_categoria"),
    path("categorias/eliminar/<int:pk>/", views.eliminar_categoria, name="eliminar_categoria"),
    path("ventas/", views.lista_ventas, name="ventas"),
path("ventas/nueva/", views.nueva_venta, name="nueva_venta"),
path("compras/", views.lista_compras, name="compras"),
path("compras/nueva/", views.nueva_compra, name="nueva_compra"),
path("proveedores/", views.lista_proveedores, name="proveedores"),
path("proveedores/nuevo/", views.crear_proveedor, name="crear_proveedor"),
path("proveedores/editar/<int:pk>/", views.editar_proveedor, name="editar_proveedor"),
path("estadisticas/", views.estadisticas, name="estadisticas"),
]
