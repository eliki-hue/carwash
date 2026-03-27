# jobs/views.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now

from .models import Job
from .serializers import JobSerializer


class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related('service', 'assigned_staff')
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    # ✅ FILTER JOBS BY STATUS (OPTIMIZED FOR MOBILE)
    def get_queryset(self):
        status = self.request.query_params.get('status')
        qs = super().get_queryset()

        if status:
            qs = qs.filter(status=status)

        return qs.order_by('-created_at')

    # ✅ START JOB
    @action(detail=True, methods=['patch'])
    def start(self, request, pk=None):
        job = self.get_object()

        # Optional: role restriction
        if request.user.role not in ['staff', 'manager']:
            return Response({"error": "Not allowed"}, status=403)

        job.status = 'in_progress'
        job.start_time = now()
        job.save()

        return Response({"message": "Job started"})

    # ✅ COMPLETE JOB
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        job = self.get_object()

        if request.user.role not in ['staff', 'manager']:
            return Response({"error": "Not allowed"}, status=403)

        job.status = 'completed'
        job.end_time = now()
        job.save()

        return Response({"message": "Job completed"})


def get_queryset(self):
    status = self.request.query_params.get('status')

    qs = Job.objects.select_related(
        'service',
        'assigned_staff'
    )

    if status:
        qs = qs.filter(status=status)

    return qs.only(
        'id',
        'plate_number',
        'status',
        'created_at',
        'service__name'
    ).order_by('-created_at')