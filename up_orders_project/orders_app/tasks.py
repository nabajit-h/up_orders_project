from celery import shared_task
from django.forms.models import model_to_dict

from orders_app.models import Order, OrderItem, Item, Store, StoreItem, CustomUser


@shared_task
def generate_order(data):
    """
    This is a Celery task, which is invoked when a Customer creates an Order.
    It takes a order payload and creates an order to save it to the database.
    It creates entries for the OrderItem table as well.
    """
    try:
        bill_amount = 0
        for item in data['items']:
            bill_amount += float(item['price'])
            store_item_obj = StoreItem.objects.get(store=data['store_id'], item=item['id'])
            if store_item_obj and store_item_obj.count == 0:
                return "Item: {} is not available.".format(item['name'])
            elif store_item_obj and store_item_obj.count > 0:
                store_item_obj.count -= 1
                store_item_obj.save()
            else:
                return "StoreItem not created."
        
        customer = CustomUser.objects.get(id=data['user_id'])
        store = Store.objects.get(pk=data['store_id'])
        order = Order.objects.create(
            customer=customer,
            merchant=store.merchant,
            store=store,
            bill_amount=bill_amount
        )
        order_id = int(order.id)

        # order_items = []
        for item in data['items']:
            item_obj = Item.objects.get(id=item['id'])
            item_id = int(item_obj.id)
            OrderItem.objects.create(order_id=order_id, item_id=item_id)

        # OrderItem.objects.bulk_create(order_items)
        return "Order created: {}".format(order)
    except Exception as e:
        print(e)
        return "{}".format(e)
