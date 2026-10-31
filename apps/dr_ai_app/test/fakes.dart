import 'dart:async';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/account/domain/support_request_data.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/domain/clinical_event_intelligence_data.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/doctor/domain/doctor_profile.dart';
import 'package:dr_ai_app/features/doctor/domain/medical_resource_fixture.dart';
import 'package:dr_ai_app/features/expected_care/domain/expected_care_data.dart';
import 'package:dr_ai_app/features/notifications/domain/notification_data.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';

const doctorUser = SessionUser(
  id: 'doctor-test-id',
  email: 'doctor.demo@example.com',
  role: AppRole.doctor,
  displayName: 'Dr. Avery Demo',
);

const patientUser = SessionUser(
  id: 'patient-test-id',
  email: 'patient.demo@example.com',
  role: AppRole.patient,
  displayName: 'Riley Demo Patient',
);

const payerUser = SessionUser(
  id: 'payer-test-id',
  email: 'payer.demo@example.com',
  role: AppRole.payer,
  displayName: 'Lin Reviewer',
);

const adminUser = SessionUser(
  id: 'admin-test-id',
  email: 'admin.demo@example.com',
  role: AppRole.admin,
  displayName: 'Hospital Administrator',
);

const adminSession = AuthSession(
  accessToken: 'admin-test-access',
  refreshToken: 'admin-test-refresh',
  user: adminUser,
);

const unsupportedRoleUser = SessionUser(
  id: 'specialist-test-id',
  email: 'specialist.future@example.com',
  role: AppRole.unsupported,
  displayName: 'Future Specialist User',
);

const doctorSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: doctorUser,
);

const doctorProfile = DoctorProfile(
  id: 'doctor-profile-test-id',
  displayName: 'Dr. Avery Demo',
  title: 'Attending physician',
  hospitalName: 'Nanshan Care Center',
  contactPhone: '+86 138 0000 1234',
  country: 'China',
  province: 'Guangdong',
  city: 'Shenzhen',
  specialty: 'Pulmonology',
  department: 'Respiratory Medicine',
  preferredLanguage: 'English',
  lastActiveAt: null,
  isRecentlyActive: true,
);

const patientSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: patientUser,
);

const payerSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: payerUser,
);

NotificationInboxItem notificationFixture({
  String id = '11111111-1111-4111-8111-111111111111',
  String eventType = 'recovery_task_due',
  String category = 'recovery_task',
  String status = 'unread',
  String title = 'Recovery reminder',
  String body = 'Open Dr. AI to review a recovery task.',
  String severity = 'action',
  String deliveryState = 'in_product_only',
  DateTime? readAt,
  DateTime? dismissedAt,
  DateTime? expiresAt,
  DateTime? supersededAt,
  bool canDismiss = true,
  bool canMarkUnread = false,
  bool deepLinkAvailable = true,
  int version = 1,
}) {
  return NotificationInboxItem(
    id: id,
    eventType: eventType,
    severity: severity,
    category: category,
    status: status,
    title: title,
    body: body,
    actorKind: 'system',
    occurredAt: DateTime.utc(2026, 7, 30, 9),
    scheduledFor: DateTime.utc(2026, 7, 30, 9),
    deliveryState: deliveryState,
    readAt: readAt,
    dismissedAt: dismissedAt,
    expiresAt: expiresAt,
    supersededAt: supersededAt,
    canDismiss: canDismiss,
    canMarkUnread: canMarkUnread,
    deepLinkAvailable: deepLinkAvailable,
    version: version,
  );
}

final notificationInboxFixture = NotificationInboxData(
  items: <NotificationInboxItem>[notificationFixture()],
  unreadCount: 1,
  generatedAt: DateTime.now().toUtc(),
);

const notificationPreferencesFixture = NotificationPreferences(
  allowedCategories: <String>[
    'medication_reminder',
    'refill_reminder',
    'recovery_task_due',
  ],
  inProductEnabled: true,
  externalChannels: <String>[],
  quietHoursStart: '22:00',
  quietHoursEnd: '07:00',
  locale: 'en',
  timeZone: 'Asia/Shanghai',
  previewLevel: 'generic',
  version: 1,
);

const notificationReadinessFixture = NotificationReadiness(
  channels: <NotificationChannelReadiness>[
    NotificationChannelReadiness(
      channel: 'apns',
      provider: 'apns',
      status: 'server_readiness',
      readinessCode: 'missing_provider_credentials',
      supported: true,
      enabled: false,
      blockers: <String>['credential_not_configured'],
    ),
    NotificationChannelReadiness(
      channel: 'android_emas',
      provider: 'alibaba_cloud_emas',
      status: 'server_readiness',
      readinessCode: 'missing_provider_credentials',
      supported: true,
      enabled: false,
      blockers: <String>['credential_not_configured'],
    ),
    NotificationChannelReadiness(
      channel: 'web_push',
      provider: 'web_push',
      status: 'server_readiness',
      readinessCode: 'missing_provider_credentials',
      supported: true,
      enabled: false,
      blockers: <String>['credential_not_configured'],
    ),
  ],
);

SupportRequestData supportRequestFixture({
  String id = 'support-request-test-id',
  String reference = 'REQ-2026-0001',
  String requestType = 'support',
  String status = 'queued',
  int version = 1,
  bool replay = false,
  List<String> availableActions = const <String>['withdraw'],
  String? retentionBoundaryCode,
  String? deletionEffectCode,
}) {
  final deletion = requestType == 'deletion';
  return SupportRequestData(
    id: id,
    publicReference: reference,
    requestType: requestType,
    status: status,
    subject: 'Account access help',
    version: version,
    timeline: <SupportRequestTimelineEntry>[
      SupportRequestTimelineEntry(
        sequence: 1,
        eventType: 'submitted',
        status: status,
        actorKind: 'requester',
        summaryCode: 'request_submitted',
        occurredAt: DateTime(2026, 7, 28, 9, 30),
      ),
    ],
    retentionBoundaryCode:
        retentionBoundaryCode ??
        (deletion
            ? 'regulated_and_audit_retention_applies'
            : 'standard_support_retention'),
    deletionEffectCode:
        deletionEffectCode ??
        (deletion
            ? 'request_only_no_immediate_deletion'
            : 'not_a_deletion_request'),
    availableActions: availableActions,
    replay: replay,
    createdAt: DateTime(2026, 7, 28, 9, 30),
    updatedAt: DateTime(2026, 7, 28, 9, 30),
  );
}

SupportRequestData _copySupportRequest(
  SupportRequestData source, {
  bool? replay,
}) {
  return SupportRequestData(
    id: source.id,
    publicReference: source.publicReference,
    requestType: source.requestType,
    status: source.status,
    subject: source.subject,
    version: source.version,
    timeline: source.timeline,
    retentionBoundaryCode: source.retentionBoundaryCode,
    deletionEffectCode: source.deletionEffectCode,
    availableActions: source.availableActions,
    replay: replay ?? source.replay,
    createdAt: source.createdAt,
    updatedAt: source.updatedAt,
  );
}

const demoPayerProfile = PayerProfileData(
  membershipId: 'payer-membership-test-id',
  displayName: 'Lin Reviewer',
  title: 'Medical expenditure reviewer',
  status: 'active',
  scope: 'synthetic_review',
  organization: PayerOrganizationData(
    id: 'payer-organization-test-id',
    name: 'Synthetic Municipal Medical Insurance',
    organizationType: 'public_payer',
    jurisdictionCode: 'CN',
    verificationStatus: 'synthetic_only',
  ),
);

const unsupportedRoleSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: unsupportedRoleUser,
);

final doctorDashboard = DashboardData(
  role: AppRole.doctor,
  data: <String, dynamic>{
    'safety_label':
        'Synthetic demonstration data only. Do not enter real patient data.',
    'hospital': <String, dynamic>{
      'name': 'Synthetic Community Hospital',
      'location': 'Demo County',
      'summary': 'Invited beta facility using synthetic demonstration data.',
    },
    'doctor': <String, dynamic>{
      'name': 'Dr. Avery Demo',
      'title': 'Head of Synthetic Community Hospital',
      'expertise': 'Synthetic care coordination',
      'rating': 4,
    },
    'quick_access': <String>[
      'Imaging records and manual review',
      'Patient medical records',
      'Patient recovery plans',
      'Medical resources (read-only)',
      'Payer requests',
    ],
    'recent_activity': <String, dynamic>{
      'title': 'Synthetic Patient - Demonstration follow-up',
      'time': '20:00',
    },
    'resources': <Map<String, dynamic>>[
      <String, dynamic>{'name': 'CT', 'available': 1, 'total': 2},
      <String, dynamic>{'name': 'MRI', 'available': 1, 'total': 1},
    ],
    'team': <String>['Dr. Rowan Demo', 'Dr. Lee Demo', 'Dr. Zhao Demo'],
  },
);

final patientDashboard = DashboardData(
  role: AppRole.patient,
  data: <String, dynamic>{
    'safety_label':
        'Synthetic demonstration data only. Do not enter real patient data.',
    'recovery_days': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Today',
        'tasks': <String>[
          '50mg demo medication fixture',
          'Drink plenty of water',
          'Avoid triggers',
        ],
      },
      <String, dynamic>{
        'label': 'Jan. 2',
        'tasks': <String>[
          'Drink plenty of water',
          'Avoid triggers',
          'Contact the demo hospital if needed',
        ],
      },
      <String, dynamic>{
        'label': 'Jan. 3',
        'tasks': <String>[
          'Drink plenty of water',
          'Avoid triggers',
          'Goal: begin light demo activities',
        ],
      },
    ],
    'doctor': <String, dynamic>{
      'name': 'Dr. Avery Demo',
      'title': 'Head of Synthetic Community Hospital',
      'expertise': 'Synthetic care coordination',
    },
    'medical_records': <Object>[],
    'imaging_results': <Object>[],
  },
);

const demoPatientDoctorContacts = PatientDoctorContactList(
  items: <PatientDoctorContact>[
    PatientDoctorContact(
      doctorId: 'doctor-profile-test-id',
      displayName: 'Dr. Avery Demo',
      title: 'Attending physician',
      hospitalName: 'Nanshan Care Center',
      specialty: 'Pulmonology',
      department: 'Respiratory Medicine',
      avatarUrl: null,
    ),
    PatientDoctorContact(
      doctorId: 'doctor-profile-test-id-2',
      displayName: 'Dr. Lin Chen',
      title: 'Rehabilitation physician',
      hospitalName: 'Longgang Community Hospital',
      specialty: 'Rehabilitation Medicine',
      department: null,
      avatarUrl: null,
    ),
  ],
);

const demoPatientSummary = PatientSummary(
  patientId: 'patient-profile-test-id',
  displayName: 'Riley Demo Patient',
  syntheticIdentifier: 'SYN-PATIENT-001',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoClinicalEvent = ClinicalEventItem(
  id: 'clinical-event-test-id',
  patientId: 'patient-profile-test-id',
  doctorId: 'doctor-profile-test-id',
  title: 'Synthetic headache care episode',
  chiefComplaint: 'Synthetic recurring headache',
  symptomSummary: 'Demo-only symptom summary for workflow validation.',
  diagnosisSummary: 'Synthetic observation only; not a clinical claim.',
  onsetDate: '2026-07-01',
  status: 'active',
  linkedResourceCounts: const <String, int>{
    'visit_history': 1,
    'diagnoses': 1,
    'medications': 1,
    'prescriptions': 1,
    'medication_reminders': 2,
    'recovery_plans': 1,
    'imaging_assets': 1,
    'doctor_notes': 1,
    'consultations': 0,
    'notifications': 0,
  },
  timeline: <ClinicalEventTimelineEntry>[
    ClinicalEventTimelineEntry(
      entryType: 'clinical_event_created',
      resourceId: 'clinical-event-test-id',
      title: 'Clinical Event created',
      occurredAt: DateTime(2026, 7, 7, 9),
    ),
    ClinicalEventTimelineEntry(
      entryType: 'imaging_review',
      resourceId: 'imaging-test-id',
      title: 'Imaging reviewed',
      occurredAt: DateTime(2026, 7, 8, 9),
    ),
    ClinicalEventTimelineEntry(
      entryType: 'patient_update',
      resourceId: 'clinical-event-update-test-id',
      title: 'Patient update: symptom_update',
      occurredAt: DateTime(2026, 7, 8, 12),
    ),
  ],
  patientUpdates: <ClinicalEventUpdateItem>[
    ClinicalEventUpdateItem(
      id: 'clinical-event-update-test-id',
      patientId: 'patient-profile-test-id',
      clinicalEventId: 'clinical-event-test-id',
      submittedByUserId: 'patient-user-test-id',
      updateType: 'symptom_update',
      summary: 'Synthetic patient update for the care episode.',
      occurredAt: DateTime(2026, 7, 8, 12),
      createdAt: DateTime(2026, 7, 8, 12),
    ),
  ],
  createdAt: DateTime(2026, 7, 7, 9),
  updatedAt: DateTime(2026, 7, 8, 9),
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoPatientCareBundle = PatientCareBundle(
  patient: PatientProfile(
    patientId: 'patient-profile-test-id',
    displayName: 'Riley Demo Patient',
    syntheticIdentifier: 'SYN-PATIENT-001',
    safetyLabel:
        'Synthetic demonstration data only. Do not enter real patient data.',
    relationshipLabel: 'Active synthetic care relationship',
    overview:
        'SYN-PATIENT-001 is synthetic demonstration content for the Dr. AI v1.0 invited beta.',
    birthDate: '1988-01-02',
    birthYear: 1988,
    sex: 'not specified',
    gender: 'not specified',
    contactPhone: '+8613800000000',
    emergencyContactName: 'Casey Cao',
    emergencyContactPhone: '+8613800000001',
    preferredLanguage: 'English',
    contactPreference: 'in-app',
    avatarUrl: null,
    country: 'China',
    province: 'Guangdong',
    city: 'Shenzhen',
    homeAddress: '100 Recovery Road',
    heightCm: 168,
    weightKg: 62,
    bloodType: 'O+',
    systolicBloodPressure: 118,
    diastolicBloodPressure: 76,
    smokingStatus: 'Never',
    alcoholConsumption: 'None or rare',
    heartHistory: null,
    endocrineHistory: null,
    neuroHistory: null,
    digestiveHistory: null,
    respiratoryHistory: null,
    kidneyHistory: null,
    cancerHistory: null,
    patientReportedMedications: null,
    surgeryHistory: null,
    familyHistory: null,
    lifestyleNotes: null,
    pregnancyStatus: 'Prefer not to say',
    medicalHistorySetupCompleted: true,
  ),
  clinicalEvents: <ClinicalEventItem>[demoClinicalEvent],
  clinicalEventUpdates: <ClinicalEventUpdateItem>[
    ClinicalEventUpdateItem(
      id: 'clinical-event-update-test-id',
      patientId: 'patient-profile-test-id',
      clinicalEventId: 'clinical-event-test-id',
      submittedByUserId: 'patient-user-test-id',
      updateType: 'symptom_update',
      summary: 'Synthetic patient update for the care episode.',
      occurredAt: DateTime(2026, 7, 8, 12),
      createdAt: DateTime(2026, 7, 8, 12),
    ),
  ],
  medicalHistoryReviews: <MedicalHistoryReviewItem>[
    MedicalHistoryReviewItem(
      id: 'medical-history-review-test-id',
      patientId: 'patient-profile-test-id',
      doctorId: 'doctor-profile-test-id',
      targetType: 'allergy',
      targetId: 'allergy-test-id',
      action: 'verified',
      amendmentSummary: null,
      correctionRequest: null,
      createdAt: DateTime(2026, 7, 8, 12),
    ),
  ],
  allergies: const <PatientAllergyItem>[
    PatientAllergyItem(
      id: 'allergy-test-id',
      label: 'Synthetic pollen sensitivity',
      reaction: 'Demo-only seasonal response',
      severity: 'mild',
      status: 'active',
    ),
  ],
  chronicDiseases: const <ChronicDiseaseItem>[
    ChronicDiseaseItem(
      id: 'condition-test-id',
      name: 'Synthetic chronic condition',
      status: 'active',
      diagnosedOn: '2026-07-01',
      notes: 'Demo-only condition note.',
    ),
  ],
  visitHistory: <VisitHistoryItem>[
    VisitHistoryItem(
      id: 'visit-test-id',
      clinicalEventId: 'clinical-event-test-id',
      visitType: 'follow_up',
      title: 'Synthetic follow-up visit',
      summary: 'Demo-only visit summary.',
      occurredAt: DateTime(2026, 7, 7),
      clinicianLabel: 'Demo clinician',
    ),
  ],
  diagnoses: const <DiagnosisItem>[
    DiagnosisItem(
      id: 'diagnosis-test-id',
      clinicalEventId: 'clinical-event-test-id',
      label: 'Synthetic observation',
      status: 'active',
      diagnosedOn: '2026-07-07',
      notes: 'Demo-only diagnosis note.',
    ),
  ],
  records: <MedicalRecordItem>[
    MedicalRecordItem(
      id: 'record-test-id',
      title: 'Synthetic intake summary',
      category: 'Demo visit',
      summary: 'Synthetic Week 2 fixture for care-loop navigation only.',
      recordedAt: DateTime(2026, 7, 1),
    ),
  ],
  imagingAssets: <MedicalImagingAsset>[
    MedicalImagingAsset(
      id: 'imaging-test-id',
      patientId: 'patient-profile-test-id',
      clinicalEventId: 'clinical-event-test-id',
      storageProvider: 'tencent_cos',
      contentType: 'image/png',
      fileExtension: 'png',
      sizeBytes: 4096,
      uploadedSizeBytes: 4096,
      uploadStatus: 'uploaded',
      reviewStatus: 'pending_review',
      findingSummary: null,
      measurementSummary: null,
      createdAt: DateTime(2026, 7, 8, 9),
      updatedAt: DateTime(2026, 7, 8, 9),
      expiresAt: DateTime(2026, 7, 8, 9, 15),
      uploadedAt: DateTime(2026, 7, 8, 9, 5),
      reviewedAt: null,
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
    ),
  ],
  medications: <MedicationItem>[
    MedicationItem(
      id: 'medication-test-id',
      clinicalEventId: 'clinical-event-test-id',
      name: 'Demo Sumatriptan Fixture',
      dosage: '50 mg',
      schedule: 'As listed in the synthetic care plan',
      status: 'active',
      note: 'Fixture medication for UI validation; not a prescription.',
    ),
  ],
  prescriptions: <PrescriptionItem>[
    PrescriptionItem(
      id: 'prescription-test-id',
      clinicalEventId: 'clinical-event-test-id',
      status: 'issued',
      issuedAt: DateTime(2026, 7, 7, 10),
      notes: 'Synthetic prescription fixture.',
      medications: const <PrescriptionMedicationItem>[
        PrescriptionMedicationItem(
          id: 'prescription-medication-test-id',
          medicationId: 'medication-test-id',
          name: 'Demo Sumatriptan Fixture',
          dosage: '50 mg',
          schedule: 'As listed in the synthetic care plan',
          startDate: '2026-07-07',
          endDate: null,
        ),
      ],
    ),
  ],
  medicationReminders: <MedicationReminderItem>[
    MedicationReminderItem(
      id: 'medication-reminder-test-id',
      clinicalEventId: 'clinical-event-test-id',
      reminderType: 'medication',
      scheduleLabel: 'In-app medication reminder',
      channel: 'in_app',
      status: 'active',
      medicationId: 'medication-test-id',
      prescriptionMedicationId: null,
      nextDueAt: DateTime(2026, 7, 8, 9),
    ),
    MedicationReminderItem(
      id: 'refill-reminder-test-id',
      clinicalEventId: 'clinical-event-test-id',
      reminderType: 'refill',
      scheduleLabel: 'In-app refill reminder',
      channel: 'in_app',
      status: 'active',
      medicationId: null,
      prescriptionMedicationId: 'prescription-medication-test-id',
      nextDueAt: DateTime(2026, 7, 12, 9),
    ),
  ],
  doctorNotes: <DoctorNoteItem>[
    DoctorNoteItem(
      id: 'note-test-id',
      clinicalEventId: 'clinical-event-test-id',
      title: 'Synthetic care-loop note',
      body: 'Doctor-facing fixture note for Week 2 navigation.',
      createdAt: DateTime(2026, 7, 5),
    ),
  ],
);

PatientCareBundle patientCareBundleWithLegacyGender(String gender) {
  final patient = demoPatientCareBundle.patient;
  return _copyCareBundle(
    demoPatientCareBundle,
    patient: PatientProfile(
      patientId: patient.patientId,
      displayName: patient.displayName,
      syntheticIdentifier: patient.syntheticIdentifier,
      safetyLabel: patient.safetyLabel,
      relationshipLabel: patient.relationshipLabel,
      overview: patient.overview,
      birthDate: patient.birthDate,
      birthYear: patient.birthYear,
      sex: gender,
      gender: gender,
      contactPhone: patient.contactPhone,
      emergencyContactName: patient.emergencyContactName,
      emergencyContactPhone: patient.emergencyContactPhone,
      preferredLanguage: patient.preferredLanguage,
      contactPreference: patient.contactPreference,
      avatarUrl: patient.avatarUrl,
      country: patient.country,
      province: patient.province,
      city: patient.city,
      homeAddress: patient.homeAddress,
      heightCm: patient.heightCm,
      weightKg: patient.weightKg,
      bloodType: patient.bloodType,
      systolicBloodPressure: patient.systolicBloodPressure,
      diastolicBloodPressure: patient.diastolicBloodPressure,
      smokingStatus: patient.smokingStatus,
      alcoholConsumption: patient.alcoholConsumption,
      heartHistory: patient.heartHistory,
      endocrineHistory: patient.endocrineHistory,
      neuroHistory: patient.neuroHistory,
      digestiveHistory: patient.digestiveHistory,
      respiratoryHistory: patient.respiratoryHistory,
      kidneyHistory: patient.kidneyHistory,
      cancerHistory: patient.cancerHistory,
      patientReportedMedications: patient.patientReportedMedications,
      surgeryHistory: patient.surgeryHistory,
      familyHistory: patient.familyHistory,
      lifestyleNotes: patient.lifestyleNotes,
      pregnancyStatus: patient.pregnancyStatus,
      medicalHistorySetupCompleted: patient.medicalHistorySetupCompleted,
    ),
  );
}

final incompleteOnboardingPatientCareBundle = _copyCareBundle(
  demoPatientCareBundle,
  patient: const PatientProfile(
    patientId: 'patient-profile-test-id',
    displayName: 'New Patient',
    syntheticIdentifier: 'SYN-PATIENT-001',
    safetyLabel:
        'Synthetic demonstration data only. Do not enter real patient data.',
    relationshipLabel: 'No doctor connected yet',
    overview: 'Complete your profile so a doctor can recognize your account.',
    birthDate: null,
    birthYear: null,
    sex: null,
    gender: null,
    contactPhone: null,
    emergencyContactName: null,
    emergencyContactPhone: null,
    preferredLanguage: null,
    contactPreference: null,
    avatarUrl: null,
    country: 'China',
    province: 'Guangdong',
    city: 'Shenzhen',
    homeAddress: null,
    heightCm: null,
    weightKg: null,
    bloodType: null,
    systolicBloodPressure: null,
    diastolicBloodPressure: null,
    smokingStatus: null,
    alcoholConsumption: null,
    heartHistory: null,
    endocrineHistory: null,
    neuroHistory: null,
    digestiveHistory: null,
    respiratoryHistory: null,
    kidneyHistory: null,
    cancerHistory: null,
    patientReportedMedications: null,
    surgeryHistory: null,
    familyHistory: null,
    lifestyleNotes: null,
    pregnancyStatus: null,
    medicalHistorySetupCompleted: false,
  ),
);

final demoPresign = DemoAssetPresign(
  assetId: 'asset-test-id',
  patientId: 'patient-profile-test-id',
  uploadUrl: 'https://demo-upload.invalid/demo-assets/patient/asset.png',
  method: 'PUT',
  objectKey: 'demo-assets/patient-profile-test-id/asset-test-id.png',
  headers: const <String, String>{
    'Content-Type': 'image/png',
    'x-dr-ai-demo-upload': 'synthetic-only',
  },
  expiresAt: DateTime(2026, 7, 5, 12),
  maxSizeBytes: 10485760,
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoImagingPresign = MedicalImagingPresign(
  assetId: 'imaging-created-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  clinicalServiceId: 'clinical-service-test-id',
  uploadUrl:
      'https://tencent-cos-upload.invalid/medical-imaging-assets/asset.png',
  method: 'PUT',
  headers: const <String, String>{
    'Content-Type': 'image/png',
    'x-dr-ai-upload-purpose': 'phase2-imaging-metadata-only',
  },
  expiresAt: DateTime(2026, 7, 8, 10),
  maxSizeBytes: 10485760,
  uploadStatus: 'pending_upload',
  reviewStatus: 'not_ready',
  storageProvider: 'tencent_cos',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoImagingUploaded = MedicalImagingAsset(
  id: 'imaging-created-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  storageProvider: 'tencent_cos',
  contentType: 'image/png',
  fileExtension: 'png',
  sizeBytes: 4096,
  uploadedSizeBytes: 4096,
  uploadStatus: 'uploaded',
  reviewStatus: 'pending_review',
  findingSummary: null,
  measurementSummary: null,
  createdAt: DateTime(2026, 7, 8, 10),
  updatedAt: DateTime(2026, 7, 8, 10),
  expiresAt: DateTime(2026, 7, 8, 10, 15),
  uploadedAt: DateTime(2026, 7, 8, 10, 2),
  reviewedAt: null,
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoImagingReviewed = MedicalImagingAsset(
  id: 'imaging-created-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  storageProvider: 'tencent_cos',
  contentType: 'image/png',
  fileExtension: 'png',
  sizeBytes: 4096,
  uploadedSizeBytes: 4096,
  uploadStatus: 'uploaded',
  reviewStatus: 'reviewed',
  findingSummary: 'Manual demo imaging finding/result.',
  measurementSummary: 'Manual demo measurement note.',
  createdAt: DateTime(2026, 7, 8, 10),
  updatedAt: DateTime(2026, 7, 8, 10, 4),
  expiresAt: DateTime(2026, 7, 8, 10, 15),
  uploadedAt: DateTime(2026, 7, 8, 10, 2),
  reviewedAt: DateTime(2026, 7, 8, 10, 4),
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
);

final demoAssessment = AssessmentResult(
  assessmentId: 'assessment-test-id',
  mode: 'simulated',
  status: 'completed',
  riskBand: 'moderate',
  demoScore: 0.54,
  inputCompleteness: 'complete',
  modelVersion: 'fixture-simulator-1.0.0',
  limitations: const <String>[
    'Synthetic fixture result; no clinical inference was performed.',
    'Not validated for diagnosis, treatment, or prognosis.',
  ],
  recommendedNextSteps: const <String>[
    'Review the synthetic case with a qualified clinician.',
  ],
  safetyLabel: 'Research simulation - not for diagnosis.',
  createdAt: DateTime(2026, 7, 5, 12),
);

final demoRecoveryPlan = RecoveryPlanData(
  planId: 'recovery-plan-test-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  title: 'Synthetic Week 3 Recovery Plan',
  instructions:
      'Demo-only recovery plan for invited beta workflow validation. Not medical advice.',
  status: 'active',
  reviewStatus: 'approved',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
  createdAt: DateTime(2026, 7, 5, 10),
  updatedAt: DateTime(2026, 7, 5, 10),
  approvedAt: DateTime(2026, 7, 5, 10),
  activatedAt: DateTime(2026, 7, 5, 10),
  progressSummary: const RecoveryPlanProgressData(
    taskCount: 4,
    completedTaskCount: 0,
    remainingTaskCount: 4,
    completionPercent: 0,
  ),
  tasks: <RecoveryTaskItem>[
    RecoveryTaskItem(
      taskId: 'recovery-task-medication',
      planId: 'recovery-plan-test-id',
      category: 'medication',
      title: 'Demo medication reminder',
      detail: 'Review synthetic medication fixture only.',
      dueLabel: 'Today',
      notificationTime: '09:00',
      isCompleted: false,
      notificationStatus: 'Local demo notification shell scheduled for 09:00',
    ),
    RecoveryTaskItem(
      taskId: 'recovery-task-exercise',
      planId: 'recovery-plan-test-id',
      category: 'exercise',
      title: 'Light demo mobility',
      detail: 'Short synthetic walking task.',
      dueLabel: 'Today',
      isCompleted: false,
    ),
    RecoveryTaskItem(
      taskId: 'recovery-task-diet',
      planId: 'recovery-plan-test-id',
      category: 'diet',
      title: 'Demo hydration check',
      detail: 'Synthetic diet task.',
      dueLabel: 'Today',
      isCompleted: false,
    ),
    RecoveryTaskItem(
      taskId: 'recovery-task-follow-up',
      planId: 'recovery-plan-test-id',
      category: 'follow_up',
      title: 'Synthetic follow-up preparation',
      detail: 'Prepare demo questions.',
      dueLabel: 'Today',
      isCompleted: false,
    ),
  ],
);

final demoPatientToday = PatientTodayData(
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
  activePlan: demoRecoveryPlan,
  progressSummary: demoRecoveryPlan.progressSummary,
  tasks: demoRecoveryPlan.tasks,
);

PatientCareBundle patientCareBundleWithRecoveryPlans(
  List<RecoveryPlanData> plans,
) {
  return _copyCareBundle(demoPatientCareBundle, recoveryPlans: plans);
}

final demoChatResult = ChatMessageResult(
  threadId: 'chat-thread-test-id',
  threadKey: 'patient-education',
  messageId: 'chat-message-user-test-id',
  assistantMessageId: 'chat-message-assistant-test-id',
  content:
      'Educational information only - not medical advice. Prepare questions for your clinician about the synthetic recovery plan.',
  responseChunks: const <String>[
    'Educational information only - not medical advice.',
    'Prepare questions for your clinician',
    'about the synthetic recovery plan.',
  ],
  safetyLabel: 'Educational information only - not medical advice.',
  isRedFlag: false,
  model: 'deepseek-v4-flash',
  createdAt: DateTime(2026, 7, 5, 12),
  groundingMode: 'approved_evidence',
  sources: const <ChatSourceCard>[
    ChatSourceCard(
      number: 1,
      passageId: 'KBPASS-SYNTHETIC-DEMO',
      title: 'Reviewed blood-pressure education',
      publisher: 'Synthetic health authority',
      officialLocator: 'https://example.invalid/reviewed-source',
      lastMedicalReviewDate: '2026-07-16',
    ),
  ],
  contextUsed: const <ChatContextCard>[
    ChatContextCard(
      category: 'measurements',
      provenance: 'patient_profile',
      recordedOn: '2026-07-16',
    ),
  ],
  uncertainties: const <String>[
    'The available information cannot confirm a diagnosis.',
  ],
);

final demoConsultation = ConsultationRequestItem(
  consultationId: 'consultation-test-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  clinicalServiceId: 'consultation-service-test-id',
  specialty: 'Pulmonology demo review',
  questionSummary: 'Synthetic review of recovery-plan education questions.',
  priority: 'routine',
  status: 'requested',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
  createdAt: DateTime(2026, 7, 5, 12),
  updatedAt: DateTime(2026, 7, 5, 12),
  consultationType: 'specialist_referral',
);

class FakeDrAiRepository implements DrAiRepository {
  FakeDrAiRepository({
    this.restoredSession,
    this.restoreCompleter,
    this.loginSession = doctorSession,
    DashboardData? dashboard,
    this.loginError,
    this.registerError,
    this.logoutError,
    this.accountEmailError,
    this.dashboardError,
    PatientListData? patientList,
    PatientCareBundle? patientCareBundle,
    PatientDoctorContactList? patientDoctorContacts,
    AssessmentListData? assessments,
    RecoveryPlanListData? recoveryPlans,
    PatientTodayData? patientToday,
    ChatMessageResult? chatResult,
    List<PatientChatThreadSummary>? chatThreads,
    ConsultationListData? consultations,
    List<MedicalResourceFixture>? medicalResources,
    Map<String, MedicalResourceDetail>? medicalResourceDetails,
    List<PayerRequestData>? payerRequests,
    CareCostLedgerData? careCostLedger,
    PayerProfileData? payerProfile,
    List<SupportRequestData>? supportRequests,
    NotificationInboxData? notificationInbox,
    NotificationPreferences? notificationPreferences,
    NotificationReadiness? notificationReadiness,
    ClinicalEventIntelligenceData? intelligenceArtifact,
    this.noIntelligenceArtifact = false,
    this.patientListError,
    this.patientCareError,
    this.presignError,
    this.imagingError,
    this.assessmentError,
    this.recoveryPlanError,
    this.recoveryPlanSaveError,
    this.patientTodayError,
    this.completionError,
    this.chatError,
    this.consultationError,
    this.careCostError,
    this.careCostCompleter,
    this.payerProfileUpdateError,
    this.supportRequestLoadError,
    this.supportRequestCreateError,
    this.supportRequestWithdrawError,
    this.notificationLoadError,
    this.notificationMutationError,
    this.notificationPreferencesError,
    this.notificationReadinessError,
    this.notificationOpenResult,
    this.intelligenceError,
    this.intelligenceCompleter,
    this.supportRequestCreateErrorAfterPersist = false,
    this.loginCompleter,
  }) : dashboard = dashboard ?? doctorDashboard,
       patientList =
           patientList ??
           const PatientListData(items: <PatientSummary>[demoPatientSummary]),
       patientCareBundle = patientCareBundle ?? demoPatientCareBundle,
       patientDoctorContacts =
           patientDoctorContacts ?? demoPatientDoctorContacts,
       assessments =
           assessments ?? const AssessmentListData(items: <AssessmentResult>[]),
       recoveryPlans =
           recoveryPlans ??
           RecoveryPlanListData(items: <RecoveryPlanData>[demoRecoveryPlan]),
       patientToday = patientToday ?? demoPatientToday,
       chatResult = chatResult ?? demoChatResult,
       chatThreads = List<PatientChatThreadSummary>.from(
         chatThreads ?? const <PatientChatThreadSummary>[],
       ),
       consultations =
           consultations ??
           const ConsultationListData(items: <ConsultationRequestItem>[]),
       medicalResources =
           medicalResources ?? authoritativeMedicalResourceCatalog,
       medicalResourceDetails = medicalResourceDetails ?? const {},
       _payerRequests = List<PayerRequestData>.from(
         payerRequests ?? <PayerRequestData>[payerRequestFixture()],
       ),
       careCostLedger = careCostLedger ?? _defaultCareCostLedger(),
       _payerProfile = payerProfile ?? demoPayerProfile,
       supportRequests = List<SupportRequestData>.from(
         supportRequests ?? const <SupportRequestData>[],
       ),
       notificationInbox = notificationInbox ?? notificationInboxFixture,
       notificationPreferences =
           notificationPreferences ?? notificationPreferencesFixture,
       notificationReadiness =
           notificationReadiness ?? notificationReadinessFixture,
       intelligenceArtifact = noIntelligenceArtifact
           ? null
           : intelligenceArtifact ?? clinicalEventIntelligenceFixture;

  @override
  Future<Map<String, dynamic>> loadDoctorHospitalResources() async =>
      <String, dynamic>{'clinics': <dynamic>[], 'resources': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> loadHospitalWorkspace({
    String? clinicId,
    String? status,
    int page = 1,
  }) async => <String, dynamic>{
    'hospital': <String, dynamic>{'name': 'Synthetic Hospital'},
    'clinics': <dynamic>[],
    'counts': <String, dynamic>{},
    'bookings': <dynamic>[],
    'resources': <dynamic>[],
    'staff': <dynamic>[],
    'total': 0,
    'page': page,
  };

  @override
  Future<void> updateHospitalResource(String id, Map<String, dynamic> data) async {}

  @override
  Future<void> updateHospitalBooking(String id, Map<String, dynamic> data) async {}

  @override
  Future<void> updateHospitalStaff(Map<String, dynamic> data) async {}

  AuthSession? restoredSession;
  Completer<AuthSession?>? restoreCompleter;
  AuthSession loginSession;
  DashboardData dashboard;
  ApiError? loginError;
  ApiError? registerError;
  Exception? logoutError;
  ApiError? accountEmailError;
  ApiError? dashboardError;
  PatientListData patientList;
  PatientCareBundle patientCareBundle;
  PatientDoctorContactList patientDoctorContacts;
  AssessmentListData assessments;
  RecoveryPlanListData recoveryPlans;
  List<RecoveryPhaseInput> lastRecoveryPhases = <RecoveryPhaseInput>[];
  int recoveryPlanSaveCallCount = 0;
  PatientTodayData patientToday;
  ChatMessageResult chatResult;
  List<PatientChatThreadSummary> chatThreads;
  ConsultationListData consultations;
  List<MedicalResourceFixture> medicalResources;
  Map<String, MedicalResourceDetail> medicalResourceDetails;
  final List<PayerRequestData> _payerRequests;
  CareCostLedgerData careCostLedger;
  PayerProfileData _payerProfile;
  List<SupportRequestData> supportRequests;
  NotificationInboxData notificationInbox;
  NotificationPreferences notificationPreferences;
  NotificationReadiness notificationReadiness;
  ClinicalEventIntelligenceData? intelligenceArtifact;
  final bool noIntelligenceArtifact;
  ApiError? patientListError;
  ApiError? patientCareError;
  ApiError? presignError;
  ApiError? imagingError;
  ApiError? assessmentError;
  ApiError? recoveryPlanError;
  ApiError? recoveryPlanSaveError;
  ApiError? patientTodayError;
  ApiError? completionError;
  ApiError? chatError;
  ApiError? consultationError;
  ApiError? careCostError;
  Completer<CareCostLedgerData>? careCostCompleter;
  ApiError? payerProfileUpdateError;
  ApiError? supportRequestLoadError;
  ApiError? supportRequestCreateError;
  ApiError? supportRequestWithdrawError;
  ApiError? notificationLoadError;
  ApiError? notificationMutationError;
  ApiError? notificationPreferencesError;
  ApiError? notificationReadinessError;
  NotificationOpenResult? notificationOpenResult;
  ApiError? intelligenceError;
  Completer<ClinicalEventIntelligenceData?>? intelligenceCompleter;
  bool supportRequestCreateErrorAfterPersist;
  Completer<AuthSession>? loginCompleter;
  bool logoutCalled = false;
  bool registerCalled = false;
  bool patientProfileUpdated = false;
  String? lastPatientBloodType;
  bool patientAllergyCreated = false;
  bool patientMedicalRecordCreated = false;
  bool chronicDiseaseCreated = false;
  bool patientConnected = false;
  bool clinicalEventSaved = false;
  bool clinicalEventUpdateSubmitted = false;
  bool medicalHistoryReviewCreated = false;
  bool medicationSaved = false;
  ClinicalFinancialDraft? lastMedicationFinancial;
  ClinicalFinancialDraft? lastConsultationFinancial;
  int consultationFinancialUpdates = 0;
  bool prescriptionCreated = false;
  bool medicationReminderSaved = false;
  bool imagingPrepared = false;
  String? lastImagingClinicalServiceId;
  bool clinicalServiceSaved = false;
  int clinicalServiceFinancialUpdates = 0;
  bool imagingCompleted = false;
  bool imagingReviewed = false;
  bool doctorProfileUpdated = false;
  bool passwordChanged = false;
  bool passwordReset = false;
  bool accountEmailUpdated = false;
  bool patientMatchPreviewed = false;
  String? lastClinicalEventId;
  String? lastLoginEmail;
  String? lastLoginPassword;
  int chatMessagesSent = 0;
  String? lastChatMessage;
  bool payerRequestCreated = false;
  List<String> lastPayerRequestItemIds = const <String>[];
  int payerReviewCallCount = 0;
  String? lastPayerClarificationMessage;
  String? lastPayerPrivateNote;
  bool payerProfileUpdated = false;
  int payerProfileUpdateCount = 0;
  int payerProfileLoadCount = 0;
  int payerDashboardLoadCount = 0;
  int supportRequestLoadCount = 0;
  int supportRequestCreateCount = 0;
  int supportRequestWithdrawCount = 0;
  final List<String> supportRequestIdempotencyKeys = <String>[];
  final List<ProductEventInput> productEvents = <ProductEventInput>[];
  final Map<String, String> _supportRequestSignatures = <String, String>{};
  final Map<String, SupportRequestData> _supportRequestsByKey =
      <String, SupportRequestData>{};

  static const clinicalEventIntelligenceFixture = ClinicalEventIntelligenceData(
    artifactId: 'intelligence-artifact-test-id',
    artifactVersion: 1,
    clinicalEventSnapshotVersion: 2,
    lifecycleState: 'validated',
    createdAt: '2026-08-01T09:00:00Z',
    location: IntelligenceLocationData(
      jurisdictionCode: 'CN',
      provinceCode: 'Guangdong',
      cityCode: 'Shenzhen',
      facilityLevel: 'tertiary',
      source: 'clinical_event_and_provider_records',
    ),
    requestedItems: <RequestedItemAssessmentData>[
      RequestedItemAssessmentData(
        requestedLineId: 'requested-line-assessment',
        label: 'Specialist assessment',
        requestedQuantity: 1,
        requestedUnit: 'visit',
        requestedAmountMinor: 1800,
        currency: 'CNY',
        codeSystem: 'Synthetic catalog',
        serviceCode: 'SYN-CONSULT-01',
        usefulness: 'Reviews progression and confirms the next care step.',
        mappedPathwayIds: <String>['pathway-typical'],
        scores: IntelligenceScoresData(
          clinicalFit: 84,
          evidenceSupport: 78,
          timingSequence: 82,
          quantityIntensity: 90,
          documentationCompleteness: 64,
          costAlignment: 76,
          aiSupportScore: 79,
          scoreContractVersion: 'cei-score-v1',
          band: 'plausible',
        ),
        estimatedQuantity: EstimatedQuantityData(
          low: 1,
          high: 1,
          unit: 'visit',
        ),
        estimatedCost: EstimatedCostData(
          lowMinor: 1200,
          highMinor: 2200,
          currency: 'CNY',
          provenanceTier: 2,
          sourceLabels: <String>['Synthetic Shenzhen regional reference'],
          isModelOnlyExploratory: false,
        ),
        supportingFacts: <String>['Symptoms progressed for seven days.'],
        contradictingFacts: <String>[],
        missingInformation: <String>['Latest laboratory report'],
        alternatives: <String>['Primary-care reassessment'],
        confidence: 'moderate',
        comment: 'Human review remains required.',
        validationState: 'validated',
        disagreementState: 'partial_disagreement',
      ),
      RequestedItemAssessmentData(
        requestedLineId: 'requested-line-tier5',
        label: 'Specialized monitoring service',
        requestedQuantity: 2,
        requestedUnit: 'sessions',
        requestedAmountMinor: 5000,
        currency: 'CNY',
        codeSystem: null,
        serviceCode: null,
        usefulness:
            'Explores a monitored alternative where references are absent.',
        mappedPathwayIds: <String>['pathway-escalated'],
        scores: IntelligenceScoresData(
          clinicalFit: 58,
          evidenceSupport: 44,
          timingSequence: 52,
          quantityIntensity: 48,
          documentationCompleteness: 35,
          costAlignment: 0,
          aiSupportScore: 47,
          scoreContractVersion: 'cei-score-v1',
          band: 'materially_uncertain',
        ),
        estimatedQuantity: EstimatedQuantityData(
          low: 1,
          high: 4,
          unit: 'sessions',
        ),
        estimatedCost: EstimatedCostData(
          lowMinor: 1000,
          highMinor: 12000,
          currency: 'CNY',
          provenanceTier: 5,
          sourceLabels: <String>[],
          isModelOnlyExploratory: true,
        ),
        supportingFacts: <String>[],
        contradictingFacts: <String>['No administered service recorded.'],
        missingInformation: <String>['Facility price', 'Monitoring duration'],
        alternatives: <String>['Standard outpatient follow-up'],
        confidence: 'low',
        comment: 'Exploratory only.',
        validationState: 'validated_with_uncertainty',
        disagreementState: 'material_disagreement',
      ),
    ],
    pathways: <IntelligencePathwayData>[
      IntelligencePathwayData(
        id: 'pathway-typical',
        type: 'typical_first_line',
        summary: 'Review current findings before changing treatment.',
        items: <PredictedPathwayItemData>[
          PredictedPathwayItemData(
            key: 'follow-up',
            category: 'consultation',
            label: 'Follow-up consultation',
            code: null,
            quantityLow: 1,
            quantityHigh: 1,
            unit: 'visit',
          ),
        ],
      ),
      IntelligencePathwayData(
        id: 'pathway-escalated',
        type: 'escalated',
        summary: 'Escalate only if structured trigger facts are confirmed.',
        items: <PredictedPathwayItemData>[
          PredictedPathwayItemData(
            key: 'monitoring',
            category: 'monitoring',
            label: 'Specialized monitoring',
            code: null,
            quantityLow: 1,
            quantityHigh: 4,
            unit: 'sessions',
          ),
        ],
      ),
    ],
    missingDocumentation: <String>[
      'Attach the latest laboratory report.',
      'Confirm whether monitoring was ordered or only planned.',
    ],
    counterfactuals: <CounterfactualData>[
      CounterfactualData(
        title: 'If recent laboratory results are normal',
        summary: 'A routine follow-up pathway may remain plausible.',
      ),
    ],
    critic: IntelligenceCriticData(
      state: 'partial_disagreement',
      summary:
          'The critic questioned monitoring intensity; deterministic validation preserved the requested line.',
    ),
    lineage: <IntelligenceLineageData>[
      IntelligenceLineageData(
        eventType: 'snapshot_frozen',
        label: 'Clinical Event snapshot frozen',
        occurredAt: '2026-08-01T08:59:00Z',
      ),
      IntelligenceLineageData(
        eventType: 'artifact_validated',
        label: 'Intelligence artifact validated',
        occurredAt: '2026-08-01T09:00:00Z',
      ),
    ],
    humanReviewState: 'awaiting_human_review',
    purposeSummary:
        'Explains the request using frozen, authorized clinical and cost facts.',
    explanationDisplayMode: 'structured_facts',
  );

  static const expectedCareFactSnapshot = CostEstimationFactSnapshotData(
    available: true,
    factsUsed: <CostEstimationFactData>[
      CostEstimationFactData(
        category: 'symptoms',
        label: 'Clinical Event symptoms and complaint',
        reason: null,
        count: 1,
        value: <String, Object>{
          'chief_complaint': 'Synthetic rehabilitation follow-up',
          'symptom_summary': 'Synthetic mobility limitation',
        },
        sourceType: 'clinical_event',
        sourceScope: 'exact_clinical_event',
      ),
      CostEstimationFactData(
        category: 'clinical_service',
        label: 'Event-linked clinical service',
        reason: null,
        count: 1,
        value: <String, Object>{
          'category': 'rehabilitation',
          'status': 'completed',
          'quantity': 2,
        },
        sourceType: 'clinical_service',
        sourceScope: 'exact_clinical_event',
      ),
    ],
    factsNotUsed: <CostEstimationFactData>[
      CostEstimationFactData(
        category: 'medical_record',
        label: '',
        reason: 'patient_wide_record_has_no_clinical_event_binding',
        count: 1,
        value: null,
        sourceType: 'medical_record',
        sourceScope: 'authorized_patient_but_not_exact_event',
      ),
    ],
    missingFacts: <CostEstimationFactData>[
      CostEstimationFactData(
        category: 'ai_imaging_observation_draft',
        label: '',
        reason:
            'DeepSeek image input is unsupported; no AI imaging draft is used.',
        count: 1,
        value: null,
        sourceType: null,
        sourceScope: null,
      ),
    ],
  );

  static const expectedCareCandidate = ExpectedCareCandidateData(
    id: 'candidate-result-test-id',
    state: 'validated_baseline_published',
    responseVersion: 0,
    latestClinicianPosition: 'not_recorded',
    clinicianResponses: <ClinicianResponseData>[],
    currency: 'CNY',
    totalLowMinor: 2000,
    totalHighMinor: 6000,
    referenceDate: '2026-07-25',
    assumptions: <String>['Public primary-care facility'],
    missingInformation: <String>['delivered_cost_lines'],
    limitations: <String>[
      'Synthetic reference data; clinician responses remain separate.',
    ],
    items: <ExpectedCareItemData>[
      ExpectedCareItemData(
        itemKey: 'initial_assessment',
        category: 'Assessment',
        unit: 'visit',
        quantityLow: 1,
        quantityHigh: 1,
        amountLowMinor: 1000,
        amountHighMinor: 2000,
      ),
      ExpectedCareItemData(
        itemKey: 'rehabilitation_session',
        category: 'Rehabilitation',
        unit: 'session',
        quantityLow: 1,
        quantityHigh: 2,
        amountLowMinor: 1000,
        amountHighMinor: 4000,
      ),
    ],
    references: <ExpectedCareReferenceData>[
      ExpectedCareReferenceData(
        releaseType: 'scenario_definition',
        version: '2026.07.1',
        releaseId: 'scenario-release-id',
        checksum: 'abc123',
        effectiveFrom: '2026-07-01',
        effectiveTo: '2027-12-31',
        sourceAuthority: 'Synthetic reference authority',
      ),
      ExpectedCareReferenceData(
        releaseType: 'pricing_reference',
        version: '2026.07.1',
        releaseId: 'price-release-id',
        checksum: 'def456',
        effectiveFrom: '2026-07-01',
        effectiveTo: '2027-12-31',
        sourceAuthority: 'Synthetic pricing authority',
      ),
    ],
    validationState: 'validated',
    factSnapshot: expectedCareFactSnapshot,
  );

  static final expectedCareBaseline = ExpectedCareBaselineData(
    id: 'baseline-test-id',
    clinicalEventId: 'clinical-event-test-id',
    version: 1,
    state: 'validated_baseline_published',
    currency: 'CNY',
    amountType: 'reference_range',
    totalLowMinor: 2000,
    totalHighMinor: 6000,
    assumptions: <String>['Public primary-care facility'],
    missingInformation: <String>[
      'Delivered services have not been reconciled.',
    ],
    limitations: <String>[
      'The range may change when the care plan or facility changes.',
    ],
    items: expectedCareCandidate.items,
    references: expectedCareCandidate.references,
    latestClinicianPosition: 'not_recorded',
    clinicianResponses: const <ClinicianResponseData>[],
    factSnapshot: expectedCareFactSnapshot,
    nextAction:
        'Discuss the baseline and any clinician difference with the responsible doctor; payer reimbursement remains a separate decision.',
    disclaimer:
        'This immutable system-generated reference range is not a quote, bill, coverage determination, reimbursement amount, prescribed care plan, or final patient responsibility.',
  );

  static const expectedCareComparison = ExpectedCareComparisonData(
    id: 'comparison-test-id',
    baselineId: 'baseline-test-id',
    version: 1,
    state: 'comparison_published',
    currency: 'CNY',
    baselineTotalLowMinor: 2000,
    baselineTotalHighMinor: 6000,
    deliveredTotalMinor: 5200,
    submittedTotalMinor: 5200,
    deliveredTotalLabel: 'within_reference_range',
    submittedTotalLabel: 'within_reference_range',
    items: <ExpectedCareComparisonItemData>[
      ExpectedCareComparisonItemData(
        itemKey: 'initial_assessment',
        unit: 'visit',
        baselineAmountLowMinor: 1000,
        baselineAmountHighMinor: 2000,
        deliveredAmountMinor: 1800,
        submittedAmountMinor: 1800,
        deliveredLabel: 'within_reference_range',
        submittedLabel: 'within_reference_range',
      ),
      ExpectedCareComparisonItemData(
        itemKey: 'rehabilitation_session',
        unit: 'session',
        baselineAmountLowMinor: 1000,
        baselineAmountHighMinor: 4000,
        deliveredAmountMinor: 3400,
        submittedAmountMinor: 3400,
        deliveredLabel: 'within_reference_range',
        submittedLabel: 'within_reference_range',
      ),
    ],
    disclaimer:
        'This deterministic numeric comparison is not a clinical, coverage, reimbursement, payment, misconduct, fraud, or patient-liability decision.',
  );

  static const expectedCareExplanation = ExpectedCareExplanationData(
    id: 'explanation-test-id',
    comparisonId: 'comparison-test-id',
    state: 'validated_displayable',
    displayMode: 'validated_ai_explanation',
    artifact: <String, dynamic>{
      'en': <String, dynamic>{
        'plain_language_range': <String, dynamic>{
          'text':
              'The validated facts place the delivered amount within the reference range.',
        },
        'uncertainty_and_limitations': <String, dynamic>{
          'text':
              'This explanation does not determine prescribed care or payment.',
        },
        'responsible_next_action': <String, dynamic>{
          'text':
              'Review the structured facts with the responsible human party.',
        },
      },
      'zh_hans': <String, dynamic>{
        'plain_language_range': <String, dynamic>{
          'text': '已验证事实显示，已交付金额位于参考范围内。',
        },
        'uncertainty_and_limitations': <String, dynamic>{
          'text': '本解释不决定处方诊疗或付款结果。',
        },
        'responsible_next_action': <String, dynamic>{'text': '请与相关负责人核对结构化事实。'},
      },
    },
  );

  @override
  Future<AuthSession?> restore() async {
    if (restoreCompleter != null) return restoreCompleter!.future;
    return restoredSession;
  }

  @override
  Future<List<SupportRequestData>> loadSupportRequests() async {
    supportRequestLoadCount += 1;
    if (supportRequestLoadError != null) throw supportRequestLoadError!;
    return List<SupportRequestData>.unmodifiable(supportRequests);
  }

  @override
  Future<SupportRequestData> createSupportRequest({
    required String requestType,
    required String subject,
    required String message,
    required String idempotencyKey,
  }) async {
    supportRequestCreateCount += 1;
    supportRequestIdempotencyKeys.add(idempotencyKey);
    final signature = '$requestType|${subject.trim()}|${message.trim()}';
    final existing = _supportRequestsByKey[idempotencyKey];
    if (existing != null) {
      if (_supportRequestSignatures[idempotencyKey] != signature) {
        throw const ApiError(
          code: 'conflict',
          message: 'Idempotency key belongs to different content.',
          statusCode: 409,
        );
      }
      return _copySupportRequest(existing, replay: true);
    }
    if (supportRequestCreateError != null &&
        !supportRequestCreateErrorAfterPersist) {
      throw supportRequestCreateError!;
    }
    final deletion = requestType == 'deletion';
    final created = SupportRequestData(
      id: 'support-request-created-$supportRequestCreateCount',
      publicReference: 'REQ-2026-NEW$supportRequestCreateCount',
      requestType: requestType,
      status: 'queued',
      subject: subject.trim(),
      version: 1,
      timeline: <SupportRequestTimelineEntry>[
        SupportRequestTimelineEntry(
          sequence: 1,
          eventType: 'submitted',
          status: 'queued',
          actorKind: 'requester',
          summaryCode: 'request_submitted',
          occurredAt: DateTime(2026, 7, 28, 10),
        ),
      ],
      retentionBoundaryCode: deletion
          ? 'regulated_and_audit_retention_applies'
          : 'standard_support_retention',
      deletionEffectCode: deletion
          ? 'request_only_no_immediate_deletion'
          : 'not_a_deletion_request',
      availableActions: const <String>['withdraw'],
      createdAt: DateTime(2026, 7, 28, 10),
      updatedAt: DateTime(2026, 7, 28, 10),
    );
    _supportRequestSignatures[idempotencyKey] = signature;
    _supportRequestsByKey[idempotencyKey] = created;
    supportRequests = <SupportRequestData>[
      created,
      ...supportRequests.where((item) => item.id != created.id),
    ];
    if (supportRequestCreateError != null &&
        supportRequestCreateErrorAfterPersist) {
      throw supportRequestCreateError!;
    }
    return created;
  }

  @override
  Future<SupportRequestData> withdrawSupportRequest({
    required String requestId,
    required int expectedVersion,
    required String idempotencyKey,
  }) async {
    supportRequestWithdrawCount += 1;
    supportRequestIdempotencyKeys.add(idempotencyKey);
    if (supportRequestWithdrawError != null) {
      throw supportRequestWithdrawError!;
    }
    final current = supportRequests.firstWhere(
      (item) => item.id == requestId,
      orElse: supportRequestFixture,
    );
    final updated = SupportRequestData(
      id: current.id,
      publicReference: current.publicReference,
      requestType: current.requestType,
      status: 'cancelled',
      subject: current.subject,
      version: expectedVersion + 1,
      timeline: <SupportRequestTimelineEntry>[
        ...current.timeline,
        SupportRequestTimelineEntry(
          sequence: current.timeline.length + 1,
          eventType: 'withdrawn',
          status: 'cancelled',
          actorKind: 'requester',
          summaryCode: 'request_withdrawn_by_requester',
          occurredAt: DateTime(2026, 7, 28, 10, 5),
        ),
      ],
      retentionBoundaryCode: current.retentionBoundaryCode,
      deletionEffectCode: current.deletionEffectCode,
      availableActions: const <String>[],
      createdAt: current.createdAt,
      updatedAt: DateTime(2026, 7, 28, 10, 5),
    );
    supportRequests = <SupportRequestData>[
      updated,
      ...supportRequests.where((item) => item.id != requestId),
    ];
    return updated;
  }

  @override
  Future<void> recordProductEvent(ProductEventInput event) async {
    productEvents.add(event);
  }

  @override
  Future<NotificationInboxData> loadNotificationInbox() async {
    if (notificationLoadError != null) throw notificationLoadError!;
    return notificationInbox;
  }

  @override
  Future<NotificationPreferences> loadNotificationPreferences() async {
    if (notificationPreferencesError != null) {
      throw notificationPreferencesError!;
    }
    return notificationPreferences;
  }

  @override
  Future<NotificationPreferences> updateNotificationPreferences(
    NotificationPreferences preferences, {
    required String idempotencyKey,
  }) async {
    if (notificationPreferencesError != null) {
      throw notificationPreferencesError!;
    }
    notificationPreferences = NotificationPreferences(
      allowedCategories: preferences.allowedCategories,
      inProductEnabled: true,
      externalChannels: preferences.externalChannels,
      quietHoursStart: preferences.quietHoursStart,
      quietHoursEnd: preferences.quietHoursEnd,
      locale: preferences.locale,
      timeZone: preferences.timeZone,
      previewLevel: preferences.previewLevel,
      version: preferences.version + 1,
    );
    return notificationPreferences;
  }

  @override
  Future<NotificationReadiness> loadNotificationReadiness() async {
    if (notificationReadinessError != null) {
      throw notificationReadinessError!;
    }
    return notificationReadiness;
  }

  @override
  Future<NotificationInboxItem> setNotificationReadStatus({
    required String notificationId,
    required bool read,
    required int expectedVersion,
    required String idempotencyKey,
  }) async {
    if (notificationMutationError != null) throw notificationMutationError!;
    final current = notificationInbox.items.firstWhere(
      (item) => item.id == notificationId,
    );
    final updated = _copyNotification(
      current,
      status: read ? 'read' : 'unread',
      readAt: read ? DateTime.utc(2026, 7, 30, 10) : null,
      clearReadAt: !read,
      version: expectedVersion + 1,
    );
    _replaceNotification(updated);
    return updated;
  }

  @override
  Future<NotificationInboxItem> dismissNotification({
    required String notificationId,
    required int expectedVersion,
    required String idempotencyKey,
  }) async {
    if (notificationMutationError != null) throw notificationMutationError!;
    final current = notificationInbox.items.firstWhere(
      (item) => item.id == notificationId,
    );
    final updated = _copyNotification(
      current,
      status: 'dismissed',
      dismissedAt: DateTime.utc(2026, 7, 30, 10),
      version: expectedVersion + 1,
    );
    _replaceNotification(updated);
    return updated;
  }

  @override
  Future<NotificationOpenResult> resolveNotificationOpen(
    String notificationId,
  ) async {
    return notificationOpenResult ??
        const NotificationOpenResult(
          status: 'resolved',
          destinationPath: '/patient/recovery-plan',
        );
  }

  void _replaceNotification(NotificationInboxItem updated) {
    final items = <NotificationInboxItem>[
      updated,
      ...notificationInbox.items.where((item) => item.id != updated.id),
    ];
    notificationInbox = NotificationInboxData(
      items: items,
      unreadCount: items.where((item) => item.isUnread).length,
      generatedAt: DateTime.now().toUtc(),
    );
  }

  @override
  Future<List<ExpectedCareCandidateData>> loadExpectedCareCandidates(
    String patientId,
    String eventId,
  ) async => const <ExpectedCareCandidateData>[expectedCareCandidate];

  @override
  Future<ClinicianResponseResultData> submitExpectedCareClinicianResponse({
    required String patientId,
    required String eventId,
    required String candidateId,
    required int expectedVersion,
    required String position,
    required String idempotencyKey,
    String? exceptionCode,
    String? rationale,
    String? patientSafeSummary,
    String? reviewerOnlyNote,
  }) async {
    return ClinicianResponseResultData(
      responseId: 'clinician-response-test-id',
      state: switch (position) {
        'acknowledge' => 'doctor_acknowledged',
        'concur' => 'doctor_concurred',
        'disagree' => 'doctor_disagreed',
        _ => 'doctor_exception_recorded',
      },
      version: expectedVersion + 1,
      idempotentReplay: false,
    );
  }

  @override
  Future<ExpectedCareBaselineData> loadPatientExpectedCareEnvelope(
    String eventId,
  ) async => expectedCareBaseline;

  @override
  Future<PayerExpectedCareData> loadPayerExpectedCareEnvelope(
    String requestId,
  ) async {
    return PayerExpectedCareData(
      baseline: expectedCareBaseline,
      payerRequestId: 'payer-request-test-id',
      submittedState: 'submitted',
      requestedTotalMinor: 5200,
      humanReviewState: 'submitted',
    );
  }

  @override
  Future<ExpectedCareComparisonData> loadDoctorExpectedCareComparison(
    String patientId,
    String eventId,
  ) async => expectedCareComparison;

  @override
  Future<ExpectedCareComparisonData> loadPatientExpectedCareComparison(
    String eventId,
  ) async => expectedCareComparison;

  @override
  Future<ExpectedCareComparisonData> loadPayerExpectedCareComparison(
    String requestId,
  ) async => expectedCareComparison;

  @override
  Future<ExpectedCareComparisonData> createDoctorExpectedCareComparison({
    required String patientId,
    required String eventId,
    String? baselineId,
    required bool includeSubmittedFacts,
    required String idempotencyKey,
  }) async => expectedCareComparison;

  @override
  Future<List<ExpectedCareComparisonData>>
  loadDoctorExpectedCareComparisonHistory({
    required String patientId,
    required String eventId,
  }) async => <ExpectedCareComparisonData>[expectedCareComparison];

  @override
  Future<ExpectedCareExplanationData> requestExpectedCareExplanation({
    required String role,
    required String parentId,
    required String eventId,
    required String comparisonId,
    required String locale,
    required String idempotencyKey,
  }) async => expectedCareExplanation;

  @override
  Future<List<ExpectedCareExplanationData>> loadExpectedCareExplanationHistory({
    required String role,
    required String parentId,
    required String eventId,
    required String comparisonId,
  }) async => <ExpectedCareExplanationData>[expectedCareExplanation];

  @override
  Future<ExpectedCareExplanationData> loadDoctorExpectedCareExplanation({
    required String patientId,
    required String eventId,
    required String comparisonId,
  }) async => expectedCareExplanation;

  @override
  Future<ExpectedCareExplanationData> loadPatientExpectedCareExplanation({
    required String eventId,
    required String comparisonId,
  }) async => expectedCareExplanation;

  @override
  Future<ExpectedCareExplanationData> loadPayerExpectedCareExplanation({
    required String requestId,
    required String comparisonId,
  }) async => expectedCareExplanation;

  @override
  Future<ClinicalEventIntelligenceData?> loadClinicalEventIntelligence({
    required AppRole role,
    required String requestId,
    required String locale,
  }) async {
    if (intelligenceError != null) throw intelligenceError!;
    if (intelligenceCompleter != null) return intelligenceCompleter!.future;
    return intelligenceArtifact;
  }

  @override
  Future<ClinicalEventIntelligenceData> generateClinicalEventIntelligence({
    required String requestId,
    required String idempotencyKey,
  }) async {
    if (intelligenceError != null) throw intelligenceError!;
    intelligenceArtifact = clinicalEventIntelligenceFixture;
    return clinicalEventIntelligenceFixture;
  }

  @override
  Future<IntelligenceResponseResultData> appendIntelligenceClinicianResponse({
    required String requestId,
    required String artifactId,
    required String action,
    required String idempotencyKey,
    String? rationale,
  }) async {
    if (intelligenceError != null) throw intelligenceError!;
    return const IntelligenceResponseResultData(
      responseId: 'intelligence-response-test-id',
      idempotentReplay: false,
    );
  }

  @override
  Future<AuthSession> login(String email, String password) async {
    lastLoginEmail = email;
    lastLoginPassword = password;
    if (loginCompleter != null) {
      return loginCompleter!.future;
    }
    if (loginError != null) {
      throw loginError!;
    }
    return loginSession;
  }

  @override
  Future<PhoneVerificationResult> requestPasswordReset(
    String phoneNumber,
  ) async {
    return const PhoneVerificationResult(
      message: 'Verification code requested.',
      expiresIn: 600,
      debugCode: '123456',
    );
  }

  @override
  Future<PhoneVerificationResult> requestRegistrationCode(
    String phoneNumber,
  ) async {
    return const PhoneVerificationResult(
      message: 'Verification code requested.',
      expiresIn: 600,
      debugCode: '123456',
    );
  }

  @override
  Future<void> resetPassword({
    required String phoneNumber,
    required String verificationCode,
    required String newPassword,
  }) async {
    passwordReset = true;
  }

  @override
  Future<AuthSession> register({
    required String phoneNumber,
    required String email,
    required String password,
    required AppRole role,
    required String verificationCode,
    required bool termsAccepted,
    PatientSignupProfile? patientProfile,
    DoctorSignupProfile? doctorProfile,
    PayerSignupProfile? payerProfile,
  }) async {
    registerCalled = true;
    if (registerError != null) {
      throw registerError!;
    }
    return AuthSession(
      accessToken: 'registered-access-token',
      refreshToken: 'registered-refresh-token',
      user: SessionUser(
        id: 'registered-user-id',
        email: email.isEmpty ? phoneNumber : email,
        role: role,
        displayName: switch (role) {
          AppRole.doctor => 'Invited Doctor',
          AppRole.patient => 'Invited Patient',
          AppRole.payer => 'Invited Reviewer',
          AppRole.admin => 'Hospital Administrator',
          AppRole.unsupported => 'Unsupported User',
        },
      ),
    );
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
    if (logoutError != null) {
      throw logoutError!;
    }
    restoredSession = null;
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    passwordChanged = true;
  }

  @override
  Future<SessionUser> updateAccountEmail(String email) async {
    accountEmailUpdated = true;
    if (accountEmailError != null) {
      throw accountEmailError!;
    }
    final current = restoredSession?.user ?? loginSession.user;
    final updated = SessionUser(
      id: current.id,
      email: email,
      phoneNumber: current.phoneNumber,
      role: current.role,
      displayName: current.displayName,
    );
    if (restoredSession != null) {
      restoredSession = AuthSession(
        accessToken: restoredSession!.accessToken,
        refreshToken: restoredSession!.refreshToken,
        user: updated,
      );
    }
    return updated;
  }

  @override
  Future<DashboardData> loadDashboard(AppRole role) async {
    if (dashboardError != null) {
      throw dashboardError!;
    }
    return dashboard;
  }

  @override
  Future<List<MedicalResourceFixture>> loadMedicalResources() async =>
      medicalResources;

  @override
  Future<MedicalResourceDetail> loadMedicalResource(String sourceId) async {
    final detail = medicalResourceDetails[sourceId];
    if (detail == null) {
      throw const ApiError(
        code: 'resource_not_found',
        message: 'The resource was not found.',
        statusCode: 404,
      );
    }
    return detail;
  }

  @override
  Future<DoctorProfile> loadOwnDoctorProfile() async => _doctorProfile;

  DoctorProfile _doctorProfile = doctorProfile;

  @override
  Future<DoctorProfile> updateOwnDoctorProfile({
    required String displayName,
    required String specialty,
    required String title,
    required String department,
    required String contactPhone,
    required String country,
    required String province,
    required String city,
    required String preferredLanguage,
    required String avatarUrl,
  }) async {
    doctorProfileUpdated = true;
    _doctorProfile = DoctorProfile(
      id: _doctorProfile.id,
      displayName: displayName,
      title: title,
      birthDate: _doctorProfile.birthDate,
      gender: _doctorProfile.gender,
      contactPhone: contactPhone,
      avatarUrl: avatarUrl.isEmpty ? _doctorProfile.avatarUrl : avatarUrl,
      country: country,
      province: province,
      city: city,
      hospitalName: _doctorProfile.hospitalName,
      specialty: specialty,
      department: department,
      preferredLanguage: preferredLanguage,
      lastActiveAt: _doctorProfile.lastActiveAt,
      isRecentlyActive: _doctorProfile.isRecentlyActive,
    );
    return _doctorProfile;
  }

  @override
  Future<PatientListData> loadPatients({String? query}) async {
    if (patientListError != null) {
      throw patientListError!;
    }
    if (query != null && query.trim().isNotEmpty) {
      final normalized = query.trim().toLowerCase();
      return PatientListData(
        items: patientList.items
            .where(
              (patient) =>
                  patient.displayName.toLowerCase().contains(normalized) ||
                  patient.syntheticIdentifier.toLowerCase().contains(
                    normalized,
                  ),
            )
            .toList(),
      );
    }
    return patientList;
  }

  @override
  Future<PatientSummary> connectPatientByCode(String patientCode) async {
    patientConnected = true;
    patientList = const PatientListData(
      items: <PatientSummary>[demoPatientSummary],
    );
    return demoPatientSummary;
  }

  @override
  Future<PatientMatchPreview> previewPatientByCode(String patientCode) async {
    patientMatchPreviewed = true;
    return const PatientMatchPreview(
      displayName: 'Riley Demo Patient',
      maskedPatientCode: 'Patient ID ending in T001',
    );
  }

  @override
  Future<PatientCareBundle> loadPatientCareBundle(String patientId) async {
    if (patientCareError != null) {
      throw patientCareError!;
    }
    return patientCareBundle;
  }

  @override
  Future<PatientCareBundle> loadOwnPatientCare() async {
    if (patientCareError != null) {
      throw patientCareError!;
    }
    return patientCareBundle;
  }

  @override
  Future<PatientDoctorContactList> loadOwnPatientContacts() async {
    return patientDoctorContacts;
  }

  @override
  Future<void> actOnDoctorRelationship({
    required String relationshipId,
    required int expectedVersion,
    required String action,
  }) async {}

  @override
  Future<PatientProfile> updateOwnPatientProfile({
    required String displayName,
    required String birthDate,
    required String gender,
    required String contactPhone,
    required String emergencyContactName,
    required String emergencyContactPhone,
    required String preferredLanguage,
    required String contactPreference,
    required String avatarUrl,
    required String country,
    required String province,
    required String city,
    required String homeAddress,
    required String heightCm,
    required String weightKg,
    required String bloodType,
    required String systolicBloodPressure,
    required String diastolicBloodPressure,
    required String smokingStatus,
    required String alcoholConsumption,
    required String heartHistory,
    required String endocrineHistory,
    required String neuroHistory,
    required String digestiveHistory,
    required String respiratoryHistory,
    required String kidneyHistory,
    required String cancerHistory,
    required String patientReportedMedications,
    required String surgeryHistory,
    required String familyHistory,
    required String lifestyleNotes,
    required String pregnancyStatus,
    required bool medicalHistorySetupCompleted,
  }) async {
    patientProfileUpdated = true;
    lastPatientBloodType = bloodType;
    final updated = PatientProfile(
      patientId: patientCareBundle.patient.patientId,
      displayName: displayName,
      syntheticIdentifier: patientCareBundle.patient.syntheticIdentifier,
      safetyLabel: patientCareBundle.patient.safetyLabel,
      relationshipLabel: patientCareBundle.patient.relationshipLabel,
      overview: patientCareBundle.patient.overview,
      birthDate: birthDate.isEmpty ? null : birthDate,
      birthYear: birthDate.length >= 4
          ? int.tryParse(birthDate.substring(0, 4))
          : null,
      sex: gender,
      gender: gender,
      contactPhone: contactPhone.isEmpty ? null : contactPhone,
      emergencyContactName: emergencyContactName.isEmpty
          ? null
          : emergencyContactName,
      emergencyContactPhone: emergencyContactPhone.isEmpty
          ? null
          : emergencyContactPhone,
      preferredLanguage: preferredLanguage,
      contactPreference: contactPreference,
      avatarUrl: avatarUrl.isEmpty
          ? patientCareBundle.patient.avatarUrl
          : avatarUrl,
      country: country.isEmpty ? patientCareBundle.patient.country : country,
      province: province.isEmpty
          ? patientCareBundle.patient.province
          : province,
      city: city.isEmpty ? patientCareBundle.patient.city : city,
      homeAddress: homeAddress.isEmpty
          ? patientCareBundle.patient.homeAddress
          : homeAddress,
      heightCm: heightCm.isEmpty
          ? patientCareBundle.patient.heightCm
          : double.tryParse(heightCm),
      weightKg: weightKg.isEmpty
          ? patientCareBundle.patient.weightKg
          : double.tryParse(weightKg),
      bloodType: bloodType,
      systolicBloodPressure: int.tryParse(systolicBloodPressure),
      diastolicBloodPressure: int.tryParse(diastolicBloodPressure),
      smokingStatus: smokingStatus,
      alcoholConsumption: alcoholConsumption,
      heartHistory: heartHistory.isEmpty ? null : heartHistory,
      endocrineHistory: endocrineHistory.isEmpty ? null : endocrineHistory,
      neuroHistory: neuroHistory.isEmpty ? null : neuroHistory,
      digestiveHistory: digestiveHistory.isEmpty ? null : digestiveHistory,
      respiratoryHistory: respiratoryHistory.isEmpty
          ? null
          : respiratoryHistory,
      kidneyHistory: kidneyHistory.isEmpty ? null : kidneyHistory,
      cancerHistory: cancerHistory.isEmpty ? null : cancerHistory,
      patientReportedMedications: patientReportedMedications.isEmpty
          ? null
          : patientReportedMedications,
      surgeryHistory: surgeryHistory.isEmpty ? null : surgeryHistory,
      familyHistory: familyHistory.isEmpty ? null : familyHistory,
      lifestyleNotes: lifestyleNotes.isEmpty ? null : lifestyleNotes,
      pregnancyStatus: pregnancyStatus,
      medicalHistorySetupCompleted: medicalHistorySetupCompleted,
    );
    patientCareBundle = _copyCareBundle(patientCareBundle, patient: updated);
    return updated;
  }

  @override
  Future<PatientAllergyItem> createPatientAllergy({
    required String patientId,
    required String label,
    required String reaction,
    required String severity,
  }) async {
    patientAllergyCreated = true;
    final allergy = PatientAllergyItem(
      id: 'created-allergy-id',
      label: label,
      reaction: reaction.isEmpty ? null : reaction,
      severity: severity,
      status: 'active',
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      allergies: <PatientAllergyItem>[allergy, ...patientCareBundle.allergies],
    );
    return allergy;
  }

  @override
  Future<PatientAllergyItem> updatePatientAllergy({
    required String patientId,
    required String allergyId,
    required String label,
    required String reaction,
    required String severity,
    required String status,
  }) async {
    final allergy = PatientAllergyItem(
      id: allergyId,
      label: label,
      reaction: reaction.isEmpty ? null : reaction,
      severity: severity,
      status: status,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      allergies: <PatientAllergyItem>[
        allergy,
        ...patientCareBundle.allergies.where((item) => item.id != allergyId),
      ],
    );
    return allergy;
  }

  @override
  Future<MedicalRecordItem> createPatientMedicalRecord({
    required String patientId,
    required String title,
    required String category,
    required String summary,
  }) async {
    patientMedicalRecordCreated = true;
    final record = MedicalRecordItem(
      id: 'created-record-id',
      title: title,
      category: category,
      summary: summary,
      recordedAt: DateTime.parse('2026-07-09T00:00:00Z'),
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      records: <MedicalRecordItem>[record, ...patientCareBundle.records],
    );
    return record;
  }

  @override
  Future<ChronicDiseaseItem> createChronicDisease({
    required String patientId,
    required String name,
    required String notes,
  }) async {
    chronicDiseaseCreated = true;
    final condition = ChronicDiseaseItem(
      id: 'created-condition-id',
      name: name,
      status: 'active',
      diagnosedOn: null,
      notes: notes.isEmpty ? null : notes,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      chronicDiseases: <ChronicDiseaseItem>[
        condition,
        ...patientCareBundle.chronicDiseases,
      ],
    );
    return condition;
  }

  @override
  Future<ChronicDiseaseItem> updateChronicDisease({
    required String patientId,
    required String conditionId,
    required String name,
    required String notes,
    required String status,
  }) async {
    final condition = ChronicDiseaseItem(
      id: conditionId,
      name: name,
      status: status,
      diagnosedOn: null,
      notes: notes.isEmpty ? null : notes,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      chronicDiseases: <ChronicDiseaseItem>[
        condition,
        ...patientCareBundle.chronicDiseases.where(
          (item) => item.id != conditionId,
        ),
      ],
    );
    return condition;
  }

  @override
  Future<ClinicalEventItem> saveClinicalEvent({
    required String patientId,
    required String? clinicalEventId,
    required String title,
    required String chiefComplaint,
    required String symptomSummary,
    required String diagnosisSummary,
    required String onsetDate,
    required String status,
  }) async {
    clinicalEventSaved = true;
    lastClinicalEventId = clinicalEventId;
    final event = ClinicalEventItem(
      id: clinicalEventId ?? 'created-clinical-event-id',
      patientId: patientId,
      doctorId: 'doctor-profile-test-id',
      title: title,
      chiefComplaint: chiefComplaint,
      symptomSummary: symptomSummary.isEmpty ? null : symptomSummary,
      diagnosisSummary: diagnosisSummary.isEmpty ? null : diagnosisSummary,
      onsetDate: onsetDate.isEmpty ? null : onsetDate,
      status: status,
      linkedResourceCounts: const <String, int>{},
      createdAt: DateTime(2026, 7, 8, 11),
      updatedAt: DateTime(2026, 7, 8, 11),
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      clinicalEvents: <ClinicalEventItem>[
        event,
        ...patientCareBundle.clinicalEvents.where(
          (item) => item.id != event.id,
        ),
      ],
    );
    return event;
  }

  @override
  Future<ClinicalEventUpdateItem> submitClinicalEventUpdate({
    required String clinicalEventId,
    required String updateType,
    required String summary,
  }) async {
    clinicalEventUpdateSubmitted = true;
    final update = ClinicalEventUpdateItem(
      id: 'created-clinical-event-update-id',
      patientId: 'patient-profile-test-id',
      clinicalEventId: clinicalEventId,
      submittedByUserId: 'patient-user-test-id',
      updateType: updateType,
      summary: summary,
      occurredAt: DateTime(2026, 7, 8, 13),
      createdAt: DateTime(2026, 7, 8, 13),
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      clinicalEventUpdates: <ClinicalEventUpdateItem>[
        update,
        ...patientCareBundle.clinicalEventUpdates,
      ],
    );
    return update;
  }

  @override
  Future<MedicalHistoryReviewItem> createMedicalHistoryReview({
    required String patientId,
    required String targetType,
    required String targetId,
    required String action,
    required String amendmentSummary,
    required String correctionRequest,
  }) async {
    medicalHistoryReviewCreated = true;
    final review = MedicalHistoryReviewItem(
      id: 'created-medical-history-review-id',
      patientId: patientId,
      doctorId: 'doctor-profile-test-id',
      targetType: targetType,
      targetId: targetId,
      action: action,
      amendmentSummary: amendmentSummary.isEmpty ? null : amendmentSummary,
      correctionRequest: correctionRequest.isEmpty ? null : correctionRequest,
      createdAt: DateTime(2026, 7, 8, 13),
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      medicalHistoryReviews: <MedicalHistoryReviewItem>[
        review,
        ...patientCareBundle.medicalHistoryReviews,
      ],
    );
    return review;
  }

  @override
  Future<MedicationItem> saveMedication({
    required String patientId,
    required String? clinicalEventId,
    required String? medicationId,
    required String name,
    required String dosage,
    required String schedule,
    required String status,
    required String note,
    ClinicalFinancialDraft? financial,
  }) async {
    medicationSaved = true;
    lastMedicationFinancial = financial;
    final medication = MedicationItem(
      id: medicationId ?? 'created-medication-id',
      clinicalEventId: clinicalEventId,
      name: name,
      dosage: dosage,
      schedule: schedule,
      status: status,
      note: note,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      medications: <MedicationItem>[
        medication,
        ...patientCareBundle.medications.where(
          (item) => item.id != medication.id,
        ),
      ],
    );
    return medication;
  }

  @override
  Future<PrescriptionItem> createPrescription({
    required String patientId,
    required String? clinicalEventId,
    required String medicationId,
    required String name,
    required String dosage,
    required String schedule,
    required String notes,
    List<PrescriptionMedicationDraft>? lines,
  }) async {
    prescriptionCreated = true;
    final prescription = PrescriptionItem(
      id: 'created-prescription-id',
      clinicalEventId: clinicalEventId,
      status: 'issued',
      issuedAt: DateTime(2026, 7, 7, 12),
      notes: notes,
      medications: <PrescriptionMedicationItem>[
        PrescriptionMedicationItem(
          id: 'created-prescription-medication-id',
          medicationId: medicationId,
          name: name,
          dosage: dosage,
          schedule: schedule,
          startDate: null,
          endDate: null,
        ),
      ],
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      prescriptions: <PrescriptionItem>[
        prescription,
        ...patientCareBundle.prescriptions,
      ],
    );
    return prescription;
  }

  @override
  Future<MedicationReminderItem> saveMedicationReminder({
    required String patientId,
    required String? reminderId,
    required String? medicationId,
    required String? prescriptionMedicationId,
    required String reminderType,
    required String scheduleLabel,
    required String status,
    required DateTime? nextDueAt,
  }) async {
    medicationReminderSaved = true;
    final reminder = MedicationReminderItem(
      id: reminderId ?? 'created-$reminderType-reminder-id',
      reminderType: reminderType,
      scheduleLabel: scheduleLabel,
      channel: 'in_app',
      status: status,
      medicationId: medicationId,
      prescriptionMedicationId: prescriptionMedicationId,
      nextDueAt: nextDueAt,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      medicationReminders: <MedicationReminderItem>[
        reminder,
        ...patientCareBundle.medicationReminders.where(
          (item) => item.id != reminder.id,
        ),
      ],
    );
    return reminder;
  }

  @override
  Future<DemoAssetPresign> presignDemoAsset({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    if (presignError != null) {
      throw presignError!;
    }
    return demoPresign;
  }

  @override
  Future<MedicalImagingPresign> presignMedicalImaging({
    required String patientId,
    required String? clinicalEventId,
    String? clinicalServiceId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    if (imagingError != null) {
      throw imagingError!;
    }
    imagingPrepared = true;
    lastImagingClinicalServiceId = clinicalServiceId;
    return demoImagingPresign;
  }

  @override
  Future<ClinicalServiceItem> saveClinicalService({
    required String patientId,
    required String? serviceId,
    required String clinicalEventId,
    required String category,
    required String name,
    required String serviceSubtype,
    required String? bodyRegion,
    required String status,
    required DateTime? scheduledAt,
    required DateTime? performedAt,
    required String indicationSummary,
    ClinicalFinancialDraft? financial,
  }) async {
    clinicalServiceSaved = true;
    final service = ClinicalServiceItem(
      id: serviceId ?? 'clinical-service-test-id',
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      category: category,
      name: name,
      serviceSubtype: serviceSubtype,
      bodyRegion: bodyRegion,
      orderedByDoctorId: 'doctor-profile-test-id',
      status: status,
      orderedAt: DateTime(2026, 7, 24),
      scheduledAt: scheduledAt,
      performedAt: performedAt,
      indicationSummary: indicationSummary,
      imagingAssetIds: const <String>[],
      createdAt: DateTime(2026, 7, 24),
      updatedAt: DateTime(2026, 7, 24),
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      clinicalServices: <ClinicalServiceItem>[
        service,
        ...patientCareBundle.clinicalServices.where(
          (item) => item.id != service.id,
        ),
      ],
    );
    return service;
  }

  @override
  Future<MedicalImagingAsset> uploadMedicalImagingBytes({
    required String patientId,
    required String assetId,
    required String contentType,
    required List<int> bytes,
  }) async {
    if (imagingError != null) throw imagingError!;
    return demoImagingUploaded;
  }

  @override
  Future<List<int>> downloadMedicalImagingBytes({
    required String patientId,
    required String assetId,
  }) async {
    if (imagingError != null) throw imagingError!;
    return List<int>.filled(demoImagingUploaded.sizeBytes, 7);
  }

  @override
  Future<CareCostItemData> updateClinicalServiceFinancial({
    required String patientId,
    required String serviceId,
    required ClinicalFinancialDraft financial,
  }) async {
    clinicalServiceFinancialUpdates += 1;
    return CareCostItemData(
      id: 'imaging-cost-test-id',
      clinicalEventId: 'clinical-event-test-id',
      itemType: 'imaging',
      label: 'CT chest',
      serviceDate: financial.serviceDate ?? DateTime(2026, 7, 24),
      status: 'scheduled',
      pricingState: financial.pricingState,
      sourceType: 'imaging',
      sourceRecordId: serviceId,
      submissionEligible: financial.pricingState != 'pending_cost',
      quantity: 1,
      currency: 'CNY',
      actualCostMinor: financial.totalCostMinor,
      payerRequestedMinor: financial.payerRequestedMinor,
      patientResponsibilityMinor: financial.patientResponsibilityMinor,
      aiReviewStatus: 'not_evaluated',
      createdAt: DateTime(2026, 7, 24),
      updatedAt: DateTime(2026, 7, 24),
    );
  }

  @override
  Future<MedicalImagingAsset> completeMedicalImagingUpload({
    required String patientId,
    required String assetId,
    required int uploadedSizeBytes,
  }) async {
    if (imagingError != null) {
      throw imagingError!;
    }
    imagingCompleted = true;
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      imagingAssets: <MedicalImagingAsset>[
        demoImagingUploaded,
        ...patientCareBundle.imagingAssets.where(
          (item) => item.id != demoImagingUploaded.id,
        ),
      ],
    );
    return demoImagingUploaded;
  }

  @override
  Future<MedicalImagingAsset> reviewMedicalImagingAsset({
    required String patientId,
    required String assetId,
    required String reviewStatus,
    required String findingSummary,
    required String measurementSummary,
  }) async {
    if (imagingError != null) {
      throw imagingError!;
    }
    imagingReviewed = true;
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      imagingAssets: <MedicalImagingAsset>[
        demoImagingReviewed,
        ...patientCareBundle.imagingAssets.where(
          (item) => item.id != demoImagingReviewed.id,
        ),
      ],
    );
    return demoImagingReviewed;
  }

  @override
  Future<AssessmentListData> loadAssessments(String patientId) async {
    if (assessmentError != null) {
      throw assessmentError!;
    }
    return assessments;
  }

  @override
  Future<AssessmentResult> createSimulatedAssessment({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  }) async {
    if (assessmentError != null) {
      throw assessmentError!;
    }
    assessments = AssessmentListData(
      items: <AssessmentResult>[demoAssessment, ...assessments.items],
    );
    return demoAssessment;
  }

  @override
  Future<RecoveryPlanListData> loadRecoveryPlans(String patientId) async {
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
    return recoveryPlans;
  }

  @override
  Future<RecoveryPlanData> createRecoveryPlan({
    required String patientId,
    required String? clinicalEventId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
    required List<RecoveryPhaseInput> phases,
  }) async {
    recoveryPlanSaveCallCount += 1;
    if (recoveryPlanSaveError != null) {
      throw recoveryPlanSaveError!;
    }
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
    lastRecoveryPhases = phases;
    final plan = _planFromInput(
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      planId: 'created-recovery-plan-id',
      title: title,
      instructions: instructions,
      status: 'draft',
      tasks: tasks,
    );
    recoveryPlans = RecoveryPlanListData(
      items: <RecoveryPlanData>[plan, ...recoveryPlans.items],
    );
    return plan;
  }

  @override
  Future<RecoveryPlanData> updateRecoveryPlan({
    required String patientId,
    required String? clinicalEventId,
    required String planId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
    required List<RecoveryPhaseInput> phases,
  }) async {
    recoveryPlanSaveCallCount += 1;
    if (recoveryPlanSaveError != null) {
      throw recoveryPlanSaveError!;
    }
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
    lastRecoveryPhases = phases;
    final plan = _planFromInput(
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      planId: planId,
      title: title,
      instructions: instructions,
      status: 'draft',
      tasks: tasks,
    );
    recoveryPlans = RecoveryPlanListData(
      items: <RecoveryPlanData>[
        plan,
        ...recoveryPlans.items.where((item) => item.planId != planId),
      ],
    );
    return plan;
  }

  @override
  Future<RecoveryPlanData> activateRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
    final current = recoveryPlans.items.firstWhere(
      (item) => item.planId == planId,
      orElse: () => demoRecoveryPlan,
    );
    final active = RecoveryPlanData(
      planId: current.planId,
      patientId: current.patientId,
      clinicalEventId: current.clinicalEventId,
      title: current.title,
      instructions: current.instructions,
      status: 'active',
      reviewStatus: 'approved',
      safetyLabel: current.safetyLabel,
      createdAt: current.createdAt,
      updatedAt: DateTime(2026, 7, 5, 12),
      submittedAt: current.submittedAt ?? DateTime(2026, 7, 5, 12),
      reviewedAt: DateTime(2026, 7, 5, 12),
      approvedAt: DateTime(2026, 7, 5, 12),
      activatedAt: DateTime(2026, 7, 5, 12),
      progressSummary: _progressForTasks(current.tasks),
      tasks: current.tasks,
    );
    recoveryPlans = RecoveryPlanListData(
      items: <RecoveryPlanData>[
        active,
        ...recoveryPlans.items.where((item) => item.planId != planId),
      ],
    );
    patientToday = PatientTodayData(
      safetyLabel: patientToday.safetyLabel,
      activePlan: active,
      progressSummary: active.progressSummary,
      tasks: active.tasks,
    );
    return active;
  }

  @override
  Future<RecoveryPlanData> submitRecoveryPlanForReview({
    required String patientId,
    required String planId,
    required int expectedVersion,
  }) async {
    final current = _currentRecoveryPlan(planId);
    final submitted = _copyPlan(
      current,
      reviewStatus: 'in_review',
      submittedAt: DateTime(2026, 7, 5, 12),
    );
    _replacePlan(submitted);
    return submitted;
  }

  @override
  Future<RecoveryPlanData> requestRecoveryPlanChanges({
    required String patientId,
    required String planId,
    required int expectedVersion,
    required String comment,
  }) async {
    final current = _currentRecoveryPlan(planId);
    final changed = _copyPlan(
      current,
      reviewStatus: 'changes_requested',
      reviewedAt: DateTime(2026, 7, 5, 12, 30),
    );
    _replacePlan(changed);
    return changed;
  }

  @override
  Future<RecoveryPlanData> approveRecoveryPlan({
    required String patientId,
    required String planId,
    required int expectedVersion,
    String? comment,
  }) async {
    return activateRecoveryPlan(patientId: patientId, planId: planId);
  }

  @override
  Future<RecoveryPlanData> completeRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    final current = _currentRecoveryPlan(planId);
    final completed = _copyPlan(
      current,
      status: 'completed',
      completedAt: DateTime(2026, 7, 5, 13),
    );
    _replacePlan(completed);
    return completed;
  }

  @override
  Future<PatientTodayData> loadPatientToday() async {
    if (patientTodayError != null) {
      throw patientTodayError!;
    }
    return patientToday;
  }

  @override
  Future<RecoveryTaskItem> completeRecoveryTask(String taskId) async {
    if (completionError != null) {
      throw completionError!;
    }
    final updatedTasks = patientToday.tasks.map((task) {
      if (task.taskId != taskId) {
        return task;
      }
      return RecoveryTaskItem(
        taskId: task.taskId,
        planId: task.planId,
        category: task.category,
        title: task.title,
        detail: task.detail,
        dueLabel: task.dueLabel,
        notificationTime: task.notificationTime,
        medicationId: task.medicationId,
        isCompleted: true,
        completedAt: DateTime(2026, 7, 5, 12),
        notificationStatus: task.notificationStatus,
      );
    }).toList();
    patientToday = PatientTodayData(
      safetyLabel: patientToday.safetyLabel,
      activePlan: patientToday.activePlan,
      progressSummary: _progressForTasks(updatedTasks),
      tasks: updatedTasks,
    );
    _syncPatientCareRecoveryPlan(updatedTasks);
    return updatedTasks.firstWhere((task) => task.taskId == taskId);
  }

  @override
  Future<RecoveryTaskItem> uncompleteRecoveryTask(String taskId) async {
    if (completionError != null) {
      throw completionError!;
    }
    final updatedTasks = patientToday.tasks.map((task) {
      if (task.taskId != taskId) {
        return task;
      }
      return RecoveryTaskItem(
        taskId: task.taskId,
        planId: task.planId,
        category: task.category,
        title: task.title,
        detail: task.detail,
        dueLabel: task.dueLabel,
        notificationTime: task.notificationTime,
        medicationId: task.medicationId,
        isCompleted: false,
        completedAt: null,
        notificationStatus: task.notificationStatus,
      );
    }).toList();
    patientToday = PatientTodayData(
      safetyLabel: patientToday.safetyLabel,
      activePlan: patientToday.activePlan,
      progressSummary: _progressForTasks(updatedTasks),
      tasks: updatedTasks,
    );
    _syncPatientCareRecoveryPlan(updatedTasks);
    return updatedTasks.firstWhere((task) => task.taskId == taskId);
  }

  void _syncPatientCareRecoveryPlan(List<RecoveryTaskItem> tasks) {
    final activePlan = patientToday.activePlan;
    if (activePlan == null) return;
    final updatedPlan = RecoveryPlanData(
      planId: activePlan.planId,
      patientId: activePlan.patientId,
      clinicalEventId: activePlan.clinicalEventId,
      title: activePlan.title,
      instructions: activePlan.instructions,
      status: activePlan.status,
      reviewStatus: activePlan.reviewStatus,
      safetyLabel: activePlan.safetyLabel,
      createdAt: activePlan.createdAt,
      updatedAt: activePlan.updatedAt,
      submittedAt: activePlan.submittedAt,
      reviewedAt: activePlan.reviewedAt,
      approvedAt: activePlan.approvedAt,
      activatedAt: activePlan.activatedAt,
      completedAt: activePlan.completedAt,
      progressSummary: _progressForTasks(tasks),
      tasks: tasks,
    );
    patientToday = PatientTodayData(
      safetyLabel: patientToday.safetyLabel,
      activePlan: updatedPlan,
      progressSummary: updatedPlan.progressSummary,
      tasks: tasks,
    );
    patientCareBundle = _copyCareBundle(
      patientCareBundle,
      recoveryPlans: patientCareBundle.recoveryPlans
          .map((plan) => plan.planId == updatedPlan.planId ? updatedPlan : plan)
          .toList(),
    );
  }

  @override
  Future<DoctorPatientContactList> loadOwnDoctorContacts() async {
    return const DoctorPatientContactList(items: <DoctorPatientContact>[]);
  }

  @override
  Future<PrivateMessageList> loadPrivateMessages(String contactId) async {
    return const PrivateMessageList(items: <PrivateMessage>[], threadId: null);
  }

  @override
  Future<PrivateMessage> sendPrivateMessage(
    String contactId,
    String message,
  ) async {
    return PrivateMessage(
      messageId: 'private-message-test-id',
      threadId: 'private-thread-test-id',
      senderUserId: 'sender-test-id',
      senderRole: 'patient',
      content: message,
      createdAt: DateTime.utc(2026, 7, 11),
    );
  }

  @override
  Future<ChatMessageResult> sendEducationalChatMessage({
    String? threadId,
    required String message,
    String language = 'zh-Hans',
  }) async {
    if (chatError != null) {
      throw chatError!;
    }
    chatMessagesSent += 1;
    lastChatMessage = message;
    return chatResult;
  }

  @override
  Future<PatientChatThreadSummary> createEducationalChatThread(
    String title,
  ) async {
    final now = DateTime.utc(2026, 7, 27);
    final thread = PatientChatThreadSummary(
      threadId: 'created-chat-thread-id',
      title: title,
      status: 'active',
      createdAt: now,
      lastMessageAt: now,
      retentionUntil: now.add(const Duration(days: 60)),
    );
    chatThreads = <PatientChatThreadSummary>[thread, ...chatThreads];
    return thread;
  }

  @override
  Future<List<PatientChatThreadSummary>> loadEducationalChatThreads({
    bool includeArchived = false,
  }) async {
    return chatThreads
        .where((thread) => includeArchived || !thread.isArchived)
        .toList();
  }

  @override
  Future<PatientChatHistory> loadEducationalChatThread(String threadId) async {
    throw StateError('No fake chat history for $threadId.');
  }

  @override
  Future<PatientChatThreadSummary> archiveEducationalChatThread(
    String threadId,
  ) async {
    final current = chatThreads.firstWhere(
      (thread) => thread.threadId == threadId,
    );
    final archived = PatientChatThreadSummary(
      threadId: current.threadId,
      title: current.title,
      status: 'archived',
      createdAt: current.createdAt,
      lastMessageAt: current.lastMessageAt,
      retentionUntil: current.retentionUntil,
      archivedAt: DateTime.utc(2026, 7, 27),
    );
    chatThreads = chatThreads
        .map((thread) => thread.threadId == threadId ? archived : thread)
        .toList();
    return archived;
  }

  @override
  Future<PatientChatThreadSummary> reopenEducationalChatThread(
    String threadId,
  ) async {
    final current = chatThreads.firstWhere(
      (thread) => thread.threadId == threadId,
    );
    final reopened = PatientChatThreadSummary(
      threadId: current.threadId,
      title: current.title,
      status: 'active',
      createdAt: current.createdAt,
      lastMessageAt: current.lastMessageAt,
      retentionUntil: current.retentionUntil,
    );
    chatThreads = chatThreads
        .map((thread) => thread.threadId == threadId ? reopened : thread)
        .toList();
    return reopened;
  }

  @override
  Future<void> deleteEducationalChatThread(String threadId) async {
    chatThreads = chatThreads
        .where((thread) => thread.threadId != threadId)
        .toList();
  }

  @override
  Future<ConsultationListData> loadConsultations() async {
    if (consultationError != null) {
      throw consultationError!;
    }
    return consultations;
  }

  @override
  Future<ConsultationRequestItem> createConsultation({
    required String patientId,
    required String? clinicalEventId,
    required String specialty,
    required String questionSummary,
    required String priority,
    ClinicalFinancialDraft? financial,
  }) async {
    if (consultationError != null) {
      throw consultationError!;
    }
    lastConsultationFinancial = financial;
    final request = ConsultationRequestItem(
      consultationId: 'created-consultation-id',
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      clinicalServiceId: 'created-consultation-service-id',
      specialty: specialty,
      questionSummary: questionSummary,
      priority: priority,
      status: 'requested',
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
      createdAt: DateTime(2026, 7, 5, 12),
      updatedAt: DateTime(2026, 7, 5, 12),
      consultationType: 'specialist_referral',
    );
    consultations = ConsultationListData(
      items: <ConsultationRequestItem>[request, ...consultations.items],
    );
    return request;
  }

  @override
  Future<ConsultationRequestItem> createClinicalEventConsultation({
    required String patientId,
    required String clinicalEventId,
    required String specialty,
    required String consultationType,
    required String status,
    required String clinicianProvider,
    required String serviceDate,
    required String reasonIndication,
    required String outcomeSummary,
    required String followUpRequirement,
    required int quantity,
    required String idempotencyKey,
    ClinicalFinancialDraft? financial,
  }) async {
    lastConsultationFinancial = financial;
    final request = ConsultationRequestItem(
      consultationId: 'clinical-event-consultation-id',
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      clinicalServiceId: 'clinical-event-consultation-service-id',
      specialty: specialty,
      questionSummary: reasonIndication,
      priority: 'routine',
      status: status,
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
      createdAt: DateTime(2026, 8, 2, 12),
      updatedAt: DateTime(2026, 8, 2, 12),
      consultationType: consultationType,
      clinicianProvider: clinicianProvider,
      serviceDate: serviceDate,
      reasonIndication: reasonIndication,
      outcomeSummary: <String, dynamic>{'summary': outcomeSummary},
      followUpRequirement: followUpRequirement,
      quantity: quantity,
    );
    consultations = ConsultationListData(
      items: <ConsultationRequestItem>[request, ...consultations.items],
    );
    return request;
  }

  @override
  Future<VisitHistoryItem> createVisitHistory({
    required String patientId,
    required String clinicalEventId,
    required String visitType,
    required String title,
    required String summary,
    required DateTime occurredAt,
    required String clinicianLabel,
  }) async {
    final item = VisitHistoryItem(
      id: 'created-visit-history-id',
      clinicalEventId: clinicalEventId,
      visitType: visitType,
      title: title,
      summary: summary,
      occurredAt: occurredAt,
      clinicianLabel: clinicianLabel,
    );
    patientCareBundle = patientCareBundle.copyWith(
      visitHistory: <VisitHistoryItem>[item, ...patientCareBundle.visitHistory],
    );
    return item;
  }

  @override
  Future<DiagnosisItem> createDiagnosis({
    required String patientId,
    required String clinicalEventId,
    required String label,
    required String status,
    required String diagnosedOn,
    required String notes,
  }) async {
    final item = DiagnosisItem(
      id: 'created-diagnosis-id',
      clinicalEventId: clinicalEventId,
      label: label,
      status: status,
      diagnosedOn: diagnosedOn,
      notes: notes,
    );
    patientCareBundle = patientCareBundle.copyWith(
      diagnoses: <DiagnosisItem>[item, ...patientCareBundle.diagnoses],
    );
    return item;
  }

  @override
  Future<CareCostItemData> updateConsultationFinancial({
    required String patientId,
    required String consultationId,
    required ClinicalFinancialDraft financial,
  }) async {
    if (consultationError != null) {
      throw consultationError!;
    }
    lastConsultationFinancial = financial;
    consultationFinancialUpdates += 1;
    return CareCostItemData(
      id: 'consultation-cost-item-test-id',
      clinicalEventId: 'clinical-event-test-id',
      itemType: 'consultation',
      label: 'Cardiology consultation',
      serviceDate: DateTime(2026, 7, 24),
      status: 'scheduled',
      pricingState: financial.pricingState,
      sourceType: 'consultation',
      sourceRecordId: consultationId,
      submissionEligible: financial.pricingState != 'pending_cost',
      quantity: 1,
      currency: 'CNY',
      actualCostMinor: financial.totalCostMinor,
      payerRequestedMinor: financial.payerRequestedMinor,
      patientResponsibilityMinor: financial.patientResponsibilityMinor,
      aiReviewStatus: 'not_evaluated',
      createdAt: DateTime(2026, 7, 24),
      updatedAt: DateTime(2026, 7, 24),
    );
  }

  @override
  Future<CareCostLedgerData> loadOwnCareCosts() async {
    if (careCostError != null) throw careCostError!;
    if (careCostCompleter != null) return careCostCompleter!.future;
    return careCostLedger;
  }

  @override
  Future<CareCostLedgerData> loadPatientCareCosts(String patientId) async {
    if (careCostError != null) throw careCostError!;
    return _copyLedgerPatient(careCostLedger, patientId);
  }

  @override
  Future<CareCostItemData> saveCareCostItem({
    required String patientId,
    required String clinicalEventId,
    String? itemId,
    required String itemType,
    required String label,
    required DateTime serviceDate,
    required String status,
    required int quantity,
    required int actualCostMinor,
    required int payerRequestedMinor,
    required int patientResponsibilityMinor,
    String? notes,
  }) async {
    return CareCostItemData(
      id: itemId ?? 'care-cost-item-test-id',
      clinicalEventId: clinicalEventId,
      itemType: itemType,
      label: label,
      serviceDate: serviceDate,
      status: status,
      pricingState: 'final',
      sourceType: 'medication',
      sourceRecordId: 'created-medication-id',
      submissionEligible: true,
      quantity: quantity,
      currency: 'CNY',
      actualCostMinor: actualCostMinor,
      payerRequestedMinor: payerRequestedMinor,
      patientResponsibilityMinor: patientResponsibilityMinor,
      aiReviewStatus: 'not_evaluated',
      notes: notes,
      createdAt: DateTime(2026, 7, 23),
      updatedAt: DateTime(2026, 7, 23),
    );
  }

  @override
  Future<void> deleteCareCostItem({
    required String patientId,
    required String clinicalEventId,
    required String itemId,
  }) async {}

  @override
  Future<List<PayerOrganizationData>> loadPayerOrganizations() async {
    return <PayerOrganizationData>[_fakeOrganization()];
  }

  @override
  Future<PayerRequestData> createPayerRequest({
    required String patientId,
    required String clinicalEventId,
    required String payerOrganizationId,
    required List<String> careCostItemIds,
    required String doctorSummary,
  }) async {
    payerRequestCreated = true;
    lastPayerRequestItemIds = List<String>.from(careCostItemIds);
    final request = _fakePayerRequest(
      patientId: patientId,
      summary: doctorSummary,
    );
    _payerRequests.insert(0, request);
    return request;
  }

  @override
  Future<List<PayerRequestData>> loadDoctorPayerRequests() async {
    return List<PayerRequestData>.unmodifiable(_payerRequests);
  }

  @override
  Future<List<PayerRequestData>> loadOwnPatientPayerRequests() async {
    return <PayerRequestData>[_fakePayerRequest()];
  }

  @override
  Future<PayerDashboardData> loadPayerDashboard() async {
    payerDashboardLoadCount += 1;
    return PayerDashboardData(
      profile: await loadPayerProfile(),
      openRequests: 1,
      clarificationRequests: 0,
      escalatedRequests: 1,
      completedReviews: 2,
      pendingRequestedTotalMinor: 50000,
      currency: 'CNY',
    );
  }

  @override
  Future<PayerProfileData> loadPayerProfile() async {
    payerProfileLoadCount += 1;
    return _payerProfile;
  }

  @override
  Future<PayerProfileData> updatePayerProfile({
    required String displayName,
    required String title,
  }) async {
    if (payerProfileUpdateError != null) {
      throw payerProfileUpdateError!;
    }
    payerProfileUpdated = true;
    payerProfileUpdateCount += 1;
    _payerProfile = PayerProfileData(
      membershipId: _payerProfile.membershipId,
      displayName: displayName,
      title: title,
      status: _payerProfile.status,
      scope: _payerProfile.scope,
      organization: _payerProfile.organization,
    );
    return _payerProfile;
  }

  @override
  Future<List<PayerRequestData>> loadPayerRequests() async {
    return List<PayerRequestData>.unmodifiable(_payerRequests);
  }

  @override
  Future<PayerRequestData> reviewPayerRequest({
    required String requestId,
    required String action,
    required String reasonCode,
    required int expectedVersion,
    required String idempotencyKey,
    String? clarificationMessage,
    String? note,
  }) async {
    payerReviewCallCount += 1;
    lastPayerClarificationMessage = clarificationMessage;
    lastPayerPrivateNote = note;
    final status = switch (action) {
      'accept' => 'accepted',
      'reject' => 'rejected',
      'request_clarification' => 'clarification_requested',
      'escalate' => 'escalated',
      'close' => 'closed',
      _ => action,
    };
    return _fakePayerRequest(status: status);
  }

  @override
  Future<PayerRequestData> appendDoctorPayerResponse({
    required String requestId,
    required int expectedVersion,
    required String responseType,
    required String summary,
    required String idempotencyKey,
    String? baselineId,
    String? comparisonId,
  }) async {
    return _fakePayerRequest();
  }

  static CareCostLedgerData _defaultCareCostLedger() {
    final item = CareCostItemData(
      id: 'care-cost-item-test-id',
      clinicalEventId: 'clinical-event-test-id',
      itemType: 'medication',
      label: 'Inhaled medication',
      serviceDate: DateTime(2026, 7, 23),
      status: 'completed',
      pricingState: 'final',
      sourceType: 'medication',
      sourceRecordId: 'medication-test-id',
      submissionEligible: true,
      quantity: 1,
      currency: 'CNY',
      actualCostMinor: 68000,
      payerRequestedMinor: 50000,
      patientResponsibilityMinor: 18000,
      aiReviewStatus: 'not_evaluated',
      createdAt: DateTime(2026, 7, 23),
      updatedAt: DateTime(2026, 7, 23),
    );
    return CareCostLedgerData(
      patientId: 'patient-profile-test-id',
      patientDisplayName: 'Riley Demo Patient',
      actualTotalMinor: 68000,
      estimatedTotalMinor: 0,
      finalTotalMinor: 68000,
      payerRequestedTotalMinor: 50000,
      patientResponsibilityTotalMinor: 18000,
      pendingCostItemCount: 0,
      currency: 'CNY',
      events: <CareCostEventData>[
        CareCostEventData(
          clinicalEventId: 'clinical-event-test-id',
          title: 'Respiratory follow-up',
          status: 'active',
          actualTotalMinor: 68000,
          payerRequestedTotalMinor: 50000,
          patientResponsibilityTotalMinor: 18000,
          currency: 'CNY',
          items: <CareCostItemData>[item],
        ),
      ],
    );
  }

  static CareCostLedgerData _copyLedgerPatient(
    CareCostLedgerData ledger,
    String patientId,
  ) {
    return CareCostLedgerData(
      patientId: patientId,
      patientDisplayName: ledger.patientDisplayName,
      actualTotalMinor: ledger.actualTotalMinor,
      estimatedTotalMinor: ledger.estimatedTotalMinor,
      finalTotalMinor: ledger.finalTotalMinor,
      payerRequestedTotalMinor: ledger.payerRequestedTotalMinor,
      patientResponsibilityTotalMinor: ledger.patientResponsibilityTotalMinor,
      pendingCostItemCount: ledger.pendingCostItemCount,
      currency: ledger.currency,
      events: ledger.events,
    );
  }

  PayerOrganizationData _fakeOrganization() {
    return const PayerOrganizationData(
      id: 'payer-organization-test-id',
      name: 'Synthetic Municipal Medical Insurance',
      organizationType: 'public_payer',
      jurisdictionCode: 'CN',
      verificationStatus: 'synthetic_only',
    );
  }

  PayerRequestData _fakePayerRequest({
    String patientId = 'patient-profile-test-id',
    String summary = 'Clinician-reviewed synthetic care request.',
    String status = 'submitted',
  }) {
    return payerRequestFixture(
      patientId: patientId,
      summary: summary,
      status: status,
      organization: _fakeOrganization(),
    );
  }

  static PayerRequestData payerRequestFixture({
    String id = 'payer-request-test-id',
    String patientId = 'patient-profile-test-id',
    String clinicalEventTitle = 'Respiratory follow-up',
    String summary = 'Clinician-reviewed synthetic care request.',
    String status = 'submitted',
    DateTime? reviewedAt,
    List<PayerReviewData> reviews = const <PayerReviewData>[],
    PayerReviewSignalsData? reviewSignals,
    PayerOrganizationData organization = const PayerOrganizationData(
      id: 'payer-organization-test-id',
      name: 'Synthetic Municipal Medical Insurance',
      organizationType: 'public_payer',
      jurisdictionCode: 'CN',
      verificationStatus: 'synthetic_only',
    ),
  }) {
    return PayerRequestData(
      id: id,
      clinicalEventId: 'clinical-event-test-id',
      clinicalEventTitle: clinicalEventTitle,
      patientId: patientId,
      patientDisplayName: 'Riley Demo Patient',
      doctorDisplayName: 'Dr. Avery Demo',
      payerOrganization: organization,
      status: status,
      currency: 'CNY',
      requestedTotalMinor: 50000,
      doctorSummary: summary,
      aiReviewStatus: 'not_evaluated',
      reviewSignals: reviewSignals,
      createdAt: DateTime(2026, 7, 23),
      reviewedAt: reviewedAt,
      lines: <PayerRequestLineData>[
        PayerRequestLineData(
          id: 'payer-request-line-test-id',
          careCostItemId: 'care-cost-item-test-id',
          itemType: 'imaging',
          label: 'Chest CT review',
          serviceDate: DateTime(2026, 7, 23),
          currency: 'CNY',
          actualCostMinor: 68000,
          requestedMinor: 50000,
          patientResponsibilityMinor: 18000,
        ),
      ],
      reviews: reviews,
    );
  }

  RecoveryPlanData _planFromInput({
    required String patientId,
    required String? clinicalEventId,
    required String planId,
    required String title,
    required String instructions,
    required String status,
    required List<RecoveryTaskInput> tasks,
  }) {
    return RecoveryPlanData(
      planId: planId,
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      title: title,
      instructions: instructions,
      status: status,
      reviewStatus: 'draft',
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
      createdAt: DateTime(2026, 7, 5, 12),
      updatedAt: DateTime(2026, 7, 5, 12),
      progressSummary: RecoveryPlanProgressData(
        taskCount: tasks.length,
        completedTaskCount: 0,
        remainingTaskCount: tasks.length,
        completionPercent: 0,
      ),
      tasks: tasks
          .map(
            (task) => RecoveryTaskItem(
              taskId: 'task-${task.category}',
              planId: planId,
              category: task.category,
              title: task.title,
              detail: task.detail,
              dueLabel: task.dueLabel,
              notificationTime: task.notificationTime,
              medicationId: task.medicationId,
              isCompleted: false,
            ),
          )
          .toList(),
    );
  }

  RecoveryPlanData _currentRecoveryPlan(String planId) {
    return recoveryPlans.items.firstWhere(
      (item) => item.planId == planId,
      orElse: () => demoRecoveryPlan,
    );
  }

  void _replacePlan(RecoveryPlanData plan) {
    recoveryPlans = RecoveryPlanListData(
      items: <RecoveryPlanData>[
        plan,
        ...recoveryPlans.items.where((item) => item.planId != plan.planId),
      ],
    );
  }

  RecoveryPlanData _copyPlan(
    RecoveryPlanData current, {
    String? status,
    String? reviewStatus,
    DateTime? submittedAt,
    DateTime? reviewedAt,
    DateTime? approvedAt,
    DateTime? activatedAt,
    DateTime? completedAt,
  }) {
    return RecoveryPlanData(
      planId: current.planId,
      patientId: current.patientId,
      clinicalEventId: current.clinicalEventId,
      title: current.title,
      instructions: current.instructions,
      status: status ?? current.status,
      reviewStatus: reviewStatus ?? current.reviewStatus,
      safetyLabel: current.safetyLabel,
      createdAt: current.createdAt,
      updatedAt: DateTime(2026, 7, 5, 12),
      submittedAt: submittedAt ?? current.submittedAt,
      reviewedAt: reviewedAt ?? current.reviewedAt,
      approvedAt: approvedAt ?? current.approvedAt,
      activatedAt: activatedAt ?? current.activatedAt,
      completedAt: completedAt ?? current.completedAt,
      progressSummary: _progressForTasks(current.tasks),
      tasks: current.tasks,
    );
  }

  RecoveryPlanProgressData _progressForTasks(List<RecoveryTaskItem> tasks) {
    final completed = tasks.where((task) => task.isCompleted).length;
    final percent = tasks.isEmpty
        ? 0
        : (completed * 100 / tasks.length).round();
    return RecoveryPlanProgressData(
      taskCount: tasks.length,
      completedTaskCount: completed,
      remainingTaskCount: tasks.length - completed,
      completionPercent: percent,
    );
  }
}

PatientCareBundle _copyCareBundle(
  PatientCareBundle bundle, {
  PatientProfile? patient,
  List<MedicationItem>? medications,
  List<ClinicalEventItem>? clinicalEvents,
  List<ClinicalServiceItem>? clinicalServices,
  List<ClinicalEventUpdateItem>? clinicalEventUpdates,
  List<MedicalHistoryReviewItem>? medicalHistoryReviews,
  List<PatientAllergyItem>? allergies,
  List<ChronicDiseaseItem>? chronicDiseases,
  List<MedicalRecordItem>? records,
  List<MedicalImagingAsset>? imagingAssets,
  List<PrescriptionItem>? prescriptions,
  List<MedicationReminderItem>? medicationReminders,
  List<RecoveryPlanData>? recoveryPlans,
}) {
  return PatientCareBundle(
    patient: patient ?? bundle.patient,
    clinicalEvents: clinicalEvents ?? bundle.clinicalEvents,
    clinicalServices: clinicalServices ?? bundle.clinicalServices,
    clinicalEventUpdates: clinicalEventUpdates ?? bundle.clinicalEventUpdates,
    medicalHistoryReviews:
        medicalHistoryReviews ?? bundle.medicalHistoryReviews,
    allergies: allergies ?? bundle.allergies,
    chronicDiseases: chronicDiseases ?? bundle.chronicDiseases,
    visitHistory: bundle.visitHistory,
    diagnoses: bundle.diagnoses,
    records: records ?? bundle.records,
    imagingAssets: imagingAssets ?? bundle.imagingAssets,
    medications: medications ?? bundle.medications,
    prescriptions: prescriptions ?? bundle.prescriptions,
    medicationReminders: medicationReminders ?? bundle.medicationReminders,
    recoveryPlans: recoveryPlans ?? bundle.recoveryPlans,
    doctorNotes: bundle.doctorNotes,
  );
}

NotificationInboxItem _copyNotification(
  NotificationInboxItem item, {
  required String status,
  DateTime? readAt,
  bool clearReadAt = false,
  DateTime? dismissedAt,
  required int version,
}) {
  return NotificationInboxItem(
    id: item.id,
    eventType: item.eventType,
    severity: item.severity,
    category: item.category,
    status: status,
    title: item.title,
    body: item.body,
    actorKind: item.actorKind,
    occurredAt: item.occurredAt,
    scheduledFor: item.scheduledFor,
    deliveryState: item.deliveryState,
    readAt: clearReadAt ? null : readAt ?? item.readAt,
    dismissedAt: dismissedAt ?? item.dismissedAt,
    expiresAt: item.expiresAt,
    supersededAt: item.supersededAt,
    canDismiss: item.canDismiss,
    canMarkUnread: status == 'read',
    deepLinkAvailable: item.deepLinkAvailable,
    version: version,
  );
}
