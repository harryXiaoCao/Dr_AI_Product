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

class PatientProfile extends PatientSummary {
  const PatientProfile({
    required super.patientId,
    required super.displayName,
    required super.syntheticIdentifier,
    required super.safetyLabel,
    required this.relationshipLabel,
    required this.overview,
  });

  factory PatientProfile.fromJson(Map<String, dynamic> json) {
    return PatientProfile(
      patientId: json['patient_id'] as String,
      displayName: json['display_name'] as String,
      syntheticIdentifier: json['synthetic_identifier'] as String,
      safetyLabel: json['safety_label'] as String,
      relationshipLabel: json['relationship_label'] as String,
      overview: json['overview'] as String,
    );
  }

  final String relationshipLabel;
  final String overview;
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
    required this.name,
    required this.dosage,
    required this.schedule,
    required this.status,
    required this.note,
  });

  factory MedicationItem.fromJson(Map<String, dynamic> json) {
    return MedicationItem(
      id: json['id'] as String,
      name: json['name'] as String,
      dosage: json['dosage'] as String,
      schedule: json['schedule'] as String,
      status: json['status'] as String,
      note: json['note'] as String,
    );
  }

  final String id;
  final String name;
  final String dosage;
  final String schedule;
  final String status;
  final String note;
}

class DoctorNoteItem {
  const DoctorNoteItem({
    required this.id,
    required this.title,
    required this.body,
    required this.createdAt,
  });

  factory DoctorNoteItem.fromJson(Map<String, dynamic> json) {
    return DoctorNoteItem(
      id: json['id'] as String,
      title: json['title'] as String,
      body: json['body'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String title;
  final String body;
  final DateTime createdAt;
}

class PatientCareBundle {
  const PatientCareBundle({
    required this.patient,
    required this.records,
    required this.medications,
    required this.doctorNotes,
  });

  factory PatientCareBundle.fromJson(Map<String, dynamic> json) {
    return PatientCareBundle(
      patient: PatientProfile.fromJson(json['patient'] as Map<String, dynamic>),
      records: (json['records'] as List)
          .map(
            (item) => MedicalRecordItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      medications: (json['medications'] as List)
          .map((item) => MedicationItem.fromJson(item as Map<String, dynamic>))
          .toList(),
      doctorNotes: (json['doctor_notes'] as List)
          .map((item) => DoctorNoteItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  final PatientProfile patient;
  final List<MedicalRecordItem> records;
  final List<MedicationItem> medications;
  final List<DoctorNoteItem> doctorNotes;
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
    required this.title,
    required this.instructions,
    required this.status,
    required this.safetyLabel,
    required this.createdAt,
    required this.updatedAt,
    required this.tasks,
    this.activatedAt,
  });

  factory RecoveryPlanData.fromJson(Map<String, dynamic> json) {
    return RecoveryPlanData(
      planId: json['plan_id'] as String,
      patientId: json['patient_id'] as String,
      title: json['title'] as String,
      instructions: json['instructions'] as String,
      status: json['status'] as String,
      safetyLabel: json['safety_label'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      activatedAt: json['activated_at'] == null
          ? null
          : DateTime.parse(json['activated_at'] as String),
      tasks: (json['tasks'] as List)
          .map(
            (item) => RecoveryTaskItem.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  final String planId;
  final String patientId;
  final String title;
  final String instructions;
  final String status;
  final String safetyLabel;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? activatedAt;
  final List<RecoveryTaskItem> tasks;
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
}

class MedicationNotificationScheduleResult {
  const MedicationNotificationScheduleResult({
    required this.scheduledCount,
    required this.label,
  });

  final int scheduledCount;
  final String label;
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
    this.emergencyLabel,
    this.fallbackReason,
  });

  factory ChatMessageResult.fromJson(Map<String, dynamic> json) {
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
}

class ConsultationRequestItem {
  const ConsultationRequestItem({
    required this.consultationId,
    required this.patientId,
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
