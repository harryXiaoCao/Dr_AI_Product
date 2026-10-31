class CareCostItemData {
  const CareCostItemData({
    required this.id,
    required this.clinicalEventId,
    required this.itemType,
    required this.label,
    required this.serviceDate,
    required this.status,
    required this.pricingState,
    required this.sourceType,
    this.sourceCategory = 'legacy',
    this.sourceStatus = 'planned',
    this.alreadySubmitted = false,
    required this.submissionEligible,
    required this.quantity,
    required this.currency,
    required this.actualCostMinor,
    required this.payerRequestedMinor,
    required this.patientResponsibilityMinor,
    required this.aiReviewStatus,
    required this.createdAt,
    required this.updatedAt,
    this.aiReviewScore,
    this.aiReviewSummary,
    this.notes,
    this.sourceRecordId,
    this.ineligibilityReason,
    this.orderedAt,
    this.scheduledAt,
    this.performedAt,
  });

  factory CareCostItemData.fromJson(Map<String, dynamic> json) {
    return CareCostItemData(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String,
      itemType: json['item_type'] as String,
      label: json['label'] as String,
      serviceDate: DateTime.parse(json['service_date'] as String),
      status: json['status'] as String,
      pricingState: json['pricing_state'] as String? ?? 'final',
      sourceType: json['source_type'] as String? ?? 'legacy',
      sourceCategory: json['source_category'] as String? ?? 'legacy',
      sourceStatus: json['source_status'] as String? ?? 'planned',
      alreadySubmitted: json['already_submitted'] as bool? ?? false,
      sourceRecordId: json['source_record_id'] as String?,
      submissionEligible: json['submission_eligible'] as bool? ?? true,
      ineligibilityReason: json['ineligibility_reason'] as String?,
      orderedAt: _optionalDate(json['ordered_at']),
      scheduledAt: _optionalDate(json['scheduled_at']),
      performedAt: _optionalDate(json['performed_at']),
      quantity: json['quantity'] as int,
      currency: json['currency'] as String,
      actualCostMinor: json['actual_cost_minor'] as int,
      payerRequestedMinor: json['payer_requested_minor'] as int,
      patientResponsibilityMinor: json['patient_responsibility_minor'] as int,
      aiReviewScore: json['ai_review_score'] as int?,
      aiReviewStatus: json['ai_review_status'] as String,
      aiReviewSummary: json['ai_review_summary'] as String?,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  final String id;
  final String clinicalEventId;
  final String itemType;
  final String label;
  final DateTime serviceDate;
  final String status;
  final String pricingState;
  final String sourceType;
  final String sourceCategory;
  final String sourceStatus;
  final bool alreadySubmitted;
  final String? sourceRecordId;
  final bool submissionEligible;
  final String? ineligibilityReason;
  final DateTime? orderedAt;
  final DateTime? scheduledAt;
  final DateTime? performedAt;
  final int quantity;
  final String currency;
  final int actualCostMinor;
  final int payerRequestedMinor;
  final int patientResponsibilityMinor;
  final int? aiReviewScore;
  final String aiReviewStatus;
  final String? aiReviewSummary;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;
}

DateTime? _optionalDate(Object? value) =>
    value is String ? DateTime.tryParse(value) : null;

class ClinicalFinancialDraft {
  const ClinicalFinancialDraft({
    required this.pricingState,
    required this.totalCostMinor,
    required this.payerRequestedMinor,
    required this.patientResponsibilityMinor,
    this.serviceDate,
  });

  final String pricingState;
  final int totalCostMinor;
  final int payerRequestedMinor;
  final int patientResponsibilityMinor;
  final DateTime? serviceDate;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'pricing_state': pricingState,
    'currency': 'CNY',
    'total_cost_minor': totalCostMinor,
    'payer_requested_minor': payerRequestedMinor,
    'patient_responsibility_minor': patientResponsibilityMinor,
    if (serviceDate != null)
      'service_date': serviceDate!.toIso8601String().split('T').first,
  };
}

class CareCostEventData {
  const CareCostEventData({
    required this.clinicalEventId,
    required this.title,
    required this.status,
    required this.actualTotalMinor,
    required this.payerRequestedTotalMinor,
    required this.patientResponsibilityTotalMinor,
    required this.currency,
    required this.items,
  });

  factory CareCostEventData.fromJson(Map<String, dynamic> json) {
    return CareCostEventData(
      clinicalEventId: json['clinical_event_id'] as String,
      title: json['title'] as String,
      status: json['status'] as String,
      actualTotalMinor: json['actual_total_minor'] as int,
      payerRequestedTotalMinor: json['payer_requested_total_minor'] as int,
      patientResponsibilityTotalMinor:
          json['patient_responsibility_total_minor'] as int,
      currency: json['currency'] as String,
      items: (json['items'] as List<dynamic>)
          .map(
            (item) => CareCostItemData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
    );
  }

  final String clinicalEventId;
  final String title;
  final String status;
  final int actualTotalMinor;
  final int payerRequestedTotalMinor;
  final int patientResponsibilityTotalMinor;
  final String currency;
  final List<CareCostItemData> items;
}

class CareCostLedgerData {
  const CareCostLedgerData({
    required this.patientId,
    required this.patientDisplayName,
    required this.actualTotalMinor,
    required this.estimatedTotalMinor,
    required this.finalTotalMinor,
    required this.payerRequestedTotalMinor,
    required this.patientResponsibilityTotalMinor,
    required this.pendingCostItemCount,
    required this.currency,
    required this.events,
  });

  factory CareCostLedgerData.fromJson(Map<String, dynamic> json) {
    return CareCostLedgerData(
      patientId: json['patient_id'] as String,
      patientDisplayName: json['patient_display_name'] as String,
      actualTotalMinor: json['actual_total_minor'] as int,
      estimatedTotalMinor: json['estimated_total_minor'] as int,
      finalTotalMinor: json['final_total_minor'] as int,
      payerRequestedTotalMinor: json['payer_requested_total_minor'] as int,
      patientResponsibilityTotalMinor:
          json['patient_responsibility_total_minor'] as int,
      pendingCostItemCount: json['pending_cost_item_count'] as int,
      currency: json['currency'] as String,
      events: (json['events'] as List<dynamic>)
          .map(
            (item) => CareCostEventData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
    );
  }

  final String patientId;
  final String patientDisplayName;
  final int actualTotalMinor;
  final int estimatedTotalMinor;
  final int finalTotalMinor;
  final int payerRequestedTotalMinor;
  final int patientResponsibilityTotalMinor;
  final int pendingCostItemCount;
  final String currency;
  final List<CareCostEventData> events;
}

class PayerOrganizationData {
  const PayerOrganizationData({
    required this.id,
    required this.name,
    required this.organizationType,
    required this.jurisdictionCode,
    required this.verificationStatus,
  });

  factory PayerOrganizationData.fromJson(Map<String, dynamic> json) {
    return PayerOrganizationData(
      id: json['id'] as String,
      name: json['name'] as String,
      organizationType: json['organization_type'] as String,
      jurisdictionCode: json['jurisdiction_code'] as String,
      verificationStatus: json['verification_status'] as String,
    );
  }

  final String id;
  final String name;
  final String organizationType;
  final String jurisdictionCode;
  final String verificationStatus;
}

class PayerRequestLineData {
  const PayerRequestLineData({
    required this.id,
    required this.careCostItemId,
    required this.itemType,
    required this.label,
    required this.serviceDate,
    required this.currency,
    required this.actualCostMinor,
    required this.requestedMinor,
    required this.patientResponsibilityMinor,
  });

  factory PayerRequestLineData.fromJson(Map<String, dynamic> json) {
    return PayerRequestLineData(
      id: json['id'] as String,
      careCostItemId: json['care_cost_item_id'] as String?,
      itemType: json['item_type'] as String,
      label: json['label'] as String,
      serviceDate: DateTime.parse(json['service_date'] as String),
      currency: json['currency'] as String,
      actualCostMinor: json['actual_cost_minor'] as int,
      requestedMinor: json['requested_minor'] as int,
      patientResponsibilityMinor: json['patient_responsibility_minor'] as int,
    );
  }

  final String id;
  final String? careCostItemId;
  final String itemType;
  final String label;
  final DateTime serviceDate;
  final String currency;
  final int actualCostMinor;
  final int requestedMinor;
  final int patientResponsibilityMinor;
}

class PayerReviewData {
  const PayerReviewData({
    required this.id,
    required this.action,
    required this.reasonCode,
    required this.createdAt,
    this.reviewerMembershipId = '',
    this.reviewerDisplayName = '',
    this.reviewerTitle = '',
    this.fromStatus = '',
    this.toStatus = '',
    this.version = 1,
    this.clarificationMessage,
    this.note,
  });

  factory PayerReviewData.fromJson(Map<String, dynamic> json) {
    return PayerReviewData(
      id: json['id'] as String,
      action: json['action'] as String,
      reasonCode: json['reason_code'] as String,
      clarificationMessage: json['clarification_message'] as String?,
      note: json['note'] as String?,
      reviewerMembershipId: json['reviewer_membership_id'] as String? ?? '',
      reviewerDisplayName: json['reviewer_display_name'] as String? ?? '',
      reviewerTitle: json['reviewer_title'] as String? ?? '',
      fromStatus: json['from_status'] as String? ?? '',
      toStatus: json['to_status'] as String? ?? '',
      version: json['version'] as int? ?? 1,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String action;
  final String reasonCode;
  final String? clarificationMessage;
  final String? note;
  final String reviewerMembershipId;
  final String reviewerDisplayName;
  final String reviewerTitle;
  final String fromStatus;
  final String toStatus;
  final int version;
  final DateTime createdAt;
}

class PayerDoctorResponseData {
  const PayerDoctorResponseData({
    required this.id,
    required this.responseType,
    required this.summary,
    required this.doctorId,
    required this.doctorDisplayName,
    required this.version,
    required this.createdAt,
    this.baselineId,
    this.comparisonId,
  });

  factory PayerDoctorResponseData.fromJson(Map<String, dynamic> json) {
    return PayerDoctorResponseData(
      id: json['id'] as String,
      responseType: json['response_type'] as String,
      summary: json['summary'] as String,
      doctorId: json['doctor_id'] as String,
      doctorDisplayName: json['doctor_display_name'] as String,
      baselineId: json['baseline_id'] as String?,
      comparisonId: json['comparison_id'] as String?,
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  final String id;
  final String responseType;
  final String summary;
  final String doctorId;
  final String doctorDisplayName;
  final String? baselineId;
  final String? comparisonId;
  final int version;
  final DateTime createdAt;
}

class PayerRequestData {
  const PayerRequestData({
    required this.id,
    required this.clinicalEventId,
    required this.clinicalEventTitle,
    required this.patientId,
    required this.patientDisplayName,
    required this.doctorDisplayName,
    required this.payerOrganization,
    required this.status,
    required this.currency,
    required this.requestedTotalMinor,
    required this.doctorSummary,
    required this.aiReviewStatus,
    required this.createdAt,
    required this.lines,
    required this.reviews,
    this.version = 1,
    this.doctorResponses = const <PayerDoctorResponseData>[],
    this.aiReviewScore,
    this.aiReviewSummary,
    this.reviewedAt,
    this.reviewSignals,
  });

  factory PayerRequestData.fromJson(Map<String, dynamic> json) {
    return PayerRequestData(
      id: json['id'] as String,
      clinicalEventId: json['clinical_event_id'] as String,
      clinicalEventTitle: json['clinical_event_title'] as String,
      patientId: json['patient_id'] as String,
      patientDisplayName: json['patient_display_name'] as String,
      doctorDisplayName: json['doctor_display_name'] as String,
      payerOrganization: PayerOrganizationData.fromJson(
        Map<String, dynamic>.from(json['payer_organization'] as Map),
      ),
      status: json['status'] as String,
      version: json['version'] as int? ?? 1,
      currency: json['currency'] as String,
      requestedTotalMinor: json['requested_total_minor'] as int,
      doctorSummary: json['doctor_summary'] as String,
      aiReviewStatus: json['ai_review_status'] as String,
      aiReviewScore: json['ai_review_score'] as int?,
      aiReviewSummary: json['ai_review_summary'] as String?,
      reviewSignals: json['review_signals'] is Map
          ? PayerReviewSignalsData.fromJson(
              Map<String, dynamic>.from(json['review_signals'] as Map),
            )
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      reviewedAt: json['reviewed_at'] == null
          ? null
          : DateTime.parse(json['reviewed_at'] as String),
      lines: (json['lines'] as List<dynamic>)
          .map(
            (item) => PayerRequestLineData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      reviews: (json['reviews'] as List<dynamic>)
          .map(
            (item) => PayerReviewData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      doctorResponses: (json['doctor_responses'] as List<dynamic>? ?? const [])
          .map(
            (item) => PayerDoctorResponseData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
    );
  }

  final String id;
  final String clinicalEventId;
  final String clinicalEventTitle;
  final String patientId;
  final String patientDisplayName;
  final String doctorDisplayName;
  final PayerOrganizationData payerOrganization;
  final String status;
  final int version;
  final String currency;
  final int requestedTotalMinor;
  final String doctorSummary;
  final String aiReviewStatus;
  final int? aiReviewScore;
  final String? aiReviewSummary;
  final PayerReviewSignalsData? reviewSignals;
  final DateTime createdAt;
  final DateTime? reviewedAt;
  final List<PayerRequestLineData> lines;
  final List<PayerReviewData> reviews;
  final List<PayerDoctorResponseData> doctorResponses;
}

class PayerReviewSignalsData {
  const PayerReviewSignalsData({
    required this.artifactVersion,
    required this.assessmentUnavailable,
    required this.lowConfidence,
    required this.missingInformation,
    required this.conflictingEvidence,
    required this.costException,
  });

  factory PayerReviewSignalsData.fromJson(Map<String, dynamic> json) =>
      PayerReviewSignalsData(
        artifactVersion: json['artifact_version'] as int,
        assessmentUnavailable: json['assessment_unavailable'] as bool? ?? false,
        lowConfidence: json['low_confidence'] as bool? ?? false,
        missingInformation: json['missing_information'] as bool? ?? false,
        conflictingEvidence: json['conflicting_evidence'] as bool? ?? false,
        costException: json['cost_exception'] as bool? ?? false,
      );

  final int artifactVersion;
  final bool assessmentUnavailable;
  final bool lowConfidence;
  final bool missingInformation;
  final bool conflictingEvidence;
  final bool costException;
}

class PayerProfileData {
  const PayerProfileData({
    required this.membershipId,
    required this.displayName,
    required this.title,
    required this.status,
    required this.scope,
    required this.organization,
  });

  factory PayerProfileData.fromJson(Map<String, dynamic> json) {
    return PayerProfileData(
      membershipId: json['membership_id'] as String,
      displayName: json['display_name'] as String,
      title: json['title'] as String,
      status: json['status'] as String,
      scope: json['scope'] as String,
      organization: PayerOrganizationData.fromJson(
        Map<String, dynamic>.from(json['organization'] as Map),
      ),
    );
  }

  final String membershipId;
  final String displayName;
  final String title;
  final String status;
  final String scope;
  final PayerOrganizationData organization;
}

class PayerDashboardData {
  const PayerDashboardData({
    required this.profile,
    required this.openRequests,
    required this.clarificationRequests,
    this.escalatedRequests = 0,
    required this.completedReviews,
    required this.pendingRequestedTotalMinor,
    required this.currency,
  });

  factory PayerDashboardData.fromJson(Map<String, dynamic> json) {
    return PayerDashboardData(
      profile: PayerProfileData.fromJson(
        Map<String, dynamic>.from(json['profile'] as Map),
      ),
      openRequests: json['open_requests'] as int,
      clarificationRequests: json['clarification_requests'] as int,
      escalatedRequests: json['escalated_requests'] as int? ?? 0,
      completedReviews: json['completed_reviews'] as int,
      pendingRequestedTotalMinor: json['pending_requested_total_minor'] as int,
      currency: json['currency'] as String,
    );
  }

  final PayerProfileData profile;
  final int openRequests;
  final int clarificationRequests;
  final int escalatedRequests;
  final int completedReviews;
  final int pendingRequestedTotalMinor;
  final String currency;
}
