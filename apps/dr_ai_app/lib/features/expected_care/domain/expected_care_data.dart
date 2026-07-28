class CostEstimationFactData {
  const CostEstimationFactData({
    required this.category,
    required this.label,
    required this.reason,
    required this.count,
    required this.value,
    required this.sourceType,
    required this.sourceScope,
  });

  factory CostEstimationFactData.fromJson(Map<String, dynamic> json) {
    final provenance = json['provenance'] as Map<Object?, Object?>?;
    return CostEstimationFactData(
      category: json['category'] as String? ?? 'unknown',
      label: json['label'] as String? ?? '',
      reason: json['reason'] as String?,
      count: json['count'] as int? ?? 1,
      value: json['value'],
      sourceType: provenance?['source_type'] as String?,
      sourceScope: provenance?['source_scope'] as String?,
    );
  }

  final String category;
  final String label;
  final String? reason;
  final int count;
  final Object? value;
  final String? sourceType;
  final String? sourceScope;

  bool get detailWithheld =>
      value is Map && (value as Map)['detail_withheld'] == true;
}

class CostEstimationFactSnapshotData {
  const CostEstimationFactSnapshotData({
    required this.available,
    required this.factsUsed,
    required this.factsNotUsed,
    required this.missingFacts,
  });

  const CostEstimationFactSnapshotData.unavailable()
    : available = false,
      factsUsed = const <CostEstimationFactData>[],
      factsNotUsed = const <CostEstimationFactData>[],
      missingFacts = const <CostEstimationFactData>[];

  factory CostEstimationFactSnapshotData.fromJson(Object? value) {
    if (value is! Map) {
      return const CostEstimationFactSnapshotData.unavailable();
    }
    final json = Map<String, dynamic>.from(value);
    List<CostEstimationFactData> parse(String key) {
      return (json[key] as List<dynamic>? ?? const <dynamic>[])
          .whereType<Map<Object?, Object?>>()
          .map(
            (item) => CostEstimationFactData.fromJson(
              Map<String, dynamic>.from(item),
            ),
          )
          .toList();
    }

    return CostEstimationFactSnapshotData(
      available: true,
      factsUsed: parse('facts_used'),
      factsNotUsed: parse('facts_not_used'),
      missingFacts: parse('missing_facts'),
    );
  }

  final bool available;
  final List<CostEstimationFactData> factsUsed;
  final List<CostEstimationFactData> factsNotUsed;
  final List<CostEstimationFactData> missingFacts;
}

class ExpectedCareItemData {
  const ExpectedCareItemData({
    required this.itemKey,
    required this.category,
    required this.unit,
    required this.quantityLow,
    required this.quantityHigh,
    required this.amountLowMinor,
    required this.amountHighMinor,
  });

  factory ExpectedCareItemData.fromJson(Map<String, dynamic> json) {
    return ExpectedCareItemData(
      itemKey: json['item_key'] as String,
      category: json['category'] as String? ?? json['item_key'] as String,
      unit: json['unit'] as String,
      quantityLow: json['quantity_low'] as int,
      quantityHigh: json['quantity_high'] as int,
      amountLowMinor: json['amount_low_minor'] as int,
      amountHighMinor: json['amount_high_minor'] as int,
    );
  }

  final String itemKey;
  final String category;
  final String unit;
  final int quantityLow;
  final int quantityHigh;
  final int amountLowMinor;
  final int amountHighMinor;
}

class ExpectedCareReferenceData {
  const ExpectedCareReferenceData({
    required this.releaseType,
    required this.version,
    this.releaseId,
    this.checksum,
    this.effectiveFrom,
    this.effectiveTo,
    this.sourceAuthority,
  });

  factory ExpectedCareReferenceData.fromJson(Map<String, dynamic> json) {
    return ExpectedCareReferenceData(
      releaseType: json['release_type'] as String? ?? 'reference',
      version: json['version'] as String? ?? '',
      releaseId: json['release_id'] as String?,
      checksum: json['payload_checksum_sha256'] as String?,
      effectiveFrom: json['effective_from'] as String?,
      effectiveTo: json['effective_to'] as String?,
      sourceAuthority: json['source_authority'] as String?,
    );
  }

  final String releaseType;
  final String version;
  final String? releaseId;
  final String? checksum;
  final String? effectiveFrom;
  final String? effectiveTo;
  final String? sourceAuthority;
}

class ExpectedCareCandidateData {
  const ExpectedCareCandidateData({
    required this.id,
    required this.state,
    required this.responseVersion,
    required this.latestClinicianPosition,
    required this.clinicianResponses,
    required this.currency,
    required this.totalLowMinor,
    required this.totalHighMinor,
    required this.referenceDate,
    required this.assumptions,
    required this.missingInformation,
    required this.limitations,
    required this.items,
    required this.references,
    required this.validationState,
    required this.factSnapshot,
  });

  factory ExpectedCareCandidateData.fromJson(Map<String, dynamic> json) {
    final validation = Map<String, dynamic>.from(json['validation'] as Map);
    return ExpectedCareCandidateData(
      id: json['candidate_result_id'] as String,
      state: json['state'] as String,
      responseVersion:
          json['response_version'] as int? ??
          json['review_version'] as int? ??
          0,
      latestClinicianPosition:
          json['latest_clinician_position'] as String? ?? 'not_recorded',
      clinicianResponses:
          (json['clinician_responses'] as List<dynamic>? ?? const <dynamic>[])
              .map(
                (item) => ClinicianResponseData.fromJson(
                  Map<String, dynamic>.from(item as Map),
                ),
              )
              .toList(),
      currency: json['currency'] as String? ?? 'CNY',
      totalLowMinor: json['total_low_minor'] as int? ?? 0,
      totalHighMinor: json['total_high_minor'] as int? ?? 0,
      referenceDate: json['reference_date'] as String? ?? '',
      assumptions: List<String>.from(json['assumptions'] as List? ?? const []),
      missingInformation: List<String>.from(
        json['missing_information'] as List? ?? const [],
      ),
      limitations: List<String>.from(json['limitations'] as List? ?? const []),
      items: (json['items'] as List<dynamic>)
          .map(
            (item) => ExpectedCareItemData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      references: (json['references'] as List<dynamic>)
          .map(
            (item) => ExpectedCareReferenceData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      validationState: validation['state'] as String? ?? 'unknown',
      factSnapshot: CostEstimationFactSnapshotData.fromJson(
        json['cost_estimation_fact_snapshot'],
      ),
    );
  }

  final String id;
  final String state;
  final int responseVersion;
  final String latestClinicianPosition;
  final List<ClinicianResponseData> clinicianResponses;
  final String currency;
  final int totalLowMinor;
  final int totalHighMinor;
  final String referenceDate;
  final List<String> assumptions;
  final List<String> missingInformation;
  final List<String> limitations;
  final List<ExpectedCareItemData> items;
  final List<ExpectedCareReferenceData> references;
  final String validationState;
  final CostEstimationFactSnapshotData factSnapshot;
}

class ClinicianResponseData {
  const ClinicianResponseData({
    required this.id,
    required this.position,
    required this.state,
    required this.version,
    required this.createdAt,
    this.patientSafeSummary,
    this.clinicalRationale,
  });

  factory ClinicianResponseData.fromJson(Map<String, dynamic> json) {
    final rationale = json['clinical_rationale'] as Map?;
    return ClinicianResponseData(
      id:
          json['response_id'] as String? ??
          json['review_id'] as String? ??
          'response',
      position: json['position'] as String? ?? 'not_recorded',
      state: json['state'] as String? ?? '',
      version: json['version'] as int? ?? 0,
      createdAt: json['created_at'] as String? ?? '',
      patientSafeSummary: json['patient_safe_summary'] as String?,
      clinicalRationale: rationale == null
          ? null
          : Map<String, dynamic>.from(rationale),
    );
  }

  final String id;
  final String position;
  final String state;
  final int version;
  final String createdAt;
  final String? patientSafeSummary;
  final Map<String, dynamic>? clinicalRationale;
}

class ExpectedCareBaselineData {
  const ExpectedCareBaselineData({
    required this.id,
    required this.clinicalEventId,
    required this.version,
    required this.state,
    required this.currency,
    required this.amountType,
    required this.totalLowMinor,
    required this.totalHighMinor,
    required this.assumptions,
    required this.missingInformation,
    required this.limitations,
    required this.items,
    required this.references,
    required this.nextAction,
    required this.disclaimer,
    required this.latestClinicianPosition,
    required this.clinicianResponses,
    required this.factSnapshot,
    this.patientSafeRationale,
  });

  factory ExpectedCareBaselineData.fromJson(Map<String, dynamic> json) {
    final referenceJson =
        json['release_lineage'] as List<dynamic>? ??
        json['source_effective_dates'] as List<dynamic>? ??
        const <dynamic>[];
    return ExpectedCareBaselineData(
      id: json['baseline_id'] as String? ?? json['envelope_id'] as String,
      clinicalEventId: json['clinical_event_id'] as String,
      version: json['version'] as int,
      state: json['state'] as String,
      currency: json['currency'] as String,
      amountType: json['amount_type'] as String,
      totalLowMinor: json['total_low_minor'] as int,
      totalHighMinor: json['total_high_minor'] as int,
      assumptions: List<String>.from(json['assumptions'] as List? ?? const []),
      missingInformation: List<String>.from(
        json['missing_information'] as List? ?? const [],
      ),
      limitations: List<String>.from(json['limitations'] as List? ?? const []),
      items: (json['items'] as List<dynamic>)
          .map(
            (item) => ExpectedCareItemData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      references: referenceJson
          .map(
            (item) => ExpectedCareReferenceData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      patientSafeRationale: json['patient_safe_rationale'] as String?,
      nextAction: json['responsible_next_action'] as String,
      disclaimer: json['disclaimer'] as String,
      latestClinicianPosition:
          json['latest_clinician_position'] as String? ?? 'not_recorded',
      clinicianResponses:
          (json['clinician_responses'] as List<dynamic>? ?? const <dynamic>[])
              .map(
                (item) => ClinicianResponseData.fromJson(
                  Map<String, dynamic>.from(item as Map),
                ),
              )
              .toList(),
      factSnapshot: CostEstimationFactSnapshotData.fromJson(
        json['cost_estimation_fact_snapshot'],
      ),
    );
  }

  final String id;
  final String clinicalEventId;
  final int version;
  final String state;
  final String currency;
  final String amountType;
  final int totalLowMinor;
  final int totalHighMinor;
  final List<String> assumptions;
  final List<String> missingInformation;
  final List<String> limitations;
  final List<ExpectedCareItemData> items;
  final List<ExpectedCareReferenceData> references;
  final String? patientSafeRationale;
  final String nextAction;
  final String disclaimer;
  final String latestClinicianPosition;
  final List<ClinicianResponseData> clinicianResponses;
  final CostEstimationFactSnapshotData factSnapshot;
}

class PayerExpectedCareData {
  const PayerExpectedCareData({
    required this.baseline,
    required this.payerRequestId,
    required this.submittedState,
    required this.requestedTotalMinor,
    required this.humanReviewState,
  });

  factory PayerExpectedCareData.fromJson(Map<String, dynamic> json) {
    final submitted = Map<String, dynamic>.from(json['submitted_facts'] as Map);
    final review = Map<String, dynamic>.from(json['human_payer_review'] as Map);
    return PayerExpectedCareData(
      baseline: ExpectedCareBaselineData.fromJson(
        Map<String, dynamic>.from(
          json['system_baseline'] as Map? ?? json['doctor_review'] as Map,
        ),
      ),
      payerRequestId: submitted['payer_request_id'] as String,
      submittedState: submitted['state'] as String,
      requestedTotalMinor: submitted['requested_total_minor'] as int,
      humanReviewState: review['state'] as String,
    );
  }

  final ExpectedCareBaselineData baseline;
  final String payerRequestId;
  final String submittedState;
  final int requestedTotalMinor;
  final String humanReviewState;
}

class ClinicianResponseResultData {
  const ClinicianResponseResultData({
    required this.responseId,
    required this.state,
    required this.version,
    required this.idempotentReplay,
  });

  factory ClinicianResponseResultData.fromJson(Map<String, dynamic> json) {
    return ClinicianResponseResultData(
      responseId: json['response_id'] as String? ?? json['review_id'] as String,
      state: json['lifecycle_state'] as String,
      version: json['version'] as int,
      idempotentReplay: json['idempotent_replay'] as bool,
    );
  }

  final String responseId;
  final String state;
  final int version;
  final bool idempotentReplay;
}

class ExpectedCareComparisonItemData {
  const ExpectedCareComparisonItemData({
    required this.itemKey,
    required this.unit,
    required this.baselineAmountLowMinor,
    required this.baselineAmountHighMinor,
    required this.deliveredLabel,
    this.deliveredAmountMinor,
    this.submittedAmountMinor,
    this.submittedLabel,
  });

  factory ExpectedCareComparisonItemData.fromJson(Map<String, dynamic> json) {
    return ExpectedCareComparisonItemData(
      itemKey: json['item_key'] as String,
      unit: json['unit'] as String,
      baselineAmountLowMinor: json['baseline_amount_low_minor'] as int,
      baselineAmountHighMinor: json['baseline_amount_high_minor'] as int,
      deliveredAmountMinor: json['delivered_amount_minor'] as int?,
      submittedAmountMinor: json['submitted_amount_minor'] as int?,
      deliveredLabel: json['delivered_label'] as String,
      submittedLabel: json['submitted_label'] as String?,
    );
  }

  final String itemKey;
  final String unit;
  final int baselineAmountLowMinor;
  final int baselineAmountHighMinor;
  final int? deliveredAmountMinor;
  final int? submittedAmountMinor;
  final String deliveredLabel;
  final String? submittedLabel;
}

class ExpectedCareComparisonData {
  const ExpectedCareComparisonData({
    required this.id,
    required this.baselineId,
    required this.version,
    required this.state,
    required this.currency,
    required this.baselineTotalLowMinor,
    required this.baselineTotalHighMinor,
    required this.deliveredTotalLabel,
    required this.items,
    required this.disclaimer,
    this.idempotentReplay = false,
    this.deliveredTotalMinor,
    this.submittedTotalMinor,
    this.submittedTotalLabel,
  });

  factory ExpectedCareComparisonData.fromJson(Map<String, dynamic> json) {
    final result = Map<String, dynamic>.from(json['result'] as Map);
    return ExpectedCareComparisonData(
      id: json['comparison_id'] as String,
      baselineId: json['baseline_id'] as String,
      version: json['version'] as int,
      state: json['state'] as String,
      currency: result['currency'] as String,
      baselineTotalLowMinor: result['baseline_total_low_minor'] as int,
      baselineTotalHighMinor: result['baseline_total_high_minor'] as int,
      deliveredTotalMinor: result['delivered_total_minor'] as int?,
      submittedTotalMinor: result['submitted_total_minor'] as int?,
      deliveredTotalLabel: result['delivered_total_label'] as String,
      submittedTotalLabel: result['submitted_total_label'] as String?,
      items: (result['items'] as List<dynamic>)
          .map(
            (item) => ExpectedCareComparisonItemData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      disclaimer: json['disclaimer'] as String,
      idempotentReplay: json['idempotent_replay'] as bool? ?? false,
    );
  }

  final String id;
  final String baselineId;
  final int version;
  final String state;
  final String currency;
  final int baselineTotalLowMinor;
  final int baselineTotalHighMinor;
  final int? deliveredTotalMinor;
  final int? submittedTotalMinor;
  final String deliveredTotalLabel;
  final String? submittedTotalLabel;
  final List<ExpectedCareComparisonItemData> items;
  final String disclaimer;
  final bool idempotentReplay;
}

class ExpectedCareExplanationData {
  const ExpectedCareExplanationData({
    required this.id,
    required this.comparisonId,
    required this.state,
    required this.displayMode,
    required this.artifact,
    this.idempotentReplay = false,
  });

  factory ExpectedCareExplanationData.fromJson(Map<String, dynamic> json) {
    return ExpectedCareExplanationData(
      id: json['explanation_id'] as String,
      comparisonId: json['comparison_id'] as String,
      state: json['state'] as String,
      displayMode: json['display_mode'] as String,
      artifact: Map<String, dynamic>.from(json['artifact'] as Map),
      idempotentReplay: json['idempotent_replay'] as bool? ?? false,
    );
  }

  final String id;
  final String comparisonId;
  final String state;
  final String displayMode;
  final Map<String, dynamic> artifact;
  final bool idempotentReplay;

  bool get isValidated =>
      displayMode == 'validated_canonical_explanation' ||
      displayMode == 'validated_ai_explanation';

  List<String> localizedSections(bool chinese) {
    final localized = artifact[chinese ? 'zh_hans' : 'en'];
    if (localized is! Map) {
      return const <String>[];
    }
    return localized.values
        .whereType<Map<dynamic, dynamic>>()
        .map((value) => value['text'])
        .whereType<String>()
        .toList();
  }
}
