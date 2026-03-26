from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Owner(models.Model):
    """Separate table for bakery owners"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    profile_image = models.ImageField(upload_to="profiles/owners/", blank=True, null=True, help_text="Profile picture")
    phone = models.CharField(max_length=15, blank=True, null=True, help_text="Contact phone number")
    address = models.TextField(blank=True, null=True, help_text="Business address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Owner: {self.user.username} ({self.user.get_full_name() or self.user.email})"
    
    class Meta:
        verbose_name = 'Owner'
        verbose_name_plural = 'Owners'
        ordering = ['-created_at']


class Employee(models.Model):
    """Separate table for bakery employees"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    profile_image = models.ImageField(upload_to="profiles/employees/", blank=True, null=True, help_text="Profile picture")
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Employee ID number")
    phone = models.CharField(max_length=15, blank=True, null=True, help_text="Contact phone number")
    position = models.CharField(max_length=100, blank=True, null=True, help_text="Job position/title")
    hire_date = models.DateField(blank=True, null=True, help_text="Date of hire")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Employee: {self.user.username} ({self.user.get_full_name() or self.user.email})"
    
    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['-created_at']

class product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    desc = models.CharField(max_length=500)
    category = models.CharField(max_length=50, default="")
    subcategory = models.CharField(max_length=50, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="products/", default="", blank=True)
    is_trending = models.BooleanField(default=False, help_text="Mark this product as trending to show on home page")
    is_special = models.BooleanField(default=False, help_text="Mark this product as special for highlighting")
    active = models.BooleanField(default=True, help_text="Whether this product is currently active/available")
    disaction = models.TextField(blank=True, null=True, help_text="Reason or description for deactivation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    def get_average_rating(self):
        """Calculate average rating for this product"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

    def get_review_count(self):
        """Get number of approved reviews for this product"""
        return self.reviews.filter(is_approved=True).count()

    def get_total_sold(self):
        """Get total quantity of this product sold from all orders"""
        from django.db.models import Sum
        total_sold = OrderItem.objects.filter(product_name=self.product_name).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        return total_sold

    @classmethod
    def get_best_selling_products(cls, limit=8, min_sales=8):
        """Get best-selling products based on total quantity sold (minimum 8+ sales)"""
        from django.db.models import Sum
        
        product_sales = OrderItem.objects.values('product_name').annotate(
            total_sold=Sum('quantity')
        ).filter(total_sold__gte=min_sales).order_by('-total_sold')
        
        best_selling_names = [item['product_name'] for item in product_sales[:limit]]
        
        if best_selling_names:
            best_selling_products = cls.objects.filter(
                product_name__in=best_selling_names,
                active=True
            ).order_by('-created_at')  
            
            product_order = {name: i for i, name in enumerate(best_selling_names)}
            best_selling_products = sorted(
                best_selling_products, 
                key=lambda x: product_order.get(x.product_name, float('inf'))
            )
            
            return best_selling_products[:limit]
        
        return cls.objects.none()


class Order(models.Model):
    """Store customer orders"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Payment'),
        ('cod', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, help_text="User who placed order (null for guest orders)")
    first_name = models.CharField(max_length=50, help_text="Customer first name")
    last_name = models.CharField(max_length=50, help_text="Customer last name")
    email = models.EmailField(help_text="Customer email")
    phone = models.CharField(max_length=15, help_text="Customer phone number")
    address = models.TextField(help_text="Delivery address")
    city = models.CharField(max_length=50, help_text="City")
    pincode = models.CharField(max_length=10, help_text="Postal code")
    notes = models.TextField(blank=True, null=True, help_text="Order notes")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total order amount")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online', help_text="Payment method")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending', help_text="Order status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name} - ₹{self.total_amount}"
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Store individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=100, help_text="Product name")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per item")
    quantity = models.IntegerField(help_text="Quantity ordered")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, help_text="Subtotal for this item")
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity} - Order #{self.order.id}"
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'


class Customer(models.Model):
    """Separate table for bakery customers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    profile_image = models.ImageField(upload_to="profiles/customers/", blank=True, null=True, help_text="Profile picture")
    phone = models.CharField(max_length=15, blank=True, null=True, help_text="Contact phone number")
    address = models.TextField(blank=True, null=True, help_text="Home address")
    city = models.CharField(max_length=50, blank=True, null=True, help_text="City")
    pincode = models.CharField(max_length=10, blank=True, null=True, help_text="Postal code")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Customer: {self.user.username} ({self.user.get_full_name() or self.user.email})"
    
    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']


class Contact(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    feedback = models.TextField(blank=True, null=True, help_text="Optional feedback about your experience")
    rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True, help_text="Rate your experience (1-5 stars)")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.rating} stars" if self.rating else self.name


class Review(models.Model):
    """Store product reviews and ratings"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="User who wrote the review (null for anonymous)")
    name = models.CharField(max_length=100, help_text="Reviewer name")
    email = models.EmailField(help_text="Reviewer email")
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Rating (1-5 stars)")
    review_text = models.TextField(help_text="Review content")
    is_approved = models.BooleanField(default=True, help_text="Whether this review is approved and visible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['product', 'email']  # One review per product per email
    
    def __str__(self):
        return f"{self.product.product_name} - {self.rating} stars by {self.name}"


class Cart(models.Model):
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.session_key[:8]}..."
    
    def get_total(self):
        return sum(item.get_subtotal() for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} x{self.quantity} - Cart {self.cart.session_key[:8]}"
    
    def get_subtotal(self):
        return float(self.price) * self.quantity
    
    class Meta:
        unique_together = ['cart', 'product_name', 'price']
