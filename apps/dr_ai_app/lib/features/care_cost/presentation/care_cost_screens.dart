import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:dr_ai_app/shared/widgets/sign_out_button.dart';
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
                  'Every service is grouped by clinical event. Amounts show what occurred, what was requested from the payer, and your current responsibility.',
                  '所有服务按临床事件归类，并分别显示实际费用、向支付方申请的金额及当前个人承担金额。',
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
            label: _copy(context, 'Actual care cost', '实际诊疗费用'),
            value: _money(ledger.currency, ledger.actualTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Requested from payer', '向支付方申请'),
            value: _money(ledger.currency, ledger.payerRequestedTotalMinor),
          ),
          _Metric(
            label: _copy(context, 'Current patient responsibility', '当前个人承担'),
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
                    'Your doctor can add planned and completed services to each clinical event.',
                    '医生可在每个临床事件下添加计划中或已完成的服务。',
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
                    DataColumn(label: Text(_copy(context, 'Actual', '实际费用'))),
                    DataColumn(label: Text(_copy(context, 'Payer', '支付方申请'))),
                    DataColumn(label: Text(_copy(context, 'Patient', '个人承担'))),
                    DataColumn(
                      label: Text(_copy(context, 'AI review', 'AI 审核')),
                    ),
                  ],
                  rows: <DataRow>[
                    for (final item in event.items)
                      DataRow(
                        cells: <DataCell>[
                          DataCell(Text(_date(context, item.serviceDate))),
                          DataCell(
                            SizedBox(
                              width: 190,
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    item.label,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  Text(
                                    item.itemType.replaceAll('_', ' '),
                                    style: const TextStyle(
                                      color: DrAiColors.inkSecondary,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          DataCell(Text(item.status.replaceAll('_', ' '))),
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

class DoctorCareCostEditor extends ConsumerWidget {
  const DoctorCareCostEditor({
    required this.patientId,
    required this.clinicalEventId,
    super.key,
  });

  final String patientId;
  final String? clinicalEventId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final eventId = clinicalEventId;
    if (eventId == null) {
      return _EmptyLedger(patientView: false);
    }
    final ledger = ref.watch(patientCareCostLedgerProvider(patientId));
    return ledger.when(
      loading: () => const DashboardLoadingView(),
      error: (error, stackTrace) => DashboardErrorView(
        message: error.toString(),
        onRetry: () => ref.invalidate(patientCareCostLedgerProvider(patientId)),
      ),
      data: (data) {
        final matches = data.events.where(
          (event) => event.clinicalEventId == eventId,
        );
        final event = matches.isEmpty ? null : matches.first;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    _copy(context, 'Care and cost items', '诊疗与费用项目'),
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                FilledButton.icon(
                  key: const Key('add-care-cost-item-button'),
                  onPressed: () =>
                      _showCareItemDialog(context, ref, patientId, eventId),
                  icon: const Icon(Icons.add),
                  label: Text(_copy(context, 'Add item', '添加项目')),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _copy(
                context,
                'Record planned or completed services and their actual allocation. AI review remains unavailable until a validated model is connected.',
                '记录计划中或已完成的服务及实际费用分配。接入经验证的模型前，AI 审核保持不可用。',
              ),
              style: const TextStyle(color: DrAiColors.inkSecondary),
            ),
            const SizedBox(height: DrAiSpacing.md),
            if (event == null || event.items.isEmpty)
              const _EmptyLedger(patientView: false)
            else ...<Widget>[
              for (final item in event.items)
                _EditableCareItem(
                  item: item,
                  onEdit: () => _showCareItemDialog(
                    context,
                    ref,
                    patientId,
                    eventId,
                    item: item,
                  ),
                  onDelete: () =>
                      _deleteItem(context, ref, patientId, eventId, item),
                ),
              const SizedBox(height: DrAiSpacing.md),
              OutlinedButton.icon(
                key: const Key('submit-payer-request-button'),
                onPressed: () => _showPayerRequestDialog(
                  context,
                  ref,
                  patientId,
                  eventId,
                  event.items,
                ),
                icon: const Icon(Icons.outbox_outlined),
                label: Text(_copy(context, 'Submit payer request', '提交支付申请')),
              ),
            ],
          ],
        );
      },
    );
  }

  Future<void> _deleteItem(
    BuildContext context,
    WidgetRef ref,
    String patientId,
    String eventId,
    CareCostItemData item,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(_copy(context, 'Delete care item?', '删除诊疗项目？')),
        content: Text(item.label),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(_copy(context, 'Cancel', '取消')),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(_copy(context, 'Delete', '删除')),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await ref
        .read(repositoryProvider)
        .deleteCareCostItem(
          patientId: patientId,
          clinicalEventId: eventId,
          itemId: item.id,
        );
    ref.invalidate(patientCareCostLedgerProvider(patientId));
  }
}

class _EditableCareItem extends StatelessWidget {
  const _EditableCareItem({
    required this.item,
    required this.onEdit,
    required this.onDelete,
  });

  final CareCostItemData item;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.sm),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: DrAiColors.outline)),
      ),
      child: Row(
        children: <Widget>[
          CircleAvatar(
            backgroundColor: DrAiColors.brandSoft,
            foregroundColor: DrAiColors.brand,
            child: Icon(_itemIcon(item.itemType), size: 20),
          ),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  item.label,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                Text(
                  '${_date(context, item.serviceDate)} · ${item.status.replaceAll('_', ' ')} · '
                  '${_money(item.currency, item.actualCostMinor)}',
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ],
            ),
          ),
          IconButton(onPressed: onEdit, icon: const Icon(Icons.edit_outlined)),
          IconButton(
            onPressed: onDelete,
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
    );
  }
}

IconData _itemIcon(String type) => switch (type) {
  'medication' || 'prescription' => Icons.medication_outlined,
  'imaging' => Icons.image_search_outlined,
  'laboratory' => Icons.science_outlined,
  'booking' || 'follow_up' => Icons.event_outlined,
  'procedure' || 'therapy' => Icons.healing_outlined,
  _ => Icons.receipt_long_outlined,
};

Future<void> _showCareItemDialog(
  BuildContext context,
  WidgetRef ref,
  String patientId,
  String eventId, {
  CareCostItemData? item,
}) async {
  final formKey = GlobalKey<FormState>();
  final label = TextEditingController(text: item?.label ?? '');
  final actual = TextEditingController(
    text: item == null ? '' : (item.actualCostMinor / 100).toStringAsFixed(2),
  );
  final payer = TextEditingController(
    text: item == null
        ? ''
        : (item.payerRequestedMinor / 100).toStringAsFixed(2),
  );
  final patient = TextEditingController(
    text: item == null
        ? ''
        : (item.patientResponsibilityMinor / 100).toStringAsFixed(2),
  );
  final notes = TextEditingController(text: item?.notes ?? '');
  var itemType = item?.itemType ?? 'medication';
  var itemStatus = item?.status ?? 'planned';
  var serviceDate = item?.serviceDate ?? DateTime.now();
  String? error;
  await showDialog<void>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(
          item == null
              ? _copy(context, 'Add care item', '添加诊疗项目')
              : _copy(context, 'Edit care item', '编辑诊疗项目'),
        ),
        content: SizedBox(
          width: 540,
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  DropdownButtonFormField<String>(
                    initialValue: itemType,
                    decoration: InputDecoration(
                      labelText: _copy(context, 'Type', '类型'),
                    ),
                    items:
                        const <String>[
                              'medication',
                              'prescription',
                              'imaging',
                              'laboratory',
                              'procedure',
                              'consultation',
                              'booking',
                              'follow_up',
                              'therapy',
                              'equipment',
                              'other',
                            ]
                            .map(
                              (value) => DropdownMenuItem(
                                value: value,
                                child: Text(value.replaceAll('_', ' ')),
                              ),
                            )
                            .toList(),
                    onChanged: (value) => itemType = value ?? itemType,
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  TextFormField(
                    controller: label,
                    decoration: InputDecoration(
                      labelText: _copy(context, 'Service name', '服务名称'),
                    ),
                    validator: (value) => (value?.trim().length ?? 0) < 2
                        ? _copy(context, 'Enter a service name', '请输入服务名称')
                        : null,
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  Row(
                    children: <Widget>[
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          initialValue: itemStatus,
                          decoration: InputDecoration(
                            labelText: _copy(context, 'Status', '状态'),
                          ),
                          items:
                              const <String>[
                                    'planned',
                                    'scheduled',
                                    'completed',
                                    'cancelled',
                                  ]
                                  .map(
                                    (value) => DropdownMenuItem(
                                      value: value,
                                      child: Text(value),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (value) =>
                              itemStatus = value ?? itemStatus,
                        ),
                      ),
                      const SizedBox(width: DrAiSpacing.sm),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final selected = await showDatePicker(
                              context: context,
                              firstDate: DateTime(2020),
                              lastDate: DateTime(2035),
                              initialDate: serviceDate,
                            );
                            if (selected != null) {
                              setState(() => serviceDate = selected);
                            }
                          },
                          icon: const Icon(Icons.calendar_today_outlined),
                          label: Text(_date(context, serviceDate)),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: DrAiSpacing.sm),
                  for (final entry in <(TextEditingController, String)>[
                    (actual, _copy(context, 'Actual cost (CNY)', '实际费用（元）')),
                    (
                      payer,
                      _copy(context, 'Requested from payer (CNY)', '向支付方申请（元）'),
                    ),
                    (
                      patient,
                      _copy(context, 'Patient responsibility (CNY)', '个人承担（元）'),
                    ),
                  ]) ...<Widget>[
                    TextFormField(
                      controller: entry.$1,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: InputDecoration(labelText: entry.$2),
                      validator: (value) => double.tryParse(value ?? '') == null
                          ? _copy(context, 'Enter a valid amount', '请输入有效金额')
                          : null,
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                  ],
                  TextFormField(
                    controller: notes,
                    maxLines: 3,
                    decoration: InputDecoration(
                      labelText: _copy(
                        context,
                        'Clinical note (optional)',
                        '临床备注（可选）',
                      ),
                    ),
                  ),
                  if (error != null) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.sm),
                    Text(
                      error!,
                      style: const TextStyle(color: DrAiColors.danger),
                    ),
                  ],
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
            onPressed: () async {
              if (!formKey.currentState!.validate()) return;
              int minor(TextEditingController controller) =>
                  ((double.parse(controller.text) * 100).round());
              final actualMinor = minor(actual);
              final payerMinor = minor(payer);
              final patientMinor = minor(patient);
              if (payerMinor + patientMinor > actualMinor) {
                setState(() {
                  error = _copy(
                    context,
                    'Payer and patient amounts cannot exceed actual cost.',
                    '支付方与个人承担金额之和不能超过实际费用。',
                  );
                });
                return;
              }
              try {
                await ref
                    .read(repositoryProvider)
                    .saveCareCostItem(
                      patientId: patientId,
                      clinicalEventId: eventId,
                      itemId: item?.id,
                      itemType: itemType,
                      label: label.text.trim(),
                      serviceDate: serviceDate,
                      status: itemStatus,
                      quantity: 1,
                      actualCostMinor: actualMinor,
                      payerRequestedMinor: payerMinor,
                      patientResponsibilityMinor: patientMinor,
                      notes: notes.text.trim().isEmpty
                          ? null
                          : notes.text.trim(),
                    );
                ref.invalidate(patientCareCostLedgerProvider(patientId));
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } on ApiError catch (apiError) {
                setState(() => error = apiError.message);
              }
            },
            child: Text(_copy(context, 'Save', '保存')),
          ),
        ],
      ),
    ),
  );
  label.dispose();
  actual.dispose();
  payer.dispose();
  patient.dispose();
  notes.dispose();
}

Future<void> _showPayerRequestDialog(
  BuildContext context,
  WidgetRef ref,
  String patientId,
  String eventId,
  List<CareCostItemData> items,
) async {
  final summary = TextEditingController();
  final organizations = await ref.read(payerOrganizationsProvider.future);
  if (!context.mounted) return;
  if (organizations.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _copy(
            context,
            'No payer organization is available yet. A payer must register first.',
            '暂无可用支付机构，请先由支付方完成注册。',
          ),
        ),
      ),
    );
    return;
  }
  var organizationId = organizations.first.id;
  String? error;
  await showDialog<void>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(_copy(context, 'Submit payer request', '提交支付申请')),
        content: SizedBox(
          width: 540,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              DropdownButtonFormField<String>(
                initialValue: organizationId,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Payer organization', '支付机构'),
                ),
                items: organizations
                    .map(
                      (organization) => DropdownMenuItem(
                        value: organization.id,
                        child: Text(organization.name),
                      ),
                    )
                    .toList(),
                onChanged: (value) => organizationId = value ?? organizationId,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              TextFormField(
                controller: summary,
                minLines: 3,
                maxLines: 6,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Clinical context and request summary',
                    '临床背景与申请说明',
                  ),
                  helperText: _copy(
                    context,
                    '${items.length} active items will be included.',
                    '将包含 ${items.length} 个有效项目。',
                  ),
                ),
              ),
              if (error != null) ...<Widget>[
                const SizedBox(height: DrAiSpacing.sm),
                Text(error!, style: const TextStyle(color: DrAiColors.danger)),
              ],
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
              if (summary.text.trim().length < 10) {
                setState(
                  () => error = _copy(
                    context,
                    'Add enough clinical context for review.',
                    '请补充足够的临床背景供审核。',
                  ),
                );
                return;
              }
              try {
                await ref
                    .read(repositoryProvider)
                    .createPayerRequest(
                      patientId: patientId,
                      clinicalEventId: eventId,
                      payerOrganizationId: organizationId,
                      careCostItemIds: items
                          .where((item) => item.status != 'cancelled')
                          .map((item) => item.id)
                          .toList(),
                      doctorSummary: summary.text.trim(),
                    );
                ref.invalidate(doctorPayerRequestsProvider);
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } on ApiError catch (apiError) {
                setState(() => error = apiError.message);
              }
            },
            child: Text(_copy(context, 'Submit', '提交')),
          ),
        ],
      ),
    ),
  );
  summary.dispose();
}

class DoctorPayerRequestsScreen extends ConsumerWidget {
  const DoctorPayerRequestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requests = ref.watch(doctorPayerRequestsProvider);
    return ResponsiveAppShell(
      role: AppRole.doctor,
      child: _RequestWorkspace(
        title: _copy(context, 'Payer requests', '支付申请'),
        description: _copy(
          context,
          'Track itemized packages submitted from clinical events and respond to human review status.',
          '追踪从临床事件提交的明细申请，并查看人工审核状态。',
        ),
        requests: requests,
        onRetry: () => ref.invalidate(doctorPayerRequestsProvider),
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

class PayerAccountScreen extends ConsumerWidget {
  const PayerAccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(payerProfileProvider);
    return ResponsiveAppShell(
      role: AppRole.payer,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: profile.when(
          loading: () => const DashboardLoadingView(),
          error: (error, stackTrace) => DashboardErrorView(
            message: error.toString(),
            onRetry: () => ref.invalidate(payerProfileProvider),
          ),
          data: (data) => ListView(
            padding: const EdgeInsets.all(DrAiSpacing.lg),
            children: <Widget>[
              Text(
                _copy(context, 'Payer account', '支付方账户'),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: DrAiSpacing.lg),
              _AccountRow(
                label: _copy(context, 'Reviewer', '审核员'),
                value: data.displayName,
              ),
              _AccountRow(
                label: _copy(context, 'Title', '职务'),
                value: data.title,
              ),
              _AccountRow(
                label: _copy(context, 'Organization', '机构'),
                value: data.organization.name,
              ),
              _AccountRow(
                label: _copy(context, 'Jurisdiction', '适用地区'),
                value: data.organization.jurisdictionCode,
              ),
              _AccountRow(
                label: _copy(context, 'Access scope', '访问范围'),
                value: data.scope.replaceAll('_', ' '),
              ),
              _AccountRow(
                label: _copy(context, 'Verification', '验证状态'),
                value: data.organization.verificationStatus.replaceAll(
                  '_',
                  ' ',
                ),
              ),
              const SizedBox(height: DrAiSpacing.xl),
              const Align(
                alignment: Alignment.centerLeft,
                child: SignOutButton(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AccountRow extends StatelessWidget {
  const _AccountRow({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.md),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: DrAiColors.outline)),
      ),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 180,
            child: Text(
              label,
              style: const TextStyle(color: DrAiColors.inkSecondary),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
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
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(request.clinicalEventTitle),
      subtitle: Text(
        '${request.payerOrganization.name} · ${request.status.replaceAll('_', ' ')}',
      ),
      trailing: Text(
        _money(request.currency, request.requestedTotalMinor),
        style: const TextStyle(fontWeight: FontWeight.w800),
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
          const SizedBox(height: DrAiSpacing.md),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: <DataColumn>[
                DataColumn(label: Text(_copy(context, 'Service', '服务'))),
                DataColumn(label: Text(_copy(context, 'Date', '日期'))),
                DataColumn(label: Text(_copy(context, 'Actual', '实际费用'))),
                DataColumn(label: Text(_copy(context, 'Requested', '申请金额'))),
                DataColumn(label: Text(_copy(context, 'Patient', '个人承担'))),
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
          if (payerActions) ...<Widget>[
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
                initialValue: action,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Action', '操作'),
                ),
                items:
                    const <String>[
                          'request_clarification',
                          'accept',
                          'escalate',
                          'close',
                        ]
                        .map(
                          (value) => DropdownMenuItem(
                            value: value,
                            child: Text(value.replaceAll('_', ' ')),
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
