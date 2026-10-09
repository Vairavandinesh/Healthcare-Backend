from rest_framework import serializers
from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(
        source="doctor.specialization", read_only=True
    )

    class Meta:
        model = PatientDoctorMapping
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "doctor_specialization", "assigned_at",
        ]
        read_only_fields = ["id", "assigned_at"]

    def validate_patient(self, patient):
        # A user may only assign doctors to their own patients
        if patient.created_by != self.context["request"].user:
            raise serializers.ValidationError("Patient not found.")
        return patient