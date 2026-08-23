import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';

class SessionLoadingRouteScreen extends StatelessWidget {
  const SessionLoadingRouteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Semantics(
          label: context.l10n.restoringSession,
          child: const CircularProgressIndicator(),
        ),
      ),
    );
  }
}
