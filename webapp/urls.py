from django.urls import path
from .views import (
    connection,
    logout,
    dashboard,
)
from .views_logs import details_logs
from .views_monitoring import(
    monitoring,
    monitoring_server,
)
from .views_queries import queries


urlpatterns = [
    path('', connection, name='connection'),
    path('dashboard/', dashboard, name="dashboard"),
    path('details_logs/', details_logs, name='details_logs'),
    path('logout/', logout, name="logout"),
    path('monitoring/', monitoring, name='monitoring'),
    path('queries/', queries, name="queries"),
    path('monitoring/<slug:name_server>', monitoring_server, name='monitoring_server'),
]
