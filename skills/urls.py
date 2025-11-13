from django.urls import path
from . import views


app_name = "skills"


urlpatterns = [
    path("", views.ClassListView.as_view(), name="class_list"),
    path("apply/", views.TeacherApplicationCreateView.as_view(), name="teacher_apply"),
    path("trades/", views.TradeOffersListView.as_view(), name="trade_offers"),
    path("trades/<int:offer_id>/accept/", views.AcceptTradeOfferView.as_view(), name="accept_trade"),
    path("trades/<int:offer_id>/decline/", views.DeclineTradeOfferView.as_view(), name="decline_trade"),
    path("trades/<int:offer_id>/cancel/", views.CancelTradeOfferView.as_view(), name="cancel_trade"),
    path("<slug:slug>/", views.ClassDetailView.as_view(), name="class_detail"),
    path("<slug:slug>/reviews/", views.ClassReviewCreateView.as_view(), name="class_review_create"),
    path("<slug:slug>/trade/propose/", views.ClassTradeProposeView.as_view(), name="class_trade_propose"),
    path("<slug:slug>/delete/", views.ClassDeleteView.as_view(), name="class_delete"),
    path("<slug:slug>/checkout/", views.ClassCheckoutView.as_view(), name="class_checkout"),
    # Scheduling URLs
    path("<slug:slug>/schedule/", views.view_class_schedule, name="view_schedule"),
    path("<slug:slug>/schedule/manage/", views.manage_class_schedule, name="manage_schedule"),
    path("<slug:slug>/schedule/create-slot/", views.create_time_slot, name="create_time_slot"),
    path("schedule/slot/<int:slot_id>/delete/", views.delete_time_slot, name="delete_time_slot"),
    path("schedule/slot/<int:slot_id>/book/", views.book_time_slot, name="book_time_slot"),
    path("schedule/booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
]


