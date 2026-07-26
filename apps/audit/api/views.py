from rest_framework import generics
from rest_framework.response import Response

from ..models import AuditLog
from ..services import detect_anomaly
from .serializers import AuditLogSerializer
from apps.accounts.permissions import RoleBasedPermission


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").all()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        table = self.request.query_params.get("table")
        if table:
            qs = qs.filter(table_name=table)
        return qs[:100]


class AnomalyCheckView(generics.GenericAPIView):
    permission_classes = [RoleBasedPermission]

    def get(self, request):
        minutes = int(request.query_params.get("minutes", 5))
        threshold = int(request.query_params.get("threshold", 10))
        anomalies = detect_anomaly(minutes=minutes, threshold=threshold)
        return Response({"anomalies": len(anomalies), "items": [str(a) for a in anomalies[:20]]})
