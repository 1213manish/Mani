from django.urls import path
from .views import (
    GroupListCreateView,
    GroupDetailView,
    GroupMemberListView,
    add_member_view,
    leave_group_view,
    remove_member_view,
)

urlpatterns = [
    path("", GroupListCreateView.as_view(), name="group-list-create"),
    path("<uuid:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("<uuid:pk>/members/", GroupMemberListView.as_view(), name="group-member-list"),
    path("<uuid:pk>/members/add/", add_member_view, name="group-member-add"),
    path("<uuid:pk>/members/leave/", leave_group_view, name="group-member-leave"),
    path("<uuid:pk>/members/<uuid:user_id>/remove/", remove_member_view, name="group-member-remove"),
]
