class PatientSummary {
  const PatientSummary({
    required this.patientId,
    required this.displayName,
    required this.syntheticIdentifier,
    required this.safetyLabel,
  });

  factory PatientSummary.fromJson(Map<String, dynamic> json) {
    return PatientSummary(
      patientId: json['patient_id'] as String,
      displayName: json['display_name'] as String,
      syntheticIdentifier: json['synthetic_identifier'] as String,
      safetyLabel: json['safety_label'] as String,
    );
  }

  final String patientId;
  final String displayName;
  final String syntheticIdentifier;
  final String safetyLabel;
}

class PatientMatchPreview {
  const PatientMatchPreview({
    required this.displayName,
    required this.maskedPatientCode,
  });

  factory PatientMatchPreview.fromJson(Map<String, dynamic> json) {
    return PatientMatchPreview(
      displayName: json['display_name'] as String,
      maskedPatientCode: json['masked_patient_code'] as String,
    );
  }

  final String displayName;
  final String maskedPatientCode;
}

class PatientProfile extends PatientSummary {
  const PatientProfile({
    required super.patientId,
    required super.displayName,
    required super.syntheticIdentifier,
    required super.safetyLabel,
    required this.relationshipLabel,
    required this.overview,
    required this.birthYear,
    required this.birthDate,
    required this.sex,
    required this.gender,
    required this.contactPhone,
    required this.emergencyContactName,
    required this.emergencyContactPhone,
    required this.preferredLanguage,
    required this.contactPreference,
    required this.avatarUrl,
    required this.country,
    required this.province,
    required this.city,
    required this.homeAddress,
    required this.heightCm,
    required this.weightKg,
    required this.bloodType,
    required this.systolicBloodPressure,
    required this.diastolicBloodPressure,
    required this.smokingStatus,
    required this.alcoholConsumption,
    required this.heartHistory,
    required this.endocrineHistory,
    required this.neuroHistory,
    required this.digestiveHistory,
    required this.respiratoryHistory,
    required this.kidneyHistory,
    required this.cancerHistory,
    required this.patientReportedMedications,
    required this.surgeryHistory,
    required this.familyHistory,
    required this.lifestyleNotes,
    required this.pregnancyStatus,
    required this.medicalHistorySetupCompleted,
  });

  factory PatientProfile.fromJson(Map<String, dynamic> json) {
    final demographics =
        (json['demographics'] as Map<String, dynamic>?) ?? <String, dynamic>{};
    return PatientProfile(
      patientId: json['patient_id'] as String,
      displayName: json['display_name'] as String,
      syntheticIdentifier: json['synthetic_identifier'] as String,
      safetyLabel: json['safety_label'] as String,
      relationshipLabel: json['relationship_label'] as String,
      overview: json['overview'] as String,
      birthDate: demographics['birth_date'] as String?,
      birthYear: demographics['birth_year'] as int?,
      sex: demographics['sex'] as String?,
      gender: demographics['gender'] as String?,
      contactPhone: demographics['contact_phone'] as String?,
      emergencyContactName: demographics['emergency_contact_name'] as String?,
      emergencyContactPhone: demographics['emergency_contact_phone'] as String?,
      preferredLanguage: demographics['preferred_language'] as String?,
      contactPreference: demographics['contact_preference'] as String?,
      avatarUrl: demographics['avatar_url'] as String?,
      country: demographics['country'] as String?,
      province: demographics['province'] as String?,
      city: demographics['city'] as String?,
      homeAddress: demographics['home_address'] as String?,
      heightCm: (demographics['height_cm'] as num?)?.toDouble(),
      weightKg: (demographics['weight_kg'] as num?)?.toDouble(),
      bloodType: demographics['blood_type'] as String?,
      systolicBloodPressure: demographics['systolic_blood_pressure'] as int?,
      diastolicBloodPressure: demographics['diastolic_blood_pressure'] as int?,
      smokingStatus: demographics['smoking_status'] as String?,
      alcoholConsumption: demographics['alcohol_consumption'] as String?,
      heartHistory: demographics['heart_history'] as String?,
      endocrineHistory: demographics['endocrine_history'] as String?,
      neuroHistory: demographics['neuro_history'] as String?,
      digestiveHistory: demographics['digestive_history'] as String?,
      respiratoryHistory: demographics['respiratory_history'] as String?,
      kidneyHistory: demographics['kidney_history'] as String?,
      cancerHistory: demographics['cancer_history'] as String?,
      patientReportedMedications:
          demographics['patient_reported_medications'] as String?,
      surgeryHistory: demographics['surgery_history'] as String?,
      familyHistory: demographics['family_history'] as String?,
      lifestyleNotes: demographics['lifestyle_notes'] as String?,
      pregnancyStatus: demographics['pregnancy_status'] as String?,
      medicalHistorySetupCompleted:
          demographics['medical_history_setup_completed'] as bool? ?? false,
    );
  }

  final String relationshipLabel;
  final String overview;
  final String? birthDate;
  final int? birthYear;
  final String? sex;
  final String? gender;
  final String? contactPhone;
  final String? emergencyContactName;
  final String? emergencyContactPhone;
  final String? preferredLanguage;
  final String? contactPreference;
  final String? avatarUrl;
  final String? country;
  final String? province;
  final String? city;
  final String? homeAddress;
  final double? heightCm;
  final double? weightKg;
  final String? bloodType;
  final int? systolicBloodPressure;
  final int? diastolicBloodPressure;
  final String? smokingStatus;
  final String? alcoholConsumption;
  final String? heartHistory;
  final String? endocrineHistory;
  final String? neuroHistory;
  final String? digestiveHistory;
  final String? respiratoryHistory;
  final String? kidneyHistory;
  final String? cancerHistory;
  final String? patientReportedMedications;
  final String? surgeryHistory;
  final String? familyHistory;
  final String? lifestyleNotes;
  final String? pregnancyStatus;
  final bool medicalHistorySetupCompleted;
}

class PatientListData {
  const PatientListData({required this.items});

  factory PatientListData.fromJson(Map<String, dynamic> json) {
    return PatientListData(
      items: (json['items'] as List)
          .map((item) => PatientSummary.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  final List<PatientSummary> items;
}

class MedicalRecordItem {
  const MedicalRecordItem({
    required this.id,
    required this.title,
    required this.category,
    required this.summary,
    required this.recordedAt,
  });

  factory MedicalRecordItem.fromJson(Map<String, dynamic> json) {
    return MedicalRecordItem(
      id: json['id'] as String,
      title: json['title'] as String,
      category: json['category'] as String,
      summary: json['summary'] as String,
      recordedAt: DateTime.parse(json['recorded_at'] as String),
    );
  }

  final String id;
  final String title;
  final String category;
  final String summary;
  final DateTime recordedAt;
}

class MedicationItem {
  const MedicationItem({
    required this.id,
    this.clinicalEventId,
    required this.name,
    required this.dosage,
    required this.schedule,
    required this.status,
    required this.note,
  });

  factory MedicationItem.fromJson(Map<String, dynamic> json) {
    return MedicationItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      name: json['name'] as String,
      dosage: json['dosage'] as String,
      schedule: json['schedule'] as String,
      status: json['status'] as String,
      note: json['note'] as String,
    );
  }

  final String id;
  final String? clinicalEventId;
  final String name;
  final String dosage;
  final String schedule;
  final String status;
  final String note;
}

class PrescriptionMedicationItem {
  const PrescriptionMedicationItem({
    required this.id,
    required this.name,
    required this.dosage,
    required this.schedule,
    required this.medicationId,
    required this.startDate,
    required this.endDate,
  });

  factory PrescriptionMedicationItem.fromJson(Map<String, dynamic> json) {
    return PrescriptionMedicationItem(
      id: json['id'] as String,
      medicationId: json['medication_id'] as String?,
      name: json['name'] as String,
      dosage: json['dosage'] as String,
      schedule: json['schedule'] as String,
      startDate: json['start_date'] as String?,
      endDate: json['end_date'] as String?,
    );
  }

  final String id;
  final String? medicationId;
  final String name;
  final String dosage;
  final String schedule;
  final String? startDate;
  final String? endDate;
}

class PrescriptionItem {
  const PrescriptionItem({
    required this.id,
    this.clinicalEventId,
    required this.status,
    required this.issuedAt,
    required this.notes,
    required this.medications,
  });

  factory PrescriptionItem.fromJson(Map<String, dynamic> json) {
    return PrescriptionItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      status: json['status'] as String,
      issuedAt: json['issued_at'] == null
          ? null
          : DateTime.parse(json['issued_at'] as String),
      notes: json['notes'] as String?,
      medications: (json['medications'] as List)
          .map(
            (item) => PrescriptionMedicationItem.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(),
    );
  }

  final String id;
  final String? clinicalEventId;
  final String status;
  final DateTime? issuedAt;
  final String? notes;
  final List<PrescriptionMedicationItem> medications;
}

class MedicationReminderItem {
  const MedicationReminderItem({
    required this.id,
    this.clinicalEventId,
    required this.reminderType,
    required this.scheduleLabel,
    required this.channel,
    required this.status,
    required this.medicationId,
    required this.prescriptionMedicationId,
    required this.nextDueAt,
  });

  factory MedicationReminderItem.fromJson(Map<String, dynamic> json) {
    return MedicationReminderItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      reminderType: json['reminder_type'] as String,
      scheduleLabel: json['schedule_label'] as String,
      channel: json['channel'] as String,
      status: json['status'] as String,
      medicationId: json['medication_id'] as String?,
      prescriptionMedicationId: json['prescription_medication_id'] as String?,
      nextDueAt: json['next_due_at'] == null
          ? null
          : DateTime.parse(json['next_due_at'] as String),
    );
  }

  final String id;
  final String? clinicalEventId;
  final String reminderType;
  final String scheduleLabel;
  final String channel;
  final String status;
  final String? medicationId;
  final String? prescriptionMedicationId;
  final DateTime? nextDueAt;
}

class DoctorNoteItem {
  const DoctorNoteItem({
    required this.id,
    this.clinicalEventId,
    required this.title,
    required this.body,
    required this.createdAt,
  });

  factory DoctorNoteItem.fromJson(Map<String, dynamic> json) {
    return DoctorNoteItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      title: json['title'] as String,
      body: json['body'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String? clinicalEventId;
  final String title;
  final String body;
  final DateTime createdAt;
}

class PatientAllergyItem {
  const PatientAllergyItem({
    required this.id,
    required this.label,
    required this.reaction,
    required this.severity,
    required this.status,
  });

  factory PatientAllergyItem.fromJson(Map<String, dynamic> json) {
    return PatientAllergyItem(
      id: json['id'] as String,
      label: json['label'] as String,
      reaction: json['reaction'] as String?,
      severity: json['severity'] as String,
      status: json['status'] as String,
    );
  }

  final String id;
  final String label;
  final String? reaction;
  final String severity;
  final String status;
}

class ChronicDiseaseItem {
  const ChronicDiseaseItem({
    required this.id,
    required this.name,
    required this.status,
    required this.diagnosedOn,
    required this.notes,
  });

  factory ChronicDiseaseItem.fromJson(Map<String, dynamic> json) {
    return ChronicDiseaseItem(
      id: json['id'] as String,
      name: json['name'] as String,
      status: json['status'] as String,
      diagnosedOn: json['diagnosed_on'] as String?,
      notes: json['notes'] as String?,
    );
  }

  final String id;
  final String name;
  final String status;
  final String? diagnosedOn;
  final String? notes;
}

class VisitHistoryItem {
  const VisitHistoryItem({
    required this.id,
    this.clinicalEventId,
    required this.visitType,
    required this.title,
    required this.summary,
    required this.occurredAt,
    required this.clinicianLabel,
  });

  factory VisitHistoryItem.fromJson(Map<String, dynamic> json) {
    return VisitHistoryItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      visitType: json['visit_type'] as String,
      title: json['title'] as String,
      summary: json['summary'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      clinicianLabel: json['clinician_label'] as String?,
    );
  }

  final String id;
  final String? clinicalEventId;
  final String visitType;
  final String title;
  final String summary;
  final DateTime occurredAt;
  final String? clinicianLabel;
}

class DiagnosisItem {
  const DiagnosisItem({
    required this.id,
    this.clinicalEventId,
    required this.label,
    required this.status,
    required this.diagnosedOn,
    required this.notes,
  });

  factory DiagnosisItem.fromJson(Map<String, dynamic> json) {
    return DiagnosisItem(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      label: json['label'] as String,
      status: json['status'] as String,
      diagnosedOn: json['diagnosed_on'] as String?,
      notes: json['notes'] as String?,
    );
  }

  final String id;
  final String? clinicalEventId;
  final String label;
  final String status;
  final String? diagnosedOn;
  final String? notes;
}

class ClinicalEventItem {
  const ClinicalEventItem({
    required this.id,
    required this.patientId,
    required this.doctorId,
    required this.title,
    required this.chiefComplaint,
    required this.symptomSummary,
    required this.diagnosisSummary,
    required this.onsetDate,
    required this.status,
    required this.linkedResourceCounts,
    this.timeline = const <ClinicalEventTimelineEntry>[],
    this.patientUpdates = const <ClinicalEventUpdateItem>[],
    required this.createdAt,
    required this.updatedAt,
    required this.safetyLabel,
  });

  factory ClinicalEventItem.fromJson(Map<String, dynamic> json) {
    return ClinicalEventItem(
      id: json['id'] as String,
      patientId: json['patient_id'] as String,
      doctorId: json['doctor_id'] as String?,
      title: json['title'] as String,
      chiefComplaint: json['chief_complaint'] as String,
      symptomSummary: json['symptom_summary'] as String?,
      diagnosisSummary: json['diagnosis_summary'] as String?,
      onsetDate: json['onset_date'] as String?,
      status: json['status'] as String,
      linkedResourceCounts:
          ((json['linked_resource_counts'] as Map<String, dynamic>?) ??
                  <String, dynamic>{})
              .map((key, value) => MapEntry(key, value as int)),
      timeline: ((json['timeline'] as List?) ?? <Object>[])
          .map(
            (item) => ClinicalEventTimelineEntry.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(),
      patientUpdates: ((json['patient_updates'] as List?) ?? <Object>[])
          .map(
            (item) =>
                ClinicalEventUpdateItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      safetyLabel: json['safety_label'] as String,
    );
  }

  final String id;
  final String patientId;
  final String? doctorId;
  final String title;
  final String chiefComplaint;
  final String? symptomSummary;
  final String? diagnosisSummary;
  final String? onsetDate;
  final String status;
  final Map<String, int> linkedResourceCounts;
  final List<ClinicalEventTimelineEntry> timeline;
  final List<ClinicalEventUpdateItem> patientUpdates;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String safetyLabel;
}

class ClinicalEventTimelineEntry {
  const ClinicalEventTimelineEntry({
    required this.entryType,
    required this.resourceId,
    required this.title,
    required this.occurredAt,
  });

  factory ClinicalEventTimelineEntry.fromJson(Map<String, dynamic> json) {
    return ClinicalEventTimelineEntry(
      entryType: json['entry_type'] as String,
      resourceId: json['resource_id'] as String?,
      title: json['title'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
    );
  }

  final String entryType;
  final String? resourceId;
  final String title;
  final DateTime occurredAt;
}

class ClinicalEventUpdateItem {
  const ClinicalEventUpdateItem({
    required this.id,
    required this.patientId,
    required this.clinicalEventId,
    required this.submittedByUserId,
    required this.updateType,
    required this.summary,
    required this.occurredAt,
    required this.createdAt,
  });

  factory ClinicalEventUpdateItem.fromJson(Map<String, dynamic> json) {
    return ClinicalEventUpdateItem(
      id: json['id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String,
      submittedByUserId: json['submitted_by_user_id'] as String,
      updateType: json['update_type'] as String,
      summary: json['summary'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String patientId;
  final String clinicalEventId;
  final String submittedByUserId;
  final String updateType;
  final String summary;
  final DateTime occurredAt;
  final DateTime createdAt;
}

class MedicalHistoryReviewItem {
  const MedicalHistoryReviewItem({
    required this.id,
    required this.patientId,
    required this.doctorId,
    required this.targetType,
    required this.targetId,
    required this.action,
    required this.amendmentSummary,
    required this.correctionRequest,
    required this.createdAt,
  });

  factory MedicalHistoryReviewItem.fromJson(Map<String, dynamic> json) {
    return MedicalHistoryReviewItem(
      id: json['id'] as String,
      patientId: json['patient_id'] as String,
      doctorId: json['doctor_id'] as String?,
      targetType: json['target_type'] as String,
      targetId: json['target_id'] as String,
      action: json['action'] as String,
      amendmentSummary: json['amendment_summary'] as String?,
      correctionRequest: json['correction_request'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String patientId;
  final String? doctorId;
  final String targetType;
  final String targetId;
  final String action;
  final String? amendmentSummary;
  final String? correctionRequest;
  final DateTime createdAt;
}

class PatientCareBundle {
  const PatientCareBundle({
    required this.patient,
    this.clinicalEvents = const <ClinicalEventItem>[],
    this.clinicalServices = const <ClinicalServiceItem>[],
    this.clinicalEventUpdates = const <ClinicalEventUpdateItem>[],
    this.medicalHistoryReviews = const <MedicalHistoryReviewItem>[],
    required this.allergies,
    required this.chronicDiseases,
    required this.visitHistory,
    required this.diagnoses,
    required this.records,
    required this.imagingAssets,
    required this.medications,
    required this.prescriptions,
    required this.medicationReminders,
    this.recoveryPlans = const <RecoveryPlanData>[],
    required this.doctorNotes,
  });

  factory PatientCareBundle.fromJson(Map<String, dynamic> json) {
    return PatientCareBundle(
      patient: PatientProfile.fromJson(json['patient'] as Map<String, dynamic>),
      clinicalEvents: ((json['clinical_events'] as List?) ?? <Object>[])
          .map(
            (item) => ClinicalEventItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      clinicalServices: ((json['clinical_services'] as List?) ?? <Object>[])
          .map(
            (item) =>
                ClinicalServiceItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      clinicalEventUpdates:
          ((json['clinical_event_updates'] as List?) ?? <Object>[])
              .map(
                (item) => ClinicalEventUpdateItem.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList(),
      medicalHistoryReviews:
          ((json['medical_history_reviews'] as List?) ?? <Object>[])
              .map(
                (item) => MedicalHistoryReviewItem.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList(),
      allergies: ((json['allergies'] as List?) ?? <Object>[])
          .map(
            (item) => PatientAllergyItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      chronicDiseases: ((json['chronic_diseases'] as List?) ?? <Object>[])
          .map(
            (item) => ChronicDiseaseItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      visitHistory: ((json['visit_history'] as List?) ?? <Object>[])
          .map(
            (item) => VisitHistoryItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      diagnoses: ((json['diagnoses'] as List?) ?? <Object>[])
          .map((item) => DiagnosisItem.fromJson(item as Map<String, dynamic>))
          .toList(),
      records: (json['records'] as List)
          .map(
            (item) => MedicalRecordItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      imagingAssets: ((json['imaging_assets'] as List?) ?? <Object>[])
          .map(
            (item) =>
                MedicalImagingAsset.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      medications: (json['medications'] as List)
          .map((item) => MedicationItem.fromJson(item as Map<String, dynamic>))
          .toList(),
      prescriptions: ((json['prescriptions'] as List?) ?? <Object>[])
          .map(
            (item) => PrescriptionItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      medicationReminders:
          ((json['medication_reminders'] as List?) ?? <Object>[])
              .map(
                (item) => MedicationReminderItem.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList(),
      recoveryPlans: ((json['recovery_plans'] as List?) ?? <Object>[])
          .map(
            (item) => RecoveryPlanData.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      doctorNotes: (json['doctor_notes'] as List)
          .map((item) => DoctorNoteItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  final PatientProfile patient;
  final List<ClinicalEventItem> clinicalEvents;
  final List<ClinicalServiceItem> clinicalServices;
  final List<ClinicalEventUpdateItem> clinicalEventUpdates;
  final List<MedicalHistoryReviewItem> medicalHistoryReviews;
  final List<PatientAllergyItem> allergies;
  final List<ChronicDiseaseItem> chronicDiseases;
  final List<VisitHistoryItem> visitHistory;
  final List<DiagnosisItem> diagnoses;
  final List<MedicalRecordItem> records;
  final List<MedicalImagingAsset> imagingAssets;
  final List<MedicationItem> medications;
  final List<PrescriptionItem> prescriptions;
  final List<MedicationReminderItem> medicationReminders;
  final List<RecoveryPlanData> recoveryPlans;
  final List<DoctorNoteItem> doctorNotes;
}

class ClinicalServiceItem {
  const ClinicalServiceItem({
    required this.id,
    required this.patientId,
    required this.clinicalEventId,
    required this.category,
    required this.name,
    required this.status,
    required this.orderedByDoctorId,
    required this.imagingAssetIds,
    required this.createdAt,
    required this.updatedAt,
    this.serviceSubtype,
    this.bodyRegion,
    this.serviceCode,
    this.performingProviderName,
    this.clinicId,
    this.appointmentId,
    this.orderedAt,
    this.scheduledAt,
    this.performedAt,
    this.indicationSummary,
  });

  factory ClinicalServiceItem.fromJson(Map<String, dynamic> json) {
    DateTime? optionalDate(String key) {
      final value = json[key] as String?;
      return value == null ? null : DateTime.parse(value);
    }

    return ClinicalServiceItem(
      id: json['id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String,
      category: json['category'] as String,
      name: json['name'] as String,
      serviceSubtype: json['service_subtype'] as String?,
      bodyRegion: json['body_region'] as String?,
      serviceCode: json['service_code'] as String?,
      orderedByDoctorId: json['ordered_by_doctor_id'] as String,
      performingProviderName: json['performing_provider_name'] as String?,
      clinicId: json['clinic_id'] as String?,
      appointmentId: json['appointment_id'] as String?,
      status: json['status'] as String,
      orderedAt: optionalDate('ordered_at'),
      scheduledAt: optionalDate('scheduled_at'),
      performedAt: optionalDate('performed_at'),
      indicationSummary: json['indication_summary'] as String?,
      imagingAssetIds: ((json['imaging_asset_ids'] as List?) ?? <Object>[])
          .cast<String>(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  final String id;
  final String patientId;
  final String clinicalEventId;
  final String category;
  final String name;
  final String? serviceSubtype;
  final String? bodyRegion;
  final String? serviceCode;
  final String orderedByDoctorId;
  final String? performingProviderName;
  final String? clinicId;
  final String? appointmentId;
  final String status;
  final DateTime? orderedAt;
  final DateTime? scheduledAt;
  final DateTime? performedAt;
  final String? indicationSummary;
  final List<String> imagingAssetIds;
  final DateTime createdAt;
  final DateTime updatedAt;
}

class MedicalImagingAsset {
  const MedicalImagingAsset({
    required this.id,
    required this.patientId,
    this.clinicalEventId,
    this.clinicalServiceId,
    required this.storageProvider,
    required this.contentType,
    required this.fileExtension,
    required this.sizeBytes,
    required this.uploadedSizeBytes,
    required this.uploadStatus,
    required this.reviewStatus,
    this.findingSummary,
    this.measurementSummary,
    this.observedAt,
    this.treatmentRelevanceDate,
    required this.createdAt,
    required this.updatedAt,
    required this.expiresAt,
    required this.uploadedAt,
    required this.reviewedAt,
    required this.safetyLabel,
    this.provenanceVersions = const <MedicalImagingProvenance>[],
  });

  factory MedicalImagingAsset.fromJson(Map<String, dynamic> json) {
    DateTime? optionalDate(String key) {
      final value = json[key] as String?;
      return value == null ? null : DateTime.parse(value);
    }

    return MedicalImagingAsset(
      id: json['id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      clinicalServiceId: json['clinical_service_id'] as String?,
      storageProvider: json['storage_provider'] as String,
      contentType: json['content_type'] as String,
      fileExtension: json['file_extension'] as String,
      sizeBytes: json['size_bytes'] as int,
      uploadedSizeBytes: json['uploaded_size_bytes'] as int?,
      uploadStatus: json['upload_status'] as String,
      reviewStatus: json['review_status'] as String,
      findingSummary: json['finding_summary'] as String?,
      measurementSummary: json['measurement_summary'] as String?,
      observedAt: optionalDate('observed_at'),
      treatmentRelevanceDate: json['treatment_relevance_date'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      expiresAt: DateTime.parse(json['expires_at'] as String),
      uploadedAt: optionalDate('uploaded_at'),
      reviewedAt: optionalDate('reviewed_at'),
      safetyLabel: json['safety_label'] as String,
      provenanceVersions:
          (json['provenance_versions'] as List<dynamic>? ?? const <dynamic>[])
              .map(
                (item) => MedicalImagingProvenance.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList(),
    );
  }

  final String id;
  final String patientId;
  final String? clinicalEventId;
  final String? clinicalServiceId;
  final String storageProvider;
  final String contentType;
  final String fileExtension;
  final int sizeBytes;
  final int? uploadedSizeBytes;
  final String uploadStatus;
  final String reviewStatus;
  final String? findingSummary;
  final String? measurementSummary;
  final DateTime? observedAt;
  final String? treatmentRelevanceDate;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime expiresAt;
  final DateTime? uploadedAt;
  final DateTime? reviewedAt;
  final String safetyLabel;
  final List<MedicalImagingProvenance> provenanceVersions;
}

class MedicalImagingProvenance {
  const MedicalImagingProvenance({
    required this.version,
    required this.storageProvider,
    required this.contentType,
    required this.sizeBytes,
    required this.checksumSha256,
    required this.createdAt,
  });

  factory MedicalImagingProvenance.fromJson(Map<String, dynamic> json) {
    return MedicalImagingProvenance(
      version: json['version'] as int,
      storageProvider: json['storage_provider'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int,
      checksumSha256: json['checksum_sha256'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final int version;
  final String storageProvider;
  final String contentType;
  final int sizeBytes;
  final String checksumSha256;
  final DateTime createdAt;
}

class MedicalImagingPresign {
  const MedicalImagingPresign({
    required this.assetId,
    required this.patientId,
    this.clinicalEventId,
    this.clinicalServiceId,
    required this.uploadUrl,
    required this.method,
    required this.headers,
    required this.expiresAt,
    required this.maxSizeBytes,
    required this.uploadStatus,
    required this.reviewStatus,
    required this.storageProvider,
    required this.safetyLabel,
  });

  factory MedicalImagingPresign.fromJson(Map<String, dynamic> json) {
    return MedicalImagingPresign(
      assetId: json['asset_id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      clinicalServiceId: json['clinical_service_id'] as String?,
      uploadUrl: json['upload_url'] as String,
      method: json['method'] as String,
      headers: (json['headers'] as Map<String, dynamic>).cast<String, String>(),
      expiresAt: DateTime.parse(json['expires_at'] as String),
      maxSizeBytes: json['max_size_bytes'] as int,
      uploadStatus: json['upload_status'] as String,
      reviewStatus: json['review_status'] as String,
      storageProvider: json['storage_provider'] as String,
      safetyLabel: json['safety_label'] as String,
    );
  }

  final String assetId;
  final String patientId;
  final String? clinicalEventId;
  final String? clinicalServiceId;
  final String uploadUrl;
  final String method;
  final Map<String, String> headers;
  final DateTime expiresAt;
  final int maxSizeBytes;
  final String uploadStatus;
  final String reviewStatus;
  final String storageProvider;
  final String safetyLabel;
}

class DemoAssetPresign {
  const DemoAssetPresign({
    required this.assetId,
    required this.patientId,
    required this.uploadUrl,
    required this.method,
    required this.objectKey,
    required this.headers,
    required this.expiresAt,
    required this.maxSizeBytes,
    required this.safetyLabel,
  });

  factory DemoAssetPresign.fromJson(Map<String, dynamic> json) {
    return DemoAssetPresign(
      assetId: json['asset_id'] as String,
      patientId: json['patient_id'] as String,
      uploadUrl: json['upload_url'] as String,
      method: json['method'] as String,
      objectKey: json['object_key'] as String,
      headers: (json['headers'] as Map<String, dynamic>).cast<String, String>(),
      expiresAt: DateTime.parse(json['expires_at'] as String),
      maxSizeBytes: json['max_size_bytes'] as int,
      safetyLabel: json['safety_label'] as String,
    );
  }

  final String assetId;
  final String patientId;
  final String uploadUrl;
  final String method;
  final String objectKey;
  final Map<String, String> headers;
  final DateTime expiresAt;
  final int maxSizeBytes;
  final String safetyLabel;
}

class AssessmentResult {
  const AssessmentResult({
    required this.assessmentId,
    required this.mode,
    required this.status,
    required this.riskBand,
    required this.demoScore,
    required this.inputCompleteness,
    required this.modelVersion,
    required this.limitations,
    required this.recommendedNextSteps,
    required this.safetyLabel,
    required this.createdAt,
  });

  factory AssessmentResult.fromJson(Map<String, dynamic> json) {
    return AssessmentResult(
      assessmentId: json['assessment_id'] as String,
      mode: json['mode'] as String,
      status: json['status'] as String,
      riskBand: json['risk_band'] as String,
      demoScore: (json['demo_score'] as num).toDouble(),
      inputCompleteness: json['input_completeness'] as String,
      modelVersion: json['model_version'] as String,
      limitations: (json['limitations'] as List).cast<String>(),
      recommendedNextSteps: (json['recommended_next_steps'] as List)
          .cast<String>(),
      safetyLabel: json['safety_label'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String assessmentId;
  final String mode;
  final String status;
  final String riskBand;
  final double demoScore;
  final String inputCompleteness;
  final String modelVersion;
  final List<String> limitations;
  final List<String> recommendedNextSteps;
  final String safetyLabel;
  final DateTime createdAt;
}

class AssessmentListData {
  const AssessmentListData({required this.items});

  factory AssessmentListData.fromJson(Map<String, dynamic> json) {
    return AssessmentListData(
      items: (json['items'] as List)
          .map(
            (item) => AssessmentResult.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final List<AssessmentResult> items;
}

class RecoveryTaskInput {
  const RecoveryTaskInput({
    required this.category,
    required this.title,
    required this.detail,
    required this.dueLabel,
    this.notificationTime,
    this.medicationId,
  });

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'category': category,
      'title': title,
      'detail': detail,
      'due_label': dueLabel,
      if (notificationTime != null) 'notification_time': notificationTime,
      if (medicationId != null) 'medication_id': medicationId,
    };
  }

  final String category;
  final String title;
  final String detail;
  final String dueLabel;
  final String? notificationTime;
  final String? medicationId;
}

class RecoveryTaskItem {
  const RecoveryTaskItem({
    required this.taskId,
    required this.planId,
    required this.category,
    required this.title,
    required this.detail,
    required this.dueLabel,
    required this.isCompleted,
    this.notificationTime,
    this.medicationId,
    this.completedAt,
    this.notificationStatus,
  });

  factory RecoveryTaskItem.fromJson(Map<String, dynamic> json) {
    final completedAt = json['completed_at'] as String?;
    return RecoveryTaskItem(
      taskId: json['task_id'] as String,
      planId: json['plan_id'] as String,
      category: json['category'] as String,
      title: json['title'] as String,
      detail: json['detail'] as String,
      dueLabel: json['due_label'] as String,
      notificationTime: json['notification_time'] as String?,
      medicationId: json['medication_id'] as String?,
      isCompleted: json['is_completed'] as bool,
      completedAt: completedAt == null ? null : DateTime.parse(completedAt),
      notificationStatus: json['notification_status'] as String?,
    );
  }

  final String taskId;
  final String planId;
  final String category;
  final String title;
  final String detail;
  final String dueLabel;
  final String? notificationTime;
  final String? medicationId;
  final bool isCompleted;
  final DateTime? completedAt;
  final String? notificationStatus;
}

class RecoveryPlanData {
  const RecoveryPlanData({
    required this.planId,
    required this.patientId,
    this.clinicalEventId,
    required this.title,
    required this.instructions,
    required this.status,
    required this.reviewStatus,
    required this.safetyLabel,
    required this.createdAt,
    required this.updatedAt,
    required this.progressSummary,
    required this.tasks,
    this.submittedAt,
    this.reviewedAt,
    this.approvedAt,
    this.activatedAt,
    this.completedAt,
  });

  factory RecoveryPlanData.fromJson(Map<String, dynamic> json) {
    DateTime? parseOptionalDate(String key) {
      final value = json[key] as String?;
      return value == null ? null : DateTime.parse(value);
    }

    return RecoveryPlanData(
      planId: json['plan_id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      title: json['title'] as String,
      instructions: json['instructions'] as String,
      status: json['status'] as String,
      reviewStatus: json['review_status'] as String? ?? 'draft',
      safetyLabel: json['safety_label'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      submittedAt: parseOptionalDate('submitted_at'),
      reviewedAt: parseOptionalDate('reviewed_at'),
      approvedAt: parseOptionalDate('approved_at'),
      activatedAt: parseOptionalDate('activated_at'),
      completedAt: parseOptionalDate('completed_at'),
      progressSummary: RecoveryPlanProgressData.fromJson(
        json['progress_summary'] as Map<String, dynamic>? ??
            const <String, dynamic>{},
      ),
      tasks: (json['tasks'] as List)
          .map(
            (item) => RecoveryTaskItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final String planId;
  final String patientId;
  final String? clinicalEventId;
  final String title;
  final String instructions;
  final String status;
  final String reviewStatus;
  final String safetyLabel;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? submittedAt;
  final DateTime? reviewedAt;
  final DateTime? approvedAt;
  final DateTime? activatedAt;
  final DateTime? completedAt;
  final RecoveryPlanProgressData progressSummary;
  final List<RecoveryTaskItem> tasks;
}

class RecoveryPlanProgressData {
  const RecoveryPlanProgressData({
    required this.taskCount,
    required this.completedTaskCount,
    required this.remainingTaskCount,
    required this.completionPercent,
  });

  factory RecoveryPlanProgressData.fromJson(Map<String, dynamic> json) {
    return RecoveryPlanProgressData(
      taskCount: json['task_count'] as int? ?? 0,
      completedTaskCount: json['completed_task_count'] as int? ?? 0,
      remainingTaskCount: json['remaining_task_count'] as int? ?? 0,
      completionPercent: json['completion_percent'] as int? ?? 0,
    );
  }

  final int taskCount;
  final int completedTaskCount;
  final int remainingTaskCount;
  final int completionPercent;
}

class RecoveryPlanListData {
  const RecoveryPlanListData({required this.items});

  factory RecoveryPlanListData.fromJson(Map<String, dynamic> json) {
    return RecoveryPlanListData(
      items: (json['items'] as List)
          .map(
            (item) => RecoveryPlanData.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final List<RecoveryPlanData> items;
}

class PatientTodayData {
  const PatientTodayData({
    required this.safetyLabel,
    required this.tasks,
    required this.progressSummary,
    this.activePlan,
  });

  factory PatientTodayData.fromDashboardJson(Map<String, dynamic> json) {
    final data = Map<String, dynamic>.from(json['data'] as Map);
    final planJson = data['active_recovery_plan'] as Map<String, dynamic>?;
    final taskItems = data['today_tasks'] as List?;
    return PatientTodayData(
      safetyLabel:
          data['safety_label'] as String? ??
          'Synthetic demonstration data only. Do not enter real patient data.',
      activePlan: planJson == null ? null : RecoveryPlanData.fromJson(planJson),
      progressSummary: RecoveryPlanProgressData.fromJson(
        data['today_progress'] as Map<String, dynamic>? ??
            const <String, dynamic>{},
      ),
      tasks: taskItems == null
          ? const <RecoveryTaskItem>[]
          : taskItems
                .map(
                  (item) =>
                      RecoveryTaskItem.fromJson(item as Map<String, dynamic>),
                )
                .toList(),
    );
  }

  final String safetyLabel;
  final RecoveryPlanData? activePlan;
  final List<RecoveryTaskItem> tasks;
  final RecoveryPlanProgressData progressSummary;
}

class ChatMessageResult {
  const ChatMessageResult({
    required this.threadId,
    required this.threadKey,
    required this.messageId,
    required this.assistantMessageId,
    required this.content,
    required this.responseChunks,
    required this.safetyLabel,
    required this.isRedFlag,
    required this.model,
    required this.createdAt,
    this.groundingMode = 'fixed_safety_response',
    this.emergencyLabel,
    this.fallbackReason,
    this.sources = const <ChatSourceCard>[],
    this.contextUsed = const <ChatContextCard>[],
    this.uncertainties = const <String>[],
    this.limitation,
    this.nextActionCode = 'none',
    this.suggestedActionCodes = const <String>[],
    this.followUpQuestion,
  });

  factory ChatMessageResult.fromJson(Map<String, dynamic> json) {
    if (json.containsKey('answer_sections')) {
      final sections = (json['answer_sections'] as List).cast<String>();
      return ChatMessageResult(
        threadId: json['session_id'] as String,
        threadKey: 'patient-rag',
        messageId: json['request_id'] as String,
        assistantMessageId: json['request_id'] as String,
        content: sections.join('\n\n'),
        responseChunks: sections,
        safetyLabel: json['safety_code'] as String,
        emergencyLabel: json['emergency'] as bool ? 'emergency' : null,
        isRedFlag: json['emergency'] as bool,
        fallbackReason: json['fallback_code'] as String?,
        model: json['model_version'] as String? ?? 'fixed-safety-response',
        createdAt: DateTime.now(),
        groundingMode:
            json['grounding_mode'] as String? ??
            (((json['sources'] as List?) ?? <Object>[]).isNotEmpty
                ? 'approved_evidence'
                : 'fixed_safety_response'),
        sources: (json['sources'] as List)
            .map(
              (item) => ChatSourceCard.fromJson(item as Map<String, dynamic>),
            )
            .toList(),
        contextUsed: ((json['context_used'] as List?) ?? <Object>[])
            .map(
              (item) => ChatContextCard.fromJson(item as Map<String, dynamic>),
            )
            .toList(),
        uncertainties: ((json['uncertainties'] as List?) ?? <Object>[])
            .cast<String>(),
        limitation: json['limitation'] as String,
        nextActionCode: json['next_action_code'] as String,
        suggestedActionCodes:
            ((json['suggested_action_codes'] as List?) ?? <Object>[])
                .cast<String>(),
        followUpQuestion: json['follow_up_question'] as String?,
      );
    }
    return ChatMessageResult(
      threadId: json['thread_id'] as String,
      threadKey: json['thread_key'] as String,
      messageId: json['message_id'] as String,
      assistantMessageId: json['assistant_message_id'] as String,
      content: json['content'] as String,
      responseChunks: (json['response_chunks'] as List).cast<String>(),
      safetyLabel: json['safety_label'] as String,
      emergencyLabel: json['emergency_label'] as String?,
      isRedFlag: json['is_red_flag'] as bool,
      fallbackReason: json['fallback_reason'] as String?,
      model: json['model'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      groundingMode: 'fixed_safety_response',
    );
  }

  final String threadId;
  final String threadKey;
  final String messageId;
  final String assistantMessageId;
  final String content;
  final List<String> responseChunks;
  final String safetyLabel;
  final String? emergencyLabel;
  final bool isRedFlag;
  final String? fallbackReason;
  final String model;
  final DateTime createdAt;
  final String groundingMode;
  final List<ChatSourceCard> sources;
  final List<ChatContextCard> contextUsed;
  final List<String> uncertainties;
  final String? limitation;
  final String nextActionCode;
  final List<String> suggestedActionCodes;
  final String? followUpQuestion;
}

class PatientChatThreadSummary {
  const PatientChatThreadSummary({
    required this.threadId,
    required this.title,
    required this.status,
    required this.createdAt,
    required this.lastMessageAt,
    required this.retentionUntil,
    this.archivedAt,
    this.deletedAt,
  });

  factory PatientChatThreadSummary.fromJson(Map<String, dynamic> json) {
    return PatientChatThreadSummary(
      threadId: json['thread_id'] as String,
      title: json['title'] as String,
      status: json['status'] as String? ?? 'active',
      createdAt: DateTime.parse(json['created_at'] as String),
      lastMessageAt: DateTime.parse(json['last_message_at'] as String),
      retentionUntil: DateTime.parse(json['retention_until'] as String),
      archivedAt: json['archived_at'] == null
          ? null
          : DateTime.parse(json['archived_at'] as String),
      deletedAt: json['deleted_at'] == null
          ? null
          : DateTime.parse(json['deleted_at'] as String),
    );
  }

  final String threadId;
  final String title;
  final String status;
  final DateTime createdAt;
  final DateTime lastMessageAt;
  final DateTime retentionUntil;
  final DateTime? archivedAt;
  final DateTime? deletedAt;

  bool get isArchived => status == 'archived';
}

class PatientChatHistoryMessage {
  const PatientChatHistoryMessage({
    required this.messageId,
    required this.role,
    required this.content,
    required this.createdAt,
    this.response,
  });

  factory PatientChatHistoryMessage.fromJson(Map<String, dynamic> json) {
    final response = json['response'];
    return PatientChatHistoryMessage(
      messageId: json['message_id'] as String,
      role: json['role'] as String,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      response: response is Map<String, dynamic>
          ? ChatMessageResult.fromJson(response)
          : null,
    );
  }

  final String messageId;
  final String role;
  final String content;
  final DateTime createdAt;
  final ChatMessageResult? response;
}

class PatientChatHistory {
  const PatientChatHistory({required this.thread, required this.messages});

  factory PatientChatHistory.fromJson(Map<String, dynamic> json) {
    return PatientChatHistory(
      thread: PatientChatThreadSummary.fromJson(
        json['thread'] as Map<String, dynamic>,
      ),
      messages: (json['messages'] as List)
          .map(
            (item) => PatientChatHistoryMessage.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(),
    );
  }

  final PatientChatThreadSummary thread;
  final List<PatientChatHistoryMessage> messages;
}

class ChatContextCard {
  const ChatContextCard({
    required this.category,
    required this.provenance,
    required this.recordedOn,
  });

  factory ChatContextCard.fromJson(Map<String, dynamic> json) {
    return ChatContextCard(
      category: json['category'] as String,
      provenance: json['provenance'] as String,
      recordedOn: json['recorded_on'] as String,
    );
  }

  final String category;
  final String provenance;
  final String recordedOn;
}

class ChatSourceCard {
  const ChatSourceCard({
    required this.number,
    required this.passageId,
    required this.title,
    required this.publisher,
    required this.officialLocator,
    this.publicationDate,
    required this.lastMedicalReviewDate,
  });

  factory ChatSourceCard.fromJson(Map<String, dynamic> json) {
    return ChatSourceCard(
      number: json['number'] as int,
      passageId: json['passage_id'] as String,
      title: json['title'] as String,
      publisher: json['publisher'] as String,
      officialLocator: json['official_locator'] as String,
      publicationDate: json['publication_date'] as String?,
      lastMedicalReviewDate: json['last_medical_review_date'] as String,
    );
  }

  final int number;
  final String passageId;
  final String title;
  final String publisher;
  final String officialLocator;
  final String? publicationDate;
  final String lastMedicalReviewDate;
}

class ConsultationRequestItem {
  const ConsultationRequestItem({
    required this.consultationId,
    required this.patientId,
    this.clinicalEventId,
    this.clinicalServiceId,
    required this.specialty,
    required this.questionSummary,
    required this.priority,
    required this.status,
    required this.safetyLabel,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ConsultationRequestItem.fromJson(Map<String, dynamic> json) {
    return ConsultationRequestItem(
      consultationId: json['consultation_id'] as String,
      patientId: json['patient_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String?,
      clinicalServiceId: json['clinical_service_id'] as String?,
      specialty: json['specialty'] as String,
      questionSummary: json['question_summary'] as String,
      priority: json['priority'] as String,
      status: json['status'] as String,
      safetyLabel: json['safety_label'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  final String consultationId;
  final String patientId;
  final String? clinicalEventId;
  final String? clinicalServiceId;
  final String specialty;
  final String questionSummary;
  final String priority;
  final String status;
  final String safetyLabel;
  final DateTime createdAt;
  final DateTime updatedAt;
}

class ConsultationListData {
  const ConsultationListData({required this.items});

  factory ConsultationListData.fromJson(Map<String, dynamic> json) {
    return ConsultationListData(
      items: (json['items'] as List)
          .map(
            (item) =>
                ConsultationRequestItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final List<ConsultationRequestItem> items;
}

class PatientDoctorContact {
  const PatientDoctorContact({
    required this.doctorId,
    required this.displayName,
    required this.title,
    required this.hospitalName,
    required this.specialty,
    required this.department,
    required this.avatarUrl,
  });

  factory PatientDoctorContact.fromJson(Map<String, dynamic> json) {
    return PatientDoctorContact(
      doctorId: json['doctor_id'] as String,
      displayName: json['display_name'] as String,
      title: json['title'] as String,
      hospitalName: json['hospital_name'] as String,
      specialty: json['specialty'] as String?,
      department: json['department'] as String?,
      avatarUrl: json['avatar_url'] as String?,
    );
  }

  final String doctorId;
  final String displayName;
  final String title;
  final String hospitalName;
  final String? specialty;
  final String? department;
  final String? avatarUrl;
}

class PatientDoctorContactList {
  const PatientDoctorContactList({required this.items});

  factory PatientDoctorContactList.fromJson(Map<String, dynamic> json) {
    return PatientDoctorContactList(
      items: (json['items'] as List)
          .map(
            (item) =>
                PatientDoctorContact.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final List<PatientDoctorContact> items;
}

class DoctorPatientContact {
  const DoctorPatientContact({
    required this.patientId,
    required this.displayName,
    required this.avatarUrl,
  });

  factory DoctorPatientContact.fromJson(Map<String, dynamic> json) {
    return DoctorPatientContact(
      patientId: json['patient_id'] as String,
      displayName: json['display_name'] as String,
      avatarUrl: json['avatar_url'] as String?,
    );
  }

  final String patientId;
  final String displayName;
  final String? avatarUrl;
}

class DoctorPatientContactList {
  const DoctorPatientContactList({required this.items});

  factory DoctorPatientContactList.fromJson(Map<String, dynamic> json) {
    return DoctorPatientContactList(
      items: (json['items'] as List)
          .map(
            (item) =>
                DoctorPatientContact.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final List<DoctorPatientContact> items;
}

class PrivateMessage {
  const PrivateMessage({
    required this.messageId,
    required this.threadId,
    required this.senderUserId,
    required this.senderRole,
    required this.content,
    required this.createdAt,
  });

  factory PrivateMessage.fromJson(Map<String, dynamic> json) {
    return PrivateMessage(
      messageId: json['message_id'] as String,
      threadId: json['thread_id'] as String,
      senderUserId: json['sender_user_id'] as String,
      senderRole: json['sender_role'] as String,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String messageId;
  final String threadId;
  final String senderUserId;
  final String senderRole;
  final String content;
  final DateTime createdAt;
}

class PrivateMessageList {
  const PrivateMessageList({required this.threadId, required this.items});

  factory PrivateMessageList.fromJson(Map<String, dynamic> json) {
    return PrivateMessageList(
      threadId: json['thread_id'] as String?,
      items: (json['items'] as List)
          .map((item) => PrivateMessage.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  final String? threadId;
  final List<PrivateMessage> items;
}
