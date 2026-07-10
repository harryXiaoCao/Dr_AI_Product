import 'package:dr_ai_app/app/app.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  _registerBundledFontLicenses();
  setUrlStrategy(PathUrlStrategy());
  runApp(const ProviderScope(child: DrAiApp()));
}

void _registerBundledFontLicenses() {
  LicenseRegistry.addLicense(() async* {
    yield LicenseEntryWithLineBreaks(const <String>[
      'Inter',
    ], await rootBundle.loadString('assets/fonts/licenses/Inter-OFL.txt'));
    yield LicenseEntryWithLineBreaks(const <String>[
      'Noto Sans SC',
    ], await rootBundle.loadString('assets/fonts/licenses/NotoSansSC-OFL.txt'));
  });
}
