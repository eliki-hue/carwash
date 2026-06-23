from django.shortcuts import render

# Create your views here.
# expenses/views.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsManagerOrOwner

from .models import (
    Expense,
    ExpenseCategory
)

from .serializers import (
    ExpenseSerializer,
    ExpenseCategorySerializer
)


class ExpenseCategoryViewSet(ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [
        IsAuthenticated,
        IsManagerOrOwner
    ]


class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects.select_related(
        "category",
        "created_by"
    )

    serializer_class = ExpenseSerializer

    permission_classes = [
        IsAuthenticated,
        IsManagerOrOwner
    ]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )