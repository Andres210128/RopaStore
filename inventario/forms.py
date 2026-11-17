
from django import forms
from .models import Producto, Categoria


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "categoria",
            "marca",
            "talla",
            "color",
            "descripcion",
            "fotografia",
            "costo_compra",
            "precio_sugerido",
            "precio_minimo",
            "stock",
            "activo",
        ]

        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "fotografia": forms.ClearableFileInput(),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej. Camisetas",
                "class": "form-control",
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Describe esta categoria...",
                "class": "form-control",
            }),
        }

from django import forms

from .models import Compra, Proveedor

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ["proveedor", "observaciones"]

        widgets = {
            "proveedor": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre del proveedor"
            }),
            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Observaciones de la compra",
                "rows": 3
            }),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor

        fields = [
            "nombre",
            "contacto",
            "telefono",
            "correo",
            "direccion",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre del proveedor"
            }),
            "contacto": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Persona de contacto"
            }),
            "telefono": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Número de teléfono"
            }),
            "correo": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Correo electrónico"
            }),
            "direccion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Dirección del proveedor"
            }),
        }
