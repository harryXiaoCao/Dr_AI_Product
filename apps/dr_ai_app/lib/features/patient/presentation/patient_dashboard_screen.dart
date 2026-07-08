import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PatientDashboardScreen extends ConsumerWidget {
  const PatientDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      child: dashboard.when(
        loading: () => const DashboardLoadingView(),
        error: (error, stackTrace) => DashboardErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(dashboardProvider),
        ),
        data: (data) => _PatientDashboard(data: data),
      ),
    );
  }
}

class _PatientDashboard extends ConsumerWidget {
  const _PatientDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (data.data.isEmpty) {
      return const Center(
        child: Text(
          'No synthetic dashboard data is available.',
          key: Key('patient-empty'),
        ),
      );
    }
    final recoveryDays = List<Map<String, dynamic>>.from(
      (data.data['recovery_days'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final doctor = Map<String, dynamic>.from(data.data['doctor'] as Map);
    final fees = List<Map<String, dynamic>>.from(
      (data.data['fee_items'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final hasRecords = (data.data['medical_records'] as List).isNotEmpty;
    final hasImages = (data.data['imaging_results'] as List).isNotEmpty;
    final care = ref.watch(ownPatientCareProvider);
    final today = ref.watch(patientTodayProvider);
    final notifications = ref.watch(medicationNotificationShellProvider);
    final consultations = ref.watch(consultationListProvider);
    final textScale = MediaQuery.textScalerOf(context).scale(1);
    final cardScale = textScale.clamp(1.0, 1.6).toDouble();

    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            key: const Key('patient-dashboard-list'),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
            children: <Widget>[
              SizedBox(
                height: 320 * cardScale,
                child: _PatientSection(
                  title: 'Today',
                  child: _PatientTodayCard(
                    today: today,
                    notifications: notifications,
                    onRetry: () {
                      ref.invalidate(patientTodayProvider);
                      ref.invalidate(medicationNotificationShellProvider);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 192 * cardScale,
                child: _PatientSection(
                  title: 'Recovery Plan',
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      for (var index = 0; index < recoveryDays.length; index++)
                        Expanded(
                          child: Padding(
                            padding: EdgeInsets.only(
                              right: index == recoveryDays.length - 1 ? 0 : 5,
                            ),
                            child: _RecoveryDay(
                              day: recoveryDays[index],
                              index: index,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 244 * cardScale,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _PatientSection(
                        title: 'Contact Doctor',
                        child: _ContactDoctor(
                          doctor: doctor,
                          consultations: consultations,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: _PatientSection(
                        title: 'Medical Fee',
                        child: _MedicalFee(items: fees),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 334 * cardScale,
                child: const _PatientSection(
                  title: 'Ask Dr. AI',
                  child: _EducationalChatCard(),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 198 * cardScale,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Medical Record',
                        icon: Icons.description_outlined,
                        emptyLabel: hasRecords
                            ? 'Synthetic records available'
                            : 'No Medical Records',
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Imaging Results',
                        icon: Icons.document_scanner_outlined,
                        emptyLabel: hasImages
                            ? 'Synthetic images available'
                            : 'No Imaging Results',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              const SearchBar(
                hintText: 'Search synthetic dashboard',
                leading: Icon(Icons.search),
              ),
              const SizedBox(height: 4),
              Text(
                data.data['safety_label'] as String,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 260 * cardScale,
                child: _PatientSelfCareCard(
                  care: care,
                  onRetry: () => ref.invalidate(ownPatientCareProvider),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PatientTodayCard extends ConsumerWidget {
  const _PatientTodayCard({
    required this.today,
    required this.notifications,
    required this.onRetry,
  });

  final AsyncValue<PatientTodayData> today;
  final AsyncValue<MedicationNotificationScheduleResult> notifications;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final completionState = ref.watch(recoveryTaskCompletionControllerProvider);
    final locallyCompleted = completionState.hasValue
        ? completionState.value ?? const <String>{}
        : const <String>{};
    return today.when(
      loading: () =>
          const DashboardLoadingView(label: 'Loading today recovery tasks'),
      error: (error, stackTrace) => DashboardErrorView(
        message: 'Unable to load today recovery tasks. Try again.',
        onRetry: onRetry,
      ),
      data: (data) {
        if (data.tasks.isEmpty) {
          return const Center(
            child: Text('No active synthetic tasks for today.'),
          );
        }
        return ListView(
          key: const Key('patient-today-task-list'),
          children: <Widget>[
            if (data.activePlan != null) ...<Widget>[
              Text(
                data.activePlan!.title,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 2),
              Text(
                data.activePlan!.instructions,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '${data.progressSummary.completedTaskCount}/'
                '${data.progressSummary.taskCount} tasks complete - '
                '${data.progressSummary.completionPercent}%',
                key: const Key('patient-today-progress-summary'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
            ],
            notifications.when(
              loading: () => const Text(
                'Preparing local medication notification shell...',
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              error: (error, stackTrace) => const Text(
                'Local medication notification shell is unavailable.',
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              data: (result) => Text(
                result.label,
                key: const Key('patient-medication-notification-shell'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            completionState.when(
              data: (_) => const SizedBox.shrink(),
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: Text(
                  'Completion could not sync. Your local tap is still visible; try again when the connection recovers.',
                  style: TextStyle(color: DrAiColors.danger, fontSize: 12),
                ),
              ),
            ),
            for (final task in data.tasks)
              _TodayTaskTile(
                task: task,
                locallyCompleted: locallyCompleted.contains(task.taskId),
                isPending: completionState.isLoading,
                onComplete: () => ref
                    .read(recoveryTaskCompletionControllerProvider.notifier)
                    .complete(task.taskId),
              ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              data.safetyLabel,
              style: const TextStyle(color: DrAiColors.mutedInk, fontSize: 11),
            ),
          ],
        );
      },
    );
  }
}

class _EducationalChatCard extends ConsumerStatefulWidget {
  const _EducationalChatCard();

  @override
  ConsumerState<_EducationalChatCard> createState() =>
      _EducationalChatCardState();
}

class _EducationalChatCardState extends ConsumerState<_EducationalChatCard> {
  final _messageController = TextEditingController();
  final _chatScrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(educationalChatControllerProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_chatScrollController.hasClients) {
        _chatScrollController.jumpTo(
          _chatScrollController.position.maxScrollExtent,
        );
      }
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        const Text(
          'Educational information only - not medical advice.',
          style: TextStyle(
            color: DrAiColors.danger,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Expanded(
          child: ListView.builder(
            key: const Key('educational-chat-message-list'),
            controller: _chatScrollController,
            padding: const EdgeInsets.only(bottom: 2),
            itemCount: chat.messages.length,
            itemBuilder: (context, index) {
              final message = chat.messages[index];
              return _ChatBubble(message: message);
            },
          ),
        ),
        if (chat.errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(top: DrAiSpacing.xs),
            child: Text(
              chat.errorMessage!,
              style: const TextStyle(color: DrAiColors.danger, fontSize: 12),
            ),
          ),
        const SizedBox(height: DrAiSpacing.xs),
        Row(
          children: <Widget>[
            Expanded(
              child: TextField(
                key: const Key('educational-chat-input'),
                controller: _messageController,
                minLines: 1,
                maxLines: 2,
                maxLength: 800,
                keyboardType: TextInputType.text,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(
                  counterText: '',
                  isDense: true,
                  hintText: 'Prepare a question for your clinician',
                  prefixIcon: Icon(Icons.chat_bubble_outline),
                ),
              ),
            ),
            const SizedBox(width: DrAiSpacing.xs),
            IconButton.filled(
              key: const Key('educational-chat-send-button'),
              tooltip: 'Send educational question',
              onPressed: chat.isSending ? null : _send,
              icon: chat.isSending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send_outlined),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _send() async {
    final sent = await ref
        .read(educationalChatControllerProvider.notifier)
        .send(_messageController.text);
    if (sent && mounted) {
      _messageController.clear();
    }
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final ChatDisplayMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        key: Key('educational-chat-${message.role}-${message.id}'),
        constraints: const BoxConstraints(maxWidth: 520),
        margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        decoration: BoxDecoration(
          color: message.isRedFlag
              ? DrAiColors.patientAccent
              : isUser
              ? DrAiColors.brand
              : DrAiColors.surfaceSubtle,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (message.content.isEmpty)
              const Text(
                'Streaming response...',
                style: TextStyle(color: DrAiColors.mutedInk),
              )
            else
              Text(
                message.content,
                style: TextStyle(
                  color: isUser ? DrAiColors.white : DrAiColors.ink,
                  fontSize: 12,
                ),
              ),
            if (message.safetyLabel != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                message.safetyLabel!,
                style: const TextStyle(
                  color: DrAiColors.danger,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
            if (message.fallbackReason != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                'Fallback: ${message.fallbackReason}',
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 10,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TodayTaskTile extends StatelessWidget {
  const _TodayTaskTile({
    required this.task,
    required this.locallyCompleted,
    required this.isPending,
    required this.onComplete,
  });

  final RecoveryTaskItem task;
  final bool locallyCompleted;
  final bool isPending;
  final VoidCallback onComplete;

  @override
  Widget build(BuildContext context) {
    final completed = task.isCompleted || locallyCompleted;
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Material(
        color: completed ? DrAiColors.patientAccent : DrAiColors.surfaceSubtle,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          side: const BorderSide(color: DrAiColors.outline),
        ),
        child: CheckboxListTile(
          key: Key('today-task-${task.category}'),
          value: completed,
          onChanged: completed || isPending ? null : (_) => onComplete(),
          controlAffinity: ListTileControlAffinity.leading,
          secondary: Icon(_taskIcon(task.category), color: DrAiColors.brand),
          title: Text(
            task.title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          subtitle: Text(
            '${_taskLabel(task.category)} - ${task.dueLabel}'
            '${task.notificationTime == null ? '' : ' - ${task.notificationTime}'}\n'
            '${task.detail}',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ),
    );
  }
}

IconData _taskIcon(String category) {
  return switch (category) {
    'medication' => Icons.medication_outlined,
    'exercise' => Icons.directions_walk_outlined,
    'diet' => Icons.restaurant_outlined,
    'follow_up' => Icons.event_available_outlined,
    _ => Icons.check_circle_outline,
  };
}

String _taskLabel(String category) {
  return switch (category) {
    'medication' => 'Medication',
    'exercise' => 'Exercise',
    'diet' => 'Diet',
    'follow_up' => 'Follow-up',
    _ => 'Task',
  };
}

class _PatientSelfCareCard extends StatelessWidget {
  const _PatientSelfCareCard({required this.care, required this.onRetry});

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _PatientSection(
      title: 'Profile and Medications',
      child: care.when(
        loading: () =>
            const DashboardLoadingView(label: 'Loading synthetic care profile'),
        error: (error, stackTrace) => DashboardErrorView(
          message: 'Unable to load synthetic profile. Try again.',
          onRetry: onRetry,
        ),
        data: (bundle) => ListView(
          children: <Widget>[
            Text(
              bundle.patient.displayName,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            Text(
              bundle.patient.syntheticIdentifier,
              style: const TextStyle(color: DrAiColors.brand, fontSize: 12),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(_patientDemographicsLine(bundle.patient)),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.records.isEmpty
                  ? 'No Medical Records'
                  : '${bundle.records.length} synthetic medical record(s)',
              key: const Key('patient-self-records'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.imagingAssets.isEmpty
                  ? 'No imaging assets'
                  : '${bundle.imagingAssets.length} imaging asset(s): '
                        '${bundle.imagingAssets.first.uploadStatus} / '
                        '${bundle.imagingAssets.first.reviewStatus}',
              key: const Key('patient-self-imaging-assets'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _patientHistorySummary(bundle),
              key: const Key('patient-self-history-summary'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            _PatientEventUpdatePanel(bundle: bundle),
            const SizedBox(height: DrAiSpacing.xs),
            if (bundle.medications.isEmpty)
              const Text('No synthetic medications')
            else
              for (final medication in bundle.medications)
                Padding(
                  padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.surfaceSubtle,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.xs),
                      child: Text(
                        '${medication.name}\n${medication.dosage} - ${medication.schedule}',
                      ),
                    ),
                  ),
                ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.prescriptions.isEmpty
                  ? 'No prescriptions'
                  : '${bundle.prescriptions.length} prescription(s)',
              key: const Key('patient-self-prescriptions'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (bundle.medicationReminders.isEmpty)
              const Text('No medication reminders')
            else
              for (final reminder in bundle.medicationReminders)
                Padding(
                  padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.surfaceSubtle,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.xs),
                      child: Text(
                        '${reminder.reminderType == 'refill' ? 'Refill' : 'Medication'} reminder\n'
                        '${reminder.scheduleLabel} - ${reminder.status}',
                      ),
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class _PatientEventUpdatePanel extends ConsumerStatefulWidget {
  const _PatientEventUpdatePanel({required this.bundle});

  final PatientCareBundle bundle;

  @override
  ConsumerState<_PatientEventUpdatePanel> createState() =>
      _PatientEventUpdatePanelState();
}

class _PatientEventUpdatePanelState
    extends ConsumerState<_PatientEventUpdatePanel> {
  final _summaryController = TextEditingController(
    text: 'Synthetic patient update for the care episode.',
  );
  String _updateType = 'general_update';
  String? _validationError;

  @override
  void dispose() {
    _summaryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final event = widget.bundle.clinicalEvents.isEmpty
        ? null
        : widget.bundle.clinicalEvents.first;
    final state = ref.watch(clinicalEventUpdateControllerProvider);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              event == null
                  ? 'No Clinical Event available for patient update'
                  : 'Update: ${event.title}',
              key: const Key('patient-event-update-title'),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            if (widget.bundle.clinicalEventUpdates.isNotEmpty)
              Text(
                'Latest patient update: ${widget.bundle.clinicalEventUpdates.first.summary}',
                key: const Key('patient-event-latest-update'),
              ),
            if (event != null) ...<Widget>[
              const SizedBox(height: 4),
              DropdownButtonFormField<String>(
                key: const Key('patient-event-update-type-field'),
                initialValue: _updateType,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Update type',
                  isDense: true,
                ),
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'general_update',
                    child: Text('General update'),
                  ),
                  DropdownMenuItem(
                    value: 'symptom_update',
                    child: Text('Symptom update'),
                  ),
                  DropdownMenuItem(
                    value: 'medication_note',
                    child: Text('Medication note'),
                  ),
                  DropdownMenuItem(
                    value: 'recovery_check_in',
                    child: Text('Recovery check-in'),
                  ),
                ],
                onChanged: (value) =>
                    setState(() => _updateType = value ?? 'general_update'),
              ),
              const SizedBox(height: 4),
              TextField(
                key: const Key('patient-event-update-summary-field'),
                controller: _summaryController,
                maxLength: 1200,
                minLines: 1,
                maxLines: 2,
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Self-reported update',
                  isDense: true,
                ),
              ),
              if (_validationError != null)
                Text(
                  _validationError!,
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              state.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, stackTrace) =>
                    Text(_patientSafeErrorMessage(error)),
                data: (update) => update == null
                    ? const SizedBox.shrink()
                    : Text('Update submitted: ${update.updateType}'),
              ),
              const SizedBox(height: 4),
              FilledButton.icon(
                key: const Key('patient-event-update-submit-button'),
                onPressed: state.isLoading ? null : () => _submit(event.id),
                icon: const Icon(Icons.send_outlined),
                label: const Text('Send update'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _submit(String eventId) {
    if (_summaryController.text.trim().length < 3) {
      setState(() => _validationError = 'Enter a short update first.');
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(clinicalEventUpdateControllerProvider.notifier)
        .submit(
          clinicalEventId: eventId,
          updateType: _updateType,
          summary: _summaryController.text.trim(),
        );
  }
}

String _patientDemographicsLine(PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null) 'Born ${patient.birthYear}',
    if (patient.sex != null) patient.sex!,
    if (patient.preferredLanguage != null) patient.preferredLanguage!,
    if (patient.contactPreference != null) patient.contactPreference!,
  ];
  return values.isEmpty ? 'Demographics not recorded' : values.join(' - ');
}

String _patientHistorySummary(PatientCareBundle bundle) {
  return <String>[
    'Allergies: ${_patientLabelsOrEmpty(bundle.allergies)}',
    'Chronic diseases: ${_patientConditionsOrEmpty(bundle.chronicDiseases)}',
    'Visit history: ${bundle.visitHistory.length}',
    'Diagnoses: ${_patientDiagnosesOrEmpty(bundle.diagnoses)}',
  ].join('\n');
}

String _patientLabelsOrEmpty(List<PatientAllergyItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.label).join(', ');
}

String _patientConditionsOrEmpty(List<ChronicDiseaseItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.name).join(', ');
}

String _patientDiagnosesOrEmpty(List<DiagnosisItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.label).join(', ');
}

class _PatientSection extends StatelessWidget {
  const _PatientSection({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              style: const TextStyle(
                color: DrAiColors.white,
                fontSize: 16,
                height: 1.4,
              ),
            ),
          ),
          Expanded(
            child: Padding(padding: const EdgeInsets.all(5), child: child),
          ),
        ],
      ),
    );
  }
}

class _RecoveryDay extends StatelessWidget {
  const _RecoveryDay({required this.day, required this.index});

  final Map<String, dynamic> day;
  final int index;

  @override
  Widget build(BuildContext context) {
    final tasks = List<String>.from(day['tasks'] as List);
    final colors = <Color>[
      DrAiColors.accentCyan,
      DrAiColors.accentBlue,
      DrAiColors.accentIndigo,
      DrAiColors.accentOrange,
      DrAiColors.accentMint,
    ];
    return Container(
      padding: const EdgeInsets.all(5),
      decoration: BoxDecoration(
        color: DrAiColors.brandDark,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        children: <Widget>[
          Text(
            day['label'] as String,
            style: const TextStyle(
              color: DrAiColors.white,
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 5),
          for (var taskIndex = 0; taskIndex < tasks.length; taskIndex++)
            Expanded(
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 5),
                padding: const EdgeInsets.symmetric(horizontal: 4),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: colors[(taskIndex + index) % colors.length],
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Text(
                  tasks[taskIndex],
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: DrAiColors.white,
                    fontSize: 10,
                    height: 1.2,
                  ),
                ),
              ),
            ),
          SizedBox(
            height: 24,
            child: Semantics(
              button: true,
              enabled: false,
              label: 'See more recovery tasks unavailable in summary',
              child: ExcludeSemantics(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.patientAccent,
                    borderRadius: BorderRadius.circular(DrAiRadii.pill),
                  ),
                  child: const Center(
                    child: Text(
                      '+  See More',
                      style: TextStyle(
                        fontSize: 10,
                        color: DrAiColors.brandDark,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ContactDoctor extends StatelessWidget {
  const _ContactDoctor({required this.doctor, required this.consultations});

  final Map<String, dynamic> doctor;
  final AsyncValue<ConsultationListData> consultations;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DrAiSpacing.xs),
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            doctor['name'] as String,
            style: const TextStyle(
              color: DrAiColors.white,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
          Text(
            doctor['title'] as String,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: DrAiColors.white),
          ),
          const Spacer(),
          Row(
            children: <Widget>[
              const CircleAvatar(
                radius: 18,
                backgroundColor: DrAiColors.white,
                child: Icon(Icons.person, color: DrAiColors.brand),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: Text(
                  doctor['expertise'] as String,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: DrAiColors.outlineMuted),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.xs),
          consultations.when(
            loading: () => const Text(
              'Checking specialist status...',
              style: TextStyle(color: DrAiColors.outlineMuted, fontSize: 11),
            ),
            error: (error, stackTrace) => Text(
              _patientSafeErrorMessage(error),
              style: const TextStyle(
                color: DrAiColors.outlineMuted,
                fontSize: 11,
              ),
            ),
            data: (data) {
              if (data.items.isEmpty) {
                return const Text(
                  'No specialist request yet',
                  style: TextStyle(
                    color: DrAiColors.outlineMuted,
                    fontSize: 11,
                  ),
                );
              }
              final latest = data.items.first;
              return Text(
                'Specialist: ${latest.status} - ${latest.specialty}',
                key: const Key('patient-consultation-status'),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DrAiColors.patientAccent,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _MedicalFee extends StatelessWidget {
  const _MedicalFee({required this.items});

  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: DrAiColors.brandDark,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        children: <Widget>[
          for (final item in items)
            Expanded(
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      '${item['label']}\n${item['amount']}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: DrAiColors.white,
                        fontSize: 10,
                        height: 1.15,
                      ),
                    ),
                  ),
                  Checkbox(
                    value: item['selected'] as bool,
                    onChanged: null,
                    side: const BorderSide(color: DrAiColors.patientAccent),
                  ),
                ],
              ),
            ),
          SizedBox(
            height: 32,
            child: Semantics(
              button: true,
              enabled: false,
              label: 'Pay now unavailable in Week 1',
              child: ExcludeSemantics(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.inkStrong,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: const Center(
                    child: Text(
                      'Pay Now',
                      style: TextStyle(color: DrAiColors.outlineMuted),
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 2),
          const Text(
            'Visual placeholder only',
            style: TextStyle(color: DrAiColors.outlineMuted, fontSize: 9),
          ),
        ],
      ),
    );
  }
}

class _EmptyFeatureCard extends StatelessWidget {
  const _EmptyFeatureCard({
    required this.title,
    required this.icon,
    required this.emptyLabel,
  });

  final String title;
  final IconData icon;
  final String emptyLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(color: DrAiColors.white),
            ),
          ),
          Expanded(
            child: DecoratedBox(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    DrAiColors.surfaceSubtle,
                    DrAiColors.patientAccent,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.vertical(
                  bottom: Radius.circular(DrAiRadii.md),
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Icon(icon, size: 50, color: DrAiColors.brand),
                  const SizedBox(height: DrAiSpacing.xs),
                  Text(
                    emptyLabel,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: DrAiColors.black),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

String _patientSafeErrorMessage(Object error) {
  if (error is ApiError) {
    if (error.code == 'rate_limited') {
      return 'Educational chat is temporarily rate limited.';
    }
    if (error.code == 'service_unavailable') {
      return 'Unable to reach Dr. AI.';
    }
    return error.message;
  }
  return 'Unable to reach Dr. AI.';
}
