import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/shared/presentation/product_history_copy.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

String _copy(BuildContext context, String en, String zh) {
  return Localizations.localeOf(context).languageCode == 'zh' ? zh : en;
}

String _money(String currency, int minor) {
  final value = minor / 100;
  return NumberFormat.currency(
    symbol: currency == 'CNY' ? '¥' : '$currency ',
    decimalDigits: 2,
  ).format(value);
}

String _date(BuildContext context, DateTime value) {
  return DateFormat.yMMMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).format(value);
}

String _requestNextAction(BuildContext context, String status) {
  return switch (status) {
    'submitted' => _copy(
      context,
      'Next: an authorized payer reviewer will review the submitted evidence.',
      '下一步：获授权的支付方审核员将审核已提交证据。',
    ),
    'clarification_requested' => _copy(
      context,
      'Next: the doctor can add clarification without changing the submitted record.',
      '下一步：医生可补充说明，但不会更改已提交记录。',
    ),
    'escalated' => _copy(
      context,
      'Next: another authorized human review is required.',
      '下一步：需要另一项获授权的人工审核。',
    ),
    'accepted' || 'rejected' || 'closed' => _copy(
      context,
      'This human review state is final for this request. Historical evidence remains available.',
      '此申请的人工审核状态已最终确定，历史证据仍可查看。',
    ),
    _ => _copy(
      context,
      'Review the current status and available actions below.',
      '请查看当前状态及下方可用操作。',
    ),
  };
}

class PatientCareCostScreen extends ConsumerWidget {
  const PatientCareCostScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ledger = ref.watch(ownCareCostLedgerProvider);
    final requests = ref.watch(ownPatientPayerRequestsProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: ledger.when(
          loading: () => const DashboardLoadingView(),
          error: (error, stackTrace) => DashboardErrorView(
            message: error.toString(),
            onRetry: () {
              ref.invalidate(ownCareCostLedgerProvider);
              ref.invalidate(ownPatientPayerRequestsProvider);
            },
          ),
          data: (data) => _CareCostLedgerView(
            ledger: data,
            payerRequests: requests.value ?? const <PayerRequestData>[],
            patientView: true,
          ),
        ),
      ),
    );
  }
}

class _CareCostLedgerView extends StatelessWidget {
  const _CareCostLedgerView({
    required this.ledger,
    required this.payerRequests,
    required this.patientView,
  });

  final CareCostLedgerData ledger;
  final List<PayerRequestData> payerRequests;
  final bool patientView;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('care-cost-ledger-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1180),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                _copy(context, 'Care & cost timeline', '诊疗与费用时间线'),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                _copy(
                  context,
                  'Billable services and products are grouped by clinical event. Amounts distinguish a recorded total or estimate, what was requested from the payer, and your expected responsibility.',
                  '可计费服务与产品按临床事件归类，并区分已记录总额或估算、向支付方申请的金额及预计个人承担金额。',
                ),
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
              const SizedBox(height: DrAiSpacing.lg),
              _LedgerTotals(ledger: ledger),
              const SizedBox(height: DrAiSpacing.lg),
              if (ledger.events.isEmpty)
                _EmptyLedger(patientView: patientView)
              else
                for (final event in ledger.events) ...<Widget>[
                  _ClinicalEventLedger(event: event),
                  const SizedBox(height: DrAiSpacing.md),
                ],
              if (payerRequests.isNotEmpty) ...<Widget>[
                const SizedBox(height: DrAiSpacing.sm),
                Text(
                  _copy(context, 'Payer request status', '支付申请状态'),
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: DrAiSpacing.sm),
                for (final request in payerRequests)
                  _PayerRequestSummary(request: request),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _LedgerTotals extends StatelessWidget {
  const _LedgerTotals({required this.ledger});

  final CareCostLedgerData ledger;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.md),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: DrAiColors.outline),
          bottom: BorderSide(color: DrAiColors.outline),
        ),
      ),
      child: Wrap(
        spacing: DrAiSpacing.xl,
        runSpacing: DrAiSpacing.md,
        children: <Widget>[
          _Metric(
            label: _copy(context, 'Recorded total', '已记录总额'),
            value: _money(ledger.currency, ledger.actualTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Estimated amounts', '估算金额'),
            value: _money(ledger.currency, ledger.estimatedTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Final amounts', '最终金额'),
            value: _money(ledger.currency, ledger.finalTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Requested from payer', '向支付方申请'),
            value: _money(ledger.currency, ledger.payerRequestedTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Expected patient responsibility', '预计个人承担'),
            value: _money(
              ledger.currency,
              ledger.patientResponsibilityTotalMinor,
            ),
          ),
          _Metric(
            label: _copy(context, 'Costs still pending', '费用待补充'),
            value: '${ledger.pendingCostItemCount}',
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 230,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(label, style: const TextStyle(color: DrAiColors.inkSecondary)),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: DrAiColors.ink,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyLedger extends StatelessWidget {
  const _EmptyLedger({required this.patientView});

  final bool patientView;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.xxl),
      child: Column(
        children: <Widget>[
          const Icon(
            Icons.receipt_long_outlined,
            size: 44,
            color: DrAiColors.mutedInk,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Text(
            _copy(context, 'No care or cost items yet', '暂无诊疗或费用项目'),
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            patientView
                ? _copy(
                    context,
                    'Billable services and products appear here after your doctor records them in the relevant clinical workflow.',
                    '医生在相应临床流程中记录可计费服务或产品后，相关信息会显示在此处。',
                  )
                : _copy(
                    context,
                    'Add the first service to make the treatment and cost path visible.',
                    '添加首个服务项目，使诊疗与费用路径清晰可见。',
                  ),
            textAlign: TextAlign.center,
            style: const TextStyle(color: DrAiColors.inkSecondary),
          ),
        ],
      ),
    );
  }
}

class _ClinicalEventLedger extends StatelessWidget {
  const _ClinicalEventLedger({required this.event});

  final CareCostEventData event;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: DrAiColors.white,
      child: Container(
        decoration: const BoxDecoration(
          border: Border(
            top: BorderSide(color: DrAiColors.outline),
            bottom: BorderSide(color: DrAiColors.outline),
          ),
        ),
        child: ExpansionTile(
          initiallyExpanded: true,
          tilePadding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
          childrenPadding: const EdgeInsets.fromLTRB(
            DrAiSpacing.sm,
            0,
            DrAiSpacing.sm,
            DrAiSpacing.md,
          ),
          title: Text(
            event.title,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          subtitle: Text(
            '${event.items.length} ${_copy(context, 'items', '项')} · '
            '${_money(event.currency, event.actualTotalMinor)}',
          ),
          children: <Widget>[
            if (event.items.isEmpty)
              const SizedBox(height: 80, child: Center(child: Text('—')))
            else
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  dataRowMinHeight: 60,
                  dataRowMaxHeight: 72,
                  headingRowColor: WidgetStateProperty.all(
                    DrAiColors.pageBackground,
                  ),
                  columns: <DataColumn>[
                    DataColumn(label: Text(_copy(context, 'Date', '日期'))),
                    DataColumn(label: Text(_copy(context, 'Service', '服务项目'))),
                    DataColumn(label: Text(_copy(context, 'Status', '状态'))),
                    DataColumn(
                      label: Text(
                        _copy(context, 'Total / estimate', '总额 / 估算'),
                      ),
                    ),
                    DataColumn(
                      label: Text(
                        _copy(context, 'Requested from payer', '向支付方申请'),
                      ),
                    ),
                    DataColumn(
                      label: Text(
                        _copy(context, 'Expected patient share', '预计个人承担'),
                      ),
                    ),
                    DataColumn(
                      label: Text(_copy(context, 'AI review', 'AI 审核')),
                    ),
                  ],
                  rows: <DataRow>[
                    for (final item in event.items)
                      DataRow(
                        cells: <DataCell>[
                          DataCell(
                            Text(
                              _date(
                                context,
                                item.performedAt ??
                                    item.scheduledAt ??
                                    item.orderedAt ??
                                    item.serviceDate,
                              ),
                            ),
                          ),
                          DataCell(
                            SizedBox(
                              width: 190,
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    item.label,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  Text(
                                    '${humanizeProductValue(item.sourceCategory)} · '
                                    '${humanizeProductValue(item.sourceStatus)}',
                                    style: const TextStyle(
                                      color: DrAiColors.inkSecondary,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          DataCell(
                            Text(
                              '${humanizeProductValue(item.status)} · '
                              '${humanizeProductValue(item.pricingState)}'
                              '${item.alreadySubmitted ? ' · ${_copy(context, 'Submitted', '已提交')}' : ''}',
                            ),
                          ),
                          DataCell(
                            Text(_money(item.currency, item.actualCostMinor)),
                          ),
                          DataCell(
                            Text(
                              _money(item.currency, item.payerRequestedMinor),
                            ),
                          ),
                          DataCell(
                            Text(
                              _money(
                                item.currency,
                                item.patientResponsibilityMinor,
                              ),
                            ),
                          ),
                          DataCell(
                            Text(
                              item.aiReviewScore == null
                                  ? _copy(context, 'Not evaluated', '尚未评估')
                                  : '${item.aiReviewScore}/100',
                              style: TextStyle(
                                color: item.aiReviewScore == null
                                    ? DrAiColors.inkSecondary
                                    : DrAiColors.brand,
                              ),
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class PayerDashboardScreen extends ConsumerWidget {
  const PayerDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(payerDashboardProvider);
    return ResponsiveAppShell(
      role: AppRole.payer,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: dashboard.when(
          loading: () => const DashboardLoadingView(),
          error: (error, stackTrace) => DashboardErrorView(
            message: error.toString(),
            onRetry: () => ref.invalidate(payerDashboardProvider),
          ),
          data: (data) => ListView(
            padding: const EdgeInsets.all(DrAiSpacing.lg),
            children: <Widget>[
              Text(
                _copy(context, 'Review dashboard', '审核工作台'),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${data.profile.organization.name} · ${_copy(context, 'synthetic review scope', '合成数据审核范围')}',
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
              const SizedBox(height: DrAiSpacing.lg),
              Wrap(
                spacing: DrAiSpacing.xl,
                runSpacing: DrAiSpacing.md,
                children: <Widget>[
                  _Metric(
                    label: _copy(context, 'Open requests', '待处理申请'),
                    value: '${data.openRequests}',
                  ),
                  _Metric(
                    label: _copy(context, 'Clarifications', '待补充说明'),
                    value: '${data.clarificationRequests}',
                  ),
                  _Metric(
                    label: _copy(context, 'Escalated', '已升级待处理'),
                    value: '${data.escalatedRequests}',
                  ),
                  _Metric(
                    label: _copy(context, 'Completed reviews', '已完成审核'),
                    value: '${data.completedReviews}',
                  ),
                  _Metric(
                    label: _copy(context, 'Pending requested amount', '待审申请金额'),
                    value: _money(
                      data.currency,
                      data.pendingRequestedTotalMinor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.xl),
              Align(
                alignment: Alignment.centerLeft,
                child: FilledButton.icon(
                  onPressed: () => context.go('/payer/requests'),
                  icon: const Icon(Icons.fact_check_outlined),
                  label: Text(_copy(context, 'Open review queue', '打开审核队列')),
                ),
              ),
              const SizedBox(height: DrAiSpacing.xl),
              Container(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                decoration: const BoxDecoration(
                  color: DrAiColors.white,
                  border: Border(
                    left: BorderSide(color: DrAiColors.brand, width: 4),
                  ),
                ),
                child: Text(
                  _copy(
                    context,
                    'AI review is not active. No score can approve, deny, reduce, or delay payment. Every current action is recorded as a human reviewer decision.',
                    'AI 审核尚未启用。任何评分均不得自动批准、拒绝、减少或延迟支付；当前所有操作均记录为人工审核决定。',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class PayerRequestsScreen extends ConsumerWidget {
  const PayerRequestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requests = ref.watch(payerRequestsProvider);
    return ResponsiveAppShell(
      role: AppRole.payer,
      selectedIndex: 1,
      child: _RequestWorkspace(
        title: _copy(context, 'Human review queue', '人工审核队列'),
        description: _copy(
          context,
          'Inspect the clinical-event context and immutable line-item snapshot before recording a review action.',
          '记录审核操作前，请查看临床事件背景与不可变更的费用明细快照。',
        ),
        requests: requests,
        onRetry: () => ref.invalidate(payerRequestsProvider),
        payerActions: true,
        onReview: (request) => _showReviewDialog(context, ref, request),
      ),
    );
  }
}

class _RequestWorkspace extends StatelessWidget {
  const _RequestWorkspace({
    required this.title,
    required this.description,
    required this.requests,
    required this.onRetry,
    this.payerActions = false,
    this.onReview,
  });

  final String title;
  final String description;
  final AsyncValue<List<PayerRequestData>> requests;
  final VoidCallback onRetry;
  final bool payerActions;
  final ValueChanged<PayerRequestData>? onReview;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: DrAiColors.pageBackground,
      child: requests.when(
        loading: () => const DashboardLoadingView(),
        error: (error, stackTrace) =>
            DashboardErrorView(message: error.toString(), onRetry: onRetry),
        data: (items) => ListView(
          padding: const EdgeInsets.all(DrAiSpacing.lg),
          children: <Widget>[
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: DrAiColors.brandDark,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              description,
              style: const TextStyle(color: DrAiColors.inkSecondary),
            ),
            const SizedBox(height: DrAiSpacing.lg),
            if (items.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.xxl),
                child: Center(
                  child: Text(_copy(context, 'No requests yet', '暂无申请')),
                ),
              )
            else
              for (final request in items) ...<Widget>[
                _PayerRequestDetail(
                  request: request,
                  payerActions: payerActions,
                  onReview: onReview,
                ),
                const SizedBox(height: DrAiSpacing.md),
              ],
          ],
        ),
      ),
    );
  }
}

class _PayerRequestSummary extends StatelessWidget {
  const _PayerRequestSummary({required this.request});
  final PayerRequestData request;
  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: ListTile(
        key: Key('patient-intelligence-${request.id}'),
        contentPadding: EdgeInsets.zero,
        onTap: () =>
            context.go('/patient/payer-requests/${request.id}/intelligence'),
        title: Text(request.clinicalEventTitle),
        subtitle: Text.rich(
          TextSpan(
            children: <InlineSpan>[
              TextSpan(
                text:
                    '${request.payerOrganization.name} · ${_payerRequestStatusText(context, request.status)}\n',
              ),
              TextSpan(
                text: _copy(
                  context,
                  'View Clinical Event intelligence',
                  '查看临床事件智能',
                ),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Text(
              _money(request.currency, request.requestedTotalMinor),
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            const Icon(Icons.arrow_forward, size: 18, color: DrAiColors.brand),
          ],
        ),
      ),
    );
  }
}

class _PayerRequestDetail extends StatelessWidget {
  const _PayerRequestDetail({
    required this.request,
    required this.payerActions,
    required this.onReview,
  });
  final PayerRequestData request;
  final bool payerActions;
  final ValueChanged<PayerRequestData>? onReview;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DrAiSpacing.md),
      decoration: const BoxDecoration(
        color: DrAiColors.white,
        border: Border(
          top: BorderSide(color: DrAiColors.outline),
          bottom: BorderSide(color: DrAiColors.outline),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  request.clinicalEventTitle,
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
              ),
              _StatusLabel(status: request.status),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${request.patientDisplayName} · ${request.doctorDisplayName} · ${request.payerOrganization.name}',
            style: const TextStyle(color: DrAiColors.inkSecondary),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Text(request.doctorSummary),
          if (request.doctorResponses.isNotEmpty) ...<Widget>[
            const SizedBox(height: DrAiSpacing.md),
            Text(
              _copy(context, 'Doctor responses', '医生补充说明'),
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            for (final entry in request.doctorResponses.indexed)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.medical_information_outlined),
                title: Text(
                  _doctorResponseTypeText(context, entry.$2.responseType),
                ),
                subtitle: Text(
                  '${entry.$2.doctorDisplayName} · ${formatProductHistoryTime(context, entry.$2.createdAt)}\n'
                  '${entry.$2.summary}',
                ),
                trailing: Text(
                  _copy(
                    context,
                    entry.$1 == request.doctorResponses.length - 1
                        ? 'Current'
                        : 'Earlier',
                    entry.$1 == request.doctorResponses.length - 1
                        ? '当前'
                        : '较早',
                  ),
                ),
              ),
          ],
          const SizedBox(height: DrAiSpacing.md),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: <DataColumn>[
                DataColumn(label: Text(_copy(context, 'Service', '服务'))),
                DataColumn(label: Text(_copy(context, 'Date', '日期'))),
                DataColumn(
                  label: Text(_copy(context, 'Recorded total', '已记录总额')),
                ),
                DataColumn(
                  label: Text(_copy(context, 'Requested from payer', '向支付方申请')),
                ),
                DataColumn(
                  label: Text(
                    _copy(context, 'Expected patient share', '预计个人承担'),
                  ),
                ),
              ],
              rows: request.lines
                  .map(
                    (line) => DataRow(
                      cells: <DataCell>[
                        DataCell(Text(line.label)),
                        DataCell(Text(_date(context, line.serviceDate))),
                        DataCell(
                          Text(_money(line.currency, line.actualCostMinor)),
                        ),
                        DataCell(
                          Text(_money(line.currency, line.requestedMinor)),
                        ),
                        DataCell(
                          Text(
                            _money(
                              line.currency,
                              line.patientResponsibilityMinor,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                  .toList(),
            ),
          ),
          const Divider(height: DrAiSpacing.lg),
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  '${_copy(context, 'Requested total', '申请总额')}: ${_money(request.currency, request.requestedTotalMinor)}',
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              Text(
                _copy(
                  context,
                  'Versioned AI support: open the intelligence artifact',
                  '版本化 AI 支持：请打开智能产物查看',
                ),
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Text(
            _requestNextAction(context, request.status),
            style: const TextStyle(
              color: DrAiColors.inkSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: DrAiSpacing.md),
          Align(
            alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              key: Key('payer-intelligence-${request.id}'),
              onPressed: () =>
                  context.go('/payer/requests/${request.id}/intelligence'),
              icon: const Icon(Icons.fact_check_outlined),
              label: Text(
                _copy(
                  context,
                  'View authorized request intelligence',
                  '查看已授权申请智能',
                ),
              ),
            ),
          ),
          if (payerActions) ...<Widget>[
            if (request.reviews.isNotEmpty) ...<Widget>[
              const Divider(height: DrAiSpacing.lg),
              Text(
                _copy(context, 'Manual transition history', '人工状态变更记录'),
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              for (final entry in request.reviews.indexed)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.history),
                  title: Text(
                    '${_payerRequestStatusText(context, entry.$2.fromStatus)} → '
                    '${_payerRequestStatusText(context, entry.$2.toStatus)}',
                  ),
                  subtitle: Text(
                    '${entry.$2.reviewerDisplayName} · ${entry.$2.reviewerTitle} · '
                    '${formatProductHistoryTime(context, entry.$2.createdAt)}\n'
                    '${_copy(context, 'Recorded reason', '记录原因')}: '
                    '${humanizeProductValue(entry.$2.reasonCode)}'
                    '${entry.$2.clarificationMessage == null ? '' : '\n${_copy(context, 'Question for the doctor', '向医生提出的问题')}: ${entry.$2.clarificationMessage}'}'
                    '${entry.$2.note == null ? '' : '\n${_copy(context, 'Private internal payer note', '支付方内部私密备注')}: ${entry.$2.note}'}',
                  ),
                  trailing: Text(
                    _copy(
                      context,
                      entry.$1 == request.reviews.length - 1
                          ? 'Current'
                          : 'Superseded',
                      entry.$1 == request.reviews.length - 1 ? '当前' : '已取代',
                    ),
                  ),
                ),
            ],
            const SizedBox(height: DrAiSpacing.md),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: () => onReview?.call(request),
                icon: const Icon(Icons.rate_review_outlined),
                label: Text(_copy(context, 'Record human review', '记录人工审核')),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: DrAiColors.brandSoft,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        _payerRequestStatusText(context, status),
        style: const TextStyle(
          color: DrAiColors.brandDark,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }
}

Future<void> _showReviewDialog(
  BuildContext context,
  WidgetRef ref,
  PayerRequestData request,
) async {
  final formKey = GlobalKey<FormState>();
  final clarificationFocusNode = FocusNode();
  final clarification = TextEditingController();
  final note = TextEditingController();
  var action = 'request_clarification';
  final reason = TextEditingController(
    text: Localizations.localeOf(context).languageCode == 'zh'
        ? '需要补充材料'
        : 'Documentation needed',
  );
  String? error;
  var submitting = false;
  await showDialog<void>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(_copy(context, 'Record human review', '记录人工审核')),
        content: SizedBox(
          width: 520,
          child: SingleChildScrollView(
            child: Form(
              key: formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  DropdownButtonFormField<String>(
                    key: const Key('payer-review-action'),
                    initialValue: action,
                    decoration: InputDecoration(
                      labelText: _copy(context, 'Action', '操作'),
                    ),
                    items:
                        const <String>[
                              'request_clarification',
                              'accept',
                              'reject',
                              'escalate',
                              'close',
                            ]
                            .map(
                              (value) => DropdownMenuItem(
                                value: value,
                                child: Text(
                                  _payerReviewActionText(context, value),
                                ),
                              ),
                            )
                            .toList(),
                    onChanged: submitting
                        ? null
                        : (value) => setState(() {
                            action = value ?? action;
                            error = null;
                          }),
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  TextFormField(
                    controller: reason,
                    maxLength: 80,
                    decoration: InputDecoration(
                      labelText: _copy(
                        context,
                        'Reason for this decision',
                        '作出此决定的原因',
                      ),
                      helperText: _copy(
                        context,
                        'Use a short structured reason; reviewer-only details belong below.',
                        '请填写简短的结构化原因；仅审核员可见的细节请写在下方。',
                      ),
                    ),
                    validator: (value) => (value?.trim().length ?? 0) < 2
                        ? _copy(
                            context,
                            'Enter a short reason for this action.',
                            '请填写此操作的简短原因。',
                          )
                        : null,
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  if (action == 'request_clarification') ...<Widget>[
                    TextFormField(
                      key: const Key('payer-clarification-message'),
                      controller: clarification,
                      focusNode: clarificationFocusNode,
                      minLines: 3,
                      maxLines: 6,
                      maxLength: 2000,
                      decoration: InputDecoration(
                        labelText: _copy(
                          context,
                          'Question or information needed from the doctor',
                          '需要医生回答的问题或补充的信息',
                        ),
                        helperText: _copy(
                          context,
                          'Required, 10–2000 characters. The assigned doctor and authorized payer reviewers can see this.',
                          '必填，10–2000 个字符。负责医生和获授权的支付方审核员可见。',
                        ),
                        alignLabelWithHint: true,
                      ),
                      validator: (value) {
                        final length = value?.trim().length ?? 0;
                        if (length == 0) {
                          return _copy(
                            context,
                            'Tell the doctor what information is needed.',
                            '请说明需要医生补充的信息。',
                          );
                        }
                        if (length < 10) {
                          return _copy(
                            context,
                            'Use at least 10 characters.',
                            '请至少填写 10 个字符。',
                          );
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                  ],
                  TextFormField(
                    key: const Key('payer-private-note'),
                    controller: note,
                    minLines: 3,
                    maxLines: 6,
                    maxLength: 4000,
                    decoration: InputDecoration(
                      labelText: _copy(
                        context,
                        'Internal payer note (optional — not shared with doctor)',
                        '支付方内部备注（可选——不与医生共享）',
                      ),
                      helperText: _copy(
                        context,
                        'Visible only to authorized payer reviewers.',
                        '仅获授权的支付方审核员可见。',
                      ),
                    ),
                  ),
                  if (error != null)
                    Semantics(
                      liveRegion: true,
                      child: Text(
                        error!,
                        style: const TextStyle(color: DrAiColors.danger),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(_copy(context, 'Cancel', '取消')),
          ),
          FilledButton(
            key: const Key('payer-review-submit'),
            onPressed: submitting
                ? null
                : () async {
                    if (!(formKey.currentState?.validate() ?? false)) {
                      if (action == 'request_clarification' &&
                          clarification.text.trim().length < 10) {
                        clarificationFocusNode.requestFocus();
                      }
                      return;
                    }
                    setState(() {
                      submitting = true;
                      error = null;
                    });
                    try {
                      await ref
                          .read(repositoryProvider)
                          .reviewPayerRequest(
                            requestId: request.id,
                            action: action,
                            reasonCode: reason.text.trim(),
                            expectedVersion: request.version,
                            idempotencyKey:
                                'payer-review-${request.id}-${DateTime.now().microsecondsSinceEpoch}',
                            clarificationMessage:
                                action == 'request_clarification'
                                ? clarification.text.trim()
                                : null,
                            note: note.text.trim().isEmpty
                                ? null
                                : note.text.trim(),
                          );
                      ref.invalidate(payerRequestsProvider);
                      ref.invalidate(payerDashboardProvider);
                      if (dialogContext.mounted) Navigator.pop(dialogContext);
                    } on ApiError catch (apiError) {
                      setState(() {
                        submitting = false;
                        error = apiError.statusCode == 409
                            ? _copy(
                                context,
                                'This request changed. Close this dialog, refresh, and review the latest version; your entries are preserved here.',
                                '此申请已更新。请关闭对话框并刷新后审核最新版本；当前填写内容仍保留在此处。',
                              )
                            : _copy(
                                context,
                                'Check the highlighted fields and try again.',
                                '请检查标出的字段后重试。',
                              );
                      });
                      if (apiError.details.any(
                            (detail) => detail.field == 'clarification_message',
                          ) &&
                          action == 'request_clarification') {
                        clarificationFocusNode.requestFocus();
                      }
                    }
                  },
            child: Text(_copy(context, 'Save review', '保存审核')),
          ),
        ],
      ),
    ),
  );
  // Let the route reverse-transition finish before releasing field controllers.
  await Future<void>.delayed(kThemeAnimationDuration);
  clarificationFocusNode.dispose();
  clarification.dispose();
  reason.dispose();
  note.dispose();
}

String _payerReviewActionText(BuildContext context, String action) {
  return switch (action) {
    'request_clarification' => _copy(
      context,
      'Request clarification',
      '要求补充说明',
    ),
    'accept' => _copy(context, 'Accept request', '接受申请'),
    'reject' => _copy(context, 'Reject request', '拒绝申请'),
    'escalate' => _copy(context, 'Escalate review', '升级审核'),
    'close' => _copy(context, 'Close review', '关闭审核'),
    _ => action.replaceAll('_', ' '),
  };
}

String _payerRequestStatusText(BuildContext context, String status) {
  return switch (status) {
    'submitted' => _copy(context, 'Submitted', '已提交'),
    'under_review' => _copy(context, 'Under human review', '人工审核中'),
    'clarification_requested' => _copy(
      context,
      'Clarification requested',
      '需要补充说明',
    ),
    'accepted' => _copy(context, 'Accepted', '已接受'),
    'rejected' => _copy(context, 'Rejected', '已拒绝'),
    'escalated' => _copy(context, 'Escalated', '已升级'),
    'closed' => _copy(context, 'Closed', '已关闭'),
    _ => humanizeProductValue(status),
  };
}

String _doctorResponseTypeText(BuildContext context, String responseType) {
  return switch (responseType) {
    'justification' => _copy(context, 'Doctor justification', '医生说明'),
    'supplemental_evidence' => _copy(context, 'Supplemental evidence', '补充证据'),
    'clarification' => _copy(context, 'Doctor clarification', '医生补充说明'),
    _ => humanizeProductValue(responseType),
  };
}
