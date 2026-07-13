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
      selectedIndex: role == AppRole.doctor ? 2 : 1,
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
      selectedIndex: widget.role == AppRole.doctor ? 2 : 1,
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
