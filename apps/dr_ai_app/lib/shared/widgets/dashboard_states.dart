import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';

class DashboardLoadingView extends StatelessWidget {
  const DashboardLoadingView({this.label, super.key});

  final String? label;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Semantics(
        label: label ?? context.l10n.loading,
        child: const CircularProgressIndicator(),
      ),
    );
  }
}

class DashboardErrorView extends StatelessWidget {
  const DashboardErrorView({
    required this.message,
    required this.onRetry,
    super.key,
  });

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const Icon(
              Icons.cloud_off_outlined,
              size: 48,
              color: DrAiColors.mutedInk,
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              message,
              key: const Key('dashboard-error'),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: DrAiSpacing.md),
            OutlinedButton(
              onPressed: onRetry,
              child: Text(context.l10n.tryAgain),
            ),
          ],
        ),
      ),
    );
  }
}
