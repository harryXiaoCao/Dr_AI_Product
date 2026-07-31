import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class BetaSupportScreen extends ConsumerWidget {
  const BetaSupportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
                  _BetaBullet(context.l10n.consentStagingData),
                  _BetaBullet(context.l10n.consentNoEmergency),
                  _BetaBullet(context.l10n.consentNoRealData),
                  _BetaText(
                    user == null
                        ? context.l10n.signInForAccountRequests
                        : context.l10n.openAccountForRequests,
                  ),
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
