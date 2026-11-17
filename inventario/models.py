
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos"
    )

    marca = models.CharField(max_length=100, blank=True)
    talla = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=50, blank=True)

    descripcion = models.TextField(blank=True)
    fotografia = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True
    )

    costo_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    precio_sugerido = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    precio_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Venta(models.Model):
    METODOS_PAGO = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("TARJETA", "Tarjeta"),
    ]

    fecha = models.DateTimeField(auto_now_add=True)

    cliente = models.CharField(
        max_length=150,
        blank=True,
        default="Cliente general"
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default="EFECTIVO"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.id} - ${self.total}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_venta"
    )

    cantidad = models.PositiveIntegerField()

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

class Compra(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)

    proveedor = models.CharField(max_length=150)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_compra"
    )

    cantidad = models.PositiveIntegerField()

    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
