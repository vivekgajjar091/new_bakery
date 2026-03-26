from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.db.models import Q, Sum, Count, Avg
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .models import Contact, product as ProductModel, Cart, CartItem, Owner, Employee, Customer, Order, OrderItem, Review

def is_admin(user):
    return user.is_superuser

def employee_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'employee_profile'):
            return redirect('employee_dashboard')
        else:
            logout(request)
            messages.error(request, 'Please use the employee login page.')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, "pages/employee/login.html", {'next': next_url, 'username': username})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:

            if hasattr(user, 'employee_profile'):
                login(request, user)
                request.session['user_type'] = 'Employee'
                
                if next_url:
                    return redirect(next_url)
                return redirect('employee_dashboard')
            else:
                messages.error(request, 'Only employees can login through this page.')
                return render(request, "pages/employee/login.html", {'next': next_url, 'username': username})
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, "pages/employee/login.html", {'next': next_url, 'username': username})
    
    return render(request, "pages/employee/login.html", {'next': request.GET.get('next')})


def owner_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'owner_profile'):
            return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
        else:
            logout(request)
            messages.error(request, 'Please use the owner login page.')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, "pages/owner/login.html", {'next': next_url, 'username': username})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:

            if hasattr(user, 'owner_profile'):
                login(request, user)
                request.session['user_type'] = 'Owner'
                
                if next_url:
                    return redirect(next_url)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
            else:
                messages.error(request, 'Only owners can login through this page.')
                return render(request, "pages/owner/login.html", {'next': next_url, 'username': username})
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, "pages/owner/login.html", {'next': next_url, 'username': username})
    
    return render(request, "pages/owner/login.html", {'next': request.GET.get('next')})


@login_required
def owner_add_employee(request):

    if not hasattr(request.user, 'owner_profile'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner access required.'})
        messages.error(request, 'Access denied. Owner access required.')
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        employee_id = request.POST.get('employee_id', '').strip()
        position = request.POST.get('position', '').strip()
        phone = request.POST.get('phone', '').strip()
        hire_date = request.POST.get('hire_date')
        
        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():   
            errors['username'] = 'Username already exists. Please choose a different one.'
        
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered. Please use a different email.'
        
        if not first_name:
            errors['first_name'] = 'First name is required.'
        
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'
        
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        
        if errors:
            error_msg = ' '.join(errors.values())
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            for error in errors.values():
                messages.error(request, error)
            return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            employee = Employee.objects.create(
                user=user,
                employee_id=employee_id if employee_id else None,
                position=position if position else None,
                phone=phone if phone else None,
                hire_date=hire_date if hire_date else None
            )
            
            success_msg = f'Employee account created successfully for {username}!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
        except Exception as e:
            error_msg = f'Error creating employee account: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
    
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')


@user_passes_test(is_admin)
def admin_add_employee(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        employee_id = request.POST.get('employee_id', '').strip()
        position = request.POST.get('position', '').strip()
        phone = request.POST.get('phone', '').strip()
        hire_date = request.POST.get('hire_date')
        
        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists. Please choose a different one.'
        
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered. Please use a different email.'
        
        if not first_name:
            errors['first_name'] = 'First name is required.'
        
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long.'
        
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        
        if errors:
            error_msg = ' '.join(errors.values())
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            for error in errors.values():
                messages.error(request, error)
            return render(request, "pages/admin/add_employee.html", {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'employee_id': employee_id,
                'position': position,
                'phone': phone,
                'hire_date': hire_date
            })
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            employee = Employee.objects.create(
                user=user,
                employee_id=employee_id if employee_id else None,
                position=position if position else None,
                phone=phone if phone else None,
                hire_date=hire_date if hire_date else None
            )
            
            success_msg = f'Employee account created successfully for {username}!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('admin_dashboard')
        except Exception as e:
            error_msg = f'Error creating employee account: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return render(request, "pages/admin/add_employee.html", {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'employee_id': employee_id,
                'position': position,
                'phone': phone,
                'hire_date': hire_date
            })
    
    return render(request, "pages/admin/add_employee.html")


@user_passes_test(is_admin)
def admin_dashboard(request):
    employees = Employee.objects.all().order_by('-created_at')
    customers = Customer.objects.all().order_by('-created_at')
    products = ProductModel.objects.all().order_by('-created_at')
    
    total_products = products.count()
    active_products = products.filter(active=True).count()
    inactive_products = products.filter(active=False).count()
    trending_products = products.filter(is_trending=True).count()
    best_selling_products = len(ProductModel.get_best_selling_products(limit=10))
    
    return render(request, "pages/admin/dashboard.html", {
        'employees': employees,
        'customers': customers,
        'products': products,
        'employee_count': employees.count(),
        'customer_count': customers.count(),
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'trending_products': trending_products,
        'best_selling_products': best_selling_products
    })


@login_required
def employee_dashboard(request):

    if not hasattr(request.user, 'employee_profile'):
        messages.error(request, 'Access denied. Employee access required.')
        return redirect('home')

    orders = Order.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    preparing_orders = orders.filter(status='preparing').count()
    ready_orders = orders.filter(status='ready').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    return render(request, "pages/employee/dashboard.html", {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'status_filter': status_filter,
        'order_status_choices': Order.ORDER_STATUS_CHOICES
    })


@login_required
def update_order_status(request, order_id):

    if not hasattr(request.user, 'employee_profile'):
        messages.error(request, 'Access denied. Employee access required.')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in Order.ORDER_STATUS_CHOICES]:
            old_status = order.status
            order.status = new_status
            order.updated_at = timezone.now()
            order.save()
            
            messages.success(request, f'Order #{order.id} status updated from {old_status} to {new_status}')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('employee_dashboard')


@login_required
def owner_update_order_status(request, order_id):

    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Access denied. Owner access required.')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in Order.ORDER_STATUS_CHOICES]:
            old_status = order.status
            order.status = new_status
            order.updated_at = timezone.now()
            order.save()
            
            messages.success(request, f'Order #{order.id} status updated from {old_status} to {new_status}')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
@login_required
def owner_dashboard(request):

    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Access denied. Owner access required.')
        return redirect('home')
    
    orders = Order.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    products = ProductModel.objects.all().order_by('-created_at')
    
    employees = Employee.objects.all().order_by('-created_at')
    
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    preparing_orders = orders.filter(status='preparing').count()
    ready_orders = orders.filter(status='ready').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    total_products = products.count()
    active_products = products.filter(active=True).count()
    inactive_products = products.filter(active=False).count()
    trending_products = products.filter(is_trending=True).count()
    best_selling_products = len(ProductModel.get_best_selling_products(limit=10))
    
    return render(request, "pages/owner/dashboard.html", {
        'orders': orders,
        'products': products,
        'employees': employees,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'status_filter': status_filter,
        'order_status_choices': Order.ORDER_STATUS_CHOICES,
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'trending_products': trending_products,
        'best_selling_products': best_selling_products
    })


@login_required
def get_product(request, product_id):
    # Allow both admin and owner to get product details
    if not (hasattr(request.user, 'owner_profile') or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Access denied. Owner or Admin access required.'})
    
    try:
        product = get_object_or_404(ProductModel, product_id=product_id)
        
        product_data = {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'price': float(product.price),
            'desc': product.desc,
            'category': product.category,
            'subcategory': product.subcategory or '',
            'is_trending': product.is_trending,
            'active': product.active,
            'image_url': product.image.url if product.image else None
        }
        
        return JsonResponse({'success': True, 'product': product_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error fetching product: {str(e)}'})


@login_required
def add_product(request):
    # Allow both admin and owner to add products
    if not (hasattr(request.user, 'owner_profile') or request.user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner or Admin access required.'})
        messages.error(request, 'Access denied. Owner or Admin access required.')
        return redirect('home')

    if request.method == 'POST':
        try:
            product_name = request.POST.get('product_name', '').strip()
            price = request.POST.get('price', '').strip()
            desc = request.POST.get('desc', '').strip()
            category = request.POST.get('category', '').strip()
            subcategory = request.POST.get('subcategory', '').strip()
            is_trending = request.POST.get('is_trending') == 'on'
            active = request.POST.get('active') == 'on'
            image = request.FILES.get('image')
 
            if not product_name:
                error_msg = 'Product name is required.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            if not price:
                error_msg = 'Price is required.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            if not desc:
                error_msg = 'Description is required.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            if not category:
                error_msg = 'Category is required.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            product = ProductModel.objects.create(
                product_name=product_name,
                price=float(price),
                desc=desc,
                category=category,
                subcategory=subcategory,
                is_trending=is_trending,
                active=active,
                image=image
            )
        
            success_msg = f'Product "{product_name}" added successfully!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            if request.user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('owner_dashboard')
 
        except ValueError as e:
            error_msg = 'Invalid price value.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f'Error adding product: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
 
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
@login_required
def edit_product(request, product_id):
    # Allow both admin and owner to edit products
    if not (hasattr(request.user, 'owner_profile') or request.user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner or Admin access required.'})
        messages.error(request, 'Access denied. Owner or Admin access required.')
        return redirect('home')
 
    product = get_object_or_404(ProductModel, product_id=product_id)
 
    if request.method == 'POST':
        try:
            product_name = request.POST.get('product_name', '').strip()
            price = request.POST.get('price', '').strip()
            desc = request.POST.get('desc', '').strip()
            category = request.POST.get('category', '').strip()
            subcategory = request.POST.get('subcategory', '').strip()
            is_trending = request.POST.get('is_trending') == 'on'
            active = request.POST.get('active') == 'on'
            image = request.FILES.get('image')
 
            if not product_name or not price or not desc or not category:
                error_msg = 'All required fields must be filled.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            product.product_name = product_name
            product.price = float(price)
            product.desc = desc
            product.category = category
            product.subcategory = subcategory
            product.is_trending = is_trending
            product.active = active
 
            if image:
                product.image = image
 
            product.save()
            success_msg = f'Product "{product_name}" updated successfully!'
 
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
 
        except ValueError:
            error_msg = 'Invalid price value.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f'Error updating product: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
 
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
 
@login_required
def toggle_product_status(request, product_id):
    # Allow both admin and owner to toggle product status
    if not (hasattr(request.user, 'owner_profile') or request.user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner or Admin access required.'})
        messages.error(request, 'Access denied. Owner or Admin access required.')
        return redirect('home')
 
    if request.method == 'POST':
        try:
            product = get_object_or_404(ProductModel, product_id=product_id)
            product.active = not product.active
            product.save()
 
            status_text = 'activated' if product.active else 'deactivated'
            success_msg = f'Product "{product.product_name}" {status_text} successfully!'
 
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
 
        except Exception as e:
            error_msg = f'Error updating product status: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
 
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
 
@login_required
def delete_product(request, product_id):
    # Allow both admin and owner to delete products
    if not (hasattr(request.user, 'owner_profile') or request.user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner or Admin access required.'})
        messages.error(request, 'Access denied. Owner or Admin access required.')
        return redirect('home')
 
    if request.method == 'POST':
        try:
            product = get_object_or_404(ProductModel, product_id=product_id)
            product_name = product.product_name
            product.delete()
 
            success_msg = f'Product "{product_name}" deleted successfully!'
 
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
 
        except Exception as e:
            error_msg = f'Error deleting product: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
 
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
 
@login_required
def get_employee(request, employee_id):
    if not hasattr(request.user, 'owner_profile'):
        return JsonResponse({'success': False, 'message': 'Access denied. Owner access required.'})
 
    try:
        employee = get_object_or_404(Employee, id=employee_id)
 
        employee_data = {
            'id': employee.id,
            'user': {
                'username': employee.user.username,
                'email': employee.user.email,
                'first_name': employee.user.first_name,
                'last_name': employee.user.last_name
            },
            'employee_id': employee.employee_id,
            'position': employee.position,
            'phone': employee.phone,
            'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else None
        }
 
        return JsonResponse({'success': True, 'employee': employee_data})
 
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error fetching employee: {str(e)}'})
 
 
@login_required
def edit_employee(request, employee_id):

    if not hasattr(request.user, 'owner_profile'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner access required.'})
        messages.error(request, 'Access denied. Owner access required.')
        return redirect('home')
 
    employee = get_object_or_404(Employee, id=employee_id)
 
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            employee_id_field = request.POST.get('employee_id_field', '').strip()
            position = request.POST.get('position', '').strip()
            phone = request.POST.get('phone', '').strip()
            hire_date = request.POST.get('hire_date')
 
            errors = {}
            if not username:
                errors['username'] = 'Username is required.'
            elif User.objects.filter(username=username).exclude(id=employee.user.id).exists():
                errors['username'] = 'Username already exists. Please choose a different one.'
 
            if not email:
                errors['email'] = 'Email is required.'
            elif User.objects.filter(email=email).exclude(id=employee.user.id).exists():
                errors['email'] = 'Email already registered. Please use a different email.'
 
            if not first_name:
                errors['first_name'] = 'First name is required.'
 
            if not last_name:
                errors['last_name'] = 'Last name is required.'
 
            if password and len(password) < 8:
                errors['password'] = 'Password must be at least 8 characters long.'
 
            if password and password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match.'
 
            if errors:
                error_msg = ' '.join(errors.values())
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                for error in errors.values():
                    messages.error(request, error)
                return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
            user = employee.user
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
 
            if password:
                user.set_password(password)
 
            user.save()
 
            employee.employee_id = employee_id_field if employee_id_field else None
            employee.position = position if position else None
            employee.phone = phone if phone else None
            employee.hire_date = hire_date if hire_date else None
            employee.save()
 
            success_msg = f'Employee "{username}" updated successfully!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
 
        except Exception as e:
            error_msg = f'Error updating employee: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
 
    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')
 
 
@login_required
def delete_employee(request, employee_id):
    if not hasattr(request.user, 'owner_profile'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Owner access required.'})
        messages.error(request, 'Access denied. Owner access required.')
        return redirect('home')
 
    if request.method == 'POST':
        try:
            employee = get_object_or_404(Employee, id=employee_id)
            username = employee.user.username
 
            employee.user.delete()
 
            success_msg = f'Employee "{username}" deleted successfully!'
 
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
 
        except Exception as e:
            error_msg = f'Error deleting employee: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)

    return redirect('admin_dashboard' if request.user.is_superuser else 'owner_dashboard')

def home(request):
    trending_products = ProductModel.objects.filter(is_trending=True, active=True)
    best_selling_products = ProductModel.get_best_selling_products(limit=5)
    special_products = ProductModel.objects.filter(is_special=True, active=True)
    
    return render(request, "pages/home.html", {
        "products": trending_products,
        "best_selling_products": best_selling_products,
        "special_products": special_products
    })

def about(request):
    return render(request, "pages/about.html")

def payment(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart_items_data = []
    cart_total = 0
    customer = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'phone': '',
        'address': '',
        'city': '',
        'pincode': '',
        'notes': ''
    }
    
    if request.method == "GET":
        try:
            cart_obj = Cart.objects.get(session_key=session_key)
            cart_items = CartItem.objects.filter(cart=cart_obj)
            cart_total = cart_obj.get_total()
            
            for item in cart_items:
                cart_items_data.append({
                    'id': item.id,
                    'name': item.product_name,
                    'price': float(item.price),
                    'quantity': item.quantity,
                    'subtotal': item.get_subtotal()
                })
        except Cart.DoesNotExist:
            pass
    
    if request.method == "POST":
        product_name = request.POST.get("product_name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity", "1")
        
        order_submission = request.POST.get("first_name")  
        
        if product_name and price and not order_submission:
            try:
                quantity = int(quantity)
                price = float(price)
                
                request.session['direct_purchase'] = {
                    'name': product_name,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': price * quantity
                }
                request.session.modified = True
                cart_total = price * quantity
                
            except (ValueError, TypeError):
                quantity = 1
                price = 0.0
        
        elif order_submission:
            direct_purchase = request.session.get('direct_purchase')
            if direct_purchase:
                cart_items_data.append(direct_purchase)
                cart_total = direct_purchase['subtotal']
            
            if session_key:
                try:
                    cart_obj = Cart.objects.get(session_key=session_key)
                    cart_items = CartItem.objects.filter(cart=cart_obj)
                    cart_total = cart_obj.get_total()

                    for item in cart_items:
                        cart_items_data.append({
                            'id': item.id,
                            'name': item.product_name,
                            'price': float(item.price),
                            'quantity': item.quantity,
                            'subtotal': item.get_subtotal()
                        })
                except Cart.DoesNotExist:
                    pass
            
            if not cart_items_data and product_name and price:
                try:
                    quantity = int(quantity)
                    price = float(price)
                    
                    cart_items_data.append({
                        'name': product_name,
                        'quantity': quantity,
                        'price': price,
                        'subtotal': price * quantity
                    })
                    cart_total = price * quantity
                    
                except (ValueError, TypeError):
                    pass
            
            if not cart_items_data:
                messages.error(request, "No products found. Please add items to your cart first.")
                return render(request, "pages/payment.html", {
                    "cart_items": cart_items_data,
                    "grand_total": cart_total,
                    "customer": customer
                })
            
            customer['first_name'] = (request.POST.get('first_name') or '').strip()
            customer['last_name'] = (request.POST.get('last_name') or '').strip()
            customer['email'] = (request.POST.get('email') or '').strip()
            customer['phone'] = (request.POST.get('phone') or '').strip()
            customer['address'] = (request.POST.get('address') or '').strip()
            customer['city'] = (request.POST.get('city') or '').strip()
            customer['pincode'] = (request.POST.get('pincode') or '').strip()
            customer['notes'] = (request.POST.get('notes') or '').strip()
            payment_method = (request.POST.get('payment_method') or 'online').strip()

            required_fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'pincode']
            missing = [f for f in required_fields if not customer[f]]

            if missing:
                messages.error(request, "Please fill all required customer details.")
                return render(request, "pages/payment.html", {
                    "cart_items": cart_items_data,
                    "grand_total": cart_total,
                    "customer": customer
                })

            if session_key:
                try:
                    cart_obj = Cart.objects.get(session_key=session_key)
                    cart_obj.delete()
                except Cart.DoesNotExist:
                    pass
            
            try:
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    first_name=customer['first_name'],
                    last_name=customer['last_name'],
                    email=customer['email'],
                    phone=customer['phone'],
                    address=customer['address'],
                    city=customer['city'],
                    pincode=customer['pincode'],
                    notes=customer['notes'],
                    total_amount=cart_total,
                    payment_method=payment_method,
                    status='confirmed'
                )
                
                for item in cart_items_data:
                    item_price = item.get('price', item['subtotal'] / item['quantity'])
                    OrderItem.objects.create(
                        order=order,
                        product_name=item['name'],
                        price=item_price,  
                        quantity=item['quantity'],
                        subtotal=item['subtotal']
                    )
                
                try:
                    order_items = OrderItem.objects.filter(order=order)
                    subject = f'Order Confirmation - Bakehouse Bill #{order.id}'
                    html_message = render_to_string('pages/email_bill.html', {
                        'order': order,
                        'items': order_items
                    })
                    
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[customer['email']],
                        html_message=html_message,
                        fail_silently=False
                    )
                    messages.success(request, 'Order placed successfully! Confirmation email sent.')
                except Exception as email_error:
                    messages.warning(request, f'Order placed successfully! However, there was an issue sending the confirmation email: {str(email_error)}')
                
                return redirect('payment')
                
            except Exception as e:
                messages.error(request, f'Error processing order: {str(e)}')
                return render(request, "pages/payment.html", {
                    "cart_items": cart_items_data,
                    "grand_total": cart_total,
                    "customer": customer
                })

    if request.user.is_authenticated:
        user = request.user
        customer['first_name'] = user.first_name or ''
        customer['last_name'] = user.last_name or ''
        customer['email'] = user.email or ''
        if hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            if profile.phone:
                customer['phone'] = profile.phone
            if profile.address:
                customer['address'] = profile.address
            if profile.city:
                customer['city'] = profile.city
            if profile.pincode:
                customer['pincode'] = profile.pincode
        elif hasattr(user, 'owner_profile'):
            profile = user.owner_profile
            if profile.phone:
                customer['phone'] = profile.phone
            if profile.address:
                customer['address'] = profile.address
        elif hasattr(user, 'employee_profile'):
            profile = user.employee_profile
            if profile.phone:
                customer['phone'] = profile.phone

    return render(request, "pages/payment.html", {
        "cart_items": cart_items_data,
        "grand_total": cart_total,
        "customer": customer
    })

def Terms(request):
    return render(request, "pages/Terms.html")

def Privacy(request):
    return render(request, "pages/Privacy.html")

def verify(request):
    return render(request, "pages/verify.html")

def otp(request):
    return render(request, "pages/otp.html")


def csignup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'email': email
            })
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'username': username
            })
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'username': username, 'email': email
            })
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'username': username, 'email': email
            })
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'email': email
            })
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, "pages/csignup.html", {
                'first_name': first_name, 'last_name': last_name, 'username': username
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        Customer.objects.create(user=user)
        login(request, user)
        request.session['user_type'] = 'Customer'
        messages.success(request, 'Account created successfully. Welcome!')
        return redirect('home')

    return render(request, "pages/csignup.html")


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, "pages/login.html", {'next': next_url, 'username': username})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:

            if hasattr(user, 'customer_profile'):
                login(request, user)
                request.session['user_type'] = 'Customer'
                
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            elif hasattr(user, 'owner_profile'):
                messages.error(request, 'Owners should use the owner login page. <a href="{% url "owner_login" %}" class="alert-link">Go to owner login</a>')
                return render(request, "pages/login.html", {'next': next_url, 'username': username})
            elif hasattr(user, 'employee_profile'):
                messages.error(request, 'Employees should use the employee login page. <a href="{% url "employee_login" %}" class="alert-link">Go to employee login</a>')
                return render(request, "pages/login.html", {'next': next_url, 'username': username})
            else:
                messages.error(request, 'Only customers can login through this page. Please contact administrator for owner/employee access.')
                return render(request, "pages/login.html", {'next': next_url, 'username': username})
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, "pages/login.html", {'next': next_url, 'username': username})
    
    return render(request, "pages/login.html", {'next': request.GET.get('next')})


def user_logout(request):
    try:
        request.session.pop('user_type', None)
    except Exception:
        pass
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password_attempted = False
        password_error = False

   
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'Email already registered by another user.')
            else:
                user.email = email
        

        if 'profile_image' in request.FILES:
            profile_image = request.FILES['profile_image']

            if hasattr(user, 'owner_profile'):
                owner = user.owner_profile

                if owner.profile_image:
                    owner.profile_image.delete(save=False)
                owner.profile_image = profile_image
                owner.save()
            elif hasattr(user, 'employee_profile'):
                employee = user.employee_profile

                if employee.profile_image:
                    employee.profile_image.delete(save=False)
                employee.profile_image = profile_image
                employee.save()
            elif hasattr(user, 'customer_profile'):
                customer = user.customer_profile

                if customer.profile_image:
                    customer.profile_image.delete(save=False)
                customer.profile_image = profile_image
                customer.save()
                

        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if old_password or new_password or confirm_password:
            password_attempted = True
            if not old_password:
                messages.error(request, 'Please enter your current password.')
                password_error = True
            elif not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
                password_error = True
            elif not new_password:
                messages.error(request, 'Please enter a new password.')
                password_error = True
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
                password_error = True
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                password_error = True
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully. ')
                return redirect('profile')
        

        user.save()
        if password_attempted and password_error:
            messages.info(request, 'Other profile details were saved, but the password was not changed.')
        else:
            messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    

    session_key = request.session.session_key
    cart_history = []
    if session_key:
        try:
            cart_obj = Cart.objects.get(session_key=session_key)
            cart_items = CartItem.objects.filter(cart=cart_obj)
            cart_history = [{
                'name': item.product_name,
                'price': float(item.price),
                'quantity': item.quantity,
                'subtotal': item.get_subtotal(),
                'date': item.created_at
            } for item in cart_items]
        except Cart.DoesNotExist:
            pass
    

    profile_image = None
    if hasattr(user, 'owner_profile') and user.owner_profile.profile_image:
        profile_image = user.owner_profile.profile_image
    elif hasattr(user, 'employee_profile') and user.employee_profile.profile_image:
        profile_image = user.employee_profile.profile_image
    elif hasattr(user, 'customer_profile') and user.customer_profile.profile_image:
        profile_image = user.customer_profile.profile_image
    
    return render(request, "pages/profile.html", {
        'user': user,
        'user_type': request.session.get('user_type'),
        'cart_history': cart_history,
        'profile_image': profile_image
    })


def product(request):
    products = ProductModel.objects.all()
    trending_products = ProductModel.objects.filter(is_trending=True, active=True)
    special_products = ProductModel.objects.filter(is_special=True, active=True)
    search_query = request.GET.get('search')
    
    if search_query:

        search_query_lower = search_query.lower().strip()
        
        filtered_products = []
        for product in products:

            product_name_words = product.product_name.lower().split()
            if search_query_lower in product_name_words:
                filtered_products.append(product)
                continue
            
            if product.desc:
                desc_words = product.desc.lower().split()
                if search_query_lower in desc_words:
                    filtered_products.append(product)
                    continue
            
            if product.category.lower() == search_query_lower:
                filtered_products.append(product)
                continue
        
        products = filtered_products
    
    return render(request, "pages/product.html", {
        "products": products, 
        "trending_products": trending_products,
        "special_products": special_products,
        "search_query": search_query
    })


def view_p(request, id):
    product = get_object_or_404(ProductModel, product_id=id)

    related_products = ProductModel.objects.filter(category=product.category).exclude(product_id=id)[:4]
    return render(request, "pages/view_p.html", {'product': product, 'related_products': related_products})


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        feedback = request.POST.get('feedback', '')
        rating = request.POST.get('rating')

        if name and email and phone:
            rating_int = None
            if rating:
                try:
                    rating_int = int(rating)
                    if rating_int < 1 or rating_int > 5:
                        rating_int = None
                except (ValueError, TypeError):
                    rating_int = None
            
            Contact.objects.create(name=name,email=email,phone=phone,feedback=feedback if feedback else None, rating=rating_int)
            
            messages.success(request, 'Thank you! Your message has been sent successfully.')
            return redirect('contact')
    
    return render(request, "pages/contact.html")

def add_review(request, product_id):
    """Handle review submission for a product"""
    product_obj = get_object_or_404(ProductModel, product_id=product_id)
    
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        
        if name and email and rating and review_text:
            try:
                rating_int = int(rating)
                if rating_int < 1 or rating_int > 5:
                    messages.error(request, 'Please select a valid rating between 1 and 5.')
                    return redirect('view_p', id=product_id)
                
                existing_review = Review.objects.filter(product=product_obj, email=email).first()
                if existing_review:
                    
                    existing_review.name = name
                    existing_review.rating = rating_int
                    existing_review.review_text = review_text
                    existing_review.save()
                    messages.success(request, 'Your review has been updated successfully!')
                else:
                    Review.objects.create(
                        product=product_obj,
                        name=name,
                        email=email,
                        rating=rating_int,
                        review_text=review_text
                    )                
                return redirect('view_p', id=product_id)
                
            except ValueError:
                messages.error(request, 'Invalid rating value.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('view_p', id=product_id)

def cart(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart_obj, created = Cart.objects.get_or_create(session_key=session_key)

    if request.method == "POST":
        update_item = request.POST.get("update_item")
        update_action = request.POST.get("update_action")

        if update_item and update_action:
            try:
                item_id = int(update_item)
                cart_item = CartItem.objects.get(id=item_id, cart=cart_obj)
                
                if update_action == 'increase':
                    cart_item.quantity += 1
                    cart_item.save()

                elif update_action == 'decrease':
                    if cart_item.quantity > 1:
                        cart_item.quantity -= 1
                        cart_item.save()
                
                    return redirect("cart")
            except CartItem.DoesNotExist:
                 messages.error(request, "Item not found.")
                 return redirect("cart")
            except Exception as e:
                messages.error(request, f"Error updating quantity: {str(e)}")
                return redirect("cart")

        remove_item = request.POST.get("remove_item")
        if remove_item is not None:
            try:
                item_id = int(remove_item)
                cart_item = get_object_or_404(CartItem, id=item_id, cart=cart_obj)
                cart_item.delete()
                return redirect("cart")
            except (ValueError, TypeError):
                messages.error(request, 'Invalid item.')
                return redirect("cart")
        
        product_name = request.POST.get("product_name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")

        if product_name and price and quantity:
            try:
                quantity = int(quantity)
                price = float(price)
            except (TypeError, ValueError):
                quantity = 1
                price = 0.0

            cart_item, created = CartItem.objects.get_or_create(cart=cart_obj,product_name=product_name,price=price,defaults={'quantity': quantity})
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Product added to cart successfully!'})
            
            referer = request.META.get('HTTP_REFERER', '/')
            return redirect(referer)

    cart_items = CartItem.objects.filter(cart=cart_obj)
    cart_total = cart_obj.get_total()

    cart_items_data = []
    for item in cart_items:

        try:
            product = ProductModel.objects.get(product_name=item.product_name)
            is_special = product.is_special
        except ProductModel.DoesNotExist:
            is_special = False
        
        cart_items_data.append({
            'id': item.id,
            'name': item.product_name,
            'price': float(item.price),
            'quantity': item.quantity,
            'subtotal': item.get_subtotal(),
            'is_special': is_special
        })

    return render(
        request,
        "pages/cart.html",
        {
            "cart_items": cart_items_data,
            "cart_total": cart_total,
        },
    )
@login_required
def order_history(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    order_data = []
    for order in orders:
        items = OrderItem.objects.filter(order=order)
        order_data.append({
            'order': order,
            'items': items,
            'item_count': items.count()
        })
    
    return render(request, "pages/order_history.html", {
        'orders': order_data,
        'user': user
    })


@login_required
def download_bill(request, order_id):
    user = request.user
    order = get_object_or_404(Order, id=order_id, user=user)
    
    items = OrderItem.objects.filter(order=order)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{order.id}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=5,
        alignment=TA_LEFT,
        textColor=colors.black
    )
    
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=3,
        leading=14,
        textColor=colors.black
    )   
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=5,
        alignment=TA_LEFT,
        textColor=colors.black
    )
    
    story.append(Paragraph("Bakehouse ", title_style))
    
    story.append(Paragraph(f"<b>Bill #:</b> {order.id}", normal_style))
    story.append(Paragraph(f"<b>Date:</b> {order.created_at.strftime('%B %d, %Y ')}", normal_style))
    story.append(Spacer(1, 8))
    
    story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.black, spaceBefore=5, spaceAfter=10))
    
    story.append(Paragraph("Customer", section_heading_style))
    story.append(Paragraph(f"{order.first_name} {order.last_name}", normal_style))
    story.append(Paragraph(order.email, normal_style))
    story.append(Paragraph(order.phone, normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Delivery Address,", section_heading_style))
    story.append(Paragraph(f"{order.address}", normal_style))
    story.append(Paragraph(f"{order.city} - {order.pincode}", normal_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Order Items-", section_heading_style))
    
    item_data = [["Item", "Price ", "Qty", "Total"]]
    
    for item in items:
        item_data.append([
            item.product_name,
            str(item.price),
            str(item.quantity),
            str(item.subtotal)
        ])
    
    item_data.append(["Grand Total", "", "", f"{order.total_amount}"])
    
    items_table = Table(item_data, colWidths=[3.2*inch, 0.8*inch, 0.5*inch, 1.0*inch])
    items_table.setStyle(TableStyle([
        
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
        ('TOPPADDING', (0, 1), (-1, -2), 6),
        
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (0, -1), (-2, -1), 'LEFT'),
        ('ALIGN', (-1, -1), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Payment Method:</b> {order.get_payment_method_display() or order.payment_method}", normal_style))
    story.append(Paragraph(f"<b>Status:</b> {order.get_status_display() or order.status}", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Thank you for shopping with Bakehouse!", ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=6
    )))
    story.append(Paragraph("<small>Computer generated bill</small>", ParagraphStyle(
        'FooterSmall',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.black
    )))
    doc.build(story)
    return response


@login_required
def sales_data(request):
    """API endpoint to fetch sales data for the owner dashboard"""

    if not hasattr(request.user, 'owner_profile'):
        return JsonResponse({'success': False, 'message': 'Access denied. Owner access required.'})
    
    period = request.GET.get('period', 'week')
    
    try:
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=7)
            
        
        orders = Order.objects.filter(created_at__gte=start_date).order_by('-created_at')
        
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders.count()
        completed_orders = orders.filter(status='completed').count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        summary = {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'avg_order_value': float(avg_order_value)
        }
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'customer_name': f"{order.first_name} {order.last_name}",
                'date': order.created_at.strftime('%Y-%m-%d'),
                'amount': f"{order.total_amount:.2f}",
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_method': order.get_payment_method_display()
            })
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'orders': orders_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching sales data: {str(e)}'
        })