import 'package:dio/dio.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/doctor/domain/doctor_profile.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class DrAiRepository {
  Future<AuthSession?> restore();
  Future<AuthSession> login(String email, String password);
  Future<PhoneVerificationResult> requestRegistrationCode(String phoneNumber);
  Future<PhoneVerificationResult> requestPasswordReset(String phoneNumber);
  Future<void> resetPassword({
    required String phoneNumber,
    required String verificationCode,
    required String newPassword,
  });
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });
  Future<SessionUser> updateAccountEmail(String email);
  Future<AuthSession> register({
    required String phoneNumber,
    required String email,
    required String password,
    required AppRole role,
    required String verificationCode,
    required bool termsAccepted,
    PatientSignupProfile? patientProfile,
    DoctorSignupProfile? doctorProfile,
  });
  Future<void> logout();
  Future<DashboardData> loadDashboard(AppRole role);
  Future<DoctorProfile> loadOwnDoctorProfile();
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
  });
  Future<PatientListData> loadPatients({String? query});
  Future<PatientSummary> connectPatientByCode(String patientCode);
  Future<PatientMatchPreview> previewPatientByCode(String patientCode);
  Future<PatientCareBundle> loadPatientCareBundle(String patientId);
  Future<PatientCareBundle> loadOwnPatientCare();
  Future<PatientDoctorContactList> loadOwnPatientContacts();
  Future<DoctorPatientContactList> loadOwnDoctorContacts();
  Future<PrivateMessageList> loadPrivateMessages(String contactId);
  Future<PrivateMessage> sendPrivateMessage(String contactId, String message);
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
    required bool medicalHistorySetupCompleted,
  });
  Future<PatientAllergyItem> createPatientAllergy({
    required String patientId,
    required String label,
    required String reaction,
    required String severity,
  });
  Future<PatientAllergyItem> updatePatientAllergy({
    required String patientId,
    required String allergyId,
    required String label,
    required String reaction,
    required String severity,
    required String status,
  });
  Future<MedicalRecordItem> createPatientMedicalRecord({
    required String patientId,
    required String title,
    required String category,
    required String summary,
  });
  Future<ChronicDiseaseItem> createChronicDisease({
    required String patientId,
    required String name,
    required String notes,
  });
  Future<ChronicDiseaseItem> updateChronicDisease({
    required String patientId,
    required String conditionId,
    required String name,
    required String notes,
    required String status,
  });
  Future<ClinicalEventItem> saveClinicalEvent({
    required String patientId,
    required String? clinicalEventId,
    required String title,
    required String chiefComplaint,
    required String symptomSummary,
    required String diagnosisSummary,
    required String onsetDate,
    required String status,
  });
  Future<ClinicalEventUpdateItem> submitClinicalEventUpdate({
    required String clinicalEventId,
    required String updateType,
    required String summary,
  });
  Future<MedicalHistoryReviewItem> createMedicalHistoryReview({
    required String patientId,
    required String targetType,
    required String targetId,
    required String action,
    required String amendmentSummary,
    required String correctionRequest,
  });
  Future<MedicationItem> saveMedication({
    required String patientId,
    required String? clinicalEventId,
    required String? medicationId,
    required String name,
    required String dosage,
    required String schedule,
    required String status,
    required String note,
  });
  Future<PrescriptionItem> createPrescription({
    required String patientId,
    required String? clinicalEventId,
    required String medicationId,
    required String name,
    required String dosage,
    required String schedule,
    required String notes,
  });
  Future<MedicationReminderItem> saveMedicationReminder({
    required String patientId,
    required String? reminderId,
    required String? medicationId,
    required String? prescriptionMedicationId,
    required String reminderType,
    required String scheduleLabel,
    required String status,
    required DateTime? nextDueAt,
  });
  Future<DemoAssetPresign> presignDemoAsset({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  });
  Future<MedicalImagingPresign> presignMedicalImaging({
    required String patientId,
    required String? clinicalEventId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  });
  Future<MedicalImagingAsset> completeMedicalImagingUpload({
    required String patientId,
    required String assetId,
    required int uploadedSizeBytes,
  });
  Future<MedicalImagingAsset> reviewMedicalImagingAsset({
    required String patientId,
    required String assetId,
    required String reviewStatus,
    required String findingSummary,
    required String measurementSummary,
  });
  Future<AssessmentListData> loadAssessments(String patientId);
  Future<AssessmentResult> createSimulatedAssessment({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  });
  Future<RecoveryPlanListData> loadRecoveryPlans(String patientId);
  Future<RecoveryPlanData> createRecoveryPlan({
    required String patientId,
    required String? clinicalEventId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  });
  Future<RecoveryPlanData> updateRecoveryPlan({
    required String patientId,
    required String? clinicalEventId,
    required String planId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  });
  Future<RecoveryPlanData> activateRecoveryPlan({
    required String patientId,
    required String planId,
  });
  Future<RecoveryPlanData> submitRecoveryPlanForReview({
    required String patientId,
    required String planId,
  });
  Future<RecoveryPlanData> requestRecoveryPlanChanges({
    required String patientId,
    required String planId,
  });
  Future<RecoveryPlanData> approveRecoveryPlan({
    required String patientId,
    required String planId,
  });
  Future<RecoveryPlanData> completeRecoveryPlan({
    required String patientId,
    required String planId,
  });
  Future<PatientTodayData> loadPatientToday();
  Future<RecoveryTaskItem> completeRecoveryTask(String taskId);
  Future<RecoveryTaskItem> uncompleteRecoveryTask(String taskId);
  Future<MedicationNotificationScheduleResult> scheduleMedicationNotifications(
    List<RecoveryTaskItem> tasks,
  );
  Future<ChatMessageResult> sendEducationalChatMessage({
    required String threadId,
    required String message,
  });
  Future<ConsultationListData> loadConsultations();
  Future<ConsultationRequestItem> createConsultation({
    required String patientId,
    required String? clinicalEventId,
    required String specialty,
    required String questionSummary,
    required String priority,
  });
}

class PatientSignupProfile {
  const PatientSignupProfile({
    required this.displayName,
    required this.birthDate,
    required this.gender,
    required this.contactPhone,
    required this.country,
    required this.province,
    required this.city,
    required this.homeAddress,
  });

  final String displayName;
  final String birthDate;
  final String gender;
  final String contactPhone;
  final String country;
  final String province;
  final String city;
  final String homeAddress;

  Map<String, dynamic> toJson() => <String, dynamic>{
    if (displayName.trim().isNotEmpty) 'display_name': displayName.trim(),
    if (birthDate.trim().isNotEmpty) 'birth_date': birthDate.trim(),
    if (gender.trim().isNotEmpty) 'gender': gender.trim(),
    if (contactPhone.trim().isNotEmpty) 'contact_phone': contactPhone.trim(),
    if (country.trim().isNotEmpty) 'country': country.trim(),
    if (province.trim().isNotEmpty) 'province': province.trim(),
    if (city.trim().isNotEmpty) 'city': city.trim(),
    if (homeAddress.trim().isNotEmpty) 'home_address': homeAddress.trim(),
  };
}

class DoctorSignupProfile {
  const DoctorSignupProfile({
    required this.displayName,
    required this.birthDate,
    required this.gender,
    required this.contactPhone,
    required this.country,
    required this.province,
    required this.city,
    required this.hospitalName,
    required this.customHospital,
  });

  final String displayName;
  final String birthDate;
  final String gender;
  final String contactPhone;
  final String country;
  final String province;
  final String city;
  final String hospitalName;
  final bool customHospital;

  Map<String, dynamic> toJson() => <String, dynamic>{
    if (displayName.trim().isNotEmpty) 'display_name': displayName.trim(),
    if (birthDate.trim().isNotEmpty) 'birth_date': birthDate.trim(),
    if (gender.trim().isNotEmpty) 'gender': gender.trim(),
    if (contactPhone.trim().isNotEmpty) 'contact_phone': contactPhone.trim(),
    if (country.trim().isNotEmpty) 'country': country.trim(),
    if (province.trim().isNotEmpty) 'province': province.trim(),
    if (city.trim().isNotEmpty) 'city': city.trim(),
    if (hospitalName.trim().isNotEmpty) 'hospital_name': hospitalName.trim(),
    'custom_hospital': customHospital,
  };
}

class DioDrAiRepository implements DrAiRepository {
  DioDrAiRepository({required this.client, required this.secureStorage});

  static const _refreshTokenKey = 'dr_ai_refresh_token';
  final Dio client;
  final FlutterSecureStorage secureStorage;
  AuthSession? _session;

  @override
  Future<AuthSession?> restore() async {
    final refreshToken = await secureStorage.read(key: _refreshTokenKey);
    if (refreshToken == null) {
      return null;
    }
    try {
      return await _refresh(refreshToken);
    } on ApiError {
      await secureStorage.delete(key: _refreshTokenKey);
      return null;
    }
  }

  @override
  Future<AuthSession> login(String email, String password) async {
    final account = email.trim();
    final data = <String, String>{'password': password};
    if (account.contains('@')) {
      data['email'] = account;
    } else {
      data['phone_number'] = account;
    }
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: data,
      );
      return await _saveSession(AuthSession.fromJson(response.data!));
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  @override
  Future<PhoneVerificationResult> requestPasswordReset(
    String phoneNumber,
  ) async {
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/password-reset/request',
        data: <String, String>{'phone_number': phoneNumber.trim()},
      );
      return PhoneVerificationResult.fromJson(response.data!);
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  @override
  Future<PhoneVerificationResult> requestRegistrationCode(
    String phoneNumber,
  ) async {
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/registration-code/request',
        data: <String, String>{'phone_number': phoneNumber.trim()},
      );
      return PhoneVerificationResult.fromJson(response.data!);
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  @override
  Future<void> resetPassword({
    required String phoneNumber,
    required String verificationCode,
    required String newPassword,
  }) async {
    try {
      await client.post<void>(
        '/api/v1/auth/password-reset',
        data: <String, String>{
          'phone_number': phoneNumber.trim(),
          'verification_code': verificationCode.trim(),
          'new_password': newPassword,
        },
      );
    } on DioException catch (error) {
      throw _toApiError(error);
    }
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
  }) async {
    final trimmedEmail = email.trim();
    final data = <String, dynamic>{
      'password': password,
      'role': role.wireValue,
      'phone_number': phoneNumber.trim(),
      'verification_code': verificationCode.trim(),
      'terms_accepted': termsAccepted,
    };
    if (trimmedEmail.isNotEmpty) {
      data['email'] = trimmedEmail;
    }
    if (patientProfile != null) {
      data['patient_profile'] = patientProfile.toJson();
    }
    if (doctorProfile != null) {
      data['doctor_profile'] = doctorProfile.toJson();
    }
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/register',
        data: data,
      );
      return await _saveSession(AuthSession.fromJson(response.data!));
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  Future<AuthSession> _refresh(String refreshToken) async {
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: <String, String>{'refresh_token': refreshToken},
      );
      return await _saveSession(AuthSession.fromJson(response.data!));
    } on DioException catch (error) {
      throw _toApiError(error);
    }
  }

  Future<AuthSession> _saveSession(AuthSession session) async {
    _session = session;
    await secureStorage.write(
      key: _refreshTokenKey,
      value: session.refreshToken,
    );
    return session;
  }

  @override
  Future<void> logout() async {
    final session = _session;
    try {
      if (session != null) {
        await client.post<void>(
          '/api/v1/auth/logout',
          data: <String, String>{'refresh_token': session.refreshToken},
          options: Options(
            headers: <String, String>{
              'Authorization': 'Bearer ${session.accessToken}',
            },
          ),
        );
      }
    } on DioException {
      // Local token removal is mandatory even when the network is unavailable.
    } finally {
      _session = null;
      await secureStorage.delete(key: _refreshTokenKey);
    }
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _authorizedPutVoid(
      '/api/v1/auth/password',
      data: <String, String>{
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
  }

  @override
  Future<SessionUser> updateAccountEmail(String email) async {
    final trimmedEmail = email.trim();
    final response = await _authorizedPatch(
      '/api/v1/auth/account/email',
      data: <String, dynamic>{
        'email': trimmedEmail.isEmpty ? null : trimmedEmail,
      },
    );
    final user = SessionUser.fromJson(response);
    final session = _session;
    if (session != null) {
      _session = AuthSession(
        accessToken: session.accessToken,
        refreshToken: session.refreshToken,
        user: user,
      );
    }
    return user;
  }

  @override
  Future<DashboardData> loadDashboard(AppRole role) async {
    final path = role == AppRole.patient
        ? '/api/v1/patient/me/today'
        : '/api/v1/me/dashboard';
    try {
      return await _getDashboard(path);
    } on ApiError catch (error) {
      if (error.statusCode != 401 || _session == null) {
        rethrow;
      }
      await _refresh(_session!.refreshToken);
      return _getDashboard(path);
    }
  }

  Future<DashboardData> _getDashboard(String path) async {
    final response = await _authorizedGet(path);
    return DashboardData.fromJson(response);
  }

  @override
  Future<DoctorProfile> loadOwnDoctorProfile() async {
    final response = await _authorizedGet('/api/v1/doctor/me/profile');
    return DoctorProfile.fromJson(response);
  }

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
    final response = await _authorizedPatch(
      '/api/v1/doctor/me/profile',
      data: <String, dynamic>{
        'display_name': displayName.trim(),
        if (specialty.trim().isNotEmpty) 'specialty': specialty.trim(),
        'title': title.trim(),
        if (department.trim().isNotEmpty) 'department': department.trim(),
        if (contactPhone.trim().isNotEmpty)
          'contact_phone': contactPhone.trim(),
        if (country.trim().isNotEmpty) 'country': country.trim(),
        if (province.trim().isNotEmpty) 'province': province.trim(),
        if (city.trim().isNotEmpty) 'city': city.trim(),
        if (preferredLanguage.trim().isNotEmpty)
          'preferred_language': preferredLanguage.trim(),
        if (avatarUrl.trim().isNotEmpty) 'avatar_url': avatarUrl.trim(),
      },
    );
    return DoctorProfile.fromJson(response);
  }

  @override
  Future<PatientListData> loadPatients({String? query}) async {
    final trimmed = query?.trim();
    final response = await _authorizedGet(
      '/api/v1/patients',
      queryParameters: <String, dynamic>{
        if (trimmed != null && trimmed.isNotEmpty) 'q': trimmed,
      },
    );
    return PatientListData.fromJson(response);
  }

  @override
  Future<PatientSummary> connectPatientByCode(String patientCode) async {
    final response = await _authorizedPost(
      '/api/v1/patients/connect',
      data: <String, String>{'patient_code': patientCode.trim()},
    );
    return PatientSummary.fromJson(response);
  }

  @override
  Future<PatientMatchPreview> previewPatientByCode(String patientCode) async {
    final response = await _authorizedPost(
      '/api/v1/patients/connect/preview',
      data: <String, String>{'patient_code': patientCode.trim()},
    );
    return PatientMatchPreview.fromJson(response);
  }

  @override
  Future<PatientCareBundle> loadPatientCareBundle(String patientId) async {
    final response = await _authorizedGet('/api/v1/patients/$patientId/care');
    return PatientCareBundle.fromJson(response);
  }

  @override
  Future<PatientCareBundle> loadOwnPatientCare() async {
    final response = await _authorizedGet('/api/v1/patient/me/care');
    return PatientCareBundle.fromJson(response);
  }

  @override
  Future<PatientDoctorContactList> loadOwnPatientContacts() async {
    final response = await _authorizedGet('/api/v1/patient/me/contacts');
    return PatientDoctorContactList.fromJson(response);
  }

  @override
  Future<DoctorPatientContactList> loadOwnDoctorContacts() async {
    final response = await _authorizedGet('/api/v1/doctor/me/contacts');
    return DoctorPatientContactList.fromJson(response);
  }

  @override
  Future<PrivateMessageList> loadPrivateMessages(String contactId) async {
    final response = await _authorizedGet(
      '/api/v1/private-chats/$contactId/messages',
    );
    return PrivateMessageList.fromJson(response);
  }

  @override
  Future<PrivateMessage> sendPrivateMessage(
    String contactId,
    String message,
  ) async {
    final response = await _authorizedPost(
      '/api/v1/private-chats/$contactId/messages',
      data: <String, String>{'message': message.trim()},
    );
    return PrivateMessage.fromJson(response);
  }

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
    required bool medicalHistorySetupCompleted,
  }) async {
    final response = await _authorizedPatch(
      '/api/v1/patient/me/profile',
      data: <String, dynamic>{
        'display_name': displayName.trim(),
        if (birthDate.trim().isNotEmpty) 'birth_date': birthDate.trim(),
        if (gender.trim().isNotEmpty) 'gender': gender.trim(),
        if (contactPhone.trim().isNotEmpty)
          'contact_phone': contactPhone.trim(),
        if (emergencyContactName.trim().isNotEmpty)
          'emergency_contact_name': emergencyContactName.trim(),
        if (emergencyContactPhone.trim().isNotEmpty)
          'emergency_contact_phone': emergencyContactPhone.trim(),
        if (preferredLanguage.trim().isNotEmpty)
          'preferred_language': preferredLanguage.trim(),
        if (contactPreference.trim().isNotEmpty)
          'contact_preference': contactPreference.trim(),
        if (avatarUrl.trim().isNotEmpty) 'avatar_url': avatarUrl.trim(),
        if (country.trim().isNotEmpty) 'country': country.trim(),
        if (province.trim().isNotEmpty) 'province': province.trim(),
        if (city.trim().isNotEmpty) 'city': city.trim(),
        if (homeAddress.trim().isNotEmpty) 'home_address': homeAddress.trim(),
        if (heightCm.trim().isNotEmpty)
          'height_cm': double.parse(heightCm.trim()),
        if (weightKg.trim().isNotEmpty)
          'weight_kg': double.parse(weightKg.trim()),
        'medical_history_setup_completed': medicalHistorySetupCompleted,
      },
    );
    return PatientProfile.fromJson(response);
  }

  @override
  Future<PatientAllergyItem> createPatientAllergy({
    required String patientId,
    required String label,
    required String reaction,
    required String severity,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/allergies',
      data: <String, dynamic>{
        'label': label.trim(),
        if (reaction.trim().isNotEmpty) 'reaction': reaction.trim(),
        'severity': severity,
        'status': 'active',
      },
    );
    return PatientAllergyItem.fromJson(response);
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
    final response = await _authorizedPut(
      '/api/v1/patients/$patientId/allergies/$allergyId',
      data: <String, dynamic>{
        'label': label.trim(),
        if (reaction.trim().isNotEmpty) 'reaction': reaction.trim(),
        'severity': severity,
        'status': status,
      },
    );
    return PatientAllergyItem.fromJson(response);
  }

  @override
  Future<MedicalRecordItem> createPatientMedicalRecord({
    required String patientId,
    required String title,
    required String category,
    required String summary,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/records',
      data: <String, String>{
        'title': title.trim(),
        'category': category.trim(),
        'summary': summary.trim(),
      },
    );
    return MedicalRecordItem.fromJson(response);
  }

  @override
  Future<ChronicDiseaseItem> createChronicDisease({
    required String patientId,
    required String name,
    required String notes,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/chronic-diseases',
      data: <String, dynamic>{
        'name': name.trim(),
        'status': 'active',
        if (notes.trim().isNotEmpty) 'notes': notes.trim(),
      },
    );
    return ChronicDiseaseItem.fromJson(response);
  }

  @override
  Future<ChronicDiseaseItem> updateChronicDisease({
    required String patientId,
    required String conditionId,
    required String name,
    required String notes,
    required String status,
  }) async {
    final response = await _authorizedPut(
      '/api/v1/patients/$patientId/chronic-diseases/$conditionId',
      data: <String, dynamic>{
        'name': name.trim(),
        'status': status,
        if (notes.trim().isNotEmpty) 'notes': notes.trim(),
      },
    );
    return ChronicDiseaseItem.fromJson(response);
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
    final data = <String, dynamic>{
      'title': title,
      'chief_complaint': chiefComplaint,
      'symptom_summary': symptomSummary.isEmpty ? null : symptomSummary,
      'diagnosis_summary': diagnosisSummary.isEmpty ? null : diagnosisSummary,
      'onset_date': onsetDate.isEmpty ? null : onsetDate,
      'status': status,
    };
    final response = clinicalEventId == null
        ? await _authorizedPost(
            '/api/v1/patients/$patientId/clinical-events',
            data: data,
          )
        : await _authorizedPut(
            '/api/v1/patients/$patientId/clinical-events/$clinicalEventId',
            data: data,
          );
    return ClinicalEventItem.fromJson(response);
  }

  @override
  Future<ClinicalEventUpdateItem> submitClinicalEventUpdate({
    required String clinicalEventId,
    required String updateType,
    required String summary,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patient/me/clinical-events/$clinicalEventId/updates',
      data: <String, dynamic>{
        'update_type': updateType,
        'summary': summary,
        'occurred_at': DateTime.now().toUtc().toIso8601String(),
      },
    );
    return ClinicalEventUpdateItem.fromJson(response);
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
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/medical-history-reviews',
      data: <String, dynamic>{
        'target_type': targetType,
        'target_id': targetId,
        'action': action,
        'amendment_summary': amendmentSummary.isEmpty ? null : amendmentSummary,
        'correction_request': correctionRequest.isEmpty
            ? null
            : correctionRequest,
      },
    );
    return MedicalHistoryReviewItem.fromJson(response);
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
    final data = <String, dynamic>{
      'name': name,
      'dosage': dosage,
      'schedule': schedule,
      'status': status,
      'note': note,
    };
    if (clinicalEventId != null) {
      data['clinical_event_id'] = clinicalEventId;
    }
    final response = medicationId == null
        ? await _authorizedPost(
            '/api/v1/patients/$patientId/medications',
            data: data,
          )
        : await _authorizedPut(
            '/api/v1/patients/$patientId/medications/$medicationId',
            data: data,
          );
    return MedicationItem.fromJson(response);
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
    final data = <String, dynamic>{
      'status': 'issued',
      'issued_at': DateTime.now().toUtc().toIso8601String(),
      'notes': notes,
      'medications': <Map<String, dynamic>>[
        <String, dynamic>{
          'medication_id': medicationId,
          'name': name,
          'dosage': dosage,
          'schedule': schedule,
        },
      ],
    };
    if (clinicalEventId != null) {
      data['clinical_event_id'] = clinicalEventId;
    }
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/prescriptions',
      data: data,
    );
    return PrescriptionItem.fromJson(response);
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
    final data = <String, dynamic>{
      'reminder_type': reminderType,
      'schedule_label': scheduleLabel,
      'channel': 'in_app',
      'status': status,
    };
    if (medicationId != null) {
      data['medication_id'] = medicationId;
    }
    if (prescriptionMedicationId != null) {
      data['prescription_medication_id'] = prescriptionMedicationId;
    }
    if (nextDueAt != null) {
      data['next_due_at'] = nextDueAt.toUtc().toIso8601String();
    }
    final response = reminderId == null
        ? await _authorizedPost(
            '/api/v1/patients/$patientId/medication-reminders',
            data: data,
          )
        : await _authorizedPut(
            '/api/v1/patients/$patientId/medication-reminders/$reminderId',
            data: data,
          );
    return MedicationReminderItem.fromJson(response);
  }

  @override
  Future<DemoAssetPresign> presignDemoAsset({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/assets/presign',
      data: <String, dynamic>{
        'filename': filename,
        'content_type': contentType,
        'size_bytes': sizeBytes,
      },
    );
    return DemoAssetPresign.fromJson(response);
  }

  @override
  Future<MedicalImagingPresign> presignMedicalImaging({
    required String patientId,
    required String? clinicalEventId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    final data = <String, dynamic>{
      'filename': filename,
      'content_type': contentType,
      'size_bytes': sizeBytes,
    };
    if (clinicalEventId != null) {
      data['clinical_event_id'] = clinicalEventId;
    }
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/imaging/presign',
      data: data,
    );
    return MedicalImagingPresign.fromJson(response);
  }

  @override
  Future<MedicalImagingAsset> completeMedicalImagingUpload({
    required String patientId,
    required String assetId,
    required int uploadedSizeBytes,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/imaging/$assetId/complete',
      data: <String, dynamic>{'uploaded_size_bytes': uploadedSizeBytes},
    );
    return MedicalImagingAsset.fromJson(response);
  }

  @override
  Future<MedicalImagingAsset> reviewMedicalImagingAsset({
    required String patientId,
    required String assetId,
    required String reviewStatus,
    required String findingSummary,
    required String measurementSummary,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/imaging/$assetId/review',
      data: <String, String?>{
        'review_status': reviewStatus,
        'finding_summary': findingSummary.isEmpty ? null : findingSummary,
        'measurement_summary': measurementSummary.isEmpty
            ? null
            : measurementSummary,
      },
    );
    return MedicalImagingAsset.fromJson(response);
  }

  @override
  Future<AssessmentListData> loadAssessments(String patientId) async {
    final response = await _authorizedGet(
      '/api/v1/patients/$patientId/assessments',
    );
    return AssessmentListData.fromJson(response);
  }

  @override
  Future<AssessmentResult> createSimulatedAssessment({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/assessments',
      data: <String, String>{
        'mode': 'simulated',
        'fixture_id': fixtureId,
        'idempotency_key': idempotencyKey,
      },
    );
    return AssessmentResult.fromJson(response);
  }

  @override
  Future<RecoveryPlanListData> loadRecoveryPlans(String patientId) async {
    final response = await _authorizedGet(
      '/api/v1/patients/$patientId/recovery-plans',
    );
    return RecoveryPlanListData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> createRecoveryPlan({
    required String patientId,
    required String? clinicalEventId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans',
      data: _recoveryPlanPayload(
        clinicalEventId: clinicalEventId,
        title: title,
        instructions: instructions,
        tasks: tasks,
      ),
    );
    return RecoveryPlanData.fromJson(response);
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
    final response = await _authorizedPut(
      '/api/v1/patients/$patientId/recovery-plans/$planId',
      data: _recoveryPlanPayload(
        clinicalEventId: clinicalEventId,
        title: title,
        instructions: instructions,
        tasks: tasks,
      ),
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> activateRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/activate',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> submitRecoveryPlanForReview({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/submit-review',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> requestRecoveryPlanChanges({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/request-changes',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> approveRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/approve',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<RecoveryPlanData> completeRecoveryPlan({
    required String patientId,
    required String planId,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/patients/$patientId/recovery-plans/$planId/complete',
      data: const <String, dynamic>{},
    );
    return RecoveryPlanData.fromJson(response);
  }

  @override
  Future<PatientTodayData> loadPatientToday() async {
    final response = await _authorizedGet('/api/v1/patient/me/today');
    return PatientTodayData.fromDashboardJson(response);
  }

  @override
  Future<RecoveryTaskItem> completeRecoveryTask(String taskId) async {
    final response = await _authorizedPost(
      '/api/v1/patient/me/tasks/$taskId/completion',
      data: const <String, bool>{'completed': true},
    );
    return RecoveryTaskItem.fromJson(response['task'] as Map<String, dynamic>);
  }

  @override
  Future<RecoveryTaskItem> uncompleteRecoveryTask(String taskId) async {
    final response = await _authorizedDelete(
      '/api/v1/patient/me/tasks/$taskId/completion',
    );
    return RecoveryTaskItem.fromJson(response['task'] as Map<String, dynamic>);
  }

  @override
  Future<MedicationNotificationScheduleResult> scheduleMedicationNotifications(
    List<RecoveryTaskItem> tasks,
  ) async {
    final medicationTasks = tasks
        .where((task) => task.category == 'medication' && !task.isCompleted)
        .length;
    return MedicationNotificationScheduleResult(
      scheduledCount: medicationTasks,
      label:
          'Local demo medication notifications armed for $medicationTasks task(s).',
    );
  }

  @override
  Future<ChatMessageResult> sendEducationalChatMessage({
    required String threadId,
    required String message,
  }) async {
    final response = await _authorizedPost(
      '/api/v1/chat/threads/$threadId/messages',
      data: <String, dynamic>{'message': message, 'stream': true},
    );
    return ChatMessageResult.fromJson(response);
  }

  @override
  Future<ConsultationListData> loadConsultations() async {
    final response = await _authorizedGet('/api/v1/consultations');
    return ConsultationListData.fromJson(response);
  }

  @override
  Future<ConsultationRequestItem> createConsultation({
    required String patientId,
    required String? clinicalEventId,
    required String specialty,
    required String questionSummary,
    required String priority,
  }) async {
    final data = <String, dynamic>{
      'patient_id': patientId,
      'specialty': specialty,
      'question_summary': questionSummary,
      'priority': priority,
    };
    if (clinicalEventId != null) {
      data['clinical_event_id'] = clinicalEventId;
    }
    final response = await _authorizedPost('/api/v1/consultations', data: data);
    return ConsultationRequestItem.fromJson(response);
  }

  Map<String, dynamic> _recoveryPlanPayload({
    required String? clinicalEventId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) {
    final data = <String, dynamic>{
      'title': title,
      'instructions': instructions,
      'tasks': tasks.map((task) => task.toJson()).toList(),
    };
    if (clinicalEventId != null) {
      data['clinical_event_id'] = clinicalEventId;
    }
    return data;
  }

  Future<Map<String, dynamic>> _authorizedGet(
    String path, {
    Map<String, dynamic>? queryParameters,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.get<Map<String, dynamic>>(
        path,
        queryParameters: queryParameters,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedGet(
          path,
          queryParameters: queryParameters,
          allowRefresh: false,
        );
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedPost(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.post<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPost(path, data: data, allowRefresh: false);
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedPut(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.put<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPut(path, data: data, allowRefresh: false);
      }
      throw apiError;
    }
  }

  Future<void> _authorizedPutVoid(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      await client.put<void>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPutVoid(path, data: data, allowRefresh: false);
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedPatch(
    String path, {
    required Map<String, dynamic> data,
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.patch<Map<String, dynamic>>(
        path,
        data: data,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedPatch(path, data: data, allowRefresh: false);
      }
      throw apiError;
    }
  }

  Future<Map<String, dynamic>> _authorizedDelete(
    String path, {
    bool allowRefresh = true,
  }) async {
    final session = _session;
    if (session == null) {
      throw const ApiError(
        code: 'unauthenticated',
        message: 'Your session has ended. Please sign in again.',
        statusCode: 401,
      );
    }
    try {
      final response = await client.delete<Map<String, dynamic>>(
        path,
        options: Options(
          headers: <String, String>{
            'Authorization': 'Bearer ${session.accessToken}',
          },
        ),
      );
      return response.data!;
    } on DioException catch (error) {
      final apiError = _toApiError(error);
      if (apiError.statusCode == 401 && allowRefresh && _session != null) {
        await _refresh(_session!.refreshToken);
        return _authorizedDelete(path, allowRefresh: false);
      }
      throw apiError;
    }
  }

  ApiError _toApiError(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final envelope = data['error'];
      if (envelope is Map<String, dynamic>) {
        return ApiError(
          code: envelope['code'] as String? ?? 'service_unavailable',
          message:
              envelope['message'] as String? ??
              'The request could not be completed.',
          requestId: envelope['request_id'] as String?,
          statusCode: error.response?.statusCode,
        );
      }
    }
    return ApiError(
      code: 'service_unavailable',
      message: 'Unable to reach Dr. AI. Check your connection and try again.',
      statusCode: error.response?.statusCode,
    );
  }
}
