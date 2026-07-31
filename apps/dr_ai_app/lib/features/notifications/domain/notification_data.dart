import 'package:dr_ai_app/app/routing/app_role.dart';

class NotificationInboxData {
  const NotificationInboxData({
    required this.items,
    required this.unreadCount,
    required this.generatedAt,
  });

  factory NotificationInboxData.fromJson(Map<String, dynamic> json) {
    final items = ((json['items'] as List?) ?? const <Object>[])
        .whereType<Map<String, dynamic>>()
        .map(NotificationInboxItem.fromJson)
        .toList(growable: false);
    return NotificationInboxData(
      items: items,
      unreadCount:
          (json['unread_count'] as num?)?.toInt() ??
          items.where((item) => item.isUnread).length,
      generatedAt: _dateTime(json['generated_at']) ?? DateTime.now().toUtc(),
    );
  }

  final List<NotificationInboxItem> items;
  final int unreadCount;
  final DateTime generatedAt;
}

class NotificationInboxItem {
  const NotificationInboxItem({
    required this.id,
    required this.eventType,
    required this.severity,
    required this.category,
    required this.status,
    required this.title,
    required this.body,
    required this.actorKind,
    required this.occurredAt,
    required this.scheduledFor,
    required this.deliveryState,
    required this.readAt,
    required this.dismissedAt,
    required this.expiresAt,
    required this.supersededAt,
    required this.canDismiss,
    required this.canMarkUnread,
    required this.deepLinkAvailable,
    required this.version,
  });

  factory NotificationInboxItem.fromJson(Map<String, dynamic> json) {
    return NotificationInboxItem(
      id: json['id'] as String,
      eventType:
          json['event_type'] as String? ??
          json['notification_type'] as String? ??
          'system_update',
      severity: json['severity'] as String? ?? 'information',
      category:
          json['category'] as String? ??
          json['source_category'] as String? ??
          'system',
      status: json['status'] as String? ?? 'scheduled',
      title: json['title'] as String? ?? 'Update available',
      body: json['body'] as String? ?? 'Open Dr. AI to review this update.',
      actorKind: json['actor_kind'] as String? ?? 'system',
      occurredAt:
          _dateTime(json['occurred_at']) ??
          _dateTime(json['created_at']) ??
          DateTime.fromMillisecondsSinceEpoch(0, isUtc: true),
      scheduledFor: _dateTime(json['scheduled_for']),
      deliveryState:
          json['delivery_state'] as String? ??
          json['external_delivery_state'] as String? ??
          'not_requested',
      readAt: _dateTime(json['read_at']),
      dismissedAt: _dateTime(json['dismissed_at']),
      expiresAt: _dateTime(json['expires_at']),
      supersededAt: _dateTime(json['superseded_at']),
      canDismiss: json['can_dismiss'] as bool? ?? true,
      canMarkUnread: json['can_mark_unread'] as bool? ?? true,
      deepLinkAvailable:
          json['deep_link_available'] as bool? ??
          json['deep_link_code'] != null,
      version: (json['version'] as num?)?.toInt() ?? 1,
    );
  }

  final String id;
  final String eventType;
  final String severity;
  final String category;
  final String status;
  final String title;
  final String body;
  final String actorKind;
  final DateTime occurredAt;
  final DateTime? scheduledFor;
  final String deliveryState;
  final DateTime? readAt;
  final DateTime? dismissedAt;
  final DateTime? expiresAt;
  final DateTime? supersededAt;
  final bool canDismiss;
  final bool canMarkUnread;
  final bool deepLinkAvailable;
  final int version;

  bool get isUnread => readAt == null && dismissedAt == null;
  bool get isDismissed => dismissedAt != null;
  bool get isExpired =>
      status == 'expired' ||
      (expiresAt != null && !expiresAt!.isAfter(DateTime.now().toUtc()));
  bool get isSuperseded => status == 'superseded' || supersededAt != null;
  bool get isActionable =>
      deepLinkAvailable && !isExpired && !isSuperseded && !isDismissed;
}

class NotificationPreferences {
  const NotificationPreferences({
    required this.allowedCategories,
    required this.inProductEnabled,
    required this.externalChannels,
    required this.quietHoursStart,
    required this.quietHoursEnd,
    required this.locale,
    required this.timeZone,
    required this.previewLevel,
    required this.version,
  });

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      allowedCategories: _stringList(
        json['allowed_categories'] ?? json['allowed_categories_json'],
      ),
      inProductEnabled: json['in_product_enabled'] as bool? ?? true,
      externalChannels: _stringList(
        json['external_channels'] ?? json['external_channels_json'],
      ),
      quietHoursStart: json['quiet_hours_start'] as String?,
      quietHoursEnd: json['quiet_hours_end'] as String?,
      locale: json['locale'] as String? ?? 'en',
      timeZone: json['time_zone'] as String? ?? 'UTC',
      previewLevel: json['preview_level'] as String? ?? 'generic',
      version: (json['version'] as num?)?.toInt() ?? 1,
    );
  }

  final List<String> allowedCategories;
  final bool inProductEnabled;
  final List<String> externalChannels;
  final String? quietHoursStart;
  final String? quietHoursEnd;
  final String locale;
  final String timeZone;
  final String previewLevel;
  final int version;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'allowed_categories': allowedCategories,
    'in_product_enabled': inProductEnabled,
    'external_channels': externalChannels,
    'quiet_hours_start': quietHoursStart,
    'quiet_hours_end': quietHoursEnd,
    'locale': locale,
    'time_zone': timeZone,
    'preview_level': previewLevel,
    'expected_version': version,
  };
}

class NotificationReadiness {
  const NotificationReadiness({required this.channels});

  factory NotificationReadiness.fromJson(Map<String, dynamic> json) {
    final raw = (json['channels'] as List?) ?? const <Object>[];
    return NotificationReadiness(
      channels: raw
          .whereType<Map<String, dynamic>>()
          .map(NotificationChannelReadiness.fromJson)
          .toList(growable: false),
    );
  }

  final List<NotificationChannelReadiness> channels;
}

class NotificationChannelReadiness {
  const NotificationChannelReadiness({
    required this.channel,
    required this.provider,
    required this.status,
    required this.readinessCode,
    required this.supported,
    required this.enabled,
    required this.blockers,
  });

  factory NotificationChannelReadiness.fromJson(Map<String, dynamic> json) {
    return NotificationChannelReadiness(
      channel: json['channel'] as String,
      provider: json['provider'] as String? ?? 'unconfigured',
      status: json['status'] as String? ?? 'server_readiness',
      readinessCode:
          json['readiness_code'] as String? ??
          json['code'] as String? ??
          'provider_unavailable',
      supported:
          json['supported'] as bool? ?? json['code'] != 'unsupported_platform',
      enabled: json['enabled'] as bool? ?? json['ready'] as bool? ?? false,
      blockers: _stringList(json['blockers']),
    );
  }

  final String channel;
  final String provider;
  final String status;
  final String readinessCode;
  final bool supported;
  final bool enabled;
  final List<String> blockers;
}

class NotificationOpenResult {
  const NotificationOpenResult({
    required this.status,
    required this.destinationPath,
  });

  factory NotificationOpenResult.fromJson(Map<String, dynamic> json) {
    return NotificationOpenResult(
      status:
          json['status'] as String? ??
          json['resolution_status'] as String? ??
          'unavailable',
      destinationPath:
          json['route_path'] as String? ??
          json['destination_path'] as String? ??
          json['path'] as String?,
    );
  }

  final String status;
  final String? destinationPath;

  String? safePathFor(AppRole role) {
    if (status != 'resolved' || destinationPath == null) return null;
    final uri = Uri.tryParse(destinationPath!);
    if (uri == null || uri.hasScheme || uri.hasAuthority) return null;
    final root = '/${role.wireValue}';
    final prefix = '/${role.wireValue}/';
    return uri.path == root || uri.path.startsWith(prefix)
        ? destinationPath
        : null;
  }
}

DateTime? _dateTime(Object? value) {
  if (value is! String || value.isEmpty) return null;
  return DateTime.tryParse(value)?.toUtc();
}

List<String> _stringList(Object? value) {
  if (value is! List) return const <String>[];
  return value.whereType<String>().toList(growable: false);
}
