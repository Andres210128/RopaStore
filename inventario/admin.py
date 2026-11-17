
from django.contrib import admin
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "marca",
        "costo_compra",
        "precio_sugerido",
        "precio_minimo",
        "stock",
        "activo",
    )

    search_fields = ("codigo", "nombre", "marca")
    list_filter = ("categoria", "marca", "activo")
    list_editable = ("activo",)
    ordering = ("nombre",)
