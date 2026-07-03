import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class DrAiApp extends StatelessWidget {
  DrAiApp({required AppRole role, super.key}) : router = createRouter(role);

  final GoRouter router;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Dr. AI',
      debugShowCheckedModeBanner: false,
      theme: DrAiTheme.light,
      routerConfig: router,
    );
  }
}
