import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class UnauthorizedScreen extends StatelessWidget {
  const UnauthorizedScreen({required this.role, super.key});

  final AppRole? role;

  @override
  Widget build(BuildContext context) {
    final dashboardPath = switch (role) {
      AppRole.doctor => '/doctor',
      AppRole.patient => '/patient',
      AppRole.payer => '/payer',
      AppRole.unsupported || null => null,
    };
    return Scaffold(
      body: Semantics(
        key: const Key('unauthorized-screen'),
        container: true,
        namesRoute: true,
        label: context.l10n.unauthorized,
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(DrAiSpacing.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const Icon(Icons.lock_outline, size: 48),
                const SizedBox(height: DrAiSpacing.md),
                Semantics(
                  header: true,
                  child: Text(
                    context.l10n.unauthorized,
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.md),
                FilledButton(
                  key: const Key('unauthorized-return-button'),
                  autofocus: true,
                  onPressed: dashboardPath == null
                      ? null
                      : () => context.go(dashboardPath),
                  child: Text(context.l10n.returnToDashboard),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
