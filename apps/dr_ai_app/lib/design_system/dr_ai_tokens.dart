import 'package:flutter/material.dart';

abstract final class DrAiColors {
  // Verified directly in the two frozen Figma target frames.
  static const Color brandDark = Color(0xFF0A0076);
  static const Color brand = Color(0xFF0A0076);
  static const Color brandSoft = Color(0xFFDEDCFC);
  static const Color sectionHeader = brand;
  static const Color pageBackground = Color(0xFFF4F7FC);
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);
  static const Color ink = Color(0xFF1E1E1E);
  static const Color inkStrong = Color(0xFF2C2C2C);
  static const Color inkSecondary = Color(0xFF444444);
  static const Color surface = white;
  static const Color surfaceSubtle = Color(0xFFF5F5F5);
  static const Color surfaceMuted = brandSoft;
  static const Color outlineMuted = Color(0xFFD9D9D9);
  static const Color outline = Color(0xFFE5E5E5);
  static const Color patientAccent = Color(0xFFB0C6FF);
  static const Color accentBlue = Color(0xFF007AFF);
  static const Color accentCyan = Color(0xFF32ADE6);
  static const Color accentMint = Color(0xFF00C7BE);
  static const Color accentOrange = Color(0xFFFF9500);
  static const Color accentIndigo = Color(0xFF5856D6);

  // Verified Material 3 library styles used by the frozen targets.
  static const Color m3Primary = Color(0xFF6750A4);
  static const Color m3OnPrimary = white;
  static const Color m3OnSurface = Color(0xFF1D1B20);
  static const Color m3OnSurfaceVariant = Color(0xFF49454F);
  static const Color m3Surface = Color(0xFFFEF7FF);
  static const Color m3Outline = Color(0xFF79747E);
  static const Color m3OutlineVariant = Color(0xFFCAC4D0);
  static const Color m3SecondaryContainer = Color(0xFFE8DEF8);
  static const Color m3PrimaryContainer = Color(0xFFEADDFF);
  static const Color m3OnPrimaryContainer = Color(0xFF4F378A);
  static const Color m3TertiaryContainer = Color(0xFFFFD8E4);
  static const Color m3OnTertiaryContainer = Color(0xFF633B48);
  static const Color m3SurfaceContainerHigh = Color(0xFFECE6F0);
  static const Color m3SurfaceContainerHighest = Color(0xFFE6E0E9);
  static const Color m3OnSurfaceState08 = Color(0x141D1B20);
  static const Color m3OnSurfaceVariantState08 = Color(0x1449454F);

  // Application semantics not exposed by either target frame.
  static const Color mutedInk = Color(0xFF6C6C75);
  static const Color danger = Color(0xFFB3261E);
}

abstract final class DrAiSpacing {
  static const double xxs = 4;
  static const double xs = 8;
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;
}

abstract final class DrAiRadii {
  static const double sm = 4;
  static const double md = 8;
  static const double lg = 12;
  static const double xl = 16;
  static const double pill = 999;
}

abstract final class DrAiBreakpoints {
  static const double mobile = 600;
  static const double desktop = 1024;
}
