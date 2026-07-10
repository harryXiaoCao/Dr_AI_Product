import 'dart:ui';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _localeStorageKey = 'dr_ai_interface_locale';

final localeControllerProvider = NotifierProvider<LocaleController, Locale?>(
  LocaleController.new,
);

class LocaleController extends Notifier<Locale?> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  @override
  Locale? build() {
    Future<void>.microtask(_restore);
    return null;
  }

  Future<void> _restore() async {
    try {
      final value = await _storage.read(key: _localeStorageKey);
      if (value == 'zh_Hans') {
        state = const Locale('zh');
      } else if (value == 'en') {
        state = const Locale('en');
      }
    } on Exception {
      // A storage failure should never prevent the app from following the
      // device locale for this session.
    }
  }

  Future<void> useEnglish() => _set(const Locale('en'), 'en');

  Future<void> useSimplifiedChinese() => _set(const Locale('zh'), 'zh_Hans');

  Future<void> useSystemLanguage() async {
    state = null;
    try {
      await _storage.delete(key: _localeStorageKey);
    } on Exception {
      // The in-memory choice still takes effect for this session.
    }
  }

  Future<void> applyProfilePreference(String value) {
    return value == 'Simplified Chinese'
        ? useSimplifiedChinese()
        : useEnglish();
  }

  Future<void> _set(Locale locale, String storedValue) async {
    state = locale;
    try {
      await _storage.write(key: _localeStorageKey, value: storedValue);
    } on Exception {
      // The in-memory choice still takes effect for this session.
    }
  }
}
