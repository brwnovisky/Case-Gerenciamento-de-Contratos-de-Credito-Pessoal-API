from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Contract, Installment
from datetime import date
import re


class InstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = [
            'installment_number',
            'amount',
            'due_date'
        ]

    def validate_installment_number(self, value):
        if value < 1:
            raise ValidationError("Número da parcela deve ser maior que zero.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Valor da parcela deve ser maior que zero.")
        return value

    def validate_due_date(self, value):
        if value < date.today():
            raise ValidationError("Data de vencimento não pode ser no passado.")
        return value


class ContractSerializer(serializers.ModelSerializer):
    installments = InstallmentSerializer(many = True)

    class Meta:
        model = Contract
        fields = [
            'id',
            'issue_date',
            'borrower_birth_date',
            'disbursed_amount',
            'document_number',
            'country',
            'state',
            'city',
            'phone_number',
            'interest_rate',
            'installments'
        ]

    def validate_document_number(self, value):
        if self.partial and 'document_number' not in self.initial_data:
            return value

        if not re.match(r'^\d{11}$', value):
            raise ValidationError("CPF deve conter exatamente 11 dígitos numéricos.")
        return value

    def validate_phone_number(self, value):
        if self.partial and 'phone_number' not in self.initial_data:
            return value

        if not re.match(r'^\d{10,11}$', value):
            raise ValidationError("Número de telefone deve conter 10 ou 11 dígitos numéricos.")
        return value

    def validate_disbursed_amount(self, value):
        if self.partial and 'disbursed_amount' not in self.initial_data:
            return value

        if value <= 0:
            raise ValidationError("Valor desembolsado deve ser maior que zero.")
        return value

    def validate_interest_rate(self, value):
        if self.partial and 'interest_rate' not in self.initial_data:
            return value

        if value <= 0 or value > 100:
            raise ValidationError("Taxa de juros deve estar entre 0 e 100.")
        return value

    def validate_borrower_birth_date(self, value):
        if self.partial and 'borrower_birth_date' not in self.initial_data:
            return value

        YEAR_FACTOR = 365.25
        MAJORITY_AGE = 18

        age = (date.today() - value).days / YEAR_FACTOR
        if age < MAJORITY_AGE:
            raise ValidationError("O tomador deve ter pelo menos 18 anos.")
        return value

    def validate(self, data):
        if self.partial and self.instance:
            instance_data = {
                field: getattr(self.instance, field)
                for field in self.fields
                if field != 'installments'
            }
            instance_data.update(data)
            data = instance_data

        if 'issue_date' in data and data['issue_date'] > date.today():
            raise ValidationError({"issue_date": "Data de emissão não pode ser no futuro."})

        if 'installments' in data:
            if not data.get('installments'):
                raise ValidationError({"installments": "É necessário informar as parcelas do contrato."})

            installment_numbers = [inst['installment_number'] for inst in data['installments']]
            if sorted(installment_numbers) != list(range(1, len(installment_numbers) + 1)):
                raise ValidationError({"installments": "Números das parcelas devem ser sequenciais começando de 1."})

            total_installments = sum(inst['amount'] for inst in data['installments'])
            if total_installments < data['disbursed_amount']:
                raise ValidationError({
                    "installments": f"Soma das parcelas({total_installments}) " +
                                    f"não pode ser menor que o valor desembolsado({data['disbursed_amount']})."
                })

        return data

    def create(self, validated_data):
        validated_data.pop('id', None)
        installments_data = validated_data.pop('installments')
        contract = Contract.objects.create(**validated_data)
        for installment_data in installments_data:
            Installment.objects.create(contract = contract, **installment_data)
        return contract

    def update(self, instance, validated_data):
        if 'installments' in validated_data:
            installments_data = validated_data.pop('installments')
            instance.installments.all().delete()
            for installment_data in installments_data:
                Installment.objects.create(contract = instance, **installment_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class ContractSummarySerializer(serializers.Serializer):
    total_receivable = serializers.DecimalField(max_digits = 12, decimal_places = 2)
    total_disbursed = serializers.DecimalField(max_digits = 12, decimal_places = 2)
    total_contracts = serializers.IntegerField()
    average_rate = serializers.DecimalField(max_digits = 5, decimal_places = 2)
