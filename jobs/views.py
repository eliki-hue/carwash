from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from django.db import transaction
from .models import Job
from .serializers import JobSerializer


class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related('service', 'assigned_staff')
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get('status')

        qs = super().get_queryset()

        if user.role == "staff":
            qs = qs.filter(assigned_staff=user)

        if status:
            qs = qs.filter(status=status)

        return qs.only(
            'id',
            'plate_number',
            'status',
            'created_at',
            'service__name',
            'assigned_staff__id'
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        with transaction.atomic():
            job = self.get_object()

            if request.user.role not in ['staff', 'manager']:
                return Response({"error": "Not allowed"}, status=403)

            if job.status != 'pending':
                return Response({"error": "Job already started"}, status=400)

            job.status = 'in_progress'
            job.start_time = now()
            job.save()

        return Response({"message": "Job started"})

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        with transaction.atomic():
            job = self.get_object()

            if request.user.role not in ['staff', 'manager']:
                return Response({"error": "Not allowed"}, status=403)

            if job.status != 'in_progress':
                return Response({"error": "Job not in progress"}, status=400)

            job.status = 'completed'
            job.end_time = now()
            job.save()

        return Response({"message": "Job completed"})