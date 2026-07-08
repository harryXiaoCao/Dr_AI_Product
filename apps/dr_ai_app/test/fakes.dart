import 'dart:async';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
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

const patientSession = AuthSession(
  accessToken: 'test-access',
  refreshToken: 'test-refresh',
  user: patientUser,
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
      'AI Supported CT Image Diagnose',
      'AI Supported X-ray Image Diagnose',
      'AI Supported MRI Image Diagnose',
      'Check Patient Medical Records',
      'Check Patient Recovery Plans',
      'Check Imaging Results',
      'Book Medical Equipment',
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
    'fee_items': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Consultation',
        'amount': '10 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Blood Test',
        'amount': '50 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Medication',
        'amount': '120 demo credits',
        'selected': true,
      },
      <String, dynamic>{
        'label': 'Ambulance Service',
        'amount': '50 demo credits',
        'selected': false,
      },
    ],
    'medical_records': <Object>[],
    'imaging_results': <Object>[],
  },
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
    birthYear: 1988,
    sex: 'not specified',
    preferredLanguage: 'English',
    contactPreference: 'in-app',
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
);

final demoConsultation = ConsultationRequestItem(
  consultationId: 'consultation-test-id',
  patientId: 'patient-profile-test-id',
  clinicalEventId: 'clinical-event-test-id',
  specialty: 'Pulmonology demo review',
  questionSummary: 'Synthetic review of recovery-plan education questions.',
  priority: 'routine',
  status: 'requested',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
  createdAt: DateTime(2026, 7, 5, 12),
  updatedAt: DateTime(2026, 7, 5, 12),
);

class FakeDrAiRepository implements DrAiRepository {
  FakeDrAiRepository({
    this.restoredSession,
    this.loginSession = doctorSession,
    DashboardData? dashboard,
    this.loginError,
    this.logoutError,
    this.dashboardError,
    PatientListData? patientList,
    PatientCareBundle? patientCareBundle,
    AssessmentListData? assessments,
    RecoveryPlanListData? recoveryPlans,
    PatientTodayData? patientToday,
    ConsultationListData? consultations,
    this.patientListError,
    this.patientCareError,
    this.presignError,
    this.imagingError,
    this.assessmentError,
    this.recoveryPlanError,
    this.patientTodayError,
    this.completionError,
    this.chatError,
    this.consultationError,
    this.loginCompleter,
  }) : dashboard = dashboard ?? doctorDashboard,
       patientList =
           patientList ??
           const PatientListData(items: <PatientSummary>[demoPatientSummary]),
       patientCareBundle = patientCareBundle ?? demoPatientCareBundle,
       assessments =
           assessments ?? const AssessmentListData(items: <AssessmentResult>[]),
       recoveryPlans =
           recoveryPlans ??
           RecoveryPlanListData(items: <RecoveryPlanData>[demoRecoveryPlan]),
       patientToday = patientToday ?? demoPatientToday,
       consultations =
           consultations ??
           const ConsultationListData(items: <ConsultationRequestItem>[]);

  AuthSession? restoredSession;
  AuthSession loginSession;
  DashboardData dashboard;
  ApiError? loginError;
  Exception? logoutError;
  ApiError? dashboardError;
  PatientListData patientList;
  PatientCareBundle patientCareBundle;
  AssessmentListData assessments;
  RecoveryPlanListData recoveryPlans;
  PatientTodayData patientToday;
  ConsultationListData consultations;
  ApiError? patientListError;
  ApiError? patientCareError;
  ApiError? presignError;
  ApiError? imagingError;
  ApiError? assessmentError;
  ApiError? recoveryPlanError;
  ApiError? patientTodayError;
  ApiError? completionError;
  ApiError? chatError;
  ApiError? consultationError;
  Completer<AuthSession>? loginCompleter;
  bool logoutCalled = false;
  bool clinicalEventSaved = false;
  bool clinicalEventUpdateSubmitted = false;
  bool medicalHistoryReviewCreated = false;
  bool medicationSaved = false;
  bool prescriptionCreated = false;
  bool medicationReminderSaved = false;
  bool imagingPrepared = false;
  bool imagingCompleted = false;
  bool imagingReviewed = false;
  String? lastClinicalEventId;
  int chatMessagesSent = 0;
  String? lastChatMessage;

  @override
  Future<AuthSession?> restore() async => restoredSession;

  @override
  Future<AuthSession> login(String email, String password) async {
    if (loginCompleter != null) {
      return loginCompleter!.future;
    }
    if (loginError != null) {
      throw loginError!;
    }
    return loginSession;
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
  Future<DashboardData> loadDashboard(AppRole role) async {
    if (dashboardError != null) {
      throw dashboardError!;
    }
    return dashboard;
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
  }) async {
    medicationSaved = true;
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
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    if (imagingError != null) {
      throw imagingError!;
    }
    imagingPrepared = true;
    return demoImagingPresign;
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
  }) async {
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
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
  }) async {
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
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
    return updatedTasks.firstWhere((task) => task.taskId == taskId);
  }

  @override
  Future<MedicationNotificationScheduleResult> scheduleMedicationNotifications(
    List<RecoveryTaskItem> tasks,
  ) async {
    final count = tasks
        .where((task) => task.category == 'medication' && !task.isCompleted)
        .length;
    return MedicationNotificationScheduleResult(
      scheduledCount: count,
      label: 'Local demo medication notifications armed for $count task(s).',
    );
  }

  @override
  Future<ChatMessageResult> sendEducationalChatMessage({
    required String threadId,
    required String message,
  }) async {
    if (chatError != null) {
      throw chatError!;
    }
    chatMessagesSent += 1;
    lastChatMessage = message;
    return demoChatResult;
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
  }) async {
    if (consultationError != null) {
      throw consultationError!;
    }
    final request = ConsultationRequestItem(
      consultationId: 'created-consultation-id',
      patientId: patientId,
      clinicalEventId: clinicalEventId,
      specialty: specialty,
      questionSummary: questionSummary,
      priority: priority,
      status: 'requested',
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
      createdAt: DateTime(2026, 7, 5, 12),
      updatedAt: DateTime(2026, 7, 5, 12),
    );
    consultations = ConsultationListData(
      items: <ConsultationRequestItem>[request, ...consultations.items],
    );
    return request;
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
  List<MedicationItem>? medications,
  List<ClinicalEventItem>? clinicalEvents,
  List<ClinicalEventUpdateItem>? clinicalEventUpdates,
  List<MedicalHistoryReviewItem>? medicalHistoryReviews,
  List<MedicalImagingAsset>? imagingAssets,
  List<PrescriptionItem>? prescriptions,
  List<MedicationReminderItem>? medicationReminders,
  List<RecoveryPlanData>? recoveryPlans,
}) {
  return PatientCareBundle(
    patient: bundle.patient,
    clinicalEvents: clinicalEvents ?? bundle.clinicalEvents,
    clinicalEventUpdates: clinicalEventUpdates ?? bundle.clinicalEventUpdates,
    medicalHistoryReviews:
        medicalHistoryReviews ?? bundle.medicalHistoryReviews,
    allergies: bundle.allergies,
    chronicDiseases: bundle.chronicDiseases,
    visitHistory: bundle.visitHistory,
    diagnoses: bundle.diagnoses,
    records: bundle.records,
    imagingAssets: imagingAssets ?? bundle.imagingAssets,
    medications: medications ?? bundle.medications,
    prescriptions: prescriptions ?? bundle.prescriptions,
    medicationReminders: medicationReminders ?? bundle.medicationReminders,
    recoveryPlans: recoveryPlans ?? bundle.recoveryPlans,
    doctorNotes: bundle.doctorNotes,
  );
}
