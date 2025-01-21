from datetime import datetime
from django.core.exceptions import BadRequest
from django.db.models import Sum, Avg, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from .models import Contract, Installment
from .serializers import ContractSerializer, ContractSummarySerializer


class ContractViewSet(viewsets.GenericViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    def _parse_date_filter(self, date_string):
        try:
            date = datetime.strptime(date_string, '%Y-%m-%d')
            return Q(issue_date=date)
        except ValueError:
            pass

        try:
            date = datetime.strptime(date_string, '%m/%Y')
            return Q(
                issue_date__year=date.year,
                issue_date__month=date.month
            )
        except ValueError:
            pass

        try:
            year = int(date_string)
            return Q(issue_date__year=year)
        except ValueError:
            pass

        return None

    def _apply_filters(self, request):
        filters = Q()
        filters_count = 0

        if id_param := request.query_params.get('id'):
            filters &= Q(id=id_param)
            filters_count += 1

        if document_number := request.query_params.get('document_number'):
            filters &= Q(document_number=document_number)
            filters_count += 1

        if state := request.query_params.get('state'):
            filters &= Q(state=state)
            filters_count += 1

        if issue_date := request.query_params.get('issue_date'):
            filters_count += 1
            date_filter = self._parse_date_filter(issue_date)
            if date_filter:
                filters &= date_filter

        if len(request.query_params) > filters_count:
            raise BadRequest('Parâmetro(s) inválido(s)')

        return self.get_queryset().filter(filters)

    @action(detail = False, methods = ['get', 'post', 'put'])
    def contracts(self, request):
        handlers = {
            'GET': self._handle_contracts_get,
            'POST': self._handle_contracts_post,
            'PUT': self._handle_contracts_put,
        }

        if request.method not in handlers:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        handler = handlers.get(request.method)
        return handler(request)

    def _handle_contracts_get(self, request):
        filtered_queryset = self._apply_filters(request)

        if request.query_params and not filtered_queryset.exists():
            raise NotFound('Não há contratos com o parâmetros fornecidos')

        if not filtered_queryset.exists():
            raise NotFound('Não há contratos cadastrados')

        page = self.paginate_queryset(filtered_queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _handle_contracts_post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance = serializer.save()
            return Response(
                self.get_serializer(instance).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            raise ValidationError(f"Error creating contract: {str(e)}.")

    def _handle_contracts_put(self, request):
        if 'id' not in request.data:
            raise ValidationError("O ID é requerido para atualizar o contrato.")

        try:
            instance = self.queryset.get(id = request.data['id'])
        except Contract.DoesNotExist:
            raise NotFound(f"Contrato de ID '{request.data['id']}' não encontrado.")

        serializer = self.get_serializer(
            instance,
            data = request.data,
            partial = True
        )
        serializer.is_valid(raise_exception=True)

        try:
            updated_instance = serializer.save()
            return Response(
                self.get_serializer(updated_instance).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            raise ValidationError(f"Error updating contract: {str(e)}.")


    @action(detail = False, methods = ['get'])
    def contracts_summary(self, request):

        if request.method != 'GET':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        filtered_queryset = self._apply_filters(request)

        ids = filtered_queryset.values_list('id', flat = True)

        try:
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

        except Exception as e:
            raise ValidationError(f"Error calculating contract summary: {str(e)}")
