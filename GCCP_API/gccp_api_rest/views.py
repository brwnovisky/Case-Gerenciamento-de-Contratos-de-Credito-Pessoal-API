from datetime import datetime
from django.db.models import Sum, Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Contract, Installment
from .serializers import ContractSerializer, ContractSummarySerializer


class ContractViewSet(viewsets.GenericViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    def _apply_filters(self, request):
        queryset = self.get_queryset()

        id = request.query_params.get('id')
        if id:
            queryset = queryset.filter(id = id)

        document_number = request.query_params.get('document_number')
        if document_number:
            queryset = queryset.filter(document_number = document_number)

        state = request.query_params.get('state')
        if state:
            queryset = queryset.filter(state = state)

        issue_date = request.query_params.get('issue_date')
        if issue_date:
            try:
                date = datetime.strptime(issue_date, '%Y-%m-%d')
                queryset = queryset.filter(issue_date = date)
            except ValueError:
                try:
                    date = datetime.strptime(issue_date, '%m/%Y')
                    queryset = queryset.filter(
                        issue_date__year = date.year,
                        issue_date__month = date.month
                    )
                except ValueError:
                    try:
                        year = int(issue_date)
                        queryset = queryset.filter(issue_date__year = year)
                        self.has_filters = True
                    except ValueError:
                        pass

        if not queryset.exists():
            raise NotFound('Não há contratos com o parâmetros fornecidos')

        return queryset


    @action(detail = False, methods = ['post', 'get', 'put', 'delete'])
    def contracts(self, request):

        if request.method == 'GET':
            filtered_queryset = self._apply_filters(request)
            serializer = self.get_serializer(filtered_queryset, many = True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status = status.HTTP_200_OK)

        if request.method == 'POST':
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)

        if request.method == 'PUT':
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

        if request.method == 'DELETE':
            filtered_queryset = self._apply_filters(request)
            serializer = self.get_serializer(filtered_queryset, many = True)
            serializer.is_valid(raise_exception = True)
            serializer.delete()
            return Response(serializer.data, status = status.HTTP_200_OK)

    @action(detail = False, methods = ['get'])
    def contracts_summary(self, request):
        filtered_queryset = self._apply_filters(request)

        ids = filtered_queryset.values_list('id', flat = True)

        total_receivable = Installment.objects.filter(contract__id__in = ids).aggregate(
            total = Sum('amount'))['total'] or 0

        total_disbursed = filtered_queryset.aggregate(Sum('disbursed_amount'))['disbursed_amount__sum'] or 0

        total_contracts = filtered_queryset.count()

        average_rate = filtered_queryset.aggregate(Avg('interest_rate'))['interest_rate__avg'] or 0

        summary = {
            'total_receivable': total_receivable,
            'total_disbursed': total_disbursed,
            'total_contracts': total_contracts,
            'average_rate': average_rate
        }

        serializer = ContractSummarySerializer(summary)
        return Response(serializer.data)

