from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

try:
    from django.conf import settings
    User = settings.AUTH_USER_MODEL
except (ImportError, AttributeError):
    from django.contrib.auth.models import User

try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone


# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    created_date = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    checked_out = models.BooleanField(default=False, verbose_name='是否结账')

    class Meta:
        verbose_name = '购物车'
        verbose_name_plural = verbose_name
        ordering = ('-created_date',)

    def __str__(self):
        return str(self.creation_date)

    def is_empty(self):
        return self.item_set.count() == 0

    def total_price(self):
        return sum(i.total_price for i in self.item_set.all())

    def total_quantity(self):
        return sum(i.quantity for i in self.item_set.all())



class ItemManager(models.Manager):
    def get(self, *args, **kwargs):
        if 'product' in kwargs:
            kwargs['content_type'] = ContentType.objects.get_for_model(type(kwargs['product']))
            kwargs['object_id'] = kwargs['product'].pk
            del (kwargs['product'])
        return super(ItemManager, self).get(*args, **kwargs)


class Item(models.Model):
    cart = models.ForeignKey(Cart, verbose_name='购物车')
    quantity = models.PositiveIntegerField(verbose_name='数量')
    unit_price = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='价格')
    # product as generic relation
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    objects = ItemManager()

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ('cart',)

    def __str__(self):
        return '%s:%s' % (self.product.__class__.__name__, self.quantity)

    def total_price(self):
        return self.quantity * self.unit_price
    total_price = property(total_price)

    # product
    def get_product(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def set_product(self, product):
        self.content_type = ContentType.objects.get_for_model(type(product))
        self.object_id = product.pk

    product = property(get_product, set_product)

    def update_quantity(self, quantity):
        self.quantity = quantity
        self.save()

    def update_price(self, price):
        self.unit_price = price
        self.save()

    def update_contenttype(self, ctype_obj):
        new_content_type = ContentType.objects.get_for_model(type(ctype_obj),
                                                             for_concrete_model=False)
        # Let's search if the new contenttype had previous items on the cart
        try:
            new_items = Item.objects.get(cart=self.cart,
                                         object_id=self.object_id,
                                         content_type=new_content_type)
            self.quantity += new_items.quantity
            new_items.delete()
        except self.DoesNotExist:
            pass

        self.content_type = new_content_type
        self.save()
