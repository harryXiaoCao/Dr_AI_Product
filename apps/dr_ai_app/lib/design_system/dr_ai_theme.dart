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
      scaffoldBackgroundColor: DrAiColors.pageBackground,
      useMaterial3: true,
      fontFamily: 'Inter',
      fontFamilyFallback: const <String>[
        'NotoSansSC',
        'PingFang SC',
        'Noto Sans SC',
        'Noto Sans CJK SC',
        'Roboto',
        'SF Pro Text',
        'SF Pro Display',
        'Helvetica Neue',
        'Arial',
      ],
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
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DrAiColors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 14,
        ),
        labelStyle: const TextStyle(
          color: DrAiColors.inkSecondary,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        hintStyle: const TextStyle(color: Color(0xFF9BA7B8), fontSize: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          borderSide: const BorderSide(color: Color(0xFFD8E1EF)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          borderSide: const BorderSide(color: Color(0xFFD8E1EF)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          borderSide: const BorderSide(color: DrAiColors.brand, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(0, 42),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          side: const BorderSide(color: DrAiColors.brand),
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
    );
  }
}
