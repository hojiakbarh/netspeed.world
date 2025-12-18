# urls.py (app level)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('test/run/', views.run_test, name='run_test'),
    path('test/result/<int:pk>/', views.test_result, name='test_result'),
    path('test/feedback/<int:pk>/', views.submit_feedback, name='submit_feedback'),
    path('history/', views.results_history, name='results_history'),
    path('statistics/', views.statistics, name='statistics'),
    path('network-issues/', views.network_issues, name='network_issues'),
    path('about/', views.about, name='about'),
]
