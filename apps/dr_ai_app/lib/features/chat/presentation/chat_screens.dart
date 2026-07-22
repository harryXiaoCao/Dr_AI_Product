import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ServiceChatScreen extends StatelessWidget {
  const ServiceChatScreen({
    required this.role,
    required this.isSystem,
    super.key,
  });

  final AppRole role;
  final bool isSystem;

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: role,
      selectedIndex: role == AppRole.doctor ? 3 : 1,
      child: _ChatPageFrame(
        title: isSystem
            ? context.l10n.systemNotifications
            : context.l10n.aiAssistant,
        subtitle: isSystem
            ? context.l10n.systemNotificationsSubtitle
            : context.l10n.aiAssistantSubtitle,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(
              isSystem
                  ? Icons.notifications_none_rounded
                  : Icons.auto_awesome_rounded,
              size: 44,
              color: isSystem
                  ? const Color(0xFF087F5B)
                  : DrAiColors.accentIndigo,
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              isSystem
                  ? context.l10n.noSystemNotifications
                  : context.l10n.aiAvailablePhase3,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: DrAiColors.ink,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              isSystem
                  ? context.l10n.systemReadOnlyNotice
                  : context.l10n.aiPlaceholderNotice,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PatientAiChatScreen extends ConsumerStatefulWidget {
  const PatientAiChatScreen({super.key});

  @override
  ConsumerState<PatientAiChatScreen> createState() =>
      _PatientAiChatScreenState();
}

class _PatientAiChatScreenState extends ConsumerState<PatientAiChatScreen> {
  final _controller = TextEditingController();
  final _messages = <_AiSessionMessage>[];
  List<PatientChatThreadSummary> _threads = const <PatientChatThreadSummary>[];
  String? _threadId;
  bool _sending = false;
  bool _loadingHistory = false;
  bool _historyOpen = true;
  bool _historyWidthInitialized = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _refreshThreads();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_historyWidthInitialized) {
      _historyOpen = MediaQuery.sizeOf(context).width >= 900;
      _historyWidthInitialized = true;
    }
  }

  Future<void> _refreshThreads() async {
    try {
      final threads = await ref
          .read(repositoryProvider)
          .loadEducationalChatThreads();
      if (mounted) setState(() => _threads = threads);
    } catch (_) {
      // A fresh chat remains usable when history cannot be loaded.
    }
  }

  void _startNewChat() {
    setState(() {
      _threadId = null;
      _messages.clear();
      _error = null;
    });
  }

  Future<void> _openThread(PatientChatThreadSummary thread) async {
    if (_loadingHistory || thread.threadId == _threadId) return;
    setState(() {
      _loadingHistory = true;
      _error = null;
    });
    try {
      final history = await ref
          .read(repositoryProvider)
          .loadEducationalChatThread(thread.threadId);
      if (!mounted) return;
      setState(() {
        _threadId = thread.threadId;
        _messages
          ..clear()
          ..addAll(history.messages.map(_AiSessionMessage.fromHistory));
      });
    } catch (_) {
      if (mounted) setState(() => _error = context.l10n.conversationLoadFailed);
    } finally {
      if (mounted) setState(() => _loadingHistory = false);
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.length < 2 || _sending) return;
    setState(() {
      _messages.add(_AiSessionMessage.user(text));
      _sending = true;
      _error = null;
    });
    _controller.clear();
    try {
      final language = Localizations.localeOf(context).languageCode == 'zh'
          ? 'zh-Hans'
          : 'en';
      final response = await ref
          .read(repositoryProvider)
          .sendEducationalChatMessage(
            threadId: _threadId,
            message: text,
            language: language,
          );
      if (mounted) {
        setState(() {
          _threadId = response.threadId;
          _messages.add(_AiSessionMessage.assistant(response));
        });
        await _refreshThreads();
      }
    } catch (_) {
      if (mounted) setState(() => _error = context.l10n.aiChatSendFailed);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  void _handleSuggestedAction(String action) {
    switch (action) {
      case 'review_measurement_guidance':
        _controller.text = context.l10n.aiMeasurementGuidancePrompt;
        return;
      case 'track_measurements':
        _controller.text = context.l10n.aiTrackMeasurementsPrompt;
        return;
      case 'prepare_doctor_questions':
        _controller.text = context.l10n.aiSuggestionDoctor;
        return;
      case 'prepare_symptom_summary':
        _controller.text = context.l10n.aiPrepareSymptomSummaryPrompt;
        return;
      case 'contact_connected_doctor':
        context.go('/patient/contact');
        return;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 1,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1180),
              child: Padding(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        IconButton(
                          onPressed: () => context.pop(),
                          tooltip: 'Back',
                          icon: const Icon(Icons.arrow_back_rounded),
                        ),
                        IconButton(
                          key: const Key('patient-ai-history-toggle'),
                          onPressed: () =>
                              setState(() => _historyOpen = !_historyOpen),
                          tooltip: context.l10n.aiChatHistory,
                          icon: Icon(
                            _historyOpen
                                ? Icons.menu_open_rounded
                                : Icons.history_rounded,
                          ),
                        ),
                        const SizedBox(width: DrAiSpacing.xs),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                context.l10n.aiAssistant,
                                style: Theme.of(context).textTheme.headlineSmall
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              Text(
                                context.l10n.aiChatSubtitle,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: DrAiColors.inkSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        FilledButton.tonalIcon(
                          key: const Key('patient-ai-new-chat'),
                          onPressed: _startNewChat,
                          icon: const Icon(Icons.add_comment_outlined),
                          label: Text(context.l10n.aiNewChat),
                        ),
                      ],
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(
                          color: DrAiColors.white,
                          border: Border.all(color: DrAiColors.outline),
                          borderRadius: BorderRadius.circular(DrAiRadii.lg),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Row(
                          children: <Widget>[
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 220),
                              curve: Curves.easeOutCubic,
                              width: _historyOpen ? 264 : 0,
                              child: _historyOpen
                                  ? _AiThreadSidebar(
                                      threads: _threads,
                                      selectedThreadId: _threadId,
                                      loading: _loadingHistory,
                                      onNewChat: _startNewChat,
                                      onThreadSelected: _openThread,
                                    )
                                  : const SizedBox.shrink(),
                            ),
                            Expanded(child: _buildConversation()),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildConversation() {
    return Padding(
      padding: const EdgeInsets.all(DrAiSpacing.md),
      child: Column(
        children: <Widget>[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(DrAiSpacing.sm),
            decoration: BoxDecoration(
              color: DrAiColors.accentIndigo.withValues(alpha: 0.07),
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(
                  Icons.verified_user_outlined,
                  size: 19,
                  color: DrAiColors.accentIndigo,
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    context.l10n.aiChatSafetyNotice,
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Expanded(
            child: _loadingHistory
                ? Center(child: Text(context.l10n.loadingConversation))
                : _messages.isEmpty
                ? _AiChatWelcome(
                    onSuggestion: (value) => _controller.text = value,
                  )
                : ListView.builder(
                    key: const Key('patient-ai-message-list'),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) => _AiMessageBubble(
                      message: _messages[index],
                      onSuggestedAction: _handleSuggestedAction,
                    ),
                  ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
              child: Text(
                _error!,
                style: const TextStyle(color: DrAiColors.danger),
              ),
            ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              Expanded(
                child: TextField(
                  key: const Key('patient-ai-input'),
                  controller: _controller,
                  minLines: 1,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: context.l10n.aiChatInputHint,
                    prefixIcon: const Icon(Icons.health_and_safety_outlined),
                  ),
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              IconButton.filled(
                key: const Key('patient-ai-send'),
                onPressed: _sending ? null : _send,
                tooltip: context.l10n.sendMessage,
                icon: _sending
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_rounded),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _AiThreadSidebar extends StatelessWidget {
  const _AiThreadSidebar({
    required this.threads,
    required this.selectedThreadId,
    required this.loading,
    required this.onNewChat,
    required this.onThreadSelected,
  });

  final List<PatientChatThreadSummary> threads;
  final String? selectedThreadId;
  final bool loading;
  final VoidCallback onNewChat;
  final ValueChanged<PatientChatThreadSummary> onThreadSelected;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Color(0xFFF7F8FC),
        border: Border(right: BorderSide(color: DrAiColors.outline)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: onNewChat,
                icon: const Icon(Icons.add_rounded),
                label: Text(context.l10n.aiNewChat),
              ),
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.aiPreviousChats,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Expanded(
              child: threads.isEmpty
                  ? Text(
                      context.l10n.aiNoPreviousChats,
                      style: const TextStyle(color: DrAiColors.inkSecondary),
                    )
                  : ListView.builder(
                      key: const Key('patient-ai-thread-list'),
                      itemCount: threads.length,
                      itemBuilder: (context, index) {
                        final thread = threads[index];
                        final selected = thread.threadId == selectedThreadId;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: ListTile(
                            key: Key('patient-ai-thread-${thread.threadId}'),
                            selected: selected,
                            enabled: !loading,
                            dense: true,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(DrAiRadii.md),
                            ),
                            leading: const Icon(
                              Icons.chat_bubble_outline,
                              size: 19,
                            ),
                            title: Text(
                              thread.title,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            onTap: () => onThreadSelected(thread),
                          ),
                        );
                      },
                    ),
            ),
            Text(
              context.l10n.aiHistoryRetentionNotice,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 11,
                height: 1.35,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AiChatWelcome extends StatelessWidget {
  const _AiChatWelcome({required this.onSuggestion});
  final ValueChanged<String> onSuggestion;

  @override
  Widget build(BuildContext context) {
    final suggestions = <String>[
      context.l10n.aiSuggestionSymptoms,
      context.l10n.aiSuggestionEducation,
      context.l10n.aiSuggestionMedication,
    ];
    return ListView(
      children: <Widget>[
        const SizedBox(height: DrAiSpacing.lg),
        const Icon(
          Icons.auto_awesome_rounded,
          size: 42,
          color: DrAiColors.accentIndigo,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        Text(
          context.l10n.aiChatWelcome,
          textAlign: TextAlign.center,
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.md),
        for (final suggestion in suggestions)
          Padding(
            padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
            child: OutlinedButton(
              onPressed: () => onSuggestion(suggestion),
              child: Text(suggestion, textAlign: TextAlign.left),
            ),
          ),
      ],
    );
  }
}

class _AiSessionMessage {
  const _AiSessionMessage({
    required this.isUser,
    required this.text,
    this.result,
  });

  factory _AiSessionMessage.user(String text) =>
      _AiSessionMessage(isUser: true, text: text);

  factory _AiSessionMessage.assistant(ChatMessageResult result) =>
      _AiSessionMessage(isUser: false, text: result.content, result: result);

  factory _AiSessionMessage.fromHistory(PatientChatHistoryMessage message) {
    return _AiSessionMessage(
      isUser: message.role == 'user',
      text: message.content,
      result: message.response,
    );
  }

  final bool isUser;
  final String text;
  final ChatMessageResult? result;
}

class _AiMessageBubble extends StatelessWidget {
  const _AiMessageBubble({
    required this.message,
    required this.onSuggestedAction,
  });
  final _AiSessionMessage message;
  final ValueChanged<String> onSuggestedAction;

  @override
  Widget build(BuildContext context) {
    final result = message.result;
    final emergency = result?.isRedFlag ?? false;
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 560),
        margin: const EdgeInsets.only(bottom: DrAiSpacing.sm),
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        decoration: BoxDecoration(
          color: message.isUser
              ? DrAiColors.brand
              : emergency
              ? DrAiColors.danger.withValues(alpha: 0.08)
              : DrAiColors.pageBackground,
          border: message.isUser
              ? null
              : Border.all(
                  color: emergency ? DrAiColors.danger : DrAiColors.outline,
                ),
          borderRadius: BorderRadius.circular(DrAiRadii.lg),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (message.isUser || result == null)
              Text(
                message.text,
                style: TextStyle(
                  color: message.isUser ? DrAiColors.white : DrAiColors.ink,
                  height: 1.45,
                ),
              )
            else
              for (
                var index = 0;
                index < result.responseChunks.length;
                index++
              ) ...<Widget>[
                if (index > 0) const SizedBox(height: DrAiSpacing.sm),
                Text(
                  result.responseChunks[index],
                  style: const TextStyle(color: DrAiColors.ink, height: 1.5),
                ),
              ],
            if (result != null && result.uncertainties.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Container(
                key: const Key('patient-ai-uncertainty'),
                width: double.infinity,
                padding: const EdgeInsets.all(DrAiSpacing.xs),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF3C4),
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Icon(
                      Icons.warning_amber_rounded,
                      size: 18,
                      color: Color(0xFF6A4C00),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            context.l10n.aiImportantUncertainty,
                            style: const TextStyle(
                              color: Color(0xFF6A4C00),
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          for (final uncertainty in result.uncertainties)
                            Padding(
                              padding: const EdgeInsets.only(top: 3),
                              child: Text(
                                uncertainty,
                                style: const TextStyle(
                                  color: Color(0xFF6A4C00),
                                  height: 1.35,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (result != null && result.sources.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Text(
                context.l10n.aiSources,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              for (final source in result.sources)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '${source.number}. ${source.title} · ${source.publisher} · '
                    '${source.lastMedicalReviewDate}',
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      fontSize: 12,
                      height: 1.35,
                    ),
                  ),
                ),
            ],
            if (result != null && result.contextUsed.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Row(
                children: <Widget>[
                  const Icon(
                    Icons.person_search_outlined,
                    size: 16,
                    color: DrAiColors.accentIndigo,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      context.l10n.aiContextUsed,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                  ),
                ],
              ),
              for (final item in result.contextUsed)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '${_contextCategoryLabel(context, item.category)} · '
                    '${_contextProvenanceLabel(context, item.provenance)} · '
                    '${item.recordedOn}',
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      fontSize: 12,
                      height: 1.35,
                    ),
                  ),
                ),
            ],
            if (result?.limitation != null) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Text(
                result!.limitation!,
                style: const TextStyle(
                  color: DrAiColors.inkSecondary,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ],
            if (result?.followUpQuestion != null) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(DrAiSpacing.xs),
                decoration: BoxDecoration(
                  color: DrAiColors.accentIndigo.withValues(alpha: 0.07),
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      context.l10n.aiFollowUpQuestion,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 4),
                    Text(result!.followUpQuestion!),
                  ],
                ),
              ),
            ],
            if (result != null &&
                result.suggestedActionCodes.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: result.suggestedActionCodes
                    .where(
                      (action) =>
                          action != 'ask_clarifying_question' &&
                          action != 'call_120' &&
                          action != 'none',
                    )
                    .map(
                      (action) => ActionChip(
                        avatar: Icon(_actionIcon(action), size: 16),
                        label: Text(_actionLabel(context, action)),
                        onPressed: () => onSuggestedAction(action),
                      ),
                    )
                    .toList(),
              ),
            ],
            if (result?.nextActionCode == 'contact_connected_doctor' &&
                !(result?.suggestedActionCodes.contains(
                      'contact_connected_doctor',
                    ) ??
                    false)) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              TextButton.icon(
                onPressed: () => context.go('/patient/contact'),
                icon: const Icon(Icons.medical_services_outlined),
                label: Text(context.l10n.aiContactDoctor),
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _actionIcon(String action) {
    return switch (action) {
      'review_measurement_guidance' => Icons.monitor_heart_outlined,
      'track_measurements' => Icons.edit_note_rounded,
      'prepare_doctor_questions' => Icons.fact_check_outlined,
      'prepare_symptom_summary' => Icons.format_list_bulleted_rounded,
      'contact_connected_doctor' => Icons.medical_services_outlined,
      _ => Icons.arrow_forward_rounded,
    };
  }

  String _actionLabel(BuildContext context, String action) {
    return switch (action) {
      'review_measurement_guidance' => context.l10n.aiReviewMeasurementGuidance,
      'track_measurements' => context.l10n.aiTrackMeasurements,
      'prepare_doctor_questions' => context.l10n.aiPrepareDoctorQuestions,
      'prepare_symptom_summary' => context.l10n.aiPrepareSymptomSummary,
      'contact_connected_doctor' => context.l10n.aiContactDoctor,
      _ => action,
    };
  }

  String _contextCategoryLabel(BuildContext context, String category) {
    return switch (category) {
      'profile' => context.l10n.aiContextProfile,
      'measurements' => context.l10n.aiContextMeasurements,
      'conditions' => context.l10n.aiContextConditions,
      'medications' => context.l10n.aiContextMedications,
      'clinical_events' => context.l10n.aiContextClinicalEvents,
      'recovery_plan' => context.l10n.aiContextRecoveryPlan,
      _ => category,
    };
  }

  String _contextProvenanceLabel(BuildContext context, String provenance) {
    return switch (provenance) {
      'patient_profile' => context.l10n.aiContextFromProfile,
      'patient_reported' => context.l10n.aiContextPatientReported,
      'doctor_record' => context.l10n.aiContextDoctorRecord,
      'current_prescription' => context.l10n.aiContextCurrentPrescription,
      'medication_schedule' => context.l10n.aiContextMedicationSchedule,
      'recovery_plan' => context.l10n.aiContextCurrentRecoveryPlan,
      _ => provenance,
    };
  }
}

class PrivateChatScreen extends ConsumerStatefulWidget {
  const PrivateChatScreen({
    required this.role,
    required this.contactId,
    required this.contactName,
    super.key,
  });

  final AppRole role;
  final String contactId;
  final String contactName;

  @override
  ConsumerState<PrivateChatScreen> createState() => _PrivateChatScreenState();
}

class _PrivateChatScreenState extends ConsumerState<PrivateChatScreen> {
  final _controller = TextEditingController();
  bool _sending = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .sendPrivateMessage(widget.contactId, text);
      _controller.clear();
      ref.invalidate(privateMessagesProvider(widget.contactId));
    } catch (_) {
      setState(() => _error = context.l10n.messageSendFailed);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(privateMessagesProvider(widget.contactId));
    return ResponsiveAppShell(
      role: widget.role,
      selectedIndex: widget.role == AppRole.doctor ? 3 : 1,
      child: _ChatPageFrame(
        title: widget.contactName,
        subtitle: context.l10n.privateCareConversation,
        child: Column(
          children: <Widget>[
            Expanded(
              child: messages.when(
                loading: () => DashboardLoadingView(
                  label: context.l10n.loadingConversation,
                ),
                error: (error, stackTrace) => DashboardErrorView(
                  message: context.l10n.conversationLoadFailed,
                  onRetry: () =>
                      ref.invalidate(privateMessagesProvider(widget.contactId)),
                ),
                data: (data) =>
                    _MessageList(messages: data.items, role: widget.role),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                child: Text(
                  _error!,
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              ),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('private-message-input'),
                    controller: _controller,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.newline,
                    decoration: InputDecoration(
                      hintText: context.l10n.writeMessage,
                      prefixIcon: const Icon(Icons.chat_bubble_outline),
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.sm),
                IconButton.filled(
                  key: const Key('private-message-send'),
                  onPressed: _sending ? null : _send,
                  tooltip: context.l10n.sendMessage,
                  icon: _sending
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send_rounded),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageList extends StatelessWidget {
  const _MessageList({required this.messages, required this.role});
  final List<PrivateMessage> messages;
  final AppRole role;

  @override
  Widget build(BuildContext context) {
    if (messages.isEmpty) {
      return Center(
        child: Text(
          context.l10n.noPrivateMessages,
          textAlign: TextAlign.center,
          style: const TextStyle(color: DrAiColors.inkSecondary),
        ),
      );
    }
    return ListView.builder(
      key: const Key('private-message-list'),
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.md),
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final message = messages[index];
        final mine = message.senderRole == role.name;
        return Align(
          alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            constraints: const BoxConstraints(maxWidth: 520),
            margin: const EdgeInsets.only(bottom: DrAiSpacing.sm),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: mine ? DrAiColors.brand : DrAiColors.white,
              border: mine ? null : Border.all(color: DrAiColors.outline),
              borderRadius: BorderRadius.circular(DrAiRadii.lg),
            ),
            child: Text(
              message.content,
              style: TextStyle(
                color: mine ? DrAiColors.white : DrAiColors.ink,
                height: 1.4,
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ChatPageFrame extends StatelessWidget {
  const _ChatPageFrame({
    required this.title,
    required this.subtitle,
    required this.child,
  });
  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: DrAiColors.pageBackground,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: Padding(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                IconButton(
                  onPressed: () => context.pop(),
                  tooltip: 'Back',
                  icon: const Icon(Icons.arrow_back_rounded),
                ),
                Text(
                  title,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.ink,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
                const SizedBox(height: DrAiSpacing.md),
                Expanded(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(DrAiSpacing.md),
                    decoration: BoxDecoration(
                      color: DrAiColors.white,
                      border: Border.all(color: DrAiColors.outline),
                      borderRadius: BorderRadius.circular(DrAiRadii.xl),
                    ),
                    child: child,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
