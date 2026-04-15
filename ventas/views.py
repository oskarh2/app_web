from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import  Venta
from .forms import VentaForm

def lista(request):
    return render(request, 'venta/lista.html', {'items': Venta.objects.all()})

def crear(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Venta  creada.')
            return redirect('ventas:lista')
    else:
        form = VentaForm()
    return render(request, 'ventas/form.html', {'form': form, 'titulo': 'Nueva Venta', 'es_creacion': True})

def editar(request, pk):
    item = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Venta  actualizada.')
            return redirect('Ventas:lista')
    else:
        form = VentaForm(instance=item)
    return render(request, 'Ventas/form.html', {'form': form, 'titulo': 'Editar Venta', 'es_creacion': False})

def eliminar(request, pk):
    item = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, '🗑️ Venta eliminada.')
        return redirect('ventas:lista')
    return render(request, 'ventas/confirm_delete.html', {'objeto': item, 'url_cancel': 'ventas:lista'})
