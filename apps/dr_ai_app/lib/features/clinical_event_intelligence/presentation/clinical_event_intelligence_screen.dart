import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/application/clinical_event_intelligence_providers.dart';
import 'package:dr_ai_app/features/clinical_event_intelligence/domain/clinical_event_intelligence_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

class ClinicalEventIntelligenceScreen extends ConsumerStatefulWidget {
  const ClinicalEventIntelligenceScreen({
    required this.role,
    required this.requestId,
    super.key,
  });

  final AppRole role;
  final String requestId;

  @override
  ConsumerState<ClinicalEventIntelligenceScreen> createState() =>
      _ClinicalEventIntelligenceScreenState();
}

class _ClinicalEventIntelligenceScreenState
    extends ConsumerState<ClinicalEventIntelligenceScreen> {
  bool _working = false;
  String? _message;
  bool _messageIsError = false;

  ClinicalEventIntelligenceScope get _scope => (
    role: widget.role,
    requestId: widget.requestId,
    locale: Localizations.localeOf(context).languageCode == 'zh'
        ? 'zh-Hans'
        : 'en',
  );

  Future<void> _generate() async {
    final idempotencyKey =
        'cei-generate-${widget.requestId}-'
        '${DateTime.now().microsecondsSinceEpoch}';
    setState(() {
      _working = true;
      _message = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .generateClinicalEventIntelligence(
            requestId: widget.requestId,
            idempotencyKey: idempotencyKey,
          );
      ref.invalidate(clinicalEventIntelligenceProvider(_scope));
      if (mounted) setState(() => _working = false);
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _working = false;
        _messageIsError = true;
        _message =
            error is ApiError &&
                (error.code == 'ai_purpose_unavailable' ||
                    error.code == 'provider_unavailable' ||
                    error.code == 'service_unavailable' ||
                    error.code == 'timeout')
            ? '${context.l10n.ceiProviderUnavailableTitle}. '
                  '${context.l10n.ceiUnavailableBody}'
            : context.l10n.ceiUnavailableBody;
      });
    }
  }

  Future<void> _respond(
    ClinicalEventIntelligenceData artifact,
    String action,
  ) async {
    String? rationale;
    if (action == 'disagree' || action == 'exception') {
      rationale = await showDialog<String>(
        context: context,
        builder: (context) => const _RationaleDialog(),
      );
      if (rationale == null) return;
    }
    setState(() {
      _working = true;
      _message = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .appendIntelligenceClinicianResponse(
            requestId: widget.requestId,
            artifactId: artifact.artifactId,
            action: action,
            rationale: rationale,
            idempotencyKey:
                'cei-response-${artifact.artifactId}-$action-${artifact.artifactVersion}',
          );
      ref.invalidate(clinicalEventIntelligenceProvider(_scope));
      if (!mounted) return;
      setState(() {
        _working = false;
        _messageIsError = false;
        _message = context.l10n.ceiResponseRecorded;
      });
    } on Object {
      if (!mounted) return;
      setState(() {
        _working = false;
        _messageIsError = true;
        _message = context.l10n.ceiResponseFailed;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final artifact = ref.watch(clinicalEventIntelligenceProvider(_scope));
    return ResponsiveAppShell(
      role: widget.role,
      selectedIndex: switch (widget.role) {
        AppRole.doctor => 3,
        AppRole.patient => 2,
        AppRole.payer => 1,
        AppRole.unsupported => 0,
      },
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: artifact.when(
          loading: () => DashboardLoadingView(label: context.l10n.ceiLoading),
          error: (error, stackTrace) {
            if (widget.role == AppRole.doctor &&
                error is ApiError &&
                error.code == 'not_found') {
              return _EmptyArtifact(
                role: widget.role,
                working: _working,
                message: _message,
                onGenerate: _generate,
                onRetry: () =>
                    ref.invalidate(clinicalEventIntelligenceProvider(_scope)),
              );
            }
            return _LoadFailure(
              providerUnavailable:
                  error is ApiError &&
                  (error.code == 'provider_unavailable' ||
                      error.code == 'service_unavailable' ||
                      error.code == 'ai_purpose_unavailable' ||
                      error.code == 'timeout'),
              onRetry: () =>
                  ref.invalidate(clinicalEventIntelligenceProvider(_scope)),
            );
          },
          data: (data) => data == null
              ? _EmptyArtifact(
                  role: widget.role,
                  working: _working,
                  message: _message,
                  onGenerate: _generate,
                  onRetry: () =>
                      ref.invalidate(clinicalEventIntelligenceProvider(_scope)),
                )
              : _ArtifactView(
                  role: widget.role,
                  artifact: data,
                  working: _working,
                  message: _message,
                  messageIsError: _messageIsError,
                  onRefresh: () =>
                      ref.invalidate(clinicalEventIntelligenceProvider(_scope)),
                  onRespond: (action) => _respond(data, action),
                ),
        ),
      ),
    );
  }
}

class _ArtifactView extends StatelessWidget {
  const _ArtifactView({
    required this.role,
    required this.artifact,
    required this.working,
    required this.message,
    required this.messageIsError,
    required this.onRefresh,
    required this.onRespond,
  });

  final AppRole role;
  final ClinicalEventIntelligenceData artifact;
  final bool working;
  final String? message;
  final bool messageIsError;
  final VoidCallback onRefresh;
  final ValueChanged<String> onRespond;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('clinical-event-intelligence-list'),
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 56),
      children: <Widget>[
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1180),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                _ArtifactHeader(
                  role: role,
                  artifact: artifact,
                  onRefresh: onRefresh,
                ),
                if (artifact.isProviderUnavailable) ...<Widget>[
                  const SizedBox(height: 16),
                  _Notice(
                    icon: Icons.cloud_off_outlined,
                    title: context.l10n.ceiProviderUnavailableTitle,
                    body: context.l10n.ceiProviderUnavailableBody,
                  ),
                ],
                if (artifact.isFallback ||
                    artifact.explanationDisplayMode ==
                        'structured_fallback') ...<Widget>[
                  const SizedBox(height: 16),
                  _Notice(
                    icon: Icons.article_outlined,
                    title: context.l10n.ceiFallbackTitle,
                    body: context.l10n.ceiFallbackBody,
                  ),
                ],
                const SizedBox(height: 16),
                _Notice(
                  key: const Key('cei-human-only-notice'),
                  icon: Icons.person_outline,
                  title: context.l10n.ceiHumanReview,
                  body: context.l10n.ceiHumanOnlyNotice,
                ),
                if (message != null) ...<Widget>[
                  const SizedBox(height: 12),
                  _Notice(
                    icon: messageIsError
                        ? Icons.error_outline
                        : Icons.check_circle_outline,
                    title: message!,
                    isError: messageIsError,
                  ),
                ],
                if (role == AppRole.doctor) ...<Widget>[
                  const SizedBox(height: 14),
                  _DoctorActions(working: working, onSelected: onRespond),
                ],
                const SizedBox(height: 28),
                _SectionTitle(
                  title: context.l10n.ceiRequestedItems,
                  description: context.l10n.ceiRequestedItemsDescription,
                ),
                const SizedBox(height: 12),
                if (artifact.requestedItems.isEmpty)
                  _Notice(
                    icon: Icons.info_outline,
                    title: context.l10n.ceiEmptyTitle,
                    body: context.l10n.ceiUnavailableBody,
                  )
                else
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final twoColumns = constraints.maxWidth >= 960;
                      final width = twoColumns
                          ? (constraints.maxWidth - 16) / 2
                          : constraints.maxWidth;
                      return Wrap(
                        spacing: 16,
                        runSpacing: 16,
                        children: artifact.requestedItems
                            .map(
                              (item) => SizedBox(
                                width: width,
                                child: _RequestedItemCard(
                                  item: item,
                                  role: role,
                                ),
                              ),
                            )
                            .toList(growable: false),
                      );
                    },
                  ),
                const SizedBox(height: 30),
                _PathwaysSection(pathways: artifact.pathways),
                const SizedBox(height: 30),
                _MissingDocumentationSection(
                  items: artifact.missingDocumentation,
                ),
                const SizedBox(height: 30),
                _CounterfactualSection(items: artifact.counterfactuals),
                const SizedBox(height: 30),
                _CriticSection(critic: artifact.critic),
                const SizedBox(height: 30),
                _LineageSection(items: artifact.lineage),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ArtifactHeader extends StatelessWidget {
  const _ArtifactHeader({
    required this.role,
    required this.artifact,
    required this.onRefresh,
  });

  final AppRole role;
  final ClinicalEventIntelligenceData artifact;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final title = switch (role) {
      AppRole.patient => context.l10n.ceiPatientTitle,
      AppRole.doctor => context.l10n.ceiDoctorTitle,
      AppRole.payer => context.l10n.ceiPayerTitle,
      AppRole.unsupported => context.l10n.ceiTitle,
    };
    final location = <String>[
      artifact.location.cityCode,
      artifact.location.provinceCode,
      artifact.location.facilityLevel,
      artifact.location.jurisdictionCode,
    ].where((value) => value.trim().isNotEmpty).join(' · ');
    return Container(
      key: const Key('cei-artifact-header'),
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: DrAiColors.sectionHeader,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      title,
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(
                            color: DrAiColors.white,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                    if (artifact.purposeSummary.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 6),
                      Text(
                        artifact.purposeSummary,
                        style: const TextStyle(
                          color: DrAiColors.white,
                          height: 1.45,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              IconButton(
                tooltip: context.l10n.ceiRefresh,
                onPressed: onRefresh,
                color: DrAiColors.white,
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              _Chip(
                icon: Icons.lock_outline,
                label:
                    '${context.l10n.ceiArtifact} v${artifact.artifactVersion} · '
                    '${_shortRef(artifact.artifactId)}',
              ),
              _Chip(
                icon: Icons.camera_alt_outlined,
                label:
                    '${context.l10n.ceiSnapshot} v${artifact.clinicalEventSnapshotVersion}',
              ),
              _Chip(
                icon: Icons.timeline_outlined,
                label: _stateLabel(context, artifact.lifecycleState),
              ),
              _Chip(
                icon: Icons.person_outline,
                label:
                    '${context.l10n.ceiHumanReview}: ${_stateLabel(context, artifact.humanReviewState)}',
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            '${context.l10n.ceiLocation}: '
            '${location.isEmpty ? _humanize('unavailable') : location}',
            style: const TextStyle(
              color: DrAiColors.white,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            context.l10n.ceiLocationSource,
            style: const TextStyle(color: DrAiColors.white),
          ),
        ],
      ),
    );
  }
}

class _RequestedItemCard extends StatelessWidget {
  const _RequestedItemCard({required this.item, required this.role});

  final RequestedItemAssessmentData item;
  final AppRole role;

  @override
  Widget build(BuildContext context) {
    final unavailable = item.isAssessmentUnavailable;
    final tier5 =
        !unavailable &&
        (item.estimatedCost.isModelOnlyExploratory ||
            item.estimatedCost.provenanceTier == 5);
    return Container(
      key: Key('intelligence-item-${item.requestedLineId}'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: tier5
            ? const Color(0xFFFFF1D6)
            : DrAiColors.m3SurfaceContainerHigh,
        border: Border.all(
          color: tier5 ? const Color(0xFFC38414) : DrAiColors.outline,
        ),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(
                child: Text(
                  item.label.isEmpty ? _humanize('requested item') : item.label,
                  style: const TextStyle(
                    color: DrAiColors.brandDark,
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              if (!unavailable)
                _Chip(
                  icon: Icons.layers_outlined,
                  label:
                      '${context.l10n.ceiTier} ${item.estimatedCost.provenanceTier}',
                ),
            ],
          ),
          const SizedBox(height: 12),
          if (role != AppRole.patient &&
              (item.codeSystem != null ||
                  item.serviceCode != null)) ...<Widget>[
            Text(
              <String>[
                if (item.codeSystem != null) item.codeSystem!,
                if (item.serviceCode != null) item.serviceCode!,
              ].join(' · '),
              style: const TextStyle(color: DrAiColors.inkSecondary),
            ),
            const SizedBox(height: 8),
          ],
          Wrap(
            spacing: 20,
            runSpacing: 8,
            children: <Widget>[
              _ValuePair(
                label: context.l10n.ceiRequested,
                value:
                    '${_quantity(item.requestedQuantity)} ${item.requestedUnit} · '
                    '${_money(item.currency, item.requestedAmountMinor)}',
              ),
              if (!unavailable)
                _ValuePair(
                  label: context.l10n.ceiEstimated,
                  value:
                      '${_quantity(item.estimatedQuantity.low)}–'
                      '${_quantity(item.estimatedQuantity.high)} '
                      '${item.estimatedQuantity.unit} · '
                      '${_money(item.estimatedCost.currency, item.estimatedCost.lowMinor)}–'
                      '${_money(item.estimatedCost.currency, item.estimatedCost.highMinor)}',
                ),
            ],
          ),
          if (unavailable) ...<Widget>[
            const SizedBox(height: 12),
            _Notice(
              key: Key('intelligence-unavailable-${item.requestedLineId}'),
              icon: Icons.cloud_off_outlined,
              title: context.l10n.ceiProviderUnavailableTitle,
              body: context.l10n.ceiHumanOnlyNotice,
            ),
          ],
          if (tier5) ...<Widget>[
            const SizedBox(height: 12),
            _Notice(
              key: Key('intelligence-tier5-${item.requestedLineId}'),
              icon: Icons.science_outlined,
              title: context.l10n.ceiTier5Title,
              body: context.l10n.ceiTier5Body,
            ),
          ],
          if (!unavailable) ...<Widget>[
            const SizedBox(height: 14),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: <Widget>[
                _Chip(
                  icon: Icons.verified_outlined,
                  label: _stateLabel(context, item.validationState),
                ),
                _Chip(
                  icon: Icons.compare_arrows,
                  label: _criticLabel(context, item.disagreementState),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _SupportScore(scores: item.scores),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth >= 540
                    ? (constraints.maxWidth - 8) / 2
                    : constraints.maxWidth;
                final scores = <(String, int)>[
                  (context.l10n.ceiClinicalFit, item.scores.clinicalFit),
                  (
                    context.l10n.ceiEvidenceSupport,
                    item.scores.evidenceSupport,
                  ),
                  (context.l10n.ceiTimingSequence, item.scores.timingSequence),
                  (
                    context.l10n.ceiQuantityIntensity,
                    item.scores.quantityIntensity,
                  ),
                  (
                    context.l10n.ceiDocumentationCompleteness,
                    item.scores.documentationCompleteness,
                  ),
                  (context.l10n.ceiCostAlignment, item.scores.costAlignment),
                ];
                return Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: scores
                      .map(
                        (score) => SizedBox(
                          width: width,
                          child: _ScoreRow(label: score.$1, score: score.$2),
                        ),
                      )
                      .toList(growable: false),
                );
              },
            ),
          ],
          const SizedBox(height: 14),
          _ValuePair(label: context.l10n.ceiUsefulness, value: item.usefulness),
          const SizedBox(height: 8),
          _ValuePair(
            label: context.l10n.ceiConfidence,
            value: context.l10n.stableValue(item.confidence),
          ),
          if (item.mappedPathwayIds.isNotEmpty) ...<Widget>[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: item.mappedPathwayIds
                  .map(
                    (id) => _Chip(icon: Icons.alt_route, label: _humanize(id)),
                  )
                  .toList(growable: false),
            ),
          ],
          if (role != AppRole.patient) ...<Widget>[
            _FactGroup(
              title: context.l10n.ceiSupportingFacts,
              items: item.supportingFacts,
            ),
            _FactGroup(
              title: context.l10n.ceiContradictingFacts,
              items: item.contradictingFacts,
            ),
          ],
          _FactGroup(
            title: context.l10n.ceiMissingInformation,
            items: item.missingInformation,
          ),
          _FactGroup(
            title: context.l10n.ceiAlternatives,
            items: item.alternatives,
          ),
          const SizedBox(height: 10),
          Text(
            tier5
                ? context.l10n.ceiNoAdmittedPriceSource
                : '${context.l10n.ceiSources}: '
                      '${item.estimatedCost.sourceLabels.isEmpty ? _humanize('source withheld') : item.estimatedCost.sourceLabels.join(' · ')}',
            style: const TextStyle(
              color: DrAiColors.inkSecondary,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _SupportScore extends StatelessWidget {
  const _SupportScore({required this.scores});

  final IntelligenceScoresData scores;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('cei-ai-support-score'),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DrAiColors.brandSoft,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  context.l10n.ceiAiSupportScore,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                Text(
                  '${_scoreBand(context, scores.aiSupportScore, scores.band)} · '
                  '${context.l10n.ceiScoreVersion} ${scores.scoreContractVersion}',
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${scores.aiSupportScore}/100',
            style: const TextStyle(
              color: DrAiColors.brandDark,
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

class _ScoreRow extends StatelessWidget {
  const _ScoreRow({required this.label, required this.score});

  final String label;
  final int score;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label $score out of 100',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: DrAiColors.outline),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: <Widget>[
            Expanded(child: Text(label)),
            Text(
              '$score/100',
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ],
        ),
      ),
    );
  }
}

class _PathwaysSection extends StatelessWidget {
  const _PathwaysSection({required this.pathways});

  final List<IntelligencePathwayData> pathways;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionTitle(
          title: context.l10n.ceiPredictedPathways,
          description: context.l10n.ceiPredictedBoundary,
        ),
        const SizedBox(height: 12),
        if (pathways.isEmpty)
          Text(context.l10n.ceiMissingInformation)
        else
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: pathways
                .map(
                  (pathway) => ConstrainedBox(
                    constraints: const BoxConstraints(
                      minWidth: 240,
                      maxWidth: 360,
                    ),
                    child: _SimpleCard(
                      title: _pathwayLabel(context, pathway.type),
                      body: pathway.summary,
                      bullets: pathway.items
                          .map((item) {
                            final quantity = item.quantityHigh > 0
                                ? '${_quantity(item.quantityLow)}–${_quantity(item.quantityHigh)} ${item.unit}'
                                : '';
                            return <String>[
                              item.label.isEmpty
                                  ? _humanize(item.category)
                                  : item.label,
                              if (quantity.isNotEmpty) quantity,
                            ].join(' · ');
                          })
                          .toList(growable: false),
                    ),
                  ),
                )
                .toList(growable: false),
          ),
      ],
    );
  }
}

class _MissingDocumentationSection extends StatelessWidget {
  const _MissingDocumentationSection({required this.items});
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionTitle(title: context.l10n.ceiMissingDocumentation),
        const SizedBox(height: 12),
        _SimpleCard(
          key: const Key('cei-missing-documentation'),
          title: items.isEmpty
              ? context.l10n.ceiMissingDocumentationEmpty
              : context.l10n.ceiMissingInformation,
          bullets: items,
          icon: Icons.assignment_late_outlined,
        ),
      ],
    );
  }
}

class _CounterfactualSection extends StatelessWidget {
  const _CounterfactualSection({required this.items});
  final List<CounterfactualData> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionTitle(
          title: context.l10n.ceiCounterfactuals,
          description: context.l10n.ceiCounterfactualBoundary,
        ),
        const SizedBox(height: 12),
        ...items.map(
          (item) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _SimpleCard(title: item.title, body: item.summary),
          ),
        ),
      ],
    );
  }
}

class _CriticSection extends StatelessWidget {
  const _CriticSection({required this.critic});
  final IntelligenceCriticData critic;

  @override
  Widget build(BuildContext context) {
    final label = switch (critic.state) {
      'agreement' => context.l10n.ceiAgreement,
      'partial_disagreement' => context.l10n.ceiPartialDisagreement,
      'material_disagreement' => context.l10n.ceiMaterialDisagreement,
      _ => context.l10n.ceiCriticUnavailable,
    };
    final body = critic.summary.isNotEmpty
        ? critic.summary
        : critic.state == 'unavailable'
        ? context.l10n.ceiCriticUnavailableBody
        : context.l10n.ceiHumanOnlyNotice;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionTitle(title: context.l10n.ceiCritic),
        const SizedBox(height: 12),
        _Notice(
          key: Key('cei-critic-${critic.state}'),
          icon: critic.state == 'agreement'
              ? Icons.check_circle_outline
              : Icons.compare_arrows,
          title: label,
          body: body,
        ),
      ],
    );
  }
}

class _LineageSection extends StatelessWidget {
  const _LineageSection({required this.items});
  final List<IntelligenceLineageData> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _SectionTitle(title: context.l10n.ceiLineage),
        const SizedBox(height: 12),
        if (items.isEmpty)
          Text(context.l10n.ceiEmptyTitle)
        else
          ...items.map(
            (item) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.history, color: DrAiColors.brand),
              title: Text(
                item.label.isEmpty ? _humanize(item.eventType) : item.label,
              ),
              subtitle: item.occurredAt.isEmpty ? null : Text(item.occurredAt),
            ),
          ),
      ],
    );
  }
}

class _DoctorActions extends StatelessWidget {
  const _DoctorActions({required this.working, required this.onSelected});

  final bool working;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        FilledButton.tonal(
          onPressed: working ? null : () => onSelected('acknowledge'),
          child: Text(context.l10n.ceiAcknowledge),
        ),
        FilledButton.tonal(
          onPressed: working ? null : () => onSelected('concur'),
          child: Text(context.l10n.ceiConcur),
        ),
        OutlinedButton(
          onPressed: working ? null : () => onSelected('disagree'),
          child: Text(context.l10n.ceiDisagree),
        ),
        OutlinedButton(
          onPressed: working ? null : () => onSelected('exception'),
          child: Text(context.l10n.ceiException),
        ),
      ],
    );
  }
}

class _EmptyArtifact extends StatelessWidget {
  const _EmptyArtifact({
    required this.role,
    required this.working,
    required this.message,
    required this.onGenerate,
    required this.onRetry,
  });

  final AppRole role;
  final bool working;
  final String? message;
  final VoidCallback onGenerate;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final body = switch (role) {
      AppRole.patient => context.l10n.ceiEmptyPatientBody,
      AppRole.doctor => context.l10n.ceiEmptyDoctorBody,
      AppRole.payer => context.l10n.ceiEmptyPayerBody,
      AppRole.unsupported => context.l10n.ceiUnavailableBody,
    };
    return _CenteredState(
      icon: Icons.fact_check_outlined,
      title: context.l10n.ceiEmptyTitle,
      body: body,
      message: message,
      actions: <Widget>[
        if (role == AppRole.doctor)
          FilledButton.icon(
            key: const Key('cei-generate'),
            onPressed: working ? null : onGenerate,
            icon: const Icon(Icons.auto_awesome_outlined),
            label: Text(
              working ? context.l10n.ceiGenerating : context.l10n.ceiGenerate,
            ),
          ),
        OutlinedButton.icon(
          onPressed: working ? null : onRetry,
          icon: const Icon(Icons.refresh),
          label: Text(context.l10n.ceiRefresh),
        ),
      ],
    );
  }
}

class _LoadFailure extends StatelessWidget {
  const _LoadFailure({
    required this.providerUnavailable,
    required this.onRetry,
  });
  final bool providerUnavailable;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _CenteredState(
      icon: providerUnavailable ? Icons.cloud_off_outlined : Icons.lock_outline,
      title: providerUnavailable
          ? context.l10n.ceiProviderUnavailableTitle
          : context.l10n.ceiUnavailableTitle,
      body: context.l10n.ceiUnavailableBody,
      actions: <Widget>[
        OutlinedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
          label: Text(context.l10n.ceiRefresh),
        ),
      ],
    );
  }
}

class _CenteredState extends StatelessWidget {
  const _CenteredState({
    required this.icon,
    required this.title,
    required this.body,
    required this.actions,
    this.message,
  });

  final IconData icon;
  final String title;
  final String body;
  final List<Widget> actions;
  final String? message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: Column(
            children: <Widget>[
              Icon(icon, size: 52, color: DrAiColors.brand),
              const SizedBox(height: 16),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                body,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: DrAiColors.inkSecondary,
                  height: 1.5,
                ),
              ),
              if (message != null) ...<Widget>[
                const SizedBox(height: 12),
                Text(message!, textAlign: TextAlign.center),
              ],
              const SizedBox(height: 18),
              Wrap(spacing: 8, runSpacing: 8, children: actions),
            ],
          ),
        ),
      ),
    );
  }
}

class _RationaleDialog extends StatefulWidget {
  const _RationaleDialog();

  @override
  State<_RationaleDialog> createState() => _RationaleDialogState();
}

class _RationaleDialogState extends State<_RationaleDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(context.l10n.ceiRationale),
      content: TextField(
        key: const Key('cei-rationale'),
        controller: _controller,
        minLines: 3,
        maxLines: 6,
        decoration: InputDecoration(labelText: context.l10n.ceiRationale),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(context.l10n.ceiCancel),
        ),
        FilledButton(
          onPressed: () {
            final value = _controller.text.trim();
            if (value.length < 4) return;
            Navigator.pop(context, value);
          },
          child: Text(context.l10n.ceiAppendResponse),
        ),
      ],
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, this.description});
  final String title;
  final String? description;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(DrAiRadii.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          ColoredBox(
            color: DrAiColors.sectionHeader,
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: DrAiSpacing.md,
                vertical: DrAiSpacing.sm,
              ),
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: DrAiColors.white,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ),
          if (description != null)
            ColoredBox(
              color: DrAiColors.patientAccent,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: DrAiSpacing.md,
                  vertical: DrAiSpacing.sm,
                ),
                child: Text(
                  description!,
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _SimpleCard extends StatelessWidget {
  const _SimpleCard({
    required this.title,
    this.body = '',
    this.bullets = const <String>[],
    this.icon = Icons.alt_route,
    super.key,
  });

  final String title;
  final String body;
  final List<String> bullets;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(icon, color: DrAiColors.brand),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          if (body.isNotEmpty) ...<Widget>[
            const SizedBox(height: 8),
            Text(body, style: const TextStyle(height: 1.45)),
          ],
          ...bullets.map(
            (item) => Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('• $item', style: const TextStyle(height: 1.4)),
            ),
          ),
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({
    required this.icon,
    required this.title,
    this.body,
    this.isError = false,
    super.key,
  });

  final IconData icon;
  final String title;
  final String? body;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isError ? const Color(0xFFFFF2F2) : const Color(0xFFF2F8F5),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(
              icon,
              color: isError ? const Color(0xFF8B1E1E) : DrAiColors.brand,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w900),
                  ),
                  if (body != null) ...<Widget>[
                    const SizedBox(height: 3),
                    Text(body!, style: const TextStyle(height: 1.4)),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: DrAiColors.pageBackground,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 15, color: DrAiColors.brand),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              label,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _ValuePair extends StatelessWidget {
  const _ValuePair({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 180, maxWidth: 420),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label,
            style: const TextStyle(
              color: DrAiColors.inkSecondary,
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
          Text(
            value.isEmpty ? _humanize('not recorded') : value,
            style: const TextStyle(fontWeight: FontWeight.w800, height: 1.35),
          ),
        ],
      ),
    );
  }
}

class _FactGroup extends StatelessWidget {
  const _FactGroup({required this.title, required this.items});
  final String title;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          ...items.map((item) => Text('• $item')),
        ],
      ),
    );
  }
}

String _pathwayLabel(BuildContext context, String value) => switch (value) {
  'typical_first_line' => context.l10n.ceiTypicalPathway,
  'reasonable_alternative' => context.l10n.ceiAlternativePathway,
  'escalated' => context.l10n.ceiEscalatedPathway,
  _ => _humanize(value),
};

String _money(String currency, int minor) => NumberFormat.currency(
  locale: 'zh_CN',
  symbol: currency == 'CNY' ? '¥' : '$currency ',
  decimalDigits: 2,
).format(minor / 100);

String _quantity(num value) =>
    value % 1 == 0 ? value.toInt().toString() : value.toStringAsFixed(1);

String _humanize(String value) {
  if (value.trim().isEmpty) return '';
  final words = value.replaceAll('_', ' ');
  return '${words[0].toUpperCase()}${words.substring(1)}';
}

String _shortRef(String value) =>
    value.length <= 8 ? value : value.substring(0, 8);

String _scoreBand(BuildContext context, int score, String band) {
  return switch (band) {
    'strongly_supported' => context.l10n.ceiStronglySupported,
    'plausible' => context.l10n.ceiPlausible,
    'materially_uncertain' => context.l10n.ceiMateriallyUncertain,
    'weakly_supported_human_review' => context.l10n.ceiWeaklySupported,
    _ when score >= 80 => context.l10n.ceiStronglySupported,
    _ when score >= 60 => context.l10n.ceiPlausible,
    _ when score >= 40 => context.l10n.ceiMateriallyUncertain,
    _ => context.l10n.ceiWeaklySupported,
  };
}

String _criticLabel(BuildContext context, String state) => switch (state) {
  'agreement' => context.l10n.ceiAgreement,
  'partial_disagreement' => context.l10n.ceiPartialDisagreement,
  'material_disagreement' => context.l10n.ceiMaterialDisagreement,
  _ => context.l10n.ceiCriticUnavailable,
};

String _stateLabel(BuildContext context, String state) => switch (state) {
  'validated' => context.l10n.ceiValidated,
  'validated_with_uncertainty' => context.l10n.ceiValidatedWithUncertainty,
  'validated_with_results' => context.l10n.ceiValidatedWithResults,
  'awaiting_human_review' => context.l10n.ceiAwaitingHumanReview,
  'human_review_required' || 'required' => context.l10n.ceiHumanReviewRequired,
  'provider_unavailable' => context.l10n.ceiProviderUnavailableTitle,
  'fallback' => context.l10n.ceiFallbackTitle,
  _ => _humanize(state),
};
