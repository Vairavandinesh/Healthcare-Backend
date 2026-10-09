from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def test_register_and_login(self):
        data = {"name": "Asha", "email": "asha@example.com", "password": "Str0ng#Pass99"}
        res = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.post(
            "/api/auth/login/",
            {"email": data["email"], "password": data["password"]},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_duplicate_email_rejected(self):
        data = {"name": "Asha", "email": "asha@example.com", "password": "Str0ng#Pass99"}
        self.client.post("/api/auth/register/", data, format="json")
        res = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protected_endpoint_requires_token(self):
        res = self.client.get("/api/patients/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthcareFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="a@x.com", email="a@x.com", password="Str0ng#Pass99"
        )
        self.other = User.objects.create_user(
            username="b@x.com", email="b@x.com", password="Str0ng#Pass99"
        )
        self.client.force_authenticate(self.user)
        self.patient = self.client.post(
            "/api/patients/",
            {"name": "Ravi", "age": 34, "gender": "M"},
            format="json",
        ).data
        self.doctor = self.client.post(
            "/api/doctors/",
            {"name": "Meera", "email": "meera@h.com", "specialization": "Cardiology"},
            format="json",
        ).data

    def test_user_only_sees_own_patients(self):
        self.client.force_authenticate(self.other)
        res = self.client.get("/api/patients/")
        self.assertEqual(len(res.data), 0)
        res = self.client.get(f"/api/patients/{self.patient['id']}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_user_cannot_edit_doctor(self):
        self.client.force_authenticate(self.other)
        res = self.client.put(
            f"/api/doctors/{self.doctor['id']}/",
            {"name": "Hacked", "email": "meera@h.com", "specialization": "X"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_mapping_flow(self):
        body = {"patient": self.patient["id"], "doctor": self.doctor["id"]}
        res = self.client.post("/api/mappings/", body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mapping_id = res.data["id"]

        # duplicate assignment is rejected
        res = self.client.post("/api/mappings/", body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # doctors for a patient
        res = self.client.get(f"/api/mappings/{self.patient['id']}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        # remove
        res = self.client.delete(f"/api/mappings/{mapping_id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)