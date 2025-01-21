from rest_framework.test import APITestCase
from .helpers import ccp_uuid_generator
from .models import Contract, Installment
from datetime import datetime, timedelta
from rest_framework import status
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal


class ContractModelTest(TestCase):
    def test_contract_creation(self):
        self.contract3Id = ccp_uuid_generator()

        contract = Contract.objects.create(
            id = self.contract3Id,
            issue_date = "2025-01-15",
            borrower_birth_date = "1990-01-01",
            disbursed_amount = 10000.00,
            document_number = "12345678901",
            country = "Brasil",
            state = "SP",
            city = "São Paulo",
            phone_number = "11999999999",
            interest_rate = 1.5
        )
        self.assertTrue(isinstance(contract, Contract))
        self.assertEqual(str(contract.id), self.contract3Id)

class InstallmentModelTest(TestCase):
    def setUp(self):
        self.contractId = ccp_uuid_generator()
        self.contract = Contract.objects.create(
            id = self.contractId,
            issue_date = "2025-01-15",
            borrower_birth_date = "1990-01-01",
            disbursed_amount = 10000.00,
            document_number = "12345678901",
            country = "Brasil",
            state = "SP",
            city = "São Paulo",
            phone_number = "11999999999",
            interest_rate = 1.5
        )

    def test_installment_creation(self):
        installment = Installment.objects.create(
            contract = self.contract,
            installment_number = 1,
            amount = 1000.00,
            due_date = "2025-02-15"
        )
        self.assertTrue(isinstance(installment, Installment))
        self.assertEqual(installment.installment_number, 1)


class ContractsAPITest(APITestCase):
    def setUp(self):
        self.contract1Id = ccp_uuid_generator()
        self.contract1 = Contract.objects.create(
            id = self.contract1Id,
            issue_date = "2025-01-15",
            borrower_birth_date = "1990-01-01",
            disbursed_amount = 10000.00,
            document_number = "12345678901",
            country = "Brasil",
            state = "SP",
            city = "São Paulo",
            phone_number = "11999999999",
            interest_rate = 1.5
        )

        self.contract2Id = ccp_uuid_generator()
        self.contract2 = Contract.objects.create(
            id = self.contract2Id,
            issue_date = "2025-02-15",
            borrower_birth_date = "1985-01-01",
            disbursed_amount = 20000.00,
            document_number = "98765432101",
            country = "Brasil",
            state = "RJ",
            city = "Rio de Janeiro",
            phone_number = "21999999999",
            interest_rate = 2.0
        )

        self.installments1 = [
            Installment.objects.create(
                contract = self.contract1,
                installment_number = i,
                amount = 1000.00,
                due_date = datetime.strptime("2025-01-15", "%Y-%m-%d").date() + timedelta(days = 30 * i)
            ) for i in range(1, 11)
        ]

        self.installments2 = [
            Installment.objects.create(
                contract = self.contract2,
                installment_number = i,
                amount = 2000.00,
                due_date = datetime.strptime("2025-02-15", "%Y-%m-%d").date() + timedelta(days = 30 * i)
            ) for i in range(1, 11)
        ]

    def test_create_contract(self):
        url = reverse('contract-contracts')
        data = {
            "issue_date": "2025-01-15",
            "borrower_birth_date": "1995-01-01",
            "disbursed_amount": "15000.00",
            "document_number": "11122233344",
            "country": "Brasil",
            "state": "MG",
            "city": "Belo Horizonte",
            "phone_number": "31999999999",
            "interest_rate": 1.8,
            "installments": [
                {
                    "installment_number": 1,
                    "amount": 15000.00,
                    "due_date": "2025-04-15"
                },
                {
                    "installment_number": 2,
                    "amount": 15000.00,
                    "due_date": "2025-05-15"
                }
            ]
        }

        response = self.client.post(url, data, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contract.objects.count(), 3)

    def test_create_contract_validation(self):
        url = reverse('contract-contracts')

        data = {
            "id": "CONT003",
            "birth_date": "1995-01-01"
        }
        response = self.client.post(url, data, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid date format
        data = {
            "id": "CONT003",
            "issue_date": "invalid-date",
            "birth_date": "1995-01-01"
        }
        response = self.client.post(url, data, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_contracts_by_filters(self):
        url = reverse('contract-contracts')

        response = self.client.get(f"{url}?id={self.contract1Id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.contract1Id)

        response = self.client.get(f"{url}?document_number=12345678901")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['document_number'], "12345678901")

        response = self.client.get(f"{url}?state=SP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['state'], "SP")

        response = self.client.get(f"{url}?issue_date=2025-01-15")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"{url}?issue_date=01/2025")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"{url}?issue_date=2025")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Combined filter tests
        response = self.client.get(f"{url}?document_number=12345678901&state=SP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['document_number'], "12345678901")
        self.assertEqual(response.data[0]['state'], "SP")

        response = self.client.get(f"{url}?issue_date=2025-01-15&state=SP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['state'], "SP")

        response = self.client.get(f"{url}?issue_date=01/2025&document_number=12345678901")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['document_number'], "12345678901")

        response = self.client.get(f"{url}?issue_date=2025&state=SP&document_number=12345678901")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['state'], "SP")
        self.assertEqual(response.data[0]['document_number'], "12345678901")

        response = self.client.get(f"{url}?state=SP&document_number=99999999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(
            f"{url}?id={self.contract1Id}&document_number=12345678901&state=SP&issue_date=2025-01-15"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.contract1Id)
        self.assertEqual(response.data[0]['document_number'], "12345678901")
        self.assertEqual(response.data[0]['state'], "SP")

        response = self.client.get(f"{url}?issue_date=invalid_date&state=SP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['state'], "SP")

        response = self.client.get(f"{url}?issue_date=01/2025&state=INVALID")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(f"{url}?issue_datX=01/2025&state=INVALID")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_contract(self):
        url = reverse('contract-contracts')

        update_data = {
            "id": self.contract1Id,
            "disbursed_amount": 12000.00,
            "interest_rate": 1.8,
            "state": "MG"
        }

        response = self.client.put(url, update_data, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_contract = Contract.objects.get(id = self.contract1Id)
        self.assertEqual(updated_contract.disbursed_amount, Decimal('12000.00'))
        self.assertEqual(updated_contract.interest_rate, Decimal('1.8'))
        self.assertEqual(updated_contract.state, "MG")

        non_existent_id = ccp_uuid_generator()
        bad_update = {
            "id": non_existent_id,
            "disbursed_amount": 15000.00
        }
        response = self.client.put(url, bad_update, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        invalid_update = {
            "disbursed_amount": 15000.00
        }
        response = self.client.put(url, invalid_update, format = 'json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_summary(self):
        url = reverse('contract-contracts-summary')

        response = self.client.get(f"{url}?state=SP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_contracts'], 1)
        self.assertEqual(Decimal(response.data['total_disbursed']), Decimal('10000.00'))
        self.assertEqual(Decimal(response.data['total_receivable']), Decimal('10000.00'))
        self.assertEqual(Decimal(response.data['average_rate']), Decimal('1.5'))

        response = self.client.get(f"{url}?document_number=12345678901")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_contracts'], 1)

        response = self.client.get(f"{url}?issue_date=2025")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_contracts'], 2)
        self.assertEqual(Decimal(response.data['total_disbursed']), Decimal('30000.00'))
        self.assertEqual(Decimal(response.data['total_receivable']), Decimal('30000.00'))
