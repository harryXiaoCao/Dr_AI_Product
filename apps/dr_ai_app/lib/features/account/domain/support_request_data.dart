class SupportRequestTimelineEntry {
  const SupportRequestTimelineEntry({
    required this.sequence,
    required this.eventType,
    required this.status,
    required this.actorKind,
    required this.summaryCode,
    required this.occurredAt,
  });

  factory SupportRequestTimelineEntry.fromJson(Map<String, dynamic> json) {
    return SupportRequestTimelineEntry(
      sequence: json['sequence'] as int? ?? 0,
      eventType:
          json['event_type'] as String? ??
          json['transition_type'] as String? ??
          'status_updated',
      status:
          json['status'] as String? ?? json['to_status'] as String? ?? 'queued',
      actorKind: json['actor_kind'] as String? ?? 'system',
      summaryCode: json['summary_code'] as String? ?? 'status_updated',
      occurredAt: DateTime.parse(json['occurred_at'] as String),
    );
  }

  final int sequence;
  final String eventType;
  final String status;
  final String actorKind;
  final String summaryCode;
  final DateTime occurredAt;
}

class SupportRequestData {
  const SupportRequestData({
    required this.id,
    required this.publicReference,
    required this.requestType,
    required this.status,
    required this.subject,
    required this.version,
    required this.timeline,
    required this.retentionBoundaryCode,
    required this.deletionEffectCode,
    required this.availableActions,
    required this.createdAt,
    required this.updatedAt,
    this.replay = false,
  });

  factory SupportRequestData.fromJson(Map<String, dynamic> json) {
    return SupportRequestData(
      id:
          json['request_id'] as String? ??
          json['id'] as String? ??
          'unavailable',
      publicReference:
          json['public_reference'] as String? ??
          json['reference'] as String? ??
          'Reference unavailable',
      requestType: json['request_type'] as String,
      status: json['status'] as String,
      subject: json['subject'] as String,
      version: json['version'] as int? ?? 1,
      timeline: (json['timeline'] as List<dynamic>? ?? const <dynamic>[])
          .map(
            (item) => SupportRequestTimelineEntry.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      retentionBoundaryCode:
          json['retention_boundary_code'] as String? ?? 'retention_applies',
      deletionEffectCode:
          json['deletion_effect_code'] as String? ?? 'not_immediate_deletion',
      availableActions: List<String>.from(
        json['available_actions'] as List<dynamic>? ?? const <dynamic>[],
      ),
      replay:
          json['replayed'] as bool? ??
          json['replay'] as bool? ??
          json['idempotent_replay'] as bool? ??
          false,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  final String id;
  final String publicReference;
  final String requestType;
  final String status;
  final String subject;
  final int version;
  final List<SupportRequestTimelineEntry> timeline;
  final String retentionBoundaryCode;
  final String deletionEffectCode;
  final List<String> availableActions;
  final bool replay;
  final DateTime createdAt;
  final DateTime updatedAt;

  bool get canWithdraw => availableActions.contains('withdraw');
}

class ProductEventInput {
  const ProductEventInput({
    required this.eventName,
    required this.journeyCode,
    required this.surfaceCode,
    required this.outcome,
    this.failureCategory,
    required this.latencyBucket,
    required this.locale,
    required this.platform,
    required this.layout,
    required this.deduplicationKey,
  });

  final String eventName;
  final String journeyCode;
  final String surfaceCode;
  final String outcome;
  final String? failureCategory;
  final String latencyBucket;
  final String locale;
  final String platform;
  final String layout;
  final String deduplicationKey;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'event_name': eventName,
    'dimensions': <String, String>{
      'journey_code': journeyCode,
      'surface_code': surfaceCode,
      'outcome': outcome,
      'failure_category': ?failureCategory,
      'latency_bucket': latencyBucket,
      'locale': locale,
      'platform': platform,
      'layout': layout,
    },
    'deduplication_key': deduplicationKey,
  };
}
