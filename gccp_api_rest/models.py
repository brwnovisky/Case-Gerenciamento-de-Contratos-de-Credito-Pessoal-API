from django.db import models
from .helpers import ccp_uuid_generator


class Contract(models.Model):
    id = models.CharField(
        auto_created=True,
        primary_key = True,
        unique = True,
        max_length=20,
        default = ccp_uuid_generator,
        help_text = "ID autogerado do Contrato de Crédito Pessoal (CCP)"
    )
    issue_date = models.DateField(
        help_text = "Data de emissão do contrato"
    )
    borrower_birth_date = models.DateField(
        help_text = "Data de nascimento do tomador"
    )
    disbursed_amount = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        help_text = "Valor desembolsado pela instituição credora"
    )
    document_number = models.CharField(
        max_length = 11,
        help_text = "Número de documento do tomador (CPF)"
    )
    country = models.CharField(
        max_length = 20,
        help_text = "País do tomador"
    )
    state = models.CharField(
        max_length = 20,
        help_text = "Estado do tomador"
    )
    city = models.CharField(
        max_length = 20,
        help_text = "Cidade do tomador"
    )
    phone_number = models.CharField(
        max_length = 20,
        help_text = "Número de contato do tomador"
    )
    interest_rate = models.DecimalField(
        max_digits = 5,
        decimal_places = 2,
        help_text = "Taxa do contrato"
    )

    class Meta:
        db_table = "contracts"

    def __str__(self):
        return f"Contract {self.id}"


class Installment(models.Model):
    contract = models.ForeignKey(
        Contract,
        related_name = 'installments',
        on_delete = models.CASCADE,
        help_text = "Contrato referente a parcela"
    )
    installment_number = models.IntegerField(
        help_text = "Número de ordem da parcela"
    )
    amount = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        help_text = "Valor da parcela"
    )
    due_date = models.DateField(
        help_text = "Data de vencimento da parcela"
    )

    class Meta:
        db_table = "installments"
        ordering = ['contract']

    def __str__(self):
        return f"Installment {self.installment_number} of Contract {self.contract.contract_id}"

