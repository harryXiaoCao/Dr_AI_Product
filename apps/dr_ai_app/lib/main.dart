import 'package:dr_ai_app/app/app.dart';
import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:flutter/material.dart';

void main() {
  const previewRole = String.fromEnvironment(
    'DR_AI_PREVIEW_ROLE',
    defaultValue: 'doctor',
  );

  runApp(DrAiApp(role: AppRole.fromEnvironment(previewRole)));
}
