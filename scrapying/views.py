# scrapying/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import PageTracking
from .forms import PageTrackingForm
import json

# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def lista(request):
    """List all page tracking records"""
    # Get filter parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    page_filter = request.GET.get('page', '')
    
    # Base queryset
    queryset = PageTracking.objects.all()
    
    # Apply filters
    if search:
        queryset = queryset.filter(
            Q(page__icontains=search) |
            Q(tracking_id__icontains=search) |
            Q(user_id__icontains=search)
        )
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if page_filter:
        queryset = queryset.filter(page__icontains=page_filter)
    
    # Pagination
    paginator = Paginator(queryset, 20)  # 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique pages for filter dropdown
    pages = PageTracking.objects.values_list('page', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'page_filter': page_filter,
        'pages': pages,
        'status_choices': PageTracking.Status.choices,
        'titulo': 'Lista de Page Tracking',
    }
    return render(request, 'scrapying/lista.html', context)

@login_required
@user_passes_test(is_admin)
def crear(request):
    """Create a new page tracking record"""
    if request.method == 'POST':
        form = PageTrackingForm(request.POST)
        if form.is_valid():
            tracking = form.save()
            messages.success(request, f'✅ Page tracking creado: {tracking.page} - {str(tracking.tracking_id)[:8]}')
            return redirect('scrapying:lista')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = PageTrackingForm()
    
    return render(request, 'scrapying/form.html', {
        'form': form,
        'titulo': 'Nuevo Page Tracking',
        'es_creacion': True
    })

@login_required
@user_passes_test(is_admin)
def detalle(request, tracking_id):
    """View page tracking details"""
    tracking = get_object_or_404(PageTracking, pk=tracking_id)
    
    # Pretty print JSON fields
    try:
        steps_json = json.dumps(tracking.steps, indent=2, ensure_ascii=False) if tracking.steps else '{}'
    except:
        steps_json = str(tracking.steps)
    
    try:
        metadata_json = json.dumps(tracking.metadata, indent=2, ensure_ascii=False) if tracking.metadata else '{}'
    except:
        metadata_json = str(tracking.metadata)
    
    return render(request, 'scrapying/detalle.html', {
        'tracking': tracking,
        'steps_json': steps_json,
        'metadata_json': metadata_json
    })

@login_required
@user_passes_test(is_admin)
def editar(request, tracking_id):
    """Edit a page tracking record"""
    tracking = get_object_or_404(PageTracking, pk=tracking_id)
    
    if request.method == 'POST':
        form = PageTrackingForm(request.POST, instance=tracking)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Page tracking actualizado: {tracking.page}')
            return redirect('scrapying:lista')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = PageTrackingForm(instance=tracking)
    
    return render(request, 'scrapying/form.html', {
        'form': form,
        'titulo': 'Editar Page Tracking',
        'es_creacion': False,
        'tracking': tracking
    })

@login_required
@user_passes_test(is_admin)
def eliminar(request, tracking_id):
    """Delete a page tracking record"""
    tracking = get_object_or_404(PageTracking, pk=tracking_id)
    
    if request.method == 'POST':
        page_name = tracking.page
        tracking.delete()
        messages.success(request, f'🗑️ Page tracking eliminado: {page_name}')
        return redirect('scrapying:lista')
    
    return render(request, 'scrapying/confirm_delete.html', {
        'objeto': tracking,
        'url_cancel': 'scrapying:lista'
    })

@login_required
@user_passes_test(is_admin)
def actualizar_estado(request, tracking_id):
    """Quick update status without full form"""
    tracking = get_object_or_404(PageTracking, pk=tracking_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in PageTracking.Status.choices]:
            old_status = tracking.status
            tracking.status = new_status
            tracking.save()
            messages.success(request, f'✅ Estado actualizado de {tracking.get_status_display()} a {tracking.get_status_display()}')
        else:
            messages.error(request, '❌ Estado inválido')
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'new_status': new_status})
        
        return redirect('scrapying:lista')
    
    return render(request, 'scrapying/actualizar_estado.html', {
        'tracking': tracking,
        'status_choices': PageTracking.Status.choices
    })

@login_required
@user_passes_test(is_admin)
def actualizar_masivo(request):
    """Bulk update status for multiple records"""
    if request.method == 'POST':
        tracking_ids = request.POST.getlist('tracking_ids')
        new_status = request.POST.get('status')
        
        if tracking_ids and new_status:
            updated_count = PageTracking.objects.filter(
                tracking_id__in=tracking_ids
            ).update(status=new_status)
            
            messages.success(request, f'✅ {updated_count} registros actualizados a estado: {new_status}')
        else:
            messages.error(request, '❌ No se seleccionaron registros o estado inválido')
        
        return redirect('scrapying:lista')
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@user_passes_test(is_admin)
def exportar_csv(request):
    """Export page tracking data to CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="page_tracking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Get filter parameters (same as lista view)
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    page_filter = request.GET.get('page', '')
    
    queryset = PageTracking.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(page__icontains=search) |
            Q(tracking_id__icontains=search) |
            Q(user_id__icontains=search)
        )
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if page_filter:
        queryset = queryset.filter(page__icontains=page_filter)
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow([
        'Page', 'Tracking ID', 'Type', 'Kind', 'Steps', 'Status', 
        'User ID', 'Created At', 'Updated At', 'Metadata'
    ])
    
    # Write data rows
    for tracking in queryset:
        writer.writerow([
            tracking.page,
            str(tracking.tracking_id),
            tracking.type,
            tracking.kind,
            json.dumps(tracking.steps, ensure_ascii=False),
            tracking.status,
            tracking.user_id or '',
            tracking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            tracking.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            json.dumps(tracking.metadata, ensure_ascii=False),
        ])
    
    messages.success(request, '📊 Datos exportados exitosamente')
    return response

@login_required
@user_passes_test(is_admin)
def estadisticas(request):
    """Show statistics about page tracking"""
    from django.db.models import Count
    
    # Total records
    total_records = PageTracking.objects.count()
    
    # Status distribution
    status_stats = PageTracking.objects.values('status').annotate(count=Count('status'))
    
    # Page distribution (top 10)
    page_stats = PageTracking.objects.values('page').annotate(count=Count('page')).order_by('-count')[:10]
    
    # Records by day (last 7 days)
    from django.db.models.functions import TruncDate
    from datetime import timedelta
    from django.utils import timezone
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    daily_stats = PageTracking.objects.filter(
        created_at__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    context = {
        'total_records': total_records,
        'status_stats': status_stats,
        'page_stats': page_stats,
        'daily_stats': daily_stats,
        'status_choices': dict(PageTracking.Status.choices),
    }
    
    return render(request, 'scrapying/estadisticas.html', context)

@login_required
@user_passes_test(is_admin)
def api_lista(request):
    """JSON API endpoint for page tracking data"""
    page = request.GET.get('page', 1)
    limit = request.GET.get('limit', 20)
    
    queryset = PageTracking.objects.all()
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    page_filter = request.GET.get('page_name')
    if page_filter:
        queryset = queryset.filter(page__icontains=page_filter)
    
    # Paginate
    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)
    
    data = {
        'total': paginator.count,
        'page': int(page),
        'total_pages': paginator.num_pages,
        'results': [
            {
                'tracking_id': str(t.tracking_id),
                'page': t.page,
                'type': t.type,
                'kind': t.kind,
                'steps': t.steps,
                'status': t.status,
                'status_display': t.get_status_display(),
                'user_id': t.user_id,
                'created_at': t.created_at.isoformat(),
                'updated_at': t.updated_at.isoformat(),
                'metadata': t.metadata,
            }
            for t in page_obj
        ]
    }
    
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin)
def duplicar(request, tracking_id):
    """Duplicate an existing page tracking record"""
    original = get_object_or_404(PageTracking, pk=tracking_id)
    
    # Create a copy
    copy = PageTracking.objects.create(
        page=original.page,
        type=original.type,
        kind=original.kind,
        steps=original.steps,
        status='PENDING',  # Reset status to pending for the copy
        user_id=original.user_id,
        metadata=original.metadata,
    )
    
    messages.success(request, f'📋 Registro duplicado: {copy.page} (Nuevo ID: {str(copy.tracking_id)[:8]})')
    return redirect('scrapying:editar', tracking_id=copy.tracking_id)