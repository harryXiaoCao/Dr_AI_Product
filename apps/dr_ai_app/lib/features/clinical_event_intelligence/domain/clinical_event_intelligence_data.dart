class ClinicalEventIntelligenceData {
  const ClinicalEventIntelligenceData({
    required this.artifactId,
    required this.artifactVersion,
    required this.clinicalEventSnapshotVersion,
    required this.lifecycleState,
    required this.createdAt,
    required this.location,
    required this.requestedItems,
    required this.pathways,
    required this.missingDocumentation,
    required this.counterfactuals,
    required this.critic,
    required this.lineage,
    required this.humanReviewState,
    required this.purposeSummary,
    required this.explanationDisplayMode,
  });

  factory ClinicalEventIntelligenceData.fromJson(Map<String, dynamic> json) {
    final explanation = _map(json['explanation']);
    final critic = _map(json['critic']);
    critic.putIfAbsent('state', () => json['disagreement_state']);
    return ClinicalEventIntelligenceData(
      artifactId: json['artifact_id'] as String,
      artifactVersion: json['artifact_version'] as int,
      clinicalEventSnapshotVersion:
          json['clinical_event_snapshot_version'] as int? ?? 1,
      lifecycleState: json['lifecycle_state'] as String? ?? 'validated',
      createdAt: json['created_at'] as String? ?? '',
      location: IntelligenceLocationData.fromJson(_map(json['location'])),
      requestedItems: _list(
        json['requested_item_assessments'],
      ).map(RequestedItemAssessmentData.fromJson).toList(growable: false),
      pathways: _list(
        json['pathways'],
      ).map(IntelligencePathwayData.fromJson).toList(growable: false),
      missingDocumentation: _strings(
        json['missing_documentation'] ??
            json['missing_information'] ??
            json['missing_or_conflicting_facts'],
      ),
      counterfactuals: _list(
        json['counterfactuals'],
      ).map(CounterfactualData.fromJson).toList(growable: false),
      critic: IntelligenceCriticData.fromJson(critic),
      lineage: _list(
        json['lineage'] ?? json['outcome_lineage'],
      ).map(IntelligenceLineageData.fromJson).toList(growable: false),
      humanReviewState:
          json['human_review_state'] as String? ?? 'human_review_required',
      purposeSummary:
          json['purpose_summary'] as String? ??
          json['purpose'] as String? ??
          '',
      explanationDisplayMode:
          json['explanation_display_mode'] as String? ??
          explanation['display_mode'] as String? ??
          'structured_facts',
    );
  }

  final String artifactId;
  final int artifactVersion;
  final int clinicalEventSnapshotVersion;
  final String lifecycleState;
  final String createdAt;
  final IntelligenceLocationData location;
  final List<RequestedItemAssessmentData> requestedItems;
  final List<IntelligencePathwayData> pathways;
  final List<String> missingDocumentation;
  final List<CounterfactualData> counterfactuals;
  final IntelligenceCriticData critic;
  final List<IntelligenceLineageData> lineage;
  final String humanReviewState;
  final String purposeSummary;
  final String explanationDisplayMode;

  bool get isProviderUnavailable => lifecycleState == 'provider_unavailable';
  bool get isFallback => lifecycleState == 'fallback';
}

class IntelligenceLocationData {
  const IntelligenceLocationData({
    required this.jurisdictionCode,
    required this.provinceCode,
    required this.cityCode,
    required this.facilityLevel,
    required this.source,
  });

  factory IntelligenceLocationData.fromJson(Map<String, dynamic> json) {
    return IntelligenceLocationData(
      jurisdictionCode: json['jurisdiction_code'] as String? ?? '',
      provinceCode: json['province_code'] as String? ?? '',
      cityCode: json['city_code'] as String? ?? '',
      facilityLevel: json['facility_level'] as String? ?? '',
      source: json['source'] as String? ?? '',
    );
  }

  final String jurisdictionCode;
  final String provinceCode;
  final String cityCode;
  final String facilityLevel;
  final String source;
}

class RequestedItemAssessmentData {
  const RequestedItemAssessmentData({
    required this.requestedLineId,
    required this.label,
    required this.requestedQuantity,
    required this.requestedUnit,
    required this.requestedAmountMinor,
    required this.currency,
    required this.codeSystem,
    required this.serviceCode,
    required this.usefulness,
    required this.mappedPathwayIds,
    required this.scores,
    required this.estimatedQuantity,
    required this.estimatedCost,
    required this.supportingFacts,
    required this.contradictingFacts,
    required this.missingInformation,
    required this.alternatives,
    required this.confidence,
    required this.comment,
    required this.validationState,
    required this.disagreementState,
  });

  factory RequestedItemAssessmentData.fromJson(Map<String, dynamic> json) {
    final proposal = _map(json['proposal']);
    final source = <String, dynamic>{...proposal, ...json};
    final requested = _map(source['requested'] ?? source['requested_line']);
    final cost = _map(source['estimated_cost']);
    final scores = <String, dynamic>{..._map(source['scores'])};
    scores.putIfAbsent('ai_support_score', () => source['ai_support_score']);
    scores.putIfAbsent(
      'score_contract_version',
      () => source['score_contract_version'],
    );
    scores.putIfAbsent('band', () => source['score_band']);
    return RequestedItemAssessmentData(
      requestedLineId: source['requested_line_id'] as String,
      label: source['label'] as String? ?? requested['label'] as String? ?? '',
      requestedQuantity: _number(
        source['requested_quantity'] ?? requested['quantity'],
      ),
      requestedUnit:
          source['requested_unit'] as String? ??
          requested['unit'] as String? ??
          '',
      requestedAmountMinor: _integer(
        source['requested_amount_minor'] ??
            requested['requested_minor'] ??
            requested['amount_minor'],
      ),
      currency:
          source['currency'] as String? ??
          requested['currency'] as String? ??
          cost['currency'] as String? ??
          'CNY',
      codeSystem:
          source['code_system'] as String? ??
          requested['code_system'] as String?,
      serviceCode:
          source['service_code'] as String? ??
          requested['service_code'] as String?,
      usefulness: source['usefulness'] as String? ?? '',
      mappedPathwayIds: _strings(source['mapped_pathway_ids']),
      scores: IntelligenceScoresData.fromJson(scores),
      estimatedQuantity: EstimatedQuantityData.fromJson(
        _map(source['estimated_quantity']),
      ),
      estimatedCost: EstimatedCostData.fromJson(cost),
      supportingFacts: _strings(
        source['supporting_facts'] ?? source['supporting_fact_ids'],
      ),
      contradictingFacts: _strings(
        source['contradicting_facts'] ?? source['contradicting_fact_ids'],
      ),
      missingInformation: _strings(source['missing_information']),
      alternatives: _strings(source['alternatives']),
      confidence: source['confidence'] as String? ?? 'unknown',
      comment: source['brief_comment'] as String? ?? '',
      validationState:
          source['validation_state'] as String? ??
          source['state'] as String? ??
          (_strings(source['validation_results']).isEmpty
              ? 'validated'
              : 'validated_with_results'),
      disagreementState: source['disagreement_state'] as String? ?? 'agreement',
    );
  }

  final String requestedLineId;
  final String label;
  final num requestedQuantity;
  final String requestedUnit;
  final int requestedAmountMinor;
  final String currency;
  final String? codeSystem;
  final String? serviceCode;
  final String usefulness;
  final List<String> mappedPathwayIds;
  final IntelligenceScoresData scores;
  final EstimatedQuantityData estimatedQuantity;
  final EstimatedCostData estimatedCost;
  final List<String> supportingFacts;
  final List<String> contradictingFacts;
  final List<String> missingInformation;
  final List<String> alternatives;
  final String confidence;
  final String comment;
  final String validationState;
  final String disagreementState;

  bool get isAssessmentUnavailable =>
      validationState == 'assessment_unavailable';
}

class IntelligenceScoresData {
  const IntelligenceScoresData({
    required this.clinicalFit,
    required this.evidenceSupport,
    required this.timingSequence,
    required this.quantityIntensity,
    required this.documentationCompleteness,
    required this.costAlignment,
    required this.aiSupportScore,
    required this.scoreContractVersion,
    required this.band,
  });

  factory IntelligenceScoresData.fromJson(Map<String, dynamic> json) {
    return IntelligenceScoresData(
      clinicalFit: _integer(json['clinical_fit']),
      evidenceSupport: _integer(json['evidence_support']),
      timingSequence: _integer(json['timing_sequence']),
      quantityIntensity: _integer(json['quantity_intensity']),
      documentationCompleteness: _integer(json['documentation_completeness']),
      costAlignment: _integer(json['cost_alignment']),
      aiSupportScore: _integer(json['ai_support_score']),
      scoreContractVersion:
          json['score_contract_version'] as String? ?? 'unknown',
      band: json['band'] as String? ?? '',
    );
  }

  final int clinicalFit;
  final int evidenceSupport;
  final int timingSequence;
  final int quantityIntensity;
  final int documentationCompleteness;
  final int costAlignment;
  final int aiSupportScore;
  final String scoreContractVersion;
  final String band;
}

class EstimatedQuantityData {
  const EstimatedQuantityData({
    required this.low,
    required this.high,
    required this.unit,
  });

  factory EstimatedQuantityData.fromJson(Map<String, dynamic> json) {
    return EstimatedQuantityData(
      low: _number(json['low']),
      high: _number(json['high']),
      unit: json['unit'] as String? ?? '',
    );
  }

  final num low;
  final num high;
  final String unit;
}

class EstimatedCostData {
  const EstimatedCostData({
    required this.lowMinor,
    required this.highMinor,
    required this.currency,
    required this.provenanceTier,
    required this.sourceLabels,
    required this.isModelOnlyExploratory,
  });

  factory EstimatedCostData.fromJson(Map<String, dynamic> json) {
    return EstimatedCostData(
      lowMinor: _integer(json['low_minor']),
      highMinor: _integer(json['high_minor']),
      currency: json['currency'] as String? ?? 'CNY',
      provenanceTier: _integer(json['provenance_tier']),
      sourceLabels: _strings(json['source_labels'] ?? json['source_ids']),
      isModelOnlyExploratory:
          json['is_model_only_exploratory'] as bool? ?? false,
    );
  }

  final int lowMinor;
  final int highMinor;
  final String currency;
  final int provenanceTier;
  final List<String> sourceLabels;
  final bool isModelOnlyExploratory;
}

class IntelligencePathwayData {
  const IntelligencePathwayData({
    required this.id,
    required this.type,
    required this.summary,
    required this.items,
  });

  factory IntelligencePathwayData.fromJson(Map<String, dynamic> json) {
    return IntelligencePathwayData(
      id: json['pathway_id'] as String,
      type: json['pathway_type'] as String? ?? 'typical_first_line',
      summary:
          json['summary'] as String? ??
          <String>[
            ..._strings(json['assumptions']),
            ..._strings(json['limitations']),
          ].join(' · '),
      items: (json['items'] as List<dynamic>? ?? const <dynamic>[])
          .map(
            (item) => item is Map
                ? PredictedPathwayItemData.fromJson(
                    Map<String, dynamic>.from(item),
                  )
                : PredictedPathwayItemData(
                    key: '',
                    category: '',
                    label: item.toString(),
                    code: null,
                    quantityLow: 0,
                    quantityHigh: 0,
                    unit: '',
                  ),
          )
          .toList(growable: false),
    );
  }

  final String id;
  final String type;
  final String summary;
  final List<PredictedPathwayItemData> items;
}

class PredictedPathwayItemData {
  const PredictedPathwayItemData({
    required this.key,
    required this.category,
    required this.label,
    required this.code,
    required this.quantityLow,
    required this.quantityHigh,
    required this.unit,
  });

  factory PredictedPathwayItemData.fromJson(Map<String, dynamic> json) {
    return PredictedPathwayItemData(
      key: json['item_key'] as String? ?? '',
      category: json['category'] as String? ?? '',
      label: json['label'] as String? ?? json['category'] as String? ?? '',
      code: json['code'] as String? ?? json['service_code'] as String?,
      quantityLow: _number(json['quantity_low']),
      quantityHigh: _number(json['quantity_high']),
      unit: json['unit'] as String? ?? '',
    );
  }

  final String key;
  final String category;
  final String label;
  final String? code;
  final num quantityLow;
  final num quantityHigh;
  final String unit;
}

class IntelligenceCriticData {
  const IntelligenceCriticData({required this.state, required this.summary});

  factory IntelligenceCriticData.fromJson(Map<String, dynamic> json) {
    return IntelligenceCriticData(
      state:
          json['state'] as String? ??
          json['agreement_state'] as String? ??
          'unavailable',
      summary: json['summary'] as String? ?? '',
    );
  }

  final String state;
  final String summary;
}

class CounterfactualData {
  const CounterfactualData({required this.title, required this.summary});

  factory CounterfactualData.fromJson(Map<String, dynamic> json) {
    return CounterfactualData(
      title: json['title'] as String? ?? '',
      summary: json['summary'] as String? ?? '',
    );
  }

  final String title;
  final String summary;
}

class IntelligenceLineageData {
  const IntelligenceLineageData({
    required this.eventType,
    required this.label,
    required this.occurredAt,
  });

  factory IntelligenceLineageData.fromJson(Map<String, dynamic> json) {
    return IntelligenceLineageData(
      eventType: json['event_type'] as String? ?? 'artifact_created',
      label: json['label'] as String? ?? '',
      occurredAt: json['occurred_at'] as String? ?? '',
    );
  }

  final String eventType;
  final String label;
  final String occurredAt;
}

class IntelligenceResponseResultData {
  const IntelligenceResponseResultData({
    required this.responseId,
    required this.idempotentReplay,
  });

  factory IntelligenceResponseResultData.fromJson(Map<String, dynamic> json) {
    return IntelligenceResponseResultData(
      responseId: json['response_id'] as String,
      idempotentReplay: json['idempotent_replay'] as bool? ?? false,
    );
  }

  final String responseId;
  final bool idempotentReplay;
}

Map<String, dynamic> _map(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const <String, dynamic>{};

List<Map<String, dynamic>> _list(Object? value) => value is List
    ? value
          .whereType<Map<Object?, Object?>>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(growable: false)
    : const <Map<String, dynamic>>[];

List<String> _strings(Object? value) => value is List
    ? value.whereType<String>().toList(growable: false)
    : const <String>[];

int _integer(Object? value) => value is num ? value.toInt() : 0;
num _number(Object? value) => value is num ? value : 0;
