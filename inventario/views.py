# Prueba de sincronizacion con GitHub
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from datetime import datetime, time, timedelta
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .models import (
    Producto, Categoria, Venta, DetalleVenta,
    Compra, DetalleCompra, Proveedor
)
from .forms import (
    ProductoForm, CategoriaForm, CompraForm, ProveedorForm
)

@login_required
def dashboard(request):
    productos = Producto.objects.filter(activo=True)

    contexto = {
        "total_productos": productos.count(),
        "total_categorias": Categoria.objects.count(),
        "total_unidades": sum(p.stock for p in productos),
        "stock_bajo": productos.filter(stock__lte=5).count(),
        "ultimos_productos": productos.order_by("-fecha_creacion")[:5],
    }

    return render(request, "inventario/dashboard.html", contexto)


@login_required
def lista_productos(request):
    busqueda = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()

    productos = Producto.objects.select_related("categoria").filter(activo=True)

    # Búsqueda por código, nombre o marca
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(codigo__icontains=busqueda) |
            Q(marca__icontains=busqueda)
        )

    # Filtro por categoría
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Paginación: 10 productos por página
    from django.core.paginator import Paginator

    paginador = Paginator(productos.order_by("nombre"), 10)
    pagina = request.GET.get("page")
    productos_paginados = paginador.get_page(pagina)

    contexto = {
        "productos": productos_paginados,
        "busqueda": busqueda,
        "categorias": Categoria.objects.all(),
        "categoria_seleccionada": categoria_id,
        "total_productos": paginador.count,
    }

    return render(request, "inventario/productos.html", contexto)

@login_required
def crear_producto(request):
    if request.method == "POST":
        formulario = ProductoForm(request.POST, request.FILES)

        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto registrado correctamente.")
            return redirect("productos")
    else:
        formulario = ProductoForm()

    return render(request, "inventario/producto_form.html", {
        "formulario": formulario,
        "titulo": "Registrar producto",
    })


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        formulario = ProductoForm(
            request.POST, request.FILES, instance=producto
        )

        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("productos")
    else:
        formulario = ProductoForm(instance=producto)

    return render(request, "inventario/producto_form.html", {
        "formulario": formulario,
        "titulo": "Editar producto",
    })


@login_required
@require_POST
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect("productos")


@login_required
def lista_categorias(request):
    busqueda = request.GET.get("q", "").strip()

    categorias = Categoria.objects.all()

    if busqueda:
        categorias = categorias.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    contexto = {
        "categorias": categorias,
        "busqueda": busqueda,
        "total_categorias": categorias.count(),
    }

    return render(
        request,
        "inventario/categorias.html",
        contexto
    )


@login_required
def crear_categoria(request):
    if request.method == "POST":
        formulario = CategoriaForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            messages.success(
                request,
                "Categoría registrada correctamente."
            )
            return redirect("categorias")
    else:
        formulario = CategoriaForm()

    return render(request, "inventario/categoria_form.html", {
        "formulario": formulario,
        "titulo": "Registrar categoría",
    })


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == "POST":
        formulario = CategoriaForm(
            request.POST,
            instance=categoria
        )

        if formulario.is_valid():
            formulario.save()
            messages.success(
                request,
                "Categoría actualizada correctamente."
            )
            return redirect("categorias")
    else:
        formulario = CategoriaForm(instance=categoria)

    return render(request, "inventario/categoria_form.html", {
        "formulario": formulario,
        "titulo": "Editar categoría",
    })


@login_required
@require_POST
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if categoria.productos.exists():
        messages.error(
            request,
            "No se puede eliminar esta categoría porque tiene productos asociados."
        )
    else:
        categoria.delete()
        messages.success(
            request,
            "Categoría eliminada correctamente."
        )

    return redirect("categorias")

@login_required
def nueva_venta(request):
    productos = Producto.objects.filter(
        activo=True,
        stock__gt=0
    ).order_by("nombre")

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto")
        cantidades = request.POST.getlist("cantidad")

        cliente = request.POST.get("cliente", "").strip()
        metodo_pago = request.POST.get("metodo_pago", "EFECTIVO")

        try:
            descuento = Decimal(
                request.POST.get("descuento", "0") or "0"
            )

            if descuento < 0:
                raise ValueError("El descuento no puede ser negativo.")

            if metodo_pago not in dict(Venta.METODOS_PAGO):
                raise ValueError("Método de pago no válido.")

            if len(productos_ids) != len(cantidades):
                raise ValueError("Los productos y cantidades no coinciden.")

            items = []

            for producto_id, cantidad_texto in zip(
                productos_ids, cantidades
            ):
                if not producto_id and not cantidad_texto:
                    continue

                cantidad = int(cantidad_texto)

                if cantidad <= 0:
                    raise ValueError("Las cantidades deben ser mayores que cero.")

                items.append((int(producto_id), cantidad))

            if not items:
                raise ValueError("Agrega al menos un producto a la venta.")

            ids = {producto_id for producto_id, cantidad in items}

            with transaction.atomic():
                productos_bloqueados = Producto.objects.select_for_update().filter(
                    id__in=ids,
                    activo=True
                )

                productos_dict = {
                    producto.id: producto
                    for producto in productos_bloqueados
                }

                if len(productos_dict) != len(ids):
                    raise ValueError("Uno de los productos no está disponible.")

                cantidades_totales = {}

                for producto_id, cantidad in items:
                    cantidades_totales[producto_id] = (
                        cantidades_totales.get(producto_id, 0) + cantidad
                    )

                for producto_id, cantidad_total in cantidades_totales.items():
                    producto = productos_dict[producto_id]

                    if producto.stock < cantidad_total:
                        raise ValueError(
                            f"Stock insuficiente para {producto.nombre}. "
                            f"Disponible: {producto.stock}."
                        )

                subtotal = sum(
                    (
                        productos_dict[producto_id].precio_sugerido * cantidad
                        for producto_id, cantidad in items
                    ),
                    Decimal("0.00")
                )

                if descuento > subtotal:
                    raise ValueError(
                        "El descuento no puede superar el subtotal."
                    )

                venta = Venta.objects.create(
                    cliente=cliente or "Cliente general",
                    metodo_pago=metodo_pago,
                    subtotal=subtotal,
                    descuento=descuento,
                    total=subtotal - descuento
                )

                for producto_id, cantidad in items:
                    producto = productos_dict[producto_id]

                    precio = producto.precio_sugerido
                    subtotal_detalle = precio * cantidad

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal_detalle
                    )

                for producto_id, cantidad_total in cantidades_totales.items():
                    producto = productos_dict[producto_id]
                    producto.stock -= cantidad_total
                    producto.save(update_fields=["stock"])

            messages.success(
                request,
                f"Venta #{venta.id} registrada correctamente. "
                f"Total: ${venta.total}"
            )
            return redirect("ventas")

        except (ValueError, InvalidOperation, TypeError):
            messages.error(
                request,
                "No se pudo registrar la venta. "
                "Revisa los productos, cantidades y descuento."
            )

    return render(
        request,
        "inventario/venta_form.html",
        {
            "productos": productos,
            "metodos_pago": Venta.METODOS_PAGO,
        }
    )


@login_required
def lista_ventas(request):
    ventas = Venta.objects.prefetch_related(
        "detalles__producto"
    ).order_by("-fecha")

    contexto = {
        "ventas": ventas,
        "total_ventas": ventas.count(),
        "ingresos_totales": sum(
            (venta.total for venta in ventas),
            Decimal("0.00")
        ),
    }

    return render(
        request,
        "inventario/ventas.html",
        contexto
    )

@login_required
def nueva_compra(request):
    productos = Producto.objects.filter(
        activo=True
    ).order_by("nombre")

    compra_form = CompraForm(request.POST or None)

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto")
        cantidades = request.POST.getlist("cantidad")
        costos = request.POST.getlist("costo_unitario")

        try:
            if not compra_form.is_valid():
                raise ValueError("Revisa los datos del proveedor.")

            if not (
                len(productos_ids) == len(cantidades) == len(costos)
            ):
                raise ValueError("Los datos de los productos no coinciden.")

            items = []

            for producto_id, cantidad_texto, costo_texto in zip(
                productos_ids, cantidades, costos
            ):
                if not producto_id and not cantidad_texto and not costo_texto:
                    continue

                producto_id = int(producto_id)
                cantidad = int(cantidad_texto)
                costo = Decimal(costo_texto)

                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor que cero.")

                if costo <= 0:
                    raise ValueError("El costo debe ser mayor que cero.")

                items.append((producto_id, cantidad, costo))

            if not items:
                raise ValueError("Agrega al menos un producto a la compra.")

            ids = {producto_id for producto_id, cantidad, costo in items}

            with transaction.atomic():
                productos_bloqueados = Producto.objects.select_for_update().filter(
                    id__in=ids,
                    activo=True
                )

                productos_dict = {
                    producto.id: producto
                    for producto in productos_bloqueados
                }

                if len(productos_dict) != len(ids):
                    raise ValueError("Uno de los productos no está disponible.")

                subtotal = sum(
                    (
                        costo * cantidad
                        for producto_id, cantidad, costo in items
                    ),
                    Decimal("0.00")
                )

                compra = compra_form.save(commit=False)
                compra.subtotal = subtotal
                compra.total = subtotal
                compra.save()

                for producto_id, cantidad, costo in items:
                    producto = productos_dict[producto_id]

                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        cantidad=cantidad,
                        costo_unitario=costo,
                        subtotal=costo * cantidad
                    )

                    producto.stock += cantidad
                    producto.save(update_fields=["stock"])

            messages.success(
                request,
                f"Compra #{compra.id} registrada correctamente. "
                f"Total: ${compra.total}"
            )

            return redirect("compras")

        except (ValueError, InvalidOperation, TypeError):
            messages.error(
                request,
                "No se pudo registrar la compra. "
                "Revisa el proveedor, los productos, las cantidades y los costos."
            )

    return render(
        request,
        "inventario/compra_form.html",
        {
            "compra_form": compra_form,
            "productos": productos,
        }
    )


@login_required
def lista_compras(request):
    compras = Compra.objects.prefetch_related(
        "detalles__producto"
    ).order_by("-fecha")

    contexto = {
        "compras": compras,
        "total_compras": compras.count(),
        "gastos_totales": sum(
            (compra.total for compra in compras),
            Decimal("0.00")
        ),
    }

    return render(
        request,
        "inventario/compras.html",
        contexto
    )

@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all().order_by("nombre")

    contexto = {
        "proveedores": proveedores,
        "total_proveedores": proveedores.count(),
        "proveedores_activos": proveedores.filter(activo=True).count(),
    }

    return render(
        request,
        "inventario/proveedores.html",
        contexto
    )


@login_required
def crear_proveedor(request):
    formulario = ProveedorForm(request.POST or None)

    if request.method == "POST":
        if formulario.is_valid():
            proveedor = formulario.save()

            messages.success(
                request,
                f"Proveedor {proveedor.nombre} registrado correctamente."
            )

            return redirect("proveedores")

    return render(
        request,
        "inventario/proveedor_form.html",
        {"formulario": formulario, "titulo": "Nuevo proveedor"}
    )


@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)

    formulario = ProveedorForm(
        request.POST or None,
        instance=proveedor
    )

    if request.method == "POST":
        if formulario.is_valid():
            formulario.save()

            messages.success(
                request,
                "Proveedor actualizado correctamente."
            )

            return redirect("proveedores")

    return render(
        request,
        "inventario/proveedor_form.html",
        {
            "formulario": formulario,
            "titulo": "Editar proveedor"
        }
    )

@login_required
def estadisticas(request):
    hoy = timezone.localdate()

    fecha_inicio_texto = request.GET.get("desde", "")
    fecha_fin_texto = request.GET.get("hasta", "")

    try:
        fecha_inicio = (
            datetime.strptime(fecha_inicio_texto, "%Y-%m-%d").date()
            if fecha_inicio_texto else hoy.replace(day=1)
        )

        fecha_fin = (
            datetime.strptime(fecha_fin_texto, "%Y-%m-%d").date()
            if fecha_fin_texto else hoy
        )

        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha inicial no puede superar la fecha final.")

    except ValueError:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
        messages.error(request, "El rango de fechas no es válido.")

    ventas = Venta.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    )

    compras = Compra.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    )

    ingresos = ventas.aggregate(
        total=Sum("total")
    )["total"] or Decimal("0.00")

    gastos = compras.aggregate(
        total=Sum("total")
    )["total"] or Decimal("0.00")

    ganancia_bruta = ingresos - ventas.aggregate(
        costo=Sum(
            ExpressionWrapper(
                F("detalles__cantidad") * F("detalles__producto__costo_compra"),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )["costo"] or Decimal("0.00")

    cantidad_vendida = DetalleVenta.objects.filter(
        venta__fecha__date__gte=fecha_inicio,
        venta__fecha__date__lte=fecha_fin
    ).aggregate(
        total=Sum("cantidad")
    )["total"] or 0

    productos_mas_vendidos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=fecha_inicio,
        venta__fecha__date__lte=fecha_fin
    ).values(
        "producto__nombre"
    ).annotate(
        cantidad=Sum("cantidad")
    ).order_by("-cantidad")[:5]

    productos_stock_bajo = Producto.objects.filter(
        activo=True,
        stock__lte=5
    ).order_by("stock")[:10]

    ventas_mensuales = ventas.annotate(
        mes=TruncMonth("fecha")
    ).values("mes").annotate(
        total=Sum("total")
    ).order_by("mes")

    compras_mensuales = compras.annotate(
        mes=TruncMonth("fecha")
    ).values("mes").annotate(
        total=Sum("total")
    ).order_by("mes")

    contexto = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ingresos": ingresos,
        "gastos": gastos,
        "ganancia_bruta": ganancia_bruta,
        "cantidad_vendida": cantidad_vendida,
        "productos_mas_vendidos": productos_mas_vendidos,
        "productos_stock_bajo": productos_stock_bajo,
        "ventas_mensuales": ventas_mensuales,
        "compras_mensuales": compras_mensuales,
    }

    return render(
        request,
        "inventario/estadisticas.html",
        contexto
    )
