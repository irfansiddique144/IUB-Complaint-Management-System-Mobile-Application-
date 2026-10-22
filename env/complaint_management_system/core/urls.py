from .views import ComplaintCategoryDetailView, ComplaintCategoryView, ComplaintView, DepartmentDetailView, DepartmentView,ComplaintDetailView, ComplaintResponseView, ComplaintResponseDetailView, ComplaintStatusHistoryView, ComplaintStatusHistoryDetailView, UserView, UserDetailView
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Category endpoints
    path('categories/', ComplaintCategoryView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', ComplaintCategoryDetailView.as_view(), name='category-detail'),

    # Department endpoints
    path('departments/', DepartmentView.as_view(), name='department-list-create'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),

    # Complaint endpoints
    path('complaints/', ComplaintView.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetailView.as_view(), name='complaint-detail'),
    
     # User endpoints
    path('users/', UserView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    path('status-histories/<int:pk>/', ComplaintStatusHistoryDetailView.as_view(), name='history-detail'),
    
    
    # This replaces your LoginView. Send a POST request with username and password.
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Use this to get a new access token when the old one expires
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]