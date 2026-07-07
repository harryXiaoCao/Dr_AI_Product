import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
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
      AppRole.unsupported || null => null,
    };
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const Icon(Icons.lock_outline, size: 48),
              const SizedBox(height: DrAiSpacing.md),
              const Text(
                'This route is not available for your role.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: DrAiSpacing.md),
              FilledButton(
                onPressed: dashboardPath == null
                    ? null
                    : () => context.go(dashboardPath),
                child: const Text('Return to dashboard'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
