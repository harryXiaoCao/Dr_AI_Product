import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:flutter/material.dart';

abstract final class DrAiTheme {
  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: DrAiColors.brand,
      brightness: Brightness.light,
      primary: DrAiColors.brand,
      surface: DrAiColors.surface,
      error: DrAiColors.danger,
    );

    return ThemeData(
      colorScheme: scheme,
      scaffoldBackgroundColor: DrAiColors.surface,
      useMaterial3: true,
      textTheme: const TextTheme(
        headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700),
        headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
        titleLarge: TextStyle(
          fontSize: 20,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
        titleMedium: TextStyle(
          fontSize: 16,
          height: 1.4,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(fontSize: 16, height: 1.4),
        bodyMedium: TextStyle(fontSize: 14, height: 20 / 14),
        labelLarge: TextStyle(
          fontSize: 14,
          height: 20 / 14,
          fontWeight: FontWeight.w600,
        ),
        labelSmall: TextStyle(fontSize: 11, height: 16 / 11),
      ).apply(bodyColor: DrAiColors.ink, displayColor: DrAiColors.ink),
      cardTheme: const CardThemeData(
        color: DrAiColors.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(DrAiRadii.md)),
          side: BorderSide(color: DrAiColors.outline),
        ),
      ),
    );
  }
}
