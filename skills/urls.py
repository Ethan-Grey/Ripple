from django.urls import path
from . import views


app_name = "skills"


urlpatterns = [
    path("", views.ClassListView.as_view(), name="class_list"),
    path("apply/", views.TeacherApplicationCreateView.as_view(), name="teacher_apply"),
    path("<slug:slug>/", views.ClassDetailView.as_view(), name="class_detail"),
    path("<slug:slug>/reviews/", views.ClassReviewCreateView.as_view(), name="class_review_create"),
    path("<slug:slug>/trade/propose/", views.ClassTradeProposeView.as_view(), name="class_trade_propose"),
    path("<slug:slug>/delete/", views.ClassDeleteView.as_view(), name="class_delete"),
    path("<slug:slug>/checkout/", views.ClassCheckoutView.as_view(), name="class_checkout"),
]


