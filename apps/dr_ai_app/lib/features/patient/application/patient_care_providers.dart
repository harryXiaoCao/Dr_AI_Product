import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

final patientSearchQueryProvider = StateProvider.autoDispose<String>(
  (ref) => '',
);

final patientListProvider = FutureProvider.autoDispose<PatientListData>((
  ref,
) async {
  ref.watch(authControllerProvider);
  final query = ref.watch(patientSearchQueryProvider);
  return ref.read(repositoryProvider).loadPatients(query: query);
});

final patientCareBundleProvider = FutureProvider.autoDispose
    .family<PatientCareBundle, String>((ref, patientId) async {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadPatientCareBundle(patientId);
    });

final ownPatientCareProvider = FutureProvider.autoDispose<PatientCareBundle>((
  ref,
) async {
  final authState = ref.watch(authControllerProvider).value;
  if (authState?.user == null) {
    throw const ApiError(
      code: 'unauthenticated',
      message: 'Your session has ended. Please sign in again.',
      statusCode: 401,
    );
  }
  return ref.read(repositoryProvider).loadOwnPatientCare();
});

final assessmentListProvider = FutureProvider.autoDispose
    .family<AssessmentListData, String>((ref, patientId) async {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadAssessments(patientId);
    });

final recoveryPlanListProvider = FutureProvider.autoDispose
    .family<RecoveryPlanListData, String>((ref, patientId) async {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadRecoveryPlans(patientId);
    });

final patientTodayProvider = FutureProvider.autoDispose<PatientTodayData>((
  ref,
) async {
  ref.watch(authControllerProvider);
  return ref.read(repositoryProvider).loadPatientToday();
});

final demoAssetPresignControllerProvider =
    StateNotifierProvider.autoDispose<
      DemoAssetPresignController,
      AsyncValue<DemoAssetPresign?>
    >((ref) {
      return DemoAssetPresignController(ref.read(repositoryProvider));
    });

class DemoAssetPresignController
    extends StateNotifier<AsyncValue<DemoAssetPresign?>> {
  DemoAssetPresignController(this._repository)
    : super(const AsyncData<DemoAssetPresign?>(null));

  final DrAiRepository _repository;

  Future<void> presign({
    required String patientId,
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    state = const AsyncLoading<DemoAssetPresign?>();
    try {
      state = AsyncData(
        await _repository.presignDemoAsset(
          patientId: patientId,
          filename: filename,
          contentType: contentType,
          sizeBytes: sizeBytes,
        ),
      );
    } catch (error, stackTrace) {
      state = AsyncError<DemoAssetPresign?>(error, stackTrace);
    }
  }
}

final assessmentCreateControllerProvider =
    StateNotifierProvider.autoDispose<
      AssessmentCreateController,
      AsyncValue<AssessmentResult?>
    >((ref) {
      return AssessmentCreateController(ref.read(repositoryProvider), ref);
    });

class AssessmentCreateController
    extends StateNotifier<AsyncValue<AssessmentResult?>> {
  AssessmentCreateController(this._repository, this._ref)
    : super(const AsyncData<AssessmentResult?>(null));

  final DrAiRepository _repository;
  final Ref _ref;

  Future<void> create({
    required String patientId,
    required String fixtureId,
    required String idempotencyKey,
  }) async {
    state = const AsyncLoading<AssessmentResult?>();
    try {
      final result = await _repository.createSimulatedAssessment(
        patientId: patientId,
        fixtureId: fixtureId,
        idempotencyKey: idempotencyKey,
      );
      state = AsyncData(result);
      _ref.invalidate(assessmentListProvider(patientId));
    } catch (error, stackTrace) {
      state = AsyncError<AssessmentResult?>(error, stackTrace);
    }
  }
}

final recoveryPlanEditorControllerProvider =
    StateNotifierProvider.autoDispose<
      RecoveryPlanEditorController,
      AsyncValue<RecoveryPlanData?>
    >((ref) {
      return RecoveryPlanEditorController(ref.read(repositoryProvider), ref);
    });

class RecoveryPlanEditorController
    extends StateNotifier<AsyncValue<RecoveryPlanData?>> {
  RecoveryPlanEditorController(this._repository, this._ref)
    : super(const AsyncData<RecoveryPlanData?>(null));

  final DrAiRepository _repository;
  final Ref _ref;

  Future<void> saveDraft({
    required String patientId,
    required String? planId,
    required String title,
    required String instructions,
    required List<RecoveryTaskInput> tasks,
  }) async {
    state = const AsyncLoading<RecoveryPlanData?>();
    try {
      final result = planId == null
          ? await _repository.createRecoveryPlan(
              patientId: patientId,
              title: title,
              instructions: instructions,
              tasks: tasks,
            )
          : await _repository.updateRecoveryPlan(
              patientId: patientId,
              planId: planId,
              title: title,
              instructions: instructions,
              tasks: tasks,
            );
      state = AsyncData(result);
      _ref.invalidate(recoveryPlanListProvider(patientId));
    } catch (error, stackTrace) {
      state = AsyncError<RecoveryPlanData?>(error, stackTrace);
    }
  }

  Future<void> activate({
    required String patientId,
    required String planId,
  }) async {
    state = const AsyncLoading<RecoveryPlanData?>();
    try {
      final result = await _repository.activateRecoveryPlan(
        patientId: patientId,
        planId: planId,
      );
      state = AsyncData(result);
      _ref.invalidate(recoveryPlanListProvider(patientId));
    } catch (error, stackTrace) {
      state = AsyncError<RecoveryPlanData?>(error, stackTrace);
    }
  }
}

final recoveryTaskCompletionControllerProvider =
    StateNotifierProvider.autoDispose<
      RecoveryTaskCompletionController,
      AsyncValue<Set<String>>
    >((ref) {
      return RecoveryTaskCompletionController(
        ref.read(repositoryProvider),
        ref,
      );
    });

class RecoveryTaskCompletionController
    extends StateNotifier<AsyncValue<Set<String>>> {
  RecoveryTaskCompletionController(this._repository, this._ref)
    : super(const AsyncData<Set<String>>(<String>{}));

  final DrAiRepository _repository;
  final Ref _ref;

  Future<void> complete(String taskId) async {
    final current = state.hasValue
        ? state.value ?? const <String>{}
        : const <String>{};
    state = AsyncData<Set<String>>(<String>{...current, taskId});
    try {
      await _repository.completeRecoveryTask(taskId);
      _ref.invalidate(patientTodayProvider);
    } catch (error, stackTrace) {
      state = AsyncError<Set<String>>(error, stackTrace);
    }
  }
}

final medicationNotificationShellProvider =
    FutureProvider.autoDispose<MedicationNotificationScheduleResult>((
      ref,
    ) async {
      final today = await ref.watch(patientTodayProvider.future);
      return ref
          .read(repositoryProvider)
          .scheduleMedicationNotifications(today.tasks);
    });

final educationalChatControllerProvider =
    StateNotifierProvider.autoDispose<
      EducationalChatController,
      EducationalChatState
    >((ref) {
      return EducationalChatController(ref.read(repositoryProvider));
    });

class EducationalChatState {
  const EducationalChatState({
    this.messages = const <ChatDisplayMessage>[],
    this.isSending = false,
    this.errorMessage,
  });

  final List<ChatDisplayMessage> messages;
  final bool isSending;
  final String? errorMessage;

  EducationalChatState copyWith({
    List<ChatDisplayMessage>? messages,
    bool? isSending,
    String? errorMessage,
  }) {
    return EducationalChatState(
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      errorMessage: errorMessage,
    );
  }
}

class ChatDisplayMessage {
  const ChatDisplayMessage({
    required this.id,
    required this.role,
    required this.content,
    this.safetyLabel,
    this.isRedFlag = false,
    this.fallbackReason,
  });

  final String id;
  final String role;
  final String content;
  final String? safetyLabel;
  final bool isRedFlag;
  final String? fallbackReason;
}

class EducationalChatController extends StateNotifier<EducationalChatState> {
  EducationalChatController(this._repository)
    : super(
        const EducationalChatState(
          messages: <ChatDisplayMessage>[
            ChatDisplayMessage(
              id: 'educational-chat-seed',
              role: 'assistant',
              content:
                  'Educational information only - not medical advice. Ask general questions to prepare for your next clinician visit.',
              safetyLabel: 'Educational information only - not medical advice.',
            ),
          ],
        ),
      );

  final DrAiRepository _repository;

  Future<bool> send(String message) async {
    final trimmed = message.trim();
    if (trimmed.length < 3 || state.isSending) {
      return false;
    }
    final localId = DateTime.now().microsecondsSinceEpoch.toString();
    final assistantId = 'assistant-$localId';
    state = EducationalChatState(
      messages: <ChatDisplayMessage>[
        ...state.messages,
        ChatDisplayMessage(id: 'user-$localId', role: 'user', content: trimmed),
        ChatDisplayMessage(id: assistantId, role: 'assistant', content: ''),
      ],
      isSending: true,
    );
    try {
      final result = await _repository.sendEducationalChatMessage(
        threadId: 'patient-education',
        message: trimmed,
      );
      var streamed = '';
      for (final chunk in result.responseChunks) {
        streamed = streamed.isEmpty ? chunk : '$streamed $chunk';
        state = state.copyWith(
          messages: _replaceAssistant(assistantId, streamed, result: result),
          isSending: true,
        );
        await Future<void>.delayed(const Duration(milliseconds: 8));
      }
      state = state.copyWith(
        messages: _replaceAssistant(
          assistantId,
          result.content,
          result: result,
        ),
        isSending: false,
      );
      return true;
    } catch (error) {
      state = state.copyWith(
        messages: state.messages
            .where((message) => message.id != assistantId)
            .toList(),
        isSending: false,
        errorMessage: _safeProviderError(error),
      );
      return false;
    }
  }

  List<ChatDisplayMessage> _replaceAssistant(
    String assistantId,
    String content, {
    required ChatMessageResult result,
  }) {
    return state.messages.map((message) {
      if (message.id != assistantId) {
        return message;
      }
      return ChatDisplayMessage(
        id: assistantId,
        role: 'assistant',
        content: content,
        safetyLabel: result.emergencyLabel ?? result.safetyLabel,
        isRedFlag: result.isRedFlag,
        fallbackReason: result.fallbackReason,
      );
    }).toList();
  }
}

final consultationListProvider =
    FutureProvider.autoDispose<ConsultationListData>((ref) async {
      ref.watch(authControllerProvider);
      return ref.read(repositoryProvider).loadConsultations();
    });

final consultationRequestControllerProvider =
    StateNotifierProvider.autoDispose<
      ConsultationRequestController,
      AsyncValue<ConsultationRequestItem?>
    >((ref) {
      return ConsultationRequestController(ref.read(repositoryProvider), ref);
    });

class ConsultationRequestController
    extends StateNotifier<AsyncValue<ConsultationRequestItem?>> {
  ConsultationRequestController(this._repository, this._ref)
    : super(const AsyncData<ConsultationRequestItem?>(null));

  final DrAiRepository _repository;
  final Ref _ref;

  Future<void> create({
    required String patientId,
    required String specialty,
    required String questionSummary,
    required String priority,
  }) async {
    state = const AsyncLoading<ConsultationRequestItem?>();
    try {
      final result = await _repository.createConsultation(
        patientId: patientId,
        specialty: specialty,
        questionSummary: questionSummary,
        priority: priority,
      );
      state = AsyncData(result);
      _ref.invalidate(consultationListProvider);
    } catch (error, stackTrace) {
      state = AsyncError<ConsultationRequestItem?>(error, stackTrace);
    }
  }
}

String _safeProviderError(Object error) {
  if (error is ApiError) {
    if (error.code == 'rate_limited') {
      return 'Educational chat is temporarily rate limited. Please try again shortly.';
    }
    if (error.code == 'service_unavailable') {
      return 'Unable to reach Dr. AI. Check your connection and try again.';
    }
    return error.message;
  }
  return 'Unable to reach Dr. AI. Check your connection and try again.';
}
