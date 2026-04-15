from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Empresa
from .forms import EmpresaForm

# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def lista(request):
    return render(request, 'empresas/lista.html', {'items': Empresa.objects.all()})

@login_required
@user_passes_test(is_admin)
def crear(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Empresa creada.')
            return redirect('empresas:lista')
    else:
        form = EmpresaForm()
    return render(request, 'empresas/form.html', {'form': form, 'titulo': 'Nueva Empresa', 'es_creacion': True})


@login_required
@user_passes_test(is_admin)
def editar(request, pk):
    item = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Empresa actualizada.')
            return redirect('empresas:lista')
    else:
        form = EmpresaForm(instance=item)
    return render(request, 'empresas/form.html', {'form': form, 'titulo': 'Editar Empresa', 'es_creacion': False})


@login_required
@user_passes_test(is_admin)
def eliminar(request, pk):
    item = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, '🗑️ Empresa eliminada.')
        return redirect('empresas:lista')
    return render(request, 'empresas/confirm_delete.html', {'objeto': item, 'url_cancel': 'empresas:lista'})
