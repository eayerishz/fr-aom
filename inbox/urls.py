from django.urls import path
from . import views

app_name = 'inbox'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('new/<int:item_pk>/', views.new_conversation, name='new'),
    path('delete/<int:contact_id>/', views.delete_contact_message, name='delete_contact_message'),
    path('detail/<int:pk>/', views.detail, name='detail'),
]
