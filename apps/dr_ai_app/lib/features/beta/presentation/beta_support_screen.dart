import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class BetaSupportScreen extends ConsumerStatefulWidget {
  const BetaSupportScreen({super.key});

  @override
  ConsumerState<BetaSupportScreen> createState() => _BetaSupportScreenState();
}

class _BetaSupportScreenState extends ConsumerState<BetaSupportScreen> {
  final _feedbackController = TextEditingController();
  final _deletionController = TextEditingController();
  bool _understandsDataBoundary = false;
  bool _understandsNoEmergencyUse = false;
  bool _understandsNoRealData = false;
  bool _deletionPrepared = false;
  bool _feedbackPrepared = false;

  @override
  void dispose() {
    _feedbackController.dispose();
    _deletionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authControllerProvider).value?.user;
    final content = ColoredBox(
      color: DrAiColors.pageBackground,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 960),
          child: ListView(
            key: const Key('beta-support-list'),
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              _BetaHero(displayName: user?.displayName),
              const SizedBox(height: DrAiSpacing.md),
              _BetaSection(
                key: const Key('beta-privacy-section'),
                icon: Icons.privacy_tip_outlined,
                title: context.l10n.privacyAndDataNotice,
                children: <Widget>[
                  _BetaText(context.l10n.privacyNoticeBody),
                  _BetaBullet(context.l10n.privacyNoData),
                  _BetaBullet(context.l10n.privacyBackendKeys),
                  _BetaBullet(context.l10n.privacyChatBoundary),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-consent-section'),
                icon: Icons.fact_check_outlined,
                title: context.l10n.consentChecklist,
                children: <Widget>[
                  _ConsentCheckbox(
                    key: const Key('consent-synthetic-only-checkbox'),
                    value: _understandsDataBoundary,
                    onChanged: (value) => setState(
                      () => _understandsDataBoundary = value ?? false,
                    ),
                    label: context.l10n.consentStagingData,
                  ),
                  _ConsentCheckbox(
                    key: const Key('consent-no-emergency-checkbox'),
                    value: _understandsNoEmergencyUse,
                    onChanged: (value) => setState(
                      () => _understandsNoEmergencyUse = value ?? false,
                    ),
                    label: context.l10n.consentNoEmergency,
                  ),
                  _ConsentCheckbox(
                    key: const Key('consent-no-real-data-checkbox'),
                    value: _understandsNoRealData,
                    onChanged: (value) =>
                        setState(() => _understandsNoRealData = value ?? false),
                    label: context.l10n.consentNoRealData,
                  ),
                  _PreparedStatus(
                    label: _consentReady
                        ? context.l10n.consentReady
                        : context.l10n.consentIncomplete,
                    isReady: _consentReady,
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-deletion-section'),
                icon: Icons.manage_accounts_outlined,
                title: context.l10n.accountDeletionRequest,
                children: <Widget>[
                  _BetaText(context.l10n.deletionLocalOnly),
                  TextField(
                    key: const Key('account-deletion-confirm-field'),
                    controller: _deletionController,
                    decoration: InputDecoration(
                      labelText: context.l10n.deletionPrompt,
                      border: const OutlineInputBorder(),
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  FilledButton.icon(
                    key: const Key('account-deletion-prepare-button'),
                    onPressed: _deletionReady ? _showDeletionPrepared : null,
                    icon: const Icon(Icons.description_outlined),
                    label: Text(context.l10n.prepareRequest),
                  ),
                  if (_deletionPrepared) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.xs),
                    _PreparedStatus(
                      label: context.l10n.deletionPrepared,
                      isReady: true,
                      statusKey: Key('account-deletion-prepared-status'),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-feedback-section'),
                icon: Icons.feedback_outlined,
                title: context.l10n.feedbackForm,
                children: <Widget>[
                  _BetaText(context.l10n.feedbackPrivacy),
                  TextField(
                    key: const Key('beta-feedback-field'),
                    controller: _feedbackController,
                    minLines: 3,
                    maxLines: 5,
                    decoration: InputDecoration(
                      labelText: context.l10n.feedbackDraft,
                      hintText: context.l10n.feedbackHint,
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  FilledButton.icon(
                    key: const Key('beta-feedback-prepare-button'),
                    onPressed: _showFeedbackPrepared,
                    icon: const Icon(Icons.assignment_turned_in_outlined),
                    label: Text(context.l10n.prepareFeedback),
                  ),
                  if (_feedbackPrepared) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.xs),
                    _PreparedStatus(
                      label: context.l10n.feedbackPrepared,
                      isReady: true,
                      statusKey: Key('beta-feedback-prepared-status'),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-limitations-section'),
                icon: Icons.report_gmailerrorred_outlined,
                title: context.l10n.knownLimitations,
                children: <Widget>[
                  _BetaBullet(context.l10n.limitationClinical),
                  _BetaBullet(context.l10n.limitationUpload),
                  _BetaBullet(context.l10n.limitationRecovery),
                  _BetaBullet(context.l10n.limitationRelease),
                ],
              ),
            ],
          ),
        ),
      ),
    );
    if (user == null) {
      return Scaffold(
        appBar: AppBar(
          title: Text(context.l10n.privacySupportTitle),
          actions: <Widget>[
            TextButton(
              onPressed: () => context.go('/login'),
              child: Text(context.l10n.signIn),
            ),
          ],
        ),
        body: content,
      );
    }
    return ResponsiveAppShell(role: user.role, child: content);
  }

  bool get _consentReady =>
      _understandsDataBoundary &&
      _understandsNoEmergencyUse &&
      _understandsNoRealData;

  bool get _deletionReady =>
      _deletionController.text.trim() == 'REQUEST ACCOUNT DELETION';

  void _showDeletionPrepared() {
    setState(() => _deletionPrepared = true);
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(context.l10n.deletionPrepared)));
  }

  void _showFeedbackPrepared() {
    setState(() => _feedbackPrepared = true);
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(context.l10n.feedbackPrepared)));
  }
}

class _ConsentCheckbox extends StatelessWidget {
  const _ConsentCheckbox({
    required this.value,
    required this.onChanged,
    required this.label,
    super.key,
  });

  final bool value;
  final ValueChanged<bool?> onChanged;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Row(
        children: <Widget>[
          Checkbox(value: value, onChanged: onChanged),
          Expanded(child: Text(label)),
        ],
      ),
    );
  }
}

class _BetaHero extends StatelessWidget {
  const _BetaHero({required this.displayName});

  final String? displayName;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              context.l10n.privacySupportHero,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: DrAiColors.white,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              displayName == null
                  ? context.l10n.accountPolicyStaging
                  : context.l10n.accountPolicyUser(displayName!),
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _BetaChip(label: context.l10n.stagingPolicyPlaceholder),
          ],
        ),
      ),
    );
  }
}

class _BetaSection extends StatelessWidget {
  const _BetaSection({
    required this.icon,
    required this.title,
    required this.children,
    super.key,
  });

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outlineMuted),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(icon, color: DrAiColors.brand),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _BetaBullet extends StatelessWidget {
  const _BetaBullet(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(
            Icons.check_circle_outline,
            size: 18,
            color: DrAiColors.brand,
          ),
          const SizedBox(width: DrAiSpacing.xs),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _BetaText extends StatelessWidget {
  const _BetaText(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.sm),
      child: Text(text),
    );
  }
}

class _BetaChip extends StatelessWidget {
  const _BetaChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.patientAccent,
        borderRadius: BorderRadius.circular(DrAiRadii.sm),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.sm,
          vertical: DrAiSpacing.xs,
        ),
        child: Text(
          label,
          style: const TextStyle(
            color: DrAiColors.ink,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}

class _PreparedStatus extends StatelessWidget {
  const _PreparedStatus({
    required this.label,
    required this.isReady,
    this.statusKey = const Key('beta-consent-readiness'),
  });

  final String label;
  final bool isReady;
  final Key statusKey;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Text(
        label,
        key: statusKey,
        style: TextStyle(
          color: isReady ? DrAiColors.brandDark : DrAiColors.mutedInk,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
