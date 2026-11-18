from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def test_inventory_pages_require_login(self):
        protected_urls = [
            reverse("dashboard"),
            reverse("productos"),
            reverse("crear_producto"),
            reverse("editar_producto", args=[1]),
            reverse("eliminar_producto", args=[1]),
            reverse("categorias"),
            reverse("crear_categoria"),
            reverse("editar_categoria", args=[1]),
            reverse("eliminar_categoria", args=[1]),
            reverse("ventas"),
            reverse("nueva_venta"),
            reverse("compras"),
            reverse("nueva_compra"),
            reverse("proveedores"),
            reverse("crear_proveedor"),
            reverse("editar_proveedor", args=[1]),
            reverse("estadisticas"),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_login_grants_access_to_inventory(self):
        user = get_user_model().objects.create_user(
            username="inventory-user",
            password="test-password-123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inventory-user")

    def test_login_page_is_public(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
