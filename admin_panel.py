from sqladmin import ModelView
import models

class UserAdmin(ModelView, model=models.User):
    column_list = [models.User.id, models.User.username, models.User.email, models.User.is_admin, models.User.created_at]
    column_searchable_list = [models.User.username, models.User.email]
    column_sortable_list = [models.User.id, models.User.created_at]
    icon = "fa-solid fa-users"

class CategoryAdmin(ModelView, model=models.Category):
    column_list = [models.Category.id, models.Category.name, models.Category.slug]
    column_searchable_list = [models.Category.name]
    icon = "fa-solid fa-tags"

class ProductAdmin(ModelView, model=models.Product):
    column_list = [models.Product.id, models.Product.name, models.Product.price, models.Product.stock, models.Product.is_available, models.Product.created_at]
    column_searchable_list = [models.Product.name, models.Product.description]
    column_sortable_list = [models.Product.price, models.Product.stock, models.Product.created_at]
    icon = "fa-solid fa-box"

class OrderAdmin(ModelView, model=models.Order):
    column_list = [models.Order.id, models.Order.full_name, models.Order.email, models.Order.total_price, models.Order.status, models.Order.created_at]
    column_searchable_list = [models.Order.full_name, models.Order.email, models.Order.city]
    column_sortable_list = [models.Order.id, models.Order.total_price, models.Order.created_at]
    icon = "fa-solid fa-cart-shopping"

class OrderItemAdmin(ModelView, model=models.OrderItem):
    column_list = [models.OrderItem.id, models.OrderItem.order_id, models.OrderItem.product_name, models.OrderItem.price, models.OrderItem.quantity]
    icon = "fa-solid fa-list-check"
