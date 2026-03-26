from django.contrib import admin
from django.http import HttpResponse
from .models import Contact, product, Cart, CartItem, Owner, Employee, Order, OrderItem
import xlsxwriter
import io


def download_excel(modeladmin, request, queryset):
    """Export selected objects to Excel"""

    output = io.BytesIO()
    
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    
    model = queryset.model
    fields = [field for field in model._meta.fields if not field.primary_key]
    
    headers = [field.verbose_name or field.name for field in fields]
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
    
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)
    
    for row_num, obj in enumerate(queryset, start=1):
        for col_num, field in enumerate(fields):
            value = getattr(obj, field.name, '')
            
            if hasattr(field, 'choices') and field.choices:
                value = dict(field.choices).get(value, value)
            elif hasattr(field, 'related_model'):
                related_obj = getattr(obj, field.name, None)
                value = str(related_obj) if related_obj else ''
            elif isinstance(value, bool):
                value = 'Yes' if value else 'No'
            
            worksheet.write(row_num, col_num, str(value))
    
    for col_num, header in enumerate(headers):
        worksheet.set_column(col_num, col_num, len(header) + 2)
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={model.__name__}_export.xlsx'
    
    return response

download_excel.short_description = "Download in Excel file"


@admin.register(product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'price', 'is_trending', 'is_special')
    list_filter = ('is_trending', 'is_special', 'category')
    search_fields = ('product_name', 'desc')
    list_editable = ('is_trending', 'is_special')
    actions = [download_excel]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product_name', 'desc', 'category', 'subcategory', 'price', 'image')
        }),
        ('Product Status', {
            'fields': ('is_trending', 'is_special', 'active', 'disaction')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at',)
    actions = [download_excel]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'created_at', 'updated_at', 'get_item_count', 'get_total')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    actions = [download_excel]
    
    def get_item_count(self, obj):
        return obj.cartitem_set.count()
    get_item_count.short_description = 'Items'
    
    def get_total(self, obj):
        return f"₹{obj.get_total():.2f}"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'cart', 'price', 'quantity', 'get_subtotal', 'created_at')
    list_filter = ('created_at', 'cart')
    readonly_fields = ('created_at',)
    actions = [download_excel]
    
    def get_subtotal(self, obj):
        return f"₹{obj.get_subtotal():.2f}"
    get_subtotal.short_description = 'Subtotal'


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('profile_image','user', 'phone', 'address', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        
        ('User Information', {
            'fields': ('profile_image','user',)
        }),
        ('Owner Details', {
            'fields': ('phone', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [download_excel]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'position', 'phone', 'hire_date', 'created_at')
    list_filter = ('position', 'hire_date', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'employee_id', 'phone', 'position')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Employee Details', {
            'fields': ('employee_id', 'position', 'phone', 'hire_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [download_excel]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product_name', 'price', 'quantity', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'email', 'phone', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'id', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = [download_excel]
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Delivery Address', {
            'fields': ('address', 'city', 'pincode')
        }),
        ('Order Details', {
            'fields': ('total_amount', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_info(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
        return "Guest Order"
    get_user_info.short_description = 'Customer'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'get_order_user', 'product_name', 'price', 'quantity', 'subtotal')
    list_filter = ('order__created_at', 'order__status', 'order__user')
    search_fields = ('product_name', 'order__first_name', 'order__last_name', 'order__email', 'order__user__username')
    readonly_fields = ('subtotal',)
    
    def get_order_user(self, obj):
        if obj.order.user:
            return f"{obj.order.user.get_full_name() or obj.order.user.username}"
        return "Guest"
    get_order_user.short_description = 'Customer'
    
    def subtotal(self, obj):
        return f"₹{obj.subtotal:.2f}"
    subtotal.short_description = 'Subtotal'
