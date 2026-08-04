import 'dart:async';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/domain/clinical_event_intelligence_data.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/presentation/clinical_event_intelligence_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

void _viewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> _pump(
  WidgetTester tester, {
  required AppRole role,
  required FakeDrAiRepository repository,
  Locale locale = const Locale('en'),
  bool settle = true,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: ClinicalEventIntelligenceScreen(
          role: role,
          requestId: 'payer-request-test-id',
        ),
      ),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  }
}

ClinicalEventIntelligenceData _artifactWith({
  String lifecycleState = 'validated',
  String explanationDisplayMode = 'structured_facts',
  String criticState = 'partial_disagreement',
}) {
  final source = FakeDrAiRepository.clinicalEventIntelligenceFixture;
  return ClinicalEventIntelligenceData(
    artifactId: source.artifactId,
    artifactVersion: source.artifactVersion,
    clinicalEventSnapshotVersion: source.clinicalEventSnapshotVersion,
    lifecycleState: lifecycleState,
    createdAt: source.createdAt,
    location: source.location,
    requestedItems: source.requestedItems,
    pathways: source.pathways,
    missingDocumentation: source.missingDocumentation,
    counterfactuals: source.counterfactuals,
    critic: IntelligenceCriticData(
      state: criticState,
      summary: source.critic.summary,
    ),
    lineage: source.lineage,
    humanReviewState: source.humanReviewState,
    purposeSummary: source.purposeSummary,
    explanationDisplayMode: explanationDisplayMode,
  );
}

void main() {
  test(
    'DTO parses structured pathways, scoring, tier 5, and line identity',
    () {
      final data = ClinicalEventIntelligenceData.fromJson(<String, dynamic>{
        'artifact_id': 'artifact',
        'artifact_version': 1,
        'clinical_event_snapshot_version': 2,
        'lifecycle_state': 'validated',
        'location': <String, dynamic>{
          'jurisdiction_code': 'CN',
          'source': 'clinical_event',
        },
        'requested_item_assessments': <Object>[
          <String, dynamic>{
            'requested_line_id': 'line-1',
            'label': 'Requested service',
            'code_system': 'catalog',
            'service_code': 'ABC',
            'requested_quantity': 1,
            'requested_unit': 'visit',
            'requested_amount_minor': 1000,
            'scores': <String, dynamic>{
              'clinical_fit': 80,
              'evidence_support': 70,
              'timing_sequence': 60,
              'quantity_intensity': 50,
              'documentation_completeness': 40,
              'cost_alignment': 0,
              'ai_support_score': 61,
              'score_contract_version': 'v1',
              'band': 'plausible',
            },
            'estimated_quantity': <String, dynamic>{
              'low': 1,
              'high': 3,
              'unit': 'visits',
            },
            'estimated_cost': <String, dynamic>{
              'low_minor': 500,
              'high_minor': 5000,
              'currency': 'CNY',
              'provenance_tier': 5,
              'source_ids': <String>[],
              'is_model_only_exploratory': true,
            },
          },
        ],
        'pathways': <Object>[
          <String, dynamic>{
            'pathway_id': 'path-1',
            'pathway_type': 'typical_first_line',
            'items': <Object>[
              <String, dynamic>{
                'item_key': 'predicted-1',
                'category': 'consultation',
                'label': 'Predicted follow-up',
                'quantity_low': 1,
                'quantity_high': 2,
                'unit': 'visits',
              },
            ],
          },
        ],
        'critic': <String, dynamic>{'state': 'agreement'},
      });

      expect(data.requestedItems.single.requestedLineId, 'line-1');
      expect(data.requestedItems.single.scores.aiSupportScore, 61);
      expect(data.requestedItems.single.estimatedCost.provenanceTier, 5);
      expect(data.pathways.single.items.single.key, 'predicted-1');

      final nested = RequestedItemAssessmentData.fromJson(<String, dynamic>{
        'proposal': <String, dynamic>{
          'requested_line_id': 'nested-line',
          'scores': <String, dynamic>{
            'clinical_fit': 80,
            'evidence_support': 70,
            'timing_sequence': 60,
            'quantity_intensity': 50,
            'documentation_completeness': 40,
            'cost_alignment': 30,
          },
          'estimated_quantity': <String, dynamic>{
            'low': 1,
            'high': 1,
            'unit': 'visit',
          },
          'estimated_cost': <String, dynamic>{
            'low_minor': 100,
            'high_minor': 200,
            'currency': 'CNY',
            'provenance_tier': 2,
          },
        },
        'ai_support_score': 62,
        'score_band': 'plausible',
        'score_contract_version': 'v-nested',
        'validation_results': <String>['line_coverage_validated'],
      });
      expect(nested.scores.aiSupportScore, 62);
      expect(nested.scores.band, 'plausible');
      expect(nested.validationState, 'validated_with_results');
    },
  );

  testWidgets('patient mobile loading state is localized', (tester) async {
    _viewport(tester, const Size(412, 917));
    await _pump(
      tester,
      role: AppRole.patient,
      locale: const Locale('zh'),
      repository: FakeDrAiRepository(
        restoredSession: patientSession,
        intelligenceCompleter: Completer<ClinicalEventIntelligenceData?>(),
      ),
      settle: false,
    );
    await tester.pump();

    expect(find.bySemanticsLabel('正在加载已冻结的临床事件智能'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor sees every requested line once and human-only controls', (
    tester,
  ) async {
    _viewport(tester, const Size(1280, 1000));
    await _pump(
      tester,
      role: AppRole.doctor,
      repository: FakeDrAiRepository(restoredSession: doctorSession),
    );

    expect(
      find.byKey(const Key('intelligence-item-requested-line-assessment')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('intelligence-item-requested-line-tier5')),
      findsOneWidget,
    );
    expect(find.text('AI support score'), findsNWidgets(2));
    expect(find.text('Clinical fit'), findsNWidgets(2));
    expect(find.text('Documentation completeness'), findsNWidgets(2));
    expect(find.text('Model-only exploratory estimate'), findsOneWidget);
    expect(find.text('No admitted price source'), findsOneWidget);
    expect(find.text('Acknowledge'), findsOneWidget);
    expect(find.text('Concur'), findsOneWidget);
    expect(find.text('Approve'), findsNothing);
    expect(find.text('Deny'), findsNothing);

    final scrollable = find.byType(Scrollable).last;
    await tester.scrollUntilVisible(
      find.text('Plausible predicted pathways'),
      700,
      scrollable: scrollable,
    );
    expect(find.textContaining('not doctor-requested items'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Missing-documentation assistant'),
      700,
      scrollable: scrollable,
    );
    expect(find.byKey(const Key('cei-missing-documentation')), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Counterfactual comparisons'),
      700,
      scrollable: scrollable,
    );
    await tester.scrollUntilVisible(
      find.text('Primary and critic'),
      700,
      scrollable: scrollable,
    );
    expect(
      find.byKey(const Key('cei-critic-partial_disagreement')),
      findsOneWidget,
    );
    await tester.scrollUntilVisible(
      find.text('Immutable outcome lineage'),
      700,
      scrollable: scrollable,
    );
    expect(find.text('Clinical Event snapshot frozen'), findsOneWidget);
  });

  testWidgets('patient mobile is bilingual and hides catalog codes', (
    tester,
  ) async {
    _viewport(tester, const Size(412, 917));
    await _pump(
      tester,
      role: AppRole.patient,
      locale: const Locale('zh'),
      repository: FakeDrAiRepository(restoredSession: patientSession),
    );

    expect(find.text('您的诊疗与费用智能'), findsOneWidget);
    expect(find.text('AI 支持分数'), findsNWidgets(2));
    expect(find.text('仅模型探索性估算'), findsOneWidget);
    expect(find.text('SYN-CONSULT-01'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'payer desktop Chinese keeps missing information, tier 5, and material disagreement visible',
    (tester) async {
      _viewport(tester, const Size(1280, 1000));
      await _pump(
        tester,
        role: AppRole.payer,
        locale: const Locale('zh'),
        repository: FakeDrAiRepository(
          restoredSession: payerSession,
          intelligenceArtifact: _artifactWith(
            criticState: 'material_disagreement',
          ),
        ),
      );

      expect(
        find.byKey(const Key('intelligence-tier5-requested-line-tier5')),
        findsOneWidget,
      );
      expect(find.text('无已准入价格来源'), findsOneWidget);
      final scrollable = find.byType(Scrollable).last;
      await tester.scrollUntilVisible(
        find.text('缺失文档助手'),
        700,
        scrollable: scrollable,
      );
      expect(
        find.byKey(const Key('cei-missing-documentation')),
        findsOneWidget,
      );
      await tester.scrollUntilVisible(
        find.text('主模型与审查模型'),
        700,
        scrollable: scrollable,
      );
      expect(
        find.byKey(const Key('cei-critic-material_disagreement')),
        findsOneWidget,
      );
      expect(find.text('重大分歧'), findsWidgets);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('patient desktop keeps structured fallback facts usable', (
    tester,
  ) async {
    _viewport(tester, const Size(1280, 900));
    await _pump(
      tester,
      role: AppRole.patient,
      repository: FakeDrAiRepository(
        restoredSession: patientSession,
        intelligenceArtifact: _artifactWith(
          explanationDisplayMode: 'structured_fallback',
        ),
      ),
    );

    expect(find.text('Structured fallback is active'), findsOneWidget);
    expect(find.byKey(const Key('cei-artifact-header')), findsOneWidget);
    expect(find.text('AI support score'), findsNWidgets(2));
    expect(find.text('SYN-CONSULT-01'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('provider failure leaves human workflow copy and retry visible', (
    tester,
  ) async {
    _viewport(tester, const Size(412, 917));
    await _pump(
      tester,
      role: AppRole.payer,
      repository: FakeDrAiRepository(
        restoredSession: payerSession,
        intelligenceError: const ApiError(
          code: 'provider_unavailable',
          message: 'unavailable',
          statusCode: 503,
        ),
      ),
    );

    expect(find.text('AI provider unavailable'), findsOneWidget);
    expect(find.textContaining('human review'), findsOneWidget);
    expect(find.text('Refresh'), findsOneWidget);
  });

  testWidgets('real unavailable assessment never renders fake score or tier', (
    tester,
  ) async {
    _viewport(tester, const Size(1280, 900));
    final frozen = ClinicalEventIntelligenceData.fromJson(<String, dynamic>{
      'artifact_id': 'fallback-artifact',
      'artifact_version': 2,
      'clinical_event_snapshot_version': 2,
      'lifecycle_state': 'provider_unavailable',
      'location': <String, dynamic>{'source': 'missing_structured_records'},
      'requested_item_assessments': <Object>[
        <String, dynamic>{
          'requested_line_id': 'requested-line-unavailable',
          'label': 'Requested synthetic panel',
          'requested_quantity': 1,
          'requested_unit': 'panel',
          'requested_amount_minor': 10000,
          'currency': 'CNY',
          'state': 'assessment_unavailable',
          'human_review_required': true,
          'no_automatic_action': true,
        },
      ],
      'critic': <String, dynamic>{'state': 'unavailable'},
      'explanation': <String, dynamic>{'display_mode': 'structured_fallback'},
    });
    await _pump(
      tester,
      role: AppRole.payer,
      repository: FakeDrAiRepository(
        restoredSession: payerSession,
        intelligenceArtifact: frozen,
      ),
    );

    expect(find.text('AI provider unavailable'), findsWidgets);
    expect(find.text('Structured fallback is active'), findsOneWidget);
    expect(
      find.byKey(
        const Key('intelligence-unavailable-requested-line-unavailable'),
      ),
      findsOneWidget,
    );
    expect(find.text('AI support score'), findsNothing);
    expect(find.text('Tier 0'), findsNothing);
  });

  testWidgets(
    'doctor can generate an empty artifact without blocking records',
    (tester) async {
      _viewport(tester, const Size(1280, 900));
      final repository = FakeDrAiRepository(
        restoredSession: doctorSession,
        noIntelligenceArtifact: true,
      );
      await _pump(tester, role: AppRole.doctor, repository: repository);

      expect(
        find.text('No validated intelligence artifact yet'),
        findsOneWidget,
      );
      expect(find.byKey(const Key('cei-generate')), findsOneWidget);
      expect(find.textContaining('pending-cost'), findsOneWidget);
    },
  );

  for (final emptyCase in <(AppRole, AuthSession, Locale, Size, String)>[
    (
      AppRole.patient,
      patientSession,
      const Locale('zh'),
      const Size(412, 917),
      '在负责的诊疗团队审核下一步期间，您的申请和诊疗记录仍可使用。',
    ),
    (
      AppRole.payer,
      payerSession,
      const Locale('en'),
      const Size(1280, 900),
      'Continue human review or request clarification. No AI artifact is required for a permitted decision.',
    ),
  ]) {
    testWidgets(
      '${emptyCase.$1.wireValue} empty state stays role-specific and read-only',
      (tester) async {
        _viewport(tester, emptyCase.$4);
        await _pump(
          tester,
          role: emptyCase.$1,
          locale: emptyCase.$3,
          repository: FakeDrAiRepository(
            restoredSession: emptyCase.$2,
            noIntelligenceArtifact: true,
          ),
        );

        expect(find.text(emptyCase.$5), findsOneWidget);
        expect(find.byKey(const Key('cei-generate')), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets(
    'doctor mobile Chinese provider-unavailable artifact remains human-usable',
    (tester) async {
      _viewport(tester, const Size(412, 917));
      final unavailable = ClinicalEventIntelligenceData.fromJson(
        <String, dynamic>{
          'artifact_id': 'provider-unavailable-artifact',
          'artifact_version': 1,
          'lifecycle_state': 'provider_unavailable',
          'location': <String, dynamic>{'source': 'missing_structured_records'},
          'requested_item_assessments': <Object>[
            <String, dynamic>{
              'requested_line_id': 'provider-unavailable-line',
              'label': 'Requested panel',
              'requested_quantity': 1,
              'requested_unit': 'panel',
              'requested_amount_minor': 10000,
              'currency': 'CNY',
              'state': 'assessment_unavailable',
            },
          ],
          'critic': <String, dynamic>{'state': 'unavailable'},
          'explanation': <String, dynamic>{
            'display_mode': 'structured_fallback',
          },
        },
      );
      await _pump(
        tester,
        role: AppRole.doctor,
        locale: const Locale('zh'),
        repository: FakeDrAiRepository(
          restoredSession: doctorSession,
          intelligenceArtifact: unavailable,
        ),
      );

      expect(find.text('AI 提供方不可用'), findsWidgets);
      expect(find.textContaining('待补费用'), findsWidgets);
      expect(find.text('AI 支持分数'), findsNothing);
      expect(find.text('溯源层级 0'), findsNothing);
      expect(find.text('确认阅读'), findsOneWidget);
      expect(find.text('同意'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
