# speedtest/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main
    path('', views.HomeView.as_view(), name='home'),
    path('test/run/', views.RunTestView.as_view(), name='run_test'),
    path('test/result/<int:pk>/', views.TestResultView.as_view(), name='test_result'),
    path('test/delete/<int:pk>/', views.DeleteTestView.as_view(), name='delete_test'),
    path('test/feedback/<int:pk>/', views.SubmitFeedbackView.as_view(), name='submit_feedback'),

    # History & Stats (Login kerak)
    path('history/', views.ResultsHistoryView.as_view(), name='results_history'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),

    # Other
    path('network-issues/', views.NetworkIssuesView.as_view(), name='network_issues'),
    path('about/', views.AboutView.as_view(), name='about'),
]