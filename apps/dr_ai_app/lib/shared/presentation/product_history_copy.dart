import 'package:flutter/widgets.dart';
import 'package:intl/intl.dart';

String humanizeProductValue(String value) {
  final words = value
      .replaceAll(RegExp(r'[_-]+'), ' ')
      .trim()
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .toList();
  if (words.isEmpty) return value;
  return words
      .map(
        (word) => word.length == 1
            ? word.toUpperCase()
            : '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}',
      )
      .join(' ');
}

String formatProductHistoryTime(BuildContext context, DateTime value) {
  return DateFormat.yMMMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).add_jm().format(value.toLocal());
}

String formatProductHistoryTimestamp(BuildContext context, String value) {
  final parsed = DateTime.tryParse(value);
  return parsed == null ? value : formatProductHistoryTime(context, parsed);
}
