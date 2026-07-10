import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/l10n/locale_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class InterfaceLanguageSelector extends ConsumerWidget {
  const InterfaceLanguageSelector({this.onPreferenceChanged, super.key});

  final ValueChanged<String>? onPreferenceChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = Localizations.localeOf(context);
    final value = locale.languageCode == 'zh'
        ? 'Simplified Chinese'
        : 'English';
    return DropdownButtonFormField<String>(
      key: const Key('interface-language-field'),
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(
        labelText: context.l10n.interfaceLanguage,
        helperText: context.l10n.interfaceLanguageDescription,
        border: const OutlineInputBorder(),
      ),
      items: <DropdownMenuItem<String>>[
        DropdownMenuItem<String>(
          value: 'Simplified Chinese',
          child: Text(context.l10n.simplifiedChinese),
        ),
        DropdownMenuItem<String>(
          value: 'English',
          child: Text(context.l10n.english),
        ),
      ],
      onChanged: (selection) {
        if (selection == null) {
          return;
        }
        ref
            .read(localeControllerProvider.notifier)
            .applyProfilePreference(selection);
        onPreferenceChanged?.call(selection);
      },
    );
  }
}
