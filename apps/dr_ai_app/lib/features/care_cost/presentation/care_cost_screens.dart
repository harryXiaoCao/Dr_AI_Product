import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
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
            label: _copy(context, 'Recorded total or estimate', '已记录总额或估算'),
            value: _money(ledger.currency, ledger.actualTotalMinor),
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
                                    '${item.sourceCategory.replaceAll('_', ' ')} · '
                                    '${item.sourceStatus.replaceAll('_', ' ')}',
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
                              '${item.status.replaceAll('_', ' ')} · '
                              '${item.pricingState.replaceAll('_', ' ')}'
                              '${item.alreadySubmitted ? ' · submitted' : ''}',
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
        key: Key('patient-expected-care-${request.clinicalEventId}'),
        contentPadding: EdgeInsets.zero,
        onTap: () =>
            context.go('/patient/expected-care/${request.clinicalEventId}'),
        title: Text(request.clinicalEventTitle),
        subtitle: Text.rich(
          TextSpan(
            children: <InlineSpan>[
              TextSpan(
                text:
                    '${request.payerOrganization.name} · ${request.status.replaceAll('_', ' ')}\n',
              ),
              TextSpan(
                text: _copy(
                  context,
                  'View immutable expected-care baseline',
                  '查看不可变预期诊疗基线',
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
            for (final response in request.doctorResponses)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.medical_information_outlined),
                title: Text(response.responseType.replaceAll('_', ' ')),
                subtitle: Text(response.summary),
                trailing: Text('v${response.version}'),
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
                request.aiReviewScore == null
                    ? _copy(context, 'AI: not evaluated', 'AI：尚未评估')
                    : 'AI: ${request.aiReviewScore}/100',
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Align(
            alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              key: Key('payer-expected-care-${request.id}'),
              onPressed: () =>
                  context.go('/payer/requests/${request.id}/expected-care'),
              icon: const Icon(Icons.fact_check_outlined),
              label: Text(
                _copy(
                  context,
                  'View authorized expected-care evidence',
                  '查看已授权的预期诊疗证据',
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
              for (final review in request.reviews)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.history),
                  title: Text(
                    '${review.fromStatus.replaceAll('_', ' ')} → '
                    '${review.toStatus.replaceAll('_', ' ')}',
                  ),
                  subtitle: Text(
                    '${review.reviewerDisplayName} · ${review.reviewerTitle}\n'
                    '${review.reasonCode.replaceAll('_', ' ')}',
                  ),
                  trailing: Text('v${review.version}'),
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
        status.replaceAll('_', ' '),
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
  final note = TextEditingController();
  var action = 'request_clarification';
  var reason = 'documentation_needed';
  String? error;
  await showDialog<void>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(_copy(context, 'Record human review', '记录人工审核')),
        content: SizedBox(
          width: 520,
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
                            child: Text(_payerReviewActionText(context, value)),
                          ),
                        )
                        .toList(),
                onChanged: (value) => action = value ?? action,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              TextFormField(
                initialValue: reason,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Reason code', '原因代码'),
                ),
                onChanged: (value) => reason = value.trim(),
              ),
              const SizedBox(height: DrAiSpacing.sm),
              TextFormField(
                controller: note,
                minLines: 3,
                maxLines: 6,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Reviewer-only note (optional)',
                    '审核员内部备注（可选）',
                  ),
                ),
              ),
              if (error != null)
                Text(error!, style: const TextStyle(color: DrAiColors.danger)),
            ],
          ),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(_copy(context, 'Cancel', '取消')),
          ),
          FilledButton(
            onPressed: () async {
              try {
                await ref
                    .read(repositoryProvider)
                    .reviewPayerRequest(
                      requestId: request.id,
                      action: action,
                      reasonCode: reason,
                      expectedVersion: request.version,
                      idempotencyKey:
                          'payer-review-${request.id}-${DateTime.now().microsecondsSinceEpoch}',
                      note: note.text.trim().isEmpty ? null : note.text.trim(),
                    );
                ref.invalidate(payerRequestsProvider);
                ref.invalidate(payerDashboardProvider);
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } on ApiError catch (apiError) {
                setState(() => error = apiError.message);
              }
            },
            child: Text(_copy(context, 'Save review', '保存审核')),
          ),
        ],
      ),
    ),
  );
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
