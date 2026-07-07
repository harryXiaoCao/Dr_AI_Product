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
  ),
  records: <MedicalRecordItem>[
    MedicalRecordItem(
      id: 'record-test-id',
      title: 'Synthetic intake summary',
      category: 'Demo visit',
      summary: 'Synthetic Week 2 fixture for care-loop navigation only.',
      recordedAt: DateTime(2026, 7, 1),
    ),
  ],
  medications: <MedicationItem>[
    MedicationItem(
      id: 'medication-test-id',
      name: 'Demo Sumatriptan Fixture',
      dosage: '50 mg',
      schedule: 'As listed in the synthetic care plan',
      status: 'active',
      note: 'Fixture medication for UI validation; not a prescription.',
    ),
  ],
  doctorNotes: <DoctorNoteItem>[
    DoctorNoteItem(
      id: 'note-test-id',
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
  title: 'Synthetic Week 3 Recovery Plan',
  instructions:
      'Demo-only recovery plan for invited beta workflow validation. Not medical advice.',
  status: 'active',
  safetyLabel:
      'Synthetic demonstration data only. Do not enter real patient data.',
  createdAt: DateTime(2026, 7, 5, 10),
  updatedAt: DateTime(2026, 7, 5, 10),
  activatedAt: DateTime(2026, 7, 5, 10),
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
  ApiError? assessmentError;
  ApiError? recoveryPlanError;
  ApiError? patientTodayError;
  ApiError? completionError;
  ApiError? chatError;
  ApiError? consultationError;
  Completer<AuthSession>? loginCompleter;
  bool logoutCalled = false;
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
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) async {
    if (recoveryPlanError != null) {
      throw recoveryPlanError!;
    }
    final plan = _planFromInput(
      patientId: patientId,
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
      title: current.title,
      instructions: current.instructions,
      status: 'active',
      safetyLabel: current.safetyLabel,
      createdAt: current.createdAt,
      updatedAt: DateTime(2026, 7, 5, 12),
      activatedAt: DateTime(2026, 7, 5, 12),
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
      tasks: active.tasks,
    );
    return active;
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
    required String planId,
    required String title,
    required String instructions,
    required String status,
    required List<RecoveryTaskInput> tasks,
  }) {
    return RecoveryPlanData(
      planId: planId,
      patientId: patientId,
      title: title,
      instructions: instructions,
      status: status,
      safetyLabel:
          'Synthetic demonstration data only. Do not enter real patient data.',
      createdAt: DateTime(2026, 7, 5, 12),
      updatedAt: DateTime(2026, 7, 5, 12),
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
}
