import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
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
  bool _understandsSyntheticOnly = false;
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
      color: DrAiColors.brandSoft,
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
                title: 'Beta privacy notice',
                children: const <Widget>[
                  _BetaText(
                    'Dr. AI v1.0 is an invited, non-clinical beta using '
                    'synthetic demonstration content only.',
                  ),
                  _BetaBullet(
                    'Do not enter names, contact information, raw records, '
                    'images, or patient-owned clinical content.',
                  ),
                  _BetaBullet(
                    'DeepSeek is reached only through the FastAPI backend; '
                    'keys never enter the Flutter app.',
                  ),
                  _BetaBullet(
                    'Chat is educational question preparation only and is '
                    'blocked by red-flag safety checks before any LLM call.',
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-consent-section'),
                icon: Icons.fact_check_outlined,
                title: 'Consent checklist',
                children: <Widget>[
                  _ConsentCheckbox(
                    key: const Key('consent-synthetic-only-checkbox'),
                    value: _understandsSyntheticOnly,
                    onChanged: (value) => setState(
                      () => _understandsSyntheticOnly = value ?? false,
                    ),
                    label:
                        'I understand this beta uses synthetic demonstration data.',
                  ),
                  _ConsentCheckbox(
                    key: const Key('consent-no-emergency-checkbox'),
                    value: _understandsNoEmergencyUse,
                    onChanged: (value) => setState(
                      () => _understandsNoEmergencyUse = value ?? false,
                    ),
                    label:
                        'I understand Dr. AI is not for emergencies, diagnosis, '
                        'or treatment decisions.',
                  ),
                  _ConsentCheckbox(
                    key: const Key('consent-no-real-data-checkbox'),
                    value: _understandsNoRealData,
                    onChanged: (value) =>
                        setState(() => _understandsNoRealData = value ?? false),
                    label: 'I understand I must not submit real patient data.',
                  ),
                  _PreparedStatus(
                    label: _consentReady
                        ? 'Consent readiness prepared locally.'
                        : 'Complete all items before a tester uses the beta.',
                    isReady: _consentReady,
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _BetaSection(
                key: const Key('beta-deletion-section'),
                icon: Icons.manage_accounts_outlined,
                title: 'Account deletion request',
                children: <Widget>[
                  const _BetaText(
                    'This local surface prepares a deletion request only. It '
                    'does not delete data, alter accounts, or contact testers.',
                  ),
                  TextField(
                    key: const Key('account-deletion-confirm-field'),
                    controller: _deletionController,
                    decoration: const InputDecoration(
                      labelText: 'Type REQUEST DEMO DELETION',
                      border: OutlineInputBorder(),
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  FilledButton.icon(
                    key: const Key('account-deletion-prepare-button'),
                    onPressed: _deletionReady ? _showDeletionPrepared : null,
                    icon: const Icon(Icons.description_outlined),
                    label: const Text('Prepare request'),
                  ),
                  if (_deletionPrepared) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.xs),
                    const _PreparedStatus(
                      label:
                          'Deletion request prepared locally. No account data was changed.',
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
                title: 'Feedback form',
                children: <Widget>[
                  const _BetaText(
                    'Use synthetic-only feedback. Do not include real patient '
                    'details, screenshots containing private data, or account '
                    'secrets.',
                  ),
                  TextField(
                    key: const Key('beta-feedback-field'),
                    controller: _feedbackController,
                    minLines: 3,
                    maxLines: 5,
                    decoration: const InputDecoration(
                      labelText: 'Feedback draft',
                      hintText:
                          'Describe the beta issue, device, browser, and synthetic step.',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  FilledButton.icon(
                    key: const Key('beta-feedback-prepare-button'),
                    onPressed: _showFeedbackPrepared,
                    icon: const Icon(Icons.assignment_turned_in_outlined),
                    label: const Text('Prepare feedback draft'),
                  ),
                  if (_feedbackPrepared) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.xs),
                    const _PreparedStatus(
                      label:
                          'Feedback draft prepared locally. No external message was sent.',
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
                title: 'Known limitations',
                children: const <Widget>[
                  _BetaBullet(
                    'Simulated lung-risk assessment only; no clinical model '
                    'or real inference is enabled.',
                  ),
                  _BetaBullet(
                    'Demo upload is metadata preparation only unless release '
                    'operators explicitly approve real COS completion.',
                  ),
                  _BetaBullet(
                    'No billing, appointments, video, voice consultation, '
                    'analytics expansion, or clinical claims are enabled.',
                  ),
                  _BetaBullet(
                    'TestFlight, Android closed testing, web deployment, '
                    'tagging, tester invites, and monitoring changes require '
                    'explicit release approval.',
                  ),
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
          title: const Text('Dr. AI beta support'),
          actions: <Widget>[
            TextButton(
              onPressed: () => context.go('/login'),
              child: const Text('Sign in'),
            ),
          ],
        ),
        body: content,
      );
    }
    return ResponsiveAppShell(role: user.role, child: content);
  }

  bool get _consentReady =>
      _understandsSyntheticOnly &&
      _understandsNoEmergencyUse &&
      _understandsNoRealData;

  bool get _deletionReady =>
      _deletionController.text.trim() == 'REQUEST DEMO DELETION';

  void _showDeletionPrepared() {
    setState(() => _deletionPrepared = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Deletion request prepared locally. No account data was changed.',
        ),
      ),
    );
  }

  void _showFeedbackPrepared() {
    setState(() => _feedbackPrepared = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Feedback draft prepared locally. No external message was sent.',
        ),
      ),
    );
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
              'Beta support',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: DrAiColors.white,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              displayName == null
                  ? 'Release-prep surfaces for the Dr. AI invited beta.'
                  : 'Release-prep surfaces for $displayName.',
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            const _BetaChip(label: 'Synthetic data only - non-clinical beta'),
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
