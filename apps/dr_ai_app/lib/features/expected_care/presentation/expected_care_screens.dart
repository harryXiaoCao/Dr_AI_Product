import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/expected_care/application/expected_care_providers.dart';
import 'package:dr_ai_app/features/expected_care/domain/expected_care_data.dart';
import 'package:dr_ai_app/shared/presentation/product_history_copy.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

String _copy(BuildContext context, String en, String zh) =>
    Localizations.localeOf(context).languageCode == 'zh' ? zh : en;

String _money(String currency, int minor) => NumberFormat.currency(
  locale: 'zh_CN',
  symbol: currency == 'CNY' ? '¥' : '$currency ',
  decimalDigits: 2,
).format(minor / 100);

String _referenceLabel(BuildContext context, String value) {
  return switch (value) {
    'scenario_definition' => _copy(context, 'Scenario definition', '适用场景定义'),
    'care_plan' => _copy(context, 'Care pathway', '诊疗路径'),
    'pricing_reference' => _copy(context, 'Pricing reference', '价格参考'),
    'utilization_rule' => _copy(context, 'Utilization rule', '服务使用规则'),
    _ => humanizeProductValue(value),
  };
}

String _evidenceStateLabel(BuildContext context, String value) {
  return switch (value) {
    'validated_baseline_published' => _copy(
      context,
      'Validated baseline published',
      '已发布经验证基线',
    ),
    'validated' => _copy(context, 'Deterministically validated', '已通过确定性验证'),
    'doctor_acknowledged' => _copy(
      context,
      'Clinician acknowledged',
      '临床医生已确认',
    ),
    'doctor_concurred' => _copy(context, 'Clinician agreed', '临床医生同意'),
    'doctor_disagreed' => _copy(context, 'Clinician disagreed', '临床医生不同意'),
    'doctor_exception_recorded' => _copy(
      context,
      'Clinical exception recorded',
      '已记录临床例外',
    ),
    'concur' => _copy(context, 'Clinician agreed', '临床医生同意'),
    'disagree' => _copy(context, 'Clinician disagreed', '临床医生不同意'),
    'exception' => _copy(context, 'Clinical exception recorded', '已记录临床例外'),
    'submitted' => _copy(context, 'Submitted', '已提交'),
    'under_review' => _copy(context, 'Under human review', '人工审核中'),
    'clarification_requested' => _copy(
      context,
      'Clarification requested',
      '需要补充说明',
    ),
    'accepted' => _copy(context, 'Accepted by human reviewer', '人工审核员已接受'),
    'rejected' => _copy(context, 'Rejected by human reviewer', '人工审核员已拒绝'),
    'not_recorded' => _copy(context, 'Not recorded', '尚未记录'),
    _ => humanizeProductValue(value),
  };
}

String _careCategoryLabel(BuildContext context, String value) {
  return switch (value) {
    'therapy' => _copy(context, 'Therapy', '治疗'),
    'consultation' => _copy(context, 'Consultation', '问诊'),
    'imaging' => _copy(context, 'Imaging', '影像检查'),
    'laboratory' => _copy(context, 'Laboratory testing', '实验室检查'),
    'medication' => _copy(context, 'Medication', '用药'),
    'rehabilitation' => _copy(context, 'Rehabilitation', '康复'),
    'treatment' => _copy(context, 'Treatment', '治疗服务'),
    _ => humanizeProductValue(value),
  };
}

String _careUnitLabel(BuildContext context, String value, int high) {
  return switch (value) {
    'session' ||
    'sessions' => _copy(context, high == 1 ? 'session' : 'sessions', '次'),
    'visit' ||
    'visits' => _copy(context, high == 1 ? 'visit' : 'visits', '次就诊'),
    'item' || 'items' => _copy(context, high == 1 ? 'item' : 'items', '项'),
    'day' || 'days' => _copy(context, high == 1 ? 'day' : 'days', '天'),
    _ => humanizeProductValue(value),
  };
}

String _clinicianPositionLabel(BuildContext context, String value) {
  return switch (value) {
    'acknowledge' => _copy(context, 'Acknowledged', '已确认阅读'),
    'concur' => _copy(context, 'Clinically concurred', '临床同意'),
    'disagree' => _copy(context, 'Disagreement recorded', '已记录不同意见'),
    'exception' => _copy(context, 'Clinical exception recorded', '已记录临床例外'),
    'not_recorded' => _copy(context, 'Not recorded', '尚未记录'),
    _ => humanizeProductValue(value),
  };
}

class DoctorExpectedCareReviewScreen extends ConsumerStatefulWidget {
  const DoctorExpectedCareReviewScreen({
    required this.patientId,
    required this.eventId,
    super.key,
  });

  final String patientId;
  final String eventId;

  @override
  ConsumerState<DoctorExpectedCareReviewScreen> createState() =>
      _DoctorExpectedCareReviewScreenState();
}

class _DoctorExpectedCareReviewScreenState
    extends ConsumerState<DoctorExpectedCareReviewScreen> {
  String? _selectedId;
  bool _submitting = false;
  String? _message;
  bool _messageIsError = false;

  ExpectedCareScope get _scope =>
      (patientId: widget.patientId, eventId: widget.eventId);

  Future<void> _submit(
    ExpectedCareCandidateData candidate,
    String position, {
    String? exceptionCode,
    String? rationale,
    String? patientSafeSummary,
    String? reviewerOnlyNote,
  }) async {
    setState(() {
      _submitting = true;
      _message = null;
    });
    try {
      final result = await ref
          .read(repositoryProvider)
          .submitExpectedCareClinicianResponse(
            patientId: widget.patientId,
            eventId: widget.eventId,
            candidateId: candidate.id,
            expectedVersion: candidate.responseVersion,
            position: position,
            idempotencyKey:
                'clinician-response-${candidate.id}-${candidate.responseVersion}-$position',
            exceptionCode: exceptionCode,
            rationale: rationale,
            patientSafeSummary: patientSafeSummary,
            reviewerOnlyNote: reviewerOnlyNote,
          );
      ref.invalidate(doctorExpectedCareCandidatesProvider(_scope));
      if (mounted) {
        setState(() {
          _submitting = false;
          _messageIsError = false;
          _message = _copy(
            context,
            'Clinician position recorded as ${_evidenceStateLabel(context, result.state)}. The published baseline was not changed.',
            '临床立场已记录为${_evidenceStateLabel(context, result.state)}，已发布基线未被更改。',
          );
        });
      }
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _messageIsError = true;
          _message = switch (error.code) {
            'conflict' => _copy(
              context,
              'The response state or admitted references changed. Refresh before continuing.',
              '响应状态或准入参考已变化，请刷新后继续。',
            ),
            'deterministic_disagreement' => _copy(
              context,
              'The response refers to information outside the immutable baseline.',
              '该响应引用了不可变基线之外的信息。',
            ),
            _ => _copy(
              context,
              'The clinician response could not be recorded. Manual clinical documentation remains available.',
              '无法记录临床响应。您仍可继续手动临床记录。',
            ),
          };
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final candidates = ref.watch(doctorExpectedCareCandidatesProvider(_scope));
    final comparison = ref.watch(doctorExpectedCareComparisonProvider(_scope));
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 1,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: candidates.when(
          loading: () => DashboardLoadingView(
            label: _copy(
              context,
              'Loading expected-care candidates',
              '正在加载预期诊疗候选范围',
            ),
          ),
          error: (error, stackTrace) => _UnavailableState(
            title: _copy(
              context,
              'Candidate review is unavailable',
              '候选范围审核暂不可用',
            ),
            body: _copy(
              context,
              'Continue ordinary clinical documentation and pending-cost work. No AI response is required.',
              '请继续常规临床记录和待补费用流程，无需等待 AI。',
            ),
            onRetry: () =>
                ref.invalidate(doctorExpectedCareCandidatesProvider(_scope)),
          ),
          data: (items) {
            if (items.isEmpty) {
              return _UnavailableState(
                title: _copy(context, 'No reviewable candidate', '暂无可审核候选范围'),
                body: _copy(
                  context,
                  'Care documentation, cost entry, and payer clarification remain available without AI.',
                  '即使没有 AI，仍可继续诊疗记录、费用录入及支付方澄清。',
                ),
                onRetry: () => ref.invalidate(
                  doctorExpectedCareCandidatesProvider(_scope),
                ),
              );
            }
            final selected = items.firstWhere(
              (item) => item.id == _selectedId,
              orElse: () => items.first,
            );
            return _DoctorWorkspace(
              items: items,
              selected: selected,
              submitting: _submitting,
              message: _message,
              messageIsError: _messageIsError,
              onSelected: (id) => setState(() => _selectedId = id),
              onAcknowledge: () => _submit(selected, 'acknowledge'),
              onConcur: () => _submit(selected, 'concur'),
              onDisagree: () async {
                final draft = await showDialog<_ResponseDraft>(
                  context: context,
                  builder: (context) =>
                      const _ClinicianResponseDialog(position: 'disagree'),
                );
                if (draft != null) {
                  await _submit(
                    selected,
                    'disagree',
                    exceptionCode: draft.exceptionCode,
                    rationale: draft.rationale,
                    patientSafeSummary: draft.patientSafeSummary,
                    reviewerOnlyNote: draft.reviewerOnlyNote,
                  );
                }
              },
              onException: () async {
                final draft = await showDialog<_ResponseDraft>(
                  context: context,
                  builder: (context) =>
                      const _ClinicianResponseDialog(position: 'exception'),
                );
                if (draft != null) {
                  await _submit(
                    selected,
                    'exception',
                    exceptionCode: draft.exceptionCode,
                    rationale: draft.rationale,
                    patientSafeSummary: draft.patientSafeSummary,
                    reviewerOnlyNote: draft.reviewerOnlyNote,
                  );
                }
              },
              onRefresh: () =>
                  ref.invalidate(doctorExpectedCareCandidatesProvider(_scope)),
              comparison: comparison,
              patientId: widget.patientId,
              eventId: widget.eventId,
            );
          },
        ),
      ),
    );
  }
}

class _DoctorWorkspace extends StatelessWidget {
  const _DoctorWorkspace({
    required this.items,
    required this.selected,
    required this.submitting,
    required this.message,
    required this.messageIsError,
    required this.onSelected,
    required this.onAcknowledge,
    required this.onConcur,
    required this.onDisagree,
    required this.onException,
    required this.onRefresh,
    required this.comparison,
    required this.patientId,
    required this.eventId,
  });

  final List<ExpectedCareCandidateData> items;
  final ExpectedCareCandidateData selected;
  final bool submitting;
  final String? message;
  final bool messageIsError;
  final ValueChanged<String> onSelected;
  final VoidCallback onAcknowledge;
  final VoidCallback onConcur;
  final VoidCallback onDisagree;
  final VoidCallback onException;
  final VoidCallback onRefresh;
  final AsyncValue<ExpectedCareComparisonData> comparison;
  final String patientId;
  final String eventId;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 920;
        final rail = _CandidateRail(
          items: items,
          selectedId: selected.id,
          onSelected: onSelected,
        );
        final detail = _DoctorCandidateDetail(
          candidate: selected,
          submitting: submitting,
          message: message,
          messageIsError: messageIsError,
          onAcknowledge: onAcknowledge,
          onConcur: onConcur,
          onDisagree: onDisagree,
          onException: onException,
          onRefresh: onRefresh,
          comparison: comparison,
          patientId: patientId,
          eventId: eventId,
        );
        if (!desktop) {
          return Column(
            children: <Widget>[
              // The lifecycle label can wrap in Chinese or with long
              // server-controlled state names. Keep enough cross-axis room
              // for both lines and the immutable range without overflow.
              SizedBox(height: 128, child: rail),
              Expanded(child: detail),
            ],
          );
        }
        return Row(
          children: <Widget>[
            SizedBox(width: 300, child: rail),
            const VerticalDivider(width: 1, color: DrAiColors.outline),
            Expanded(child: detail),
          ],
        );
      },
    );
  }
}

class _CandidateRail extends StatelessWidget {
  const _CandidateRail({
    required this.items,
    required this.selectedId,
    required this.onSelected,
  });

  final List<ExpectedCareCandidateData> items;
  final String selectedId;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: DrAiColors.white,
      child: ListView.separated(
        scrollDirection: MediaQuery.sizeOf(context).width < 920
            ? Axis.horizontal
            : Axis.vertical,
        padding: const EdgeInsets.all(DrAiSpacing.md),
        itemCount: items.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8, height: 8),
        itemBuilder: (context, index) {
          final item = items[index];
          final selected = item.id == selectedId;
          return Semantics(
            button: true,
            selected: selected,
            label: _copy(
              context,
              'Immutable system baseline ${index + 1}',
              '不可变系统基线 ${index + 1}',
            ),
            child: InkWell(
              onTap: () => onSelected(item.id),
              borderRadius: BorderRadius.circular(12),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: 248,
                padding: const EdgeInsets.all(DrAiSpacing.sm),
                decoration: BoxDecoration(
                  color: selected ? DrAiColors.brandSoft : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: selected ? DrAiColors.brand : DrAiColors.outline,
                  ),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      '${_copy(context, 'System baseline', '系统基线')} · '
                      '${_evidenceStateLabel(context, item.state)}',
                      style: const TextStyle(
                        color: DrAiColors.brandDark,
                        fontWeight: FontWeight.w800,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${_money(item.currency, item.totalLowMinor)}–'
                      '${_money(item.currency, item.totalHighMinor)}',
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _DoctorCandidateDetail extends StatelessWidget {
  const _DoctorCandidateDetail({
    required this.candidate,
    required this.submitting,
    required this.message,
    required this.messageIsError,
    required this.onAcknowledge,
    required this.onConcur,
    required this.onDisagree,
    required this.onException,
    required this.onRefresh,
    required this.comparison,
    required this.patientId,
    required this.eventId,
  });

  final ExpectedCareCandidateData candidate;
  final bool submitting;
  final String? message;
  final bool messageIsError;
  final VoidCallback onAcknowledge;
  final VoidCallback onConcur;
  final VoidCallback onDisagree;
  final VoidCallback onException;
  final VoidCallback onRefresh;
  final AsyncValue<ExpectedCareComparisonData> comparison;
  final String patientId;
  final String eventId;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        DrAiSpacing.lg,
        DrAiSpacing.lg,
        DrAiSpacing.lg,
        DrAiSpacing.xxl,
      ),
      children: <Widget>[
        Wrap(
          alignment: WrapAlignment.spaceBetween,
          runSpacing: 12,
          children: <Widget>[
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  _copy(
                    context,
                    'Immutable expected-care baseline',
                    '不可变预期诊疗基线',
                  ),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _copy(
                    context,
                    'System-published after deterministic validation. No clinician can edit, reject, or hide this baseline.',
                    '经确定性验证后由系统发布。任何医生均无法编辑、拒绝或隐藏此基线。',
                  ),
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ],
            ),
            IconButton(
              tooltip: _copy(context, 'Refresh', '刷新'),
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _RangeBand(
          currency: candidate.currency,
          low: candidate.totalLowMinor,
          high: candidate.totalHighMinor,
          label: _copy(context, 'Immutable reference range', '不可变参考范围'),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _StatusStrip(candidate: candidate),
        if (message != null) ...<Widget>[
          const SizedBox(height: DrAiSpacing.md),
          _InlineMessage(text: message!, isError: messageIsError),
        ],
        const SizedBox(height: DrAiSpacing.md),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            FilledButton.icon(
              onPressed: submitting ? null : onAcknowledge,
              icon: const Icon(Icons.visibility_outlined),
              label: Text(_copy(context, 'Acknowledge', '确认已阅')),
            ),
            OutlinedButton.icon(
              onPressed: submitting ? null : onConcur,
              icon: const Icon(Icons.check_circle_outline),
              label: Text(_copy(context, 'Clinically concur', '临床同意')),
            ),
            OutlinedButton.icon(
              onPressed: submitting ? null : onDisagree,
              icon: const Icon(Icons.compare_arrows_outlined),
              label: Text(_copy(context, 'Record disagreement', '记录不同意见')),
            ),
            TextButton.icon(
              onPressed: submitting ? null : onException,
              icon: const Icon(Icons.note_add_outlined),
              label: Text(_copy(context, 'Record exception', '记录临床例外')),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _Section(
          title: _copy(context, 'Immutable baseline items', '不可变基线项目'),
          child: Column(
            children: candidate.items
                .map(
                  (item) =>
                      _DoctorItemRow(item: item, currency: candidate.currency),
                )
                .toList(),
          ),
        ),
        _RoleComparisonAndExplanation(
          comparison: comparison,
          role: 'doctor',
          parentId: patientId,
          eventId: eventId,
        ),
        _Section(
          title: _copy(context, 'Exact admitted references', '确切准入参考'),
          child: Column(
            children: candidate.references
                .map(
                  (reference) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    leading: const Icon(Icons.verified_outlined),
                    title: Text(
                      _referenceLabel(context, reference.releaseType),
                    ),
                    subtitle: Text(
                      _copy(
                        context,
                        reference.effectiveFrom == null
                            ? 'Governed reference preserved for this baseline'
                            : 'Effective ${reference.effectiveFrom} · governed reference preserved',
                        reference.effectiveFrom == null
                            ? '此基线保留的受治理参考'
                            : '生效日期 ${reference.effectiveFrom} · 已保留受治理参考',
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ),
        _FactsSection(candidate: candidate),
        _CostFactTransparency(snapshot: candidate.factSnapshot),
        _Section(
          title: _copy(
            context,
            'Immutable baseline and response history',
            '不可变基线与响应历史',
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              _TimelineEntry(
                title: _copy(context, 'Candidate generated', '候选范围已生成'),
                detail: _copy(
                  context,
                  'Original AI candidate preserved without modification · ${candidate.referenceDate}',
                  '原始 AI 候选范围未经修改并已保留 · ${candidate.referenceDate}',
                ),
              ),
              _TimelineEntry(
                title: _copy(context, 'Deterministic validation', '确定性验证'),
                detail: _evidenceStateLabel(context, candidate.validationState),
              ),
              _TimelineEntry(
                title: _copy(context, 'Baseline published', '基线已发布'),
                detail:
                    '${_evidenceStateLabel(context, candidate.state)} · '
                    '${_copy(context, 'cannot be edited or hidden', '不可编辑或隐藏')}',
              ),
              ...candidate.clinicianResponses.indexed.map(
                (entry) => _TimelineEntry(
                  title: _copy(
                    context,
                    entry.$1 == candidate.clinicianResponses.length - 1
                        ? 'Current doctor response'
                        : 'Earlier doctor response',
                    entry.$1 == candidate.clinicianResponses.length - 1
                        ? '当前医生响应'
                        : '较早的医生响应',
                  ),
                  detail: _copy(
                    context,
                    'Recorded by the doctor · ${formatProductHistoryTimestamp(context, entry.$2.createdAt)}\n'
                        '${_clinicianPositionLabel(context, entry.$2.position)}'
                        '${entry.$2.patientSafeSummary == null ? '' : ' · ${entry.$2.patientSafeSummary}'}',
                    '由医生记录 · ${formatProductHistoryTimestamp(context, entry.$2.createdAt)}\n'
                        '${_clinicianPositionLabel(context, entry.$2.position)}'
                        '${entry.$2.patientSafeSummary == null ? '' : ' · ${entry.$2.patientSafeSummary}'}',
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StatusStrip extends StatelessWidget {
  const _StatusStrip({required this.candidate});

  final ExpectedCareCandidateData candidate;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        _StatusChip(
          icon: Icons.auto_awesome_outlined,
          label: _copy(context, 'AI candidate preserved', 'AI 候选范围已保留'),
        ),
        _StatusChip(
          icon: Icons.rule_outlined,
          label: _copy(context, 'Validated', '已验证'),
        ),
        _StatusChip(
          icon: Icons.lock_outline,
          label: _copy(context, 'Baseline immutable and visible', '基线不可变且保持可见'),
        ),
        _StatusChip(
          icon: Icons.medical_services_outlined,
          label: candidate.latestClinicianPosition == 'not_recorded'
              ? _copy(context, 'Clinician response optional', '可选择记录临床响应')
              : _copy(
                  context,
                  'Clinician: ${_clinicianPositionLabel(context, candidate.latestClinicianPosition)}',
                  '临床立场：${_clinicianPositionLabel(context, candidate.latestClinicianPosition)}',
                ),
        ),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(100),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 16, color: DrAiColors.brand),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _FactsSection extends StatelessWidget {
  const _FactsSection({required this.candidate});

  final ExpectedCareCandidateData candidate;

  @override
  Widget build(BuildContext context) {
    return _Section(
      title: _copy(
        context,
        'Assumptions, missing information, and limitations',
        '假设、缺失信息与局限',
      ),
      child: Wrap(
        spacing: 24,
        runSpacing: 18,
        children: <Widget>[
          _FactList(
            title: _copy(context, 'Assumptions', '假设'),
            items: candidate.assumptions,
          ),
          _FactList(
            title: _copy(context, 'Missing information', '缺失信息'),
            items: candidate.missingInformation,
          ),
          _FactList(
            title: _copy(context, 'Limitations', '局限'),
            items: candidate.limitations,
          ),
        ],
      ),
    );
  }
}

class _DoctorItemRow extends StatelessWidget {
  const _DoctorItemRow({required this.item, required this.currency});

  final ExpectedCareItemData item;
  final String currency;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  _careCategoryLabel(context, item.category),
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  '${item.quantityLow}–${item.quantityHigh} '
                  '${_careUnitLabel(context, item.unit, item.quantityHigh)}',
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ],
            ),
          ),
          Text(
            '${_money(currency, item.amountLowMinor)}–'
            '${_money(currency, item.amountHighMinor)}',
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _ResponseDraft {
  const _ResponseDraft({
    required this.exceptionCode,
    required this.rationale,
    required this.patientSafeSummary,
    required this.reviewerOnlyNote,
  });

  final String exceptionCode;
  final String rationale;
  final String patientSafeSummary;
  final String reviewerOnlyNote;
}

class _ClinicianResponseDialog extends StatefulWidget {
  const _ClinicianResponseDialog({required this.position});

  final String position;

  @override
  State<_ClinicianResponseDialog> createState() =>
      _ClinicianResponseDialogState();
}

class _ClinicianResponseDialogState extends State<_ClinicianResponseDialog> {
  final _exception = TextEditingController();
  final _rationale = TextEditingController();
  final _patientSafe = TextEditingController();
  final _reviewerOnly = TextEditingController();

  @override
  void dispose() {
    _exception.dispose();
    _rationale.dispose();
    _patientSafe.dispose();
    _reviewerOnly.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
        widget.position == 'disagree'
            ? _copy(context, 'Record clinical disagreement', '记录临床不同意见')
            : _copy(context, 'Record clinical exception', '记录临床例外'),
      ),
      content: SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              _InlineMessage(
                text: _copy(
                  context,
                  'Your response is appended beside the baseline. It cannot change, reject, or hide the system-published values.',
                  '您的响应将追加显示在基线旁，不能更改、拒绝或隐藏系统发布的数值。',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _exception,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Exception / reason code',
                    '例外／理由代码',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _rationale,
                minLines: 2,
                maxLines: 4,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Attributable clinical rationale',
                    '可归属的临床理由',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _patientSafe,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Patient-safe summary (optional)',
                    '患者可见摘要（可选）',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _reviewerOnly,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Reviewer-only note (optional)',
                    '仅审核者可见备注（可选）',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(_copy(context, 'Cancel', '取消')),
        ),
        FilledButton(
          onPressed: () {
            final code = _exception.text.trim();
            final rationale = _rationale.text.trim();
            if (code.length < 2 || rationale.length < 4) {
              return;
            }
            Navigator.pop(
              context,
              _ResponseDraft(
                exceptionCode: code,
                rationale: rationale,
                patientSafeSummary: _patientSafe.text.trim(),
                reviewerOnlyNote: _reviewerOnly.text.trim(),
              ),
            );
          },
          child: Text(_copy(context, 'Append response', '追加响应')),
        ),
      ],
    );
  }
}

class PatientExpectedCareScreen extends ConsumerWidget {
  const PatientExpectedCareScreen({required this.eventId, super.key});

  final String eventId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final baseline = ref.watch(patientExpectedCareEnvelopeProvider(eventId));
    final comparison = ref.watch(
      patientExpectedCareComparisonProvider(eventId),
    );
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: baseline.when(
          loading: () => DashboardLoadingView(
            label: _copy(context, 'Loading published baseline', '正在加载已发布基线'),
          ),
          error: (error, stackTrace) => _UnavailableState(
            title: _copy(context, 'No validated baseline available', '暂无有效基线'),
            body: _copy(
              context,
              'Invalid or unsafe model output is never presented as guidance. Your ordinary care and cost records remain available.',
              '无效或不安全的模型输出不会作为指导展示。常规诊疗和费用记录仍可使用。',
            ),
            onRetry: () =>
                ref.invalidate(patientExpectedCareEnvelopeProvider(eventId)),
          ),
          data: (data) => _PatientBaseline(data: data, comparison: comparison),
        ),
      ),
    );
  }
}

class _PatientBaseline extends StatelessWidget {
  const _PatientBaseline({required this.data, required this.comparison});

  final ExpectedCareBaselineData data;
  final AsyncValue<ExpectedCareComparisonData> comparison;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 48),
      children: <Widget>[
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 820),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  _copy(context, 'System expected-care baseline', '系统预期诊疗基线'),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  _copy(
                    context,
                    'Published after deterministic validation. Your doctor cannot edit or hide it and may add a separate clinical response.',
                    '经确定性验证后发布。医生无法编辑或隐藏基线，但可另行添加临床响应。',
                  ),
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
                const SizedBox(height: 24),
                _RangeBand(
                  currency: data.currency,
                  low: data.totalLowMinor,
                  high: data.totalHighMinor,
                  label: _copy(context, 'Reference range', '参考范围'),
                ),
                const SizedBox(height: 16),
                _InlineMessage(
                  text: _copy(
                    context,
                    data.disclaimer,
                    '此不可变系统参考范围不是报价、账单、保障决定、处方诊疗计划、报销金额或最终个人应付金额。',
                  ),
                ),
                const SizedBox(height: 20),
                _Section(
                  title: _copy(context, 'What the range includes', '范围包含内容'),
                  child: Column(
                    children: data.items
                        .map(
                          (item) => _DoctorItemRow(
                            item: item,
                            currency: data.currency,
                          ),
                        )
                        .toList(),
                  ),
                ),
                _PlainFacts(data: data),
                _CostFactTransparency(snapshot: data.factSnapshot),
                _RoleComparisonAndExplanation(
                  comparison: comparison,
                  role: 'patient',
                  parentId: '',
                  eventId: data.clinicalEventId,
                ),
                _ClinicianResponses(
                  responses: data.clinicianResponses,
                  latestPosition: data.latestClinicianPosition,
                  patientSafe: true,
                ),
                _Section(
                  title: _copy(context, 'Responsible next action', '下一步负责人'),
                  child: Text(
                    _copy(
                      context,
                      data.nextAction,
                      '请与负责医生讨论基线及任何临床差异；支付方报销仍是独立决定。',
                    ),
                    style: const TextStyle(height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _PlainFacts extends StatelessWidget {
  const _PlainFacts({required this.data});

  final ExpectedCareBaselineData data;

  @override
  Widget build(BuildContext context) {
    return _Section(
      title: _copy(context, 'What may change this range', '哪些因素可能改变该范围'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _FactList(
            title: _copy(context, 'Assumptions', '当前假设'),
            items: data.assumptions,
          ),
          const SizedBox(height: 14),
          _FactList(
            title: _copy(context, 'Still unknown', '仍未知的信息'),
            items: data.missingInformation,
          ),
          const SizedBox(height: 14),
          _FactList(
            title: _copy(context, 'Uncertainty', '不确定性'),
            items: data.limitations,
          ),
          if (data.references.isNotEmpty) ...<Widget>[
            const SizedBox(height: 14),
            Text(
              _copy(
                context,
                'Sources: ${data.references.map((item) => '${_referenceLabel(context, item.releaseType)}${item.effectiveFrom == null ? '' : ', effective ${item.effectiveFrom}'}').join(' · ')}',
                '来源：${data.references.map((item) => '${_referenceLabel(context, item.releaseType)}${item.effectiveFrom == null ? '' : '，生效于 ${item.effectiveFrom}'}').join(' · ')}',
              ),
              style: const TextStyle(color: DrAiColors.inkSecondary),
            ),
          ],
        ],
      ),
    );
  }
}

class _CostFactTransparency extends StatelessWidget {
  const _CostFactTransparency({required this.snapshot});

  final CostEstimationFactSnapshotData snapshot;

  @override
  Widget build(BuildContext context) {
    final title = _copy(context, 'Cost-estimation fact accounting', '费用估算事实清单');
    return Semantics(
      container: true,
      label: title,
      child: _Section(
        title: title,
        child: snapshot.available
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    _copy(
                      context,
                      'This server-built list shows the minimum-necessary facts admitted to the estimate, facts deliberately excluded, and facts that were unavailable. It does not transfer diagnosis or payer decision authority.',
                      '此服务端生成清单展示费用估算所准入的最少必要事实、被明确排除的事实及当时不可用的事实。清单不会转移诊断权或支付方决定权。',
                    ),
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      height: 1.45,
                    ),
                  ),
                  const SizedBox(height: 16),
                  _CostFactGroup(
                    title: _copy(context, 'Facts used', '已使用事实'),
                    facts: snapshot.factsUsed,
                    emptyCopy: _copy(
                      context,
                      'No admitted facts were recorded.',
                      '未记录已准入事实。',
                    ),
                  ),
                  const SizedBox(height: 18),
                  _CostFactGroup(
                    title: _copy(context, 'Facts not used', '未使用事实'),
                    facts: snapshot.factsNotUsed,
                    emptyCopy: _copy(
                      context,
                      'No excluded facts were recorded.',
                      '未记录被排除的事实。',
                    ),
                  ),
                  const SizedBox(height: 18),
                  _CostFactGroup(
                    title: _copy(context, 'Missing facts', '缺失事实'),
                    facts: snapshot.missingFacts,
                    emptyCopy: _copy(
                      context,
                      'No missing fact categories were recorded.',
                      '未记录缺失事实类别。',
                    ),
                  ),
                ],
              )
            : _InlineMessage(
                text: _copy(
                  context,
                  'Fact accounting is unavailable for this older baseline. This does not mean that no facts were used.',
                  '此较早基线暂无事实清单。这并不表示当时未使用任何事实。',
                ),
              ),
      ),
    );
  }
}

class _CostFactGroup extends StatelessWidget {
  const _CostFactGroup({
    required this.title,
    required this.facts,
    required this.emptyCopy,
  });

  final String title;
  final List<CostEstimationFactData> facts;
  final String emptyCopy;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: title,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: const TextStyle(
              color: DrAiColors.brandDark,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          if (facts.isEmpty)
            Text(
              emptyCopy,
              style: const TextStyle(color: DrAiColors.inkSecondary),
            )
          else
            ...facts.map(
              (fact) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _CostFactRow(fact: fact),
              ),
            ),
        ],
      ),
    );
  }
}

class _CostFactRow extends StatelessWidget {
  const _CostFactRow({required this.fact});

  final CostEstimationFactData fact;

  @override
  Widget build(BuildContext context) {
    final category = _factCategory(context, fact.category);
    final title = fact.label.trim().isEmpty ? category : fact.label;
    final reason = _factReason(context, fact);
    final value = fact.detailWithheld ? null : _factValue(context, fact.value);
    final provenance = <String>[
      if (fact.sourceType != null)
        _copy(context, 'Source: ', '来源：') +
            _factCategory(context, fact.sourceType!),
      if (fact.sourceScope != null)
        _copy(context, 'Scope: ', '范围：') +
            _factScope(context, fact.sourceScope!),
    ];
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(
                Icons.fact_check_outlined,
                size: 18,
                color: DrAiColors.brand,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              if (fact.count > 1)
                Text(
                  _copy(context, '${fact.count} records', '${fact.count} 条记录'),
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
            ],
          ),
          if (fact.detailWithheld) ...<Widget>[
            const SizedBox(height: 6),
            Text(
              _copy(
                context,
                'This category was used, but detail is withheld in this role view under the minimum-necessary rule.',
                '此类别已用于估算，但根据最少必要原则，本角色视图不显示具体内容。',
              ),
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                height: 1.4,
              ),
            ),
          ] else if (value != null && value.isNotEmpty) ...<Widget>[
            const SizedBox(height: 6),
            Text(value, style: const TextStyle(height: 1.4)),
          ],
          if (reason != null) ...<Widget>[
            const SizedBox(height: 6),
            Text(
              reason,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                height: 1.4,
              ),
            ),
          ],
          if (provenance.isNotEmpty) ...<Widget>[
            const SizedBox(height: 6),
            Text(
              provenance.join(' · '),
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

String _factCategory(BuildContext context, String category) {
  return switch (category) {
    'symptoms' => _copy(context, 'Symptoms', '症状'),
    'medical_history' => _copy(context, 'Medical history', '病史'),
    'allergy' => _copy(context, 'Allergies', '过敏信息'),
    'chronic_condition' => _copy(context, 'Chronic conditions', '慢性病'),
    'current_medication' || 'medication' => _copy(context, 'Medications', '用药'),
    'event_update' => _copy(context, 'Clinical Event updates', '临床事件更新'),
    'medical_record' => _copy(context, 'Medical records', '医疗记录'),
    'doctor_confirmed_finding' => _copy(
      context,
      'Doctor-confirmed findings',
      '医生确认发现',
    ),
    'imaging' => _copy(context, 'Imaging', '影像'),
    'ai_imaging_observation_draft' => _copy(
      context,
      'AI imaging observation draft',
      'AI 影像观察草稿',
    ),
    'prescription' => _copy(context, 'Prescriptions', '处方'),
    'recovery_progress' => _copy(context, 'Recovery progress', '康复进展'),
    'consultation' => _copy(context, 'Consultations', '会诊'),
    'clinical_service' => _copy(context, 'Clinical services', '临床服务'),
    'cost' => _copy(context, 'Delivered costs', '已交付费用'),
    'doctor_note' => _copy(context, 'Doctor notes', '医生记录'),
    'clinical_event' => _copy(context, 'Clinical Event', '临床事件'),
    _ => category.replaceAll('_', ' '),
  };
}

String _factScope(BuildContext context, String scope) {
  return switch (scope) {
    'exact_clinical_event' => _copy(context, 'exact Clinical Event', '确切临床事件'),
    'authorized_patient_but_not_exact_event' => _copy(
      context,
      'authorized patient, not linked to this event',
      '已授权患者，但未关联本次事件',
    ),
    _ => scope.replaceAll('_', ' '),
  };
}

String? _factReason(BuildContext context, CostEstimationFactData fact) {
  final reason = fact.reason;
  if (reason == null || reason.trim().isEmpty) {
    return null;
  }
  return switch (reason) {
    'patient_wide_record_has_no_clinical_event_binding' => _copy(
      context,
      'Patient-wide record was not used because it is not linked to this Clinical Event.',
      '患者级记录未关联本次临床事件，因此未使用。',
    ),
    'upload_not_finalized' => _copy(
      context,
      'Imaging upload is not finalized.',
      '影像上传尚未完成。',
    ),
    'free_text_note_not_required_for_cost_estimation' => _copy(
      context,
      'Free-text note was outside the minimum-necessary cost scope.',
      '自由文本记录不属于费用估算所需的最少范围。',
    ),
    'bounded_minimum_necessary_limit' => _copy(
      context,
      'Additional records were excluded by the bounded minimum-necessary limit.',
      '其余记录因最少必要数量限制而未纳入。',
    ),
    'DeepSeek image input is unsupported; no AI imaging draft is used.' =>
      _copy(context, reason, 'DeepSeek 当前不支持图像输入，因此未使用 AI 影像草稿。'),
    _ =>
      Localizations.localeOf(context).languageCode == 'zh'
          ? '尚无可用的${_factCategory(context, fact.category)}。'
          : reason,
  };
}

String? _factValue(BuildContext context, Object? value) {
  if (value == null) {
    return null;
  }
  if (value is Map) {
    final entries = value.entries
        .where((entry) {
          final key = entry.key.toString().toLowerCase();
          return key != 'detail_withheld' &&
              key != 'present' &&
              key != 'withholding_reason' &&
              !key.endsWith('_id') &&
              !key.contains('checksum') &&
              !key.contains('item_key') &&
              !key.contains('internal_code');
        })
        .take(5)
        .map((entry) {
          final label = humanizeProductValue(entry.key.toString());
          final displayValue = _factValue(context, entry.value);
          return displayValue == null ? null : '$label: $displayValue';
        })
        .whereType<String>();
    final text = entries.join(' · ');
    return text.isEmpty ? null : text;
  }
  if (value is Iterable) {
    final text = value
        .map((item) => _factValue(context, item))
        .whereType<String>()
        .join(', ');
    return text.isEmpty ? null : text;
  }
  if (value is bool) {
    return value ? _copy(context, 'Yes', '是') : _copy(context, 'No', '否');
  }
  return value.toString();
}

class _ClinicianResponses extends StatelessWidget {
  const _ClinicianResponses({
    required this.responses,
    required this.latestPosition,
    this.patientSafe = false,
  });

  final List<ClinicianResponseData> responses;
  final String latestPosition;
  final bool patientSafe;

  @override
  Widget build(BuildContext context) {
    return _Section(
      title: _copy(
        context,
        'Clinician response — separate from baseline',
        '临床响应——与基线分开记录',
      ),
      child: responses.isEmpty
          ? _InlineMessage(
              text: _copy(
                context,
                'No clinician position has been recorded. The baseline remains visible and unchanged.',
                '尚未记录临床立场。基线仍保持可见且未经更改。',
              ),
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  _copy(
                    context,
                    'Latest position: ${_clinicianPositionLabel(context, latestPosition)}',
                    '最新立场：${_clinicianPositionLabel(context, latestPosition)}',
                  ),
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 10),
                ...responses.indexed.map(
                  (entry) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        const Icon(
                          Icons.account_circle_outlined,
                          size: 20,
                          color: DrAiColors.brand,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${_copy(context, entry.$1 == responses.length - 1 ? 'Current doctor response' : 'Earlier doctor response', entry.$1 == responses.length - 1 ? '当前医生响应' : '较早的医生响应')}'
                            ' · ${formatProductHistoryTimestamp(context, entry.$2.createdAt)}\n'
                            '${_clinicianPositionLabel(context, entry.$2.position)}'
                            '${entry.$2.patientSafeSummary == null ? '' : '\n${entry.$2.patientSafeSummary}'}'
                            '${patientSafe || entry.$2.clinicalRationale == null ? '' : '\n${entry.$2.clinicalRationale!['rationale']}'}',
                            style: const TextStyle(height: 1.45),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}

class PayerExpectedCareScreen extends ConsumerWidget {
  const PayerExpectedCareScreen({required this.requestId, super.key});

  final String requestId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(payerExpectedCareEnvelopeProvider(requestId));
    final comparison = ref.watch(
      payerExpectedCareComparisonProvider(requestId),
    );
    return ResponsiveAppShell(
      role: AppRole.payer,
      selectedIndex: 1,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: data.when(
          loading: () => DashboardLoadingView(
            label: _copy(
              context,
              'Loading authorized review evidence',
              '正在加载已授权审核证据',
            ),
          ),
          error: (error, stackTrace) => _UnavailableState(
            title: _copy(context, 'Published baseline unavailable', '已发布基线不可用'),
            body: _copy(
              context,
              'Access requires an active organization membership and the exact immutable payer request.',
              '访问需要有效的机构成员身份及确切的不可变支付申请。',
            ),
            onRetry: () =>
                ref.invalidate(payerExpectedCareEnvelopeProvider(requestId)),
          ),
          data: (value) => _PayerEvidence(data: value, comparison: comparison),
        ),
      ),
    );
  }
}

class _PayerEvidence extends StatelessWidget {
  const _PayerEvidence({required this.data, required this.comparison});

  final PayerExpectedCareData data;
  final AsyncValue<ExpectedCareComparisonData> comparison;

  @override
  Widget build(BuildContext context) {
    final baseline = data.baseline;
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 48),
      children: <Widget>[
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1060),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  _copy(
                    context,
                    'Authorized expected-care evidence',
                    '已授权的预期诊疗证据',
                  ),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  _copy(
                    context,
                    'Read-only clinical context for human payer review. No automated reimbursement or adverse conclusion.',
                    '供支付方人工审核使用的只读临床背景，不作自动报销或不利结论。',
                  ),
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
                const SizedBox(height: 24),
                _EvidenceFlow(data: data),
                const SizedBox(height: 24),
                _RangeBand(
                  currency: baseline.currency,
                  low: baseline.totalLowMinor,
                  high: baseline.totalHighMinor,
                  label: _copy(context, 'Immutable system baseline', '不可变系统基线'),
                ),
                const SizedBox(height: 18),
                _Section(
                  title: _copy(context, 'Immutable baseline items', '不可变基线项目'),
                  child: Column(
                    children: baseline.items
                        .map(
                          (item) => _DoctorItemRow(
                            item: item,
                            currency: baseline.currency,
                          ),
                        )
                        .toList(),
                  ),
                ),
                _Section(
                  title: _copy(context, 'Submitted facts', '已提交事实'),
                  child: Text(
                    _copy(
                      context,
                      'Submitted evidence snapshot · ${_evidenceStateLabel(context, data.submittedState)} · requested ${_money(baseline.currency, data.requestedTotalMinor)}',
                      '已提交证据快照 · ${_evidenceStateLabel(context, data.submittedState)} · 申请金额 ${_money(baseline.currency, data.requestedTotalMinor)}',
                    ),
                  ),
                ),
                _ClinicianResponses(
                  responses: baseline.clinicianResponses,
                  latestPosition: baseline.latestClinicianPosition,
                ),
                _RoleComparisonAndExplanation(
                  comparison: comparison,
                  role: 'payer',
                  parentId: data.payerRequestId,
                  eventId: baseline.clinicalEventId,
                ),
                _PlainFacts(data: baseline),
                _CostFactTransparency(snapshot: baseline.factSnapshot),
                _InlineMessage(
                  text: _copy(
                    context,
                    'The baseline cannot be modified or hidden by a clinician. It is evidence, not a coverage decision; reimbursement remains a separate human payer action.',
                    '医生无法更改或隐藏该基线。基线仅为证据，不是保障决定；报销仍由支付方另行人工处理。',
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _RoleComparisonAndExplanation extends ConsumerStatefulWidget {
  const _RoleComparisonAndExplanation({
    required this.comparison,
    required this.role,
    required this.parentId,
    required this.eventId,
  });

  final AsyncValue<ExpectedCareComparisonData> comparison;
  final String role;
  final String parentId;
  final String eventId;

  @override
  ConsumerState<_RoleComparisonAndExplanation> createState() =>
      _RoleComparisonAndExplanationState();
}

class _RoleComparisonAndExplanationState
    extends ConsumerState<_RoleComparisonAndExplanation> {
  bool _working = false;
  bool _includeSubmittedFacts = true;
  String? _actionMessage;
  bool _actionError = false;

  ExpectedCareExplanationScope _scope(ExpectedCareComparisonData data) => (
    role: widget.role,
    parentId: widget.parentId,
    eventId: widget.eventId,
    comparisonId: data.id,
  );

  void _invalidateComparison() {
    switch (widget.role) {
      case 'doctor':
        ref.invalidate(
          doctorExpectedCareComparisonProvider((
            patientId: widget.parentId,
            eventId: widget.eventId,
          )),
        );
        return;
      case 'patient':
        ref.invalidate(patientExpectedCareComparisonProvider(widget.eventId));
        return;
      case 'payer':
        ref.invalidate(payerExpectedCareComparisonProvider(widget.parentId));
        return;
    }
  }

  Future<void> _createComparison(ExpectedCareComparisonData? current) async {
    setState(() {
      _working = true;
      _actionMessage = null;
    });
    try {
      final created = await ref
          .read(repositoryProvider)
          .createDoctorExpectedCareComparison(
            patientId: widget.parentId,
            eventId: widget.eventId,
            baselineId: current?.baselineId,
            includeSubmittedFacts: _includeSubmittedFacts,
            idempotencyKey:
                'comparison-${current?.baselineId ?? widget.eventId}-submitted-'
                '$_includeSubmittedFacts-after-v${current?.version ?? 0}',
          );
      _invalidateComparison();
      if (mounted) {
        setState(() {
          _working = false;
          _actionError = false;
          _actionMessage = created.idempotentReplay
              ? _copy(
                  context,
                  'The same content-bound request was replayed safely.',
                  '相同的内容绑定请求已安全重放。',
                )
              : _copy(
                  context,
                  'A new immutable comparison was added to the history.',
                  '新的不可变比较已加入历史记录。',
                );
        });
      }
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _working = false;
          _actionError = true;
          _actionMessage = error.code == 'conflict'
              ? _copy(
                  context,
                  'Facts or release lineage changed. Refresh and try again.',
                  '事实或发布沿袭已变化，请刷新后重试。',
                )
              : _copy(
                  context,
                  'The comparison could not be appended. Existing baseline and history remain available.',
                  '无法追加比较。现有基线和历史记录仍可使用。',
                );
        });
      }
    }
  }

  Future<void> _requestExplanation(ExpectedCareComparisonData data) async {
    setState(() {
      _working = true;
      _actionMessage = null;
    });
    final locale = Localizations.localeOf(context).languageCode == 'zh'
        ? 'zh-Hans'
        : 'en';
    try {
      final result = await ref
          .read(repositoryProvider)
          .requestExpectedCareExplanation(
            role: widget.role,
            parentId: widget.parentId,
            eventId: widget.eventId,
            comparisonId: data.id,
            locale: locale,
            idempotencyKey:
                'explanation-${widget.role}-${data.id}-$locale-v${data.version}',
          );
      ref.invalidate(expectedCareExplanationProvider(_scope(data)));
      if (mounted) {
        setState(() {
          _working = false;
          _actionError = false;
          _actionMessage = result.displayMode == 'structured_fallback'
              ? _copy(
                  context,
                  'Structured fallback is active; the baseline and comparison remain visible.',
                  '当前使用结构化后备内容；基线和比较仍然可见。',
                )
              : result.idempotentReplay
              ? _copy(
                  context,
                  'The same validated explanation request was replayed safely.',
                  '相同的已验证解释请求已安全重放。',
                )
              : _copy(
                  context,
                  'A server-rendered bilingual explanation was appended.',
                  '已追加由服务器渲染的双语解释。',
                );
        });
      }
    } on ApiError {
      if (mounted) {
        setState(() {
          _working = false;
          _actionError = true;
          _actionMessage = _copy(
            context,
            'Explanation unavailable. Use the structured comparison and retry when ready.',
            '解释暂不可用。请使用结构化比较，并在合适时重试。',
          );
        });
      }
    }
  }

  Future<void> _showHistory(ExpectedCareComparisonData data) async {
    setState(() => _working = true);
    try {
      final explanations = await ref
          .read(repositoryProvider)
          .loadExpectedCareExplanationHistory(
            role: widget.role,
            parentId: widget.parentId,
            eventId: widget.eventId,
            comparisonId: data.id,
          );
      final comparisons = widget.role == 'doctor'
          ? await ref
                .read(repositoryProvider)
                .loadDoctorExpectedCareComparisonHistory(
                  patientId: widget.parentId,
                  eventId: widget.eventId,
                )
          : <ExpectedCareComparisonData>[data];
      if (!mounted) return;
      setState(() => _working = false);
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(_copy(context, 'Immutable history', '不可变历史记录')),
          content: SizedBox(
            width: 520,
            child: ListView(
              shrinkWrap: true,
              children: <Widget>[
                Text(
                  _copy(
                    context,
                    '${comparisons.length} comparison version(s)',
                    '${comparisons.length} 个比较版本',
                  ),
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                ...comparisons.indexed.map(
                  (entry) => ListTile(
                    leading: const Icon(Icons.calculate_outlined),
                    title: Text(
                      _copy(
                        context,
                        entry.$1 == 0
                            ? 'Current immutable comparison'
                            : 'Earlier immutable comparison',
                        entry.$1 == 0 ? '当前不可变比较' : '较早的不可变比较',
                      ),
                    ),
                    subtitle: Text(
                      '${_comparisonLabel(context, entry.$2.deliveredTotalLabel)} · '
                      '${_copy(context, entry.$1 == 0 ? 'current' : 'superseded by a later comparison', entry.$1 == 0 ? '当前记录' : '已被后续比较取代')}',
                    ),
                  ),
                ),
                const Divider(),
                Text(
                  _copy(
                    context,
                    '${explanations.length} explanation attempt(s)',
                    '${explanations.length} 次解释尝试',
                  ),
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                ...explanations.indexed.map(
                  (entry) => ListTile(
                    leading: Icon(
                      entry.$2.isValidated
                          ? Icons.verified_outlined
                          : Icons.shield_outlined,
                    ),
                    title: Text(
                      _copy(
                        context,
                        entry.$2.isValidated
                            ? 'Validated explanation'
                            : 'Structured fallback',
                        entry.$2.isValidated ? '已验证解释' : '结构化回退',
                      ),
                    ),
                    subtitle: Text(
                      _copy(
                        context,
                        entry.$1 == 0
                            ? 'Current display record'
                            : 'Earlier display record',
                        entry.$1 == 0 ? '当前展示记录' : '较早的展示记录',
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(_copy(context, 'Close', '关闭')),
            ),
          ],
        ),
      );
    } on ApiError {
      if (mounted) {
        setState(() {
          _working = false;
          _actionError = true;
          _actionMessage = _copy(
            context,
            'History is temporarily unavailable.',
            '历史记录暂不可用。',
          );
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Section(
      title: _copy(
        context,
        'Deterministic comparison and validated explanation',
        '确定性比较与已验证解释',
      ),
      child: widget.comparison.when(
        loading: () => Semantics(
          liveRegion: true,
          label: _copy(context, 'Loading comparison', '正在加载比较'),
          child: const LinearProgressIndicator(),
        ),
        error: (error, stackTrace) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _ComparisonFallback(
              title: _copy(context, 'Comparison not available', '比较暂不可用'),
              body: _copy(
                context,
                'The immutable baseline remains visible. Missing cost, pending-cost, manual documentation, and clarification workflows continue normally.',
                '不可变基线仍然可见。缺失费用、待补费用、手动记录和澄清流程均可照常继续。',
              ),
            ),
            if (widget.role == 'doctor') ...<Widget>[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _working ? null : () => _createComparison(null),
                icon: const Icon(Icons.add_chart_outlined),
                label: Text(
                  _copy(
                    context,
                    'Create first immutable comparison',
                    '创建首个不可变比较',
                  ),
                ),
              ),
            ],
          ],
        ),
        data: (data) {
          final scope = (
            role: widget.role,
            parentId: widget.parentId,
            eventId: widget.eventId,
            comparisonId: data.id,
          );
          final explanation = ref.watch(expectedCareExplanationProvider(scope));
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: <Widget>[
                  _EvidenceChip(
                    icon: Icons.calculate_outlined,
                    label: _copy(
                      context,
                      'Delivered: ${_comparisonLabel(context, data.deliveredTotalLabel)}',
                      '已交付：${_comparisonLabel(context, data.deliveredTotalLabel)}',
                    ),
                  ),
                  if (widget.role != 'patient' &&
                      data.submittedTotalLabel != null)
                    _EvidenceChip(
                      icon: Icons.receipt_long_outlined,
                      label: _copy(
                        context,
                        'Submitted: ${_comparisonLabel(context, data.submittedTotalLabel!)}',
                        '已提交：${_comparisonLabel(context, data.submittedTotalLabel!)}',
                      ),
                    ),
                  _EvidenceChip(
                    icon: Icons.history_outlined,
                    label: _copy(
                      context,
                      'Current immutable comparison',
                      '当前不可变比较',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ...data.items.indexed.map(
                (entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Icon(
                        Icons.rule_outlined,
                        size: 18,
                        color: DrAiColors.brand,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '${_copy(context, 'Care item ${entry.$1 + 1}', '诊疗项目 ${entry.$1 + 1}')} · '
                          '${_comparisonLabel(context, entry.$2.deliveredLabel)}'
                          '${entry.$2.deliveredAmountMinor == null ? '' : ' · ${_money(data.currency, entry.$2.deliveredAmountMinor!)}'}',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 4),
              _InlineMessage(
                text: _copy(
                  context,
                  data.disclaimer,
                  '此确定性数值比较不构成临床必要性、保障、报销、付款、违规、欺诈或个人责任结论。',
                ),
              ),
              if (_actionMessage != null) ...<Widget>[
                const SizedBox(height: 12),
                _InlineMessage(text: _actionMessage!, isError: _actionError),
              ],
              const SizedBox(height: 12),
              if (widget.role == 'doctor')
                Material(
                  color: Colors.transparent,
                  child: CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _includeSubmittedFacts,
                    onChanged: _working
                        ? null
                        : (value) => setState(
                            () => _includeSubmittedFacts = value ?? true,
                          ),
                    title: Text(
                      _copy(
                        context,
                        'Include immutable submitted facts when available',
                        '在可用时纳入不可变的已提交事实',
                      ),
                    ),
                    subtitle: Text(
                      _copy(
                        context,
                        'Delivered facts are always server-owned. Flutter never constructs provider facts.',
                        '已交付事实始终由服务器管理，Flutter 不会构造提供方事实。',
                      ),
                    ),
                  ),
                ),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: <Widget>[
                  if (widget.role == 'doctor')
                    FilledButton.icon(
                      onPressed: _working
                          ? null
                          : () => _createComparison(data),
                      icon: const Icon(Icons.add_chart_outlined),
                      label: Text(_copy(context, 'Append comparison', '追加比较')),
                    ),
                  OutlinedButton.icon(
                    onPressed: _working
                        ? null
                        : () => _requestExplanation(data),
                    icon: const Icon(Icons.auto_awesome_outlined),
                    label: Text(
                      _copy(
                        context,
                        widget.role == 'patient'
                            ? 'Request or retry safe explanation'
                            : 'Request or retry scoped explanation',
                        widget.role == 'patient' ? '请求或重试安全解释' : '请求或重试限定范围解释',
                      ),
                    ),
                  ),
                  TextButton.icon(
                    onPressed: _working ? null : () => _showHistory(data),
                    icon: const Icon(Icons.history_outlined),
                    label: Text(_copy(context, 'View history', '查看历史')),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              explanation.when(
                loading: () => Semantics(
                  liveRegion: true,
                  label: _copy(context, 'Loading explanation', '正在加载解释'),
                  child: const LinearProgressIndicator(),
                ),
                error: (error, stackTrace) => _ComparisonFallback(
                  title: _copy(
                    context,
                    'AI explanation unavailable',
                    'AI 解释暂不可用',
                  ),
                  body: _copy(
                    context,
                    'The validated structured comparison above is the display fallback.',
                    '上方已验证的结构化比较为当前展示后备内容。',
                  ),
                ),
                data: (value) => _ExplanationCard(data: value),
              ),
            ],
          );
        },
      ),
    );
  }
}

String _comparisonLabel(BuildContext context, String value) {
  return switch (value) {
    'within_reference_range' => _copy(
      context,
      'within reference range',
      '在参考范围内',
    ),
    'below_reference_range' => _copy(
      context,
      'below reference range',
      '低于参考范围',
    ),
    'above_reference_range' => _copy(
      context,
      'above reference range',
      '高于参考范围',
    ),
    'missing_cost' => _copy(context, 'cost missing', '费用缺失'),
    _ => _copy(context, 'not comparable', '不可比较'),
  };
}

class _ComparisonFallback extends StatelessWidget {
  const _ComparisonFallback({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: '$title. $body',
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: DrAiColors.pageBackground,
          border: Border.all(color: DrAiColors.outline),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(body, style: const TextStyle(height: 1.45)),
          ],
        ),
      ),
    );
  }
}

class _EvidenceChip extends StatelessWidget {
  const _EvidenceChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: label,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 320),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        decoration: BoxDecoration(
          color: DrAiColors.pageBackground,
          border: Border.all(color: DrAiColors.outline),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 16, color: DrAiColors.brand),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ExplanationCard extends StatelessWidget {
  const _ExplanationCard({required this.data});

  final ExpectedCareExplanationData data;

  @override
  Widget build(BuildContext context) {
    final chinese = Localizations.localeOf(context).languageCode == 'zh';
    final sections = data.localizedSections(chinese);
    if (!data.isValidated || sections.isEmpty) {
      return _ComparisonFallback(
        title: _copy(context, 'Structured facts fallback', '结构化事实后备内容'),
        body: _copy(
          context,
          'Generated prose did not become displayable. The baseline and deterministic comparison remain authoritative for this screen.',
          '生成文字未通过展示验证。本页面仍以基线和确定性比较为准。',
        ),
      );
    }
    return Semantics(
      container: true,
      label: _copy(
        context,
        'AI explanation of validated facts',
        '基于已验证事实的 AI 解释',
      ),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: DrAiColors.brandSoft,
          border: Border.all(color: DrAiColors.brand),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.auto_awesome_outlined),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _copy(
                      context,
                      'AI explanation of validated facts',
                      '基于已验证事实的 AI 解释',
                    ),
                    style: const TextStyle(fontWeight: FontWeight.w900),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ...sections.map(
              (text) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(text, style: const TextStyle(height: 1.5)),
              ),
            ),
            Text(
              _copy(
                context,
                'AI may rephrase admitted facts only. Deterministic validation always wins.',
                'AI 仅可改写已准入事实，确定性验证始终优先。',
              ),
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EvidenceFlow extends StatelessWidget {
  const _EvidenceFlow({required this.data});

  final PayerExpectedCareData data;

  @override
  Widget build(BuildContext context) {
    final steps = <(IconData, String, String)>[
      (
        Icons.auto_awesome_outlined,
        _copy(context, 'AI candidate', 'AI 候选范围'),
        _copy(context, 'Preserved without modification', '未经修改并已保留'),
      ),
      (
        Icons.rule_outlined,
        _copy(context, 'Deterministic validation', '确定性验证'),
        _copy(context, 'Server authority', '服务器权威'),
      ),
      (
        Icons.medical_services_outlined,
        _copy(context, 'Published baseline', '已发布基线'),
        _evidenceStateLabel(context, data.baseline.state),
      ),
      (
        Icons.comment_outlined,
        _copy(context, 'Clinician response', '临床响应'),
        _evidenceStateLabel(context, data.baseline.latestClinicianPosition),
      ),
      (
        Icons.receipt_long_outlined,
        _copy(context, 'Delivered / submitted facts', '已交付／已提交事实'),
        _evidenceStateLabel(context, data.submittedState),
      ),
      (
        Icons.person_outline,
        _copy(context, 'Human payer review', '支付方人工审核'),
        _evidenceStateLabel(context, data.humanReviewState),
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 800;
        final cards = steps.indexed.map((entry) {
          final step = entry.$2;
          return Container(
            margin: EdgeInsets.only(
              right: wide && entry.$1 < steps.length - 1 ? 8 : 0,
              bottom: !wide && entry.$1 < steps.length - 1 ? 8 : 0,
            ),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: DrAiColors.white,
              border: Border.all(color: DrAiColors.outline),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: <Widget>[
                Icon(step.$1, color: DrAiColors.brand),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        step.$2,
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      Text(
                        step.$3,
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }).toList();
        if (!wide) {
          return Column(children: cards);
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: cards.map((card) => Expanded(child: card)).toList(),
        );
      },
    );
  }
}

class _RangeBand extends StatelessWidget {
  const _RangeBand({
    required this.currency,
    required this.low,
    required this.high,
    required this.label,
  });

  final String currency;
  final int low;
  final int high;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label ${_money(currency, low)} to ${_money(currency, high)}',
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: DrAiColors.brandDark,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(label, style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 6),
            FittedBox(
              child: Text(
                '${_money(currency, low)} – ${_money(currency, high)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: DrAiColors.brandDark,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 10),
          DecoratedBox(
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: DrAiColors.outline)),
            ),
            child: Padding(
              padding: const EdgeInsets.only(top: 8),
              child: child,
            ),
          ),
        ],
      ),
    );
  }
}

class _FactList extends StatelessWidget {
  const _FactList({required this.title, required this.items});

  final String title;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 220, maxWidth: 440),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          if (items.isEmpty)
            Text(_copy(context, 'None recorded', '暂无记录'))
          else
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Text('• $item', style: const TextStyle(height: 1.4)),
              ),
            ),
        ],
      ),
    );
  }
}

class _TimelineEntry extends StatelessWidget {
  const _TimelineEntry({required this.title, required this.detail});

  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Padding(
            padding: EdgeInsets.only(top: 4),
            child: Icon(Icons.circle, size: 10, color: DrAiColors.brand),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  detail,
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InlineMessage extends StatelessWidget {
  const _InlineMessage({required this.text, this.isError = false});

  final String text;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isError ? const Color(0xFFFFF1F1) : const Color(0xFFF1F8F5),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: isError ? const Color(0xFF8B1E1E) : DrAiColors.brandDark,
          height: 1.45,
        ),
      ),
    );
  }
}

class _UnavailableState extends StatelessWidget {
  const _UnavailableState({
    required this.title,
    required this.body,
    required this.onRetry,
  });

  final String title;
  final String body;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Column(
            children: <Widget>[
              const Icon(
                Icons.fact_check_outlined,
                size: 48,
                color: DrAiColors.brand,
              ),
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
              const SizedBox(height: 18),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: Text(_copy(context, 'Refresh', '刷新')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
