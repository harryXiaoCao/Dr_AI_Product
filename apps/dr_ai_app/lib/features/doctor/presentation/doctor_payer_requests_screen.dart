import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/shared/presentation/product_history_copy.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

enum _WorkspaceView { create, history }

enum _RequestHistoryFilter { all, pending, accepted, rejected, closed }

class DoctorPayerRequestsScreen extends ConsumerStatefulWidget {
  const DoctorPayerRequestsScreen({
    this.initialPatientId,
    this.initialClinicalEventId,
    this.initialRequestId,
    super.key,
  });

  final String? initialPatientId;
  final String? initialClinicalEventId;
  final String? initialRequestId;

  @override
  ConsumerState<DoctorPayerRequestsScreen> createState() =>
      _DoctorPayerRequestsScreenState();
}

class _DoctorPayerRequestsScreenState
    extends ConsumerState<DoctorPayerRequestsScreen> {
  final _searchController = TextEditingController();
  final _summaryController = TextEditingController();
  final Set<String> _selectedItemIds = <String>{};

  _WorkspaceView _view = _WorkspaceView.create;
  String? _patientId;
  String? _clinicalEventId;
  String? _payerOrganizationId;
  int _step = 0;
  bool _confirmed = false;
  bool _submitting = false;
  String? _submissionError;
  PayerRequestData? _createdRequest;

  @override
  void initState() {
    super.initState();
    if (widget.initialRequestId != null) {
      _view = _WorkspaceView.history;
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _summaryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final patients = ref.watch(patientListProvider);
    final organizations = ref.watch(payerOrganizationsProvider);
    final requests = ref.watch(doctorPayerRequestsProvider);
    final patientId = _patientId ?? widget.initialPatientId;
    final eventId = _clinicalEventId ?? widget.initialClinicalEventId;
    final ledger = patientId == null
        ? null
        : ref.watch(patientCareCostLedgerProvider(patientId));
    final bundle = patientId == null
        ? null
        : ref.watch(patientCareBundleProvider(patientId));

    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 3,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Column(
          children: <Widget>[
            _WorkspaceHeader(
              view: _view,
              onViewChanged: (value) => setState(() => _view = value),
              onRefresh: () {
                ref.invalidate(doctorPayerRequestsProvider);
                if (patientId != null) {
                  ref.invalidate(patientCareCostLedgerProvider(patientId));
                  ref.invalidate(patientCareBundleProvider(patientId));
                }
              },
            ),
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 220),
                child: _view == _WorkspaceView.create
                    ? _buildCreateWorkspace(
                        patients: patients,
                        organizations: organizations,
                        requests: requests,
                        patientId: patientId,
                        eventId: eventId,
                        ledger: ledger,
                        bundle: bundle,
                      )
                    : _RequestHistory(
                        requests: requests,
                        initialRequestId: widget.initialRequestId,
                        onRetry: () =>
                            ref.invalidate(doctorPayerRequestsProvider),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCreateWorkspace({
    required AsyncValue<PatientListData> patients,
    required AsyncValue<List<PayerOrganizationData>> organizations,
    required AsyncValue<List<PayerRequestData>> requests,
    required String? patientId,
    required String? eventId,
    required AsyncValue<CareCostLedgerData>? ledger,
    required AsyncValue<PatientCareBundle>? bundle,
  }) {
    final requestItems = requests.asData?.value ?? const <PayerRequestData>[];
    final previouslySubmitted = <String>{
      for (final request in requestItems)
        for (final line in request.lines)
          if (line.careCostItemId != null) line.careCostItemId!,
    };
    final selectedLedger = ledger?.asData?.value;
    final selectedEvent = selectedLedger?.events
        .where((event) => event.clinicalEventId == eventId)
        .firstOrNull;
    final selectedItems =
        selectedEvent?.items
            .where((item) => _selectedItemIds.contains(item.id))
            .toList() ??
        const <CareCostItemData>[];
    final organizationItems =
        organizations.asData?.value ?? const <PayerOrganizationData>[];
    final selectedOrganization = organizationItems
        .where((item) => item.id == _payerOrganizationId)
        .firstOrNull;
    final selectedPatient = patients.asData?.value.items
        .where((item) => item.patientId == patientId)
        .firstOrNull;

    return Column(
      key: const ValueKey<String>('create-payment-request'),
      children: <Widget>[
        _ProgressHeader(
          currentStep: _step,
          onStepSelected: (step) {
            if (step <=
                _furthestAvailableStep(
                  patientId: patientId,
                  eventId: eventId,
                  selectedItems: selectedItems,
                )) {
              setState(() => _step = step);
            }
          },
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(
              DrAiSpacing.md,
              DrAiSpacing.sm,
              DrAiSpacing.md,
              DrAiSpacing.xl,
            ),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1120),
                child: _StepCard(
                  child: switch (_step) {
                    0 => _PatientAndEventStep(
                      patients: patients,
                      ledger: ledger,
                      bundle: bundle,
                      searchController: _searchController,
                      selectedPatientId: patientId,
                      selectedEventId: eventId,
                      onSearchChanged: (value) =>
                          ref.read(patientSearchQueryProvider.notifier).state =
                              value,
                      onRetryPatients: () =>
                          ref.invalidate(patientListProvider),
                      onRetryLedger: patientId == null
                          ? null
                          : () {
                              ref.invalidate(
                                patientCareCostLedgerProvider(patientId),
                              );
                              ref.invalidate(
                                patientCareBundleProvider(patientId),
                              );
                            },
                      onPatientSelected: (id) => setState(() {
                        _patientId = id;
                        _clinicalEventId = null;
                        _selectedItemIds.clear();
                        _confirmed = false;
                        _createdRequest = null;
                      }),
                      onEventSelected: (id) => setState(() {
                        _patientId = patientId;
                        _clinicalEventId = id;
                        _selectedItemIds.clear();
                        _confirmed = false;
                        _createdRequest = null;
                      }),
                    ),
                    1 => _ItemSelectionStep(
                      event: selectedEvent,
                      submittedItemIds: previouslySubmitted,
                      selectedItemIds: _selectedItemIds,
                      onSelectionChanged: (id, selected) => setState(() {
                        if (selected) {
                          _selectedItemIds.add(id);
                        } else {
                          _selectedItemIds.remove(id);
                        }
                        _confirmed = false;
                      }),
                    ),
                    2 => _PayerAndSummaryStep(
                      organizations: organizations,
                      selectedOrganizationId: _payerOrganizationId,
                      summaryController: _summaryController,
                      onOrganizationChanged: (id) => setState(() {
                        _payerOrganizationId = id;
                        _confirmed = false;
                      }),
                      onRetry: () => ref.invalidate(payerOrganizationsProvider),
                      onSummaryChanged: (_) => setState(() {
                        _submissionError = null;
                        _confirmed = false;
                      }),
                    ),
                    _ => _ReviewStep(
                      patient: selectedPatient,
                      event: selectedEvent,
                      organization: selectedOrganization,
                      items: selectedItems,
                      summary: _summaryController.text.trim(),
                      confirmed: _confirmed,
                      submitting: _submitting,
                      submissionError: _submissionError,
                      createdRequest: _createdRequest,
                      onConfirmedChanged: _createdRequest == null
                          ? (value) =>
                                setState(() => _confirmed = value ?? false)
                          : null,
                      onSubmit:
                          _canSubmit(
                            patientId: patientId,
                            eventId: eventId,
                            organization: selectedOrganization,
                            selectedItems: selectedItems,
                          )
                          ? () => _submit(
                              patientId: patientId!,
                              eventId: eventId!,
                              organizationId: selectedOrganization!.id,
                              items: selectedItems,
                            )
                          : null,
                      onViewHistory: () =>
                          setState(() => _view = _WorkspaceView.history),
                    ),
                  },
                ),
              ),
            ),
          ),
        ),
        _StepActions(
          step: _step,
          canContinue: _canContinue(
            patientId: patientId,
            eventId: eventId,
            selectedItems: selectedItems,
            organization: selectedOrganization,
          ),
          onBack: _step == 0 ? null : () => setState(() => _step -= 1),
          onContinue: _step == 3 ? null : () => setState(() => _step += 1),
        ),
      ],
    );
  }

  int _furthestAvailableStep({
    required String? patientId,
    required String? eventId,
    required List<CareCostItemData> selectedItems,
  }) {
    if (patientId == null || eventId == null) return 0;
    if (selectedItems.isEmpty) return 1;
    if (_payerOrganizationId == null ||
        _summaryController.text.trim().length < 20) {
      return 2;
    }
    return 3;
  }

  bool _canContinue({
    required String? patientId,
    required String? eventId,
    required List<CareCostItemData> selectedItems,
    required PayerOrganizationData? organization,
  }) {
    return switch (_step) {
      0 => patientId != null && eventId != null,
      1 => selectedItems.isNotEmpty,
      2 => organization != null && _summaryController.text.trim().length >= 20,
      _ => false,
    };
  }

  bool _canSubmit({
    required String? patientId,
    required String? eventId,
    required PayerOrganizationData? organization,
    required List<CareCostItemData> selectedItems,
  }) {
    return !_submitting &&
        _createdRequest == null &&
        _confirmed &&
        patientId != null &&
        eventId != null &&
        organization != null &&
        selectedItems.isNotEmpty &&
        _summaryController.text.trim().length >= 20;
  }

  Future<void> _submit({
    required String patientId,
    required String eventId,
    required String organizationId,
    required List<CareCostItemData> items,
  }) async {
    setState(() {
      _submitting = true;
      _submissionError = null;
    });
    try {
      final created = await ref
          .read(repositoryProvider)
          .createPayerRequest(
            patientId: patientId,
            clinicalEventId: eventId,
            payerOrganizationId: organizationId,
            careCostItemIds: items.map((item) => item.id).toList(),
            doctorSummary: _summaryController.text.trim(),
          );
      if (!mounted) return;
      setState(() {
        _createdRequest = created;
        _submitting = false;
      });
      ref.invalidate(doctorPayerRequestsProvider);
    } on ApiError catch (error) {
      if (!mounted) return;
      setState(() {
        _submissionError = error.message;
        _submitting = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _submissionError = error.toString();
        _submitting = false;
      });
    }
  }
}

class _WorkspaceHeader extends StatelessWidget {
  const _WorkspaceHeader({
    required this.view,
    required this.onViewChanged,
    required this.onRefresh,
  });

  final _WorkspaceView view;
  final ValueChanged<_WorkspaceView> onViewChanged;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: DrAiColors.sectionHeader,
      padding: const EdgeInsets.fromLTRB(
        DrAiSpacing.md,
        DrAiSpacing.md,
        DrAiSpacing.md,
        DrAiSpacing.sm,
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          _copy(context, 'Payment Requests', '支付申请'),
                          style: Theme.of(context).textTheme.headlineMedium
                              ?.copyWith(
                                color: DrAiColors.white,
                                fontWeight: FontWeight.w900,
                              ),
                        ),
                        Text(
                          _copy(
                            context,
                            'Prepare an itemized request and track its human-review status.',
                            '准备明细申请，并跟踪人工审核状态。',
                          ),
                          style: const TextStyle(color: DrAiColors.white),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: _copy(context, 'Refresh workspace', '刷新工作台'),
                    onPressed: onRefresh,
                    color: DrAiColors.white,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              SegmentedButton<_WorkspaceView>(
                style: ButtonStyle(
                  foregroundColor: WidgetStateProperty.resolveWith(
                    (states) => states.contains(WidgetState.selected)
                        ? DrAiColors.sectionHeader
                        : DrAiColors.white,
                  ),
                  backgroundColor: WidgetStateProperty.resolveWith(
                    (states) => states.contains(WidgetState.selected)
                        ? DrAiColors.patientAccent
                        : Colors.transparent,
                  ),
                  side: const WidgetStatePropertyAll(
                    BorderSide(color: DrAiColors.white),
                  ),
                ),
                segments: <ButtonSegment<_WorkspaceView>>[
                  ButtonSegment<_WorkspaceView>(
                    value: _WorkspaceView.create,
                    icon: const Icon(Icons.add_card_outlined),
                    label: Text(_copy(context, 'New request', '新建申请')),
                  ),
                  ButtonSegment<_WorkspaceView>(
                    value: _WorkspaceView.history,
                    icon: const Icon(Icons.history_outlined),
                    label: Text(_copy(context, 'Request history', '申请记录')),
                  ),
                ],
                selected: <_WorkspaceView>{view},
                onSelectionChanged: (value) => onViewChanged(value.first),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProgressHeader extends StatelessWidget {
  const _ProgressHeader({
    required this.currentStep,
    required this.onStepSelected,
  });

  final int currentStep;
  final ValueChanged<int> onStepSelected;

  @override
  Widget build(BuildContext context) {
    final labels = <String>[
      _copy(context, 'Patient & event', '患者与临床事件'),
      _copy(context, 'Care items', '诊疗项目'),
      _copy(context, 'Payer & summary', '支付方与说明'),
      _copy(context, 'Review', '确认提交'),
    ];
    return Container(
      color: DrAiColors.white,
      padding: const EdgeInsets.symmetric(
        horizontal: DrAiSpacing.md,
        vertical: DrAiSpacing.sm,
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1120),
          child: LayoutBuilder(
            builder: (context, constraints) {
              if (constraints.maxWidth < 680) {
                return Row(
                  children: <Widget>[
                    Expanded(
                      child: Text(
                        '${_copy(context, 'Step', '步骤')} ${currentStep + 1}/4 · ${labels[currentStep]}',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
                    const SizedBox(width: DrAiSpacing.sm),
                    SizedBox(
                      width: 100,
                      child: LinearProgressIndicator(
                        value: (currentStep + 1) / 4,
                        minHeight: 7,
                        borderRadius: BorderRadius.circular(999),
                      ),
                    ),
                  ],
                );
              }
              return Row(
                children: List<Widget>.generate(labels.length, (index) {
                  final active = index == currentStep;
                  final complete = index < currentStep;
                  return Expanded(
                    child: InkWell(
                      onTap: () => onStepSelected(index),
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: <Widget>[
                            CircleAvatar(
                              radius: 14,
                              backgroundColor: active || complete
                                  ? DrAiColors.brand
                                  : DrAiColors.outline,
                              foregroundColor: active || complete
                                  ? DrAiColors.white
                                  : DrAiColors.inkSecondary,
                              child: complete
                                  ? const Icon(Icons.check, size: 16)
                                  : Text('${index + 1}'),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                labels[index],
                                style: TextStyle(
                                  color: active
                                      ? DrAiColors.brandDark
                                      : DrAiColors.inkSecondary,
                                  fontWeight: active
                                      ? FontWeight.w800
                                      : FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _StepCard extends StatelessWidget {
  const _StepCard({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: DrAiColors.white,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: child,
      ),
    );
  }
}

class _PatientAndEventStep extends StatelessWidget {
  const _PatientAndEventStep({
    required this.patients,
    required this.ledger,
    required this.bundle,
    required this.searchController,
    required this.selectedPatientId,
    required this.selectedEventId,
    required this.onSearchChanged,
    required this.onRetryPatients,
    required this.onRetryLedger,
    required this.onPatientSelected,
    required this.onEventSelected,
  });

  final AsyncValue<PatientListData> patients;
  final AsyncValue<CareCostLedgerData>? ledger;
  final AsyncValue<PatientCareBundle>? bundle;
  final TextEditingController searchController;
  final String? selectedPatientId;
  final String? selectedEventId;
  final ValueChanged<String> onSearchChanged;
  final VoidCallback onRetryPatients;
  final VoidCallback? onRetryLedger;
  final ValueChanged<String> onPatientSelected;
  final ValueChanged<String> onEventSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _StepTitle(
          title: _copy(
            context,
            'Choose the patient and Clinical Event',
            '选择患者与临床事件',
          ),
          description: _copy(
            context,
            'Only patients assigned to your authenticated account are available here.',
            '此处仅显示当前登录医生获授权访问的患者。',
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth >= 820;
            final patientPane = _PatientPicker(
              patients: patients,
              controller: searchController,
              selectedPatientId: selectedPatientId,
              onSearchChanged: onSearchChanged,
              onRetry: onRetryPatients,
              onSelected: onPatientSelected,
            );
            final eventPane = _EventPicker(
              ledger: ledger,
              bundle: bundle,
              selectedEventId: selectedEventId,
              onRetry: onRetryLedger,
              onSelected: onEventSelected,
            );
            if (!wide) {
              return Column(
                children: <Widget>[
                  patientPane,
                  const SizedBox(height: DrAiSpacing.lg),
                  eventPane,
                ],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(flex: 4, child: patientPane),
                const SizedBox(width: DrAiSpacing.lg),
                Expanded(flex: 6, child: eventPane),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _PatientPicker extends StatelessWidget {
  const _PatientPicker({
    required this.patients,
    required this.controller,
    required this.selectedPatientId,
    required this.onSearchChanged,
    required this.onRetry,
    required this.onSelected,
  });

  final AsyncValue<PatientListData> patients;
  final TextEditingController controller;
  final String? selectedPatientId;
  final ValueChanged<String> onSearchChanged;
  final VoidCallback onRetry;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          _copy(context, '1. Assigned patient', '1. 已分配患者'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        TextField(
          key: const Key('payment-request-patient-search'),
          controller: controller,
          onChanged: onSearchChanged,
          decoration: InputDecoration(
            labelText: _copy(context, 'Search assigned patients', '搜索已分配患者'),
            prefixIcon: const Icon(Icons.search),
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        patients.when(
          loading: () => const Padding(
            padding: EdgeInsets.all(DrAiSpacing.lg),
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (error, stackTrace) => _InlineError(
            message: _copy(
              context,
              'Assigned patients could not be loaded.',
              '无法加载已分配患者。',
            ),
            onRetry: onRetry,
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return _InlineEmpty(
                icon: Icons.person_search_outlined,
                title: _copy(context, 'No assigned patients found', '未找到已分配患者'),
                body: _copy(
                  context,
                  'Change the search or connect a patient from Patient Management.',
                  '请更改搜索条件，或前往患者管理连接患者。',
                ),
              );
            }
            return ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 330),
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: data.items.length,
                separatorBuilder: (_, _) =>
                    const Divider(height: 1, color: DrAiColors.outline),
                itemBuilder: (context, index) {
                  final patient = data.items[index];
                  final selected = patient.patientId == selectedPatientId;
                  return ListTile(
                    key: Key('payment-request-patient-${patient.patientId}'),
                    selected: selected,
                    selectedTileColor: DrAiColors.brandSoft,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    leading: CircleAvatar(
                      backgroundColor: selected
                          ? DrAiColors.brand
                          : DrAiColors.pageBackground,
                      foregroundColor: selected
                          ? DrAiColors.white
                          : DrAiColors.brandDark,
                      child: Text(
                        patient.displayName.trim().isEmpty
                            ? '?'
                            : patient.displayName.trim().characters.first,
                      ),
                    ),
                    title: Text(
                      patient.displayName,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    subtitle: Text(
                      _copy(
                        context,
                        'Patient ID · ${patient.syntheticIdentifier}',
                        '患者编号 · ${patient.syntheticIdentifier}',
                      ),
                    ),
                    trailing: selected
                        ? const Icon(
                            Icons.check_circle,
                            color: DrAiColors.brand,
                          )
                        : null,
                    onTap: () => onSelected(patient.patientId),
                  );
                },
              ),
            );
          },
        ),
      ],
    );
  }
}

class _EventPicker extends StatelessWidget {
  const _EventPicker({
    required this.ledger,
    required this.bundle,
    required this.selectedEventId,
    required this.onRetry,
    required this.onSelected,
  });

  final AsyncValue<CareCostLedgerData>? ledger;
  final AsyncValue<PatientCareBundle>? bundle;
  final String? selectedEventId;
  final VoidCallback? onRetry;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          _copy(context, '2. Clinical Event', '2. 临床事件'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        if (ledger == null)
          _InlineEmpty(
            icon: Icons.arrow_back_outlined,
            title: _copy(context, 'Select a patient first', '请先选择患者'),
            body: _copy(
              context,
              'Their authorized care-and-cost ledger will load here.',
              '获授权的诊疗费用记录将显示在此处。',
            ),
          )
        else
          ledger!.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(DrAiSpacing.xl),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (error, stackTrace) => _InlineError(
              message: _copy(
                context,
                'The patient ledger could not be loaded.',
                '无法加载该患者的费用记录。',
              ),
              onRetry: onRetry!,
            ),
            data: (data) {
              if (data.events.isEmpty) {
                return _InlineEmpty(
                  icon: Icons.event_busy_outlined,
                  title: _copy(
                    context,
                    'No Clinical Events available',
                    '暂无可用临床事件',
                  ),
                  body: _copy(
                    context,
                    'Create a Clinical Event and add care-cost items in Patient Management before preparing a request.',
                    '请先在患者管理中创建临床事件并添加诊疗费用项目。',
                  ),
                );
              }
              final clinicalEvents =
                  bundle?.asData?.value.clinicalEvents ??
                  const <ClinicalEventItem>[];
              return Column(
                children: <Widget>[
                  for (final event in data.events) ...<Widget>[
                    _ClinicalEventCard(
                      event: event,
                      clinicalEvent: clinicalEvents
                          .where((item) => item.id == event.clinicalEventId)
                          .firstOrNull,
                      selected: event.clinicalEventId == selectedEventId,
                      onTap: () => onSelected(event.clinicalEventId),
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                  ],
                ],
              );
            },
          ),
      ],
    );
  }
}

class _ClinicalEventCard extends StatelessWidget {
  const _ClinicalEventCard({
    required this.event,
    required this.clinicalEvent,
    required this.selected,
    required this.onTap,
  });

  final CareCostEventData event;
  final ClinicalEventItem? clinicalEvent;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final dates = <String>[
      if (clinicalEvent?.onsetDate != null)
        '${_copy(context, 'Onset', '起始')} ${clinicalEvent!.onsetDate}',
      if (clinicalEvent != null)
        '${_copy(context, 'Updated', '更新')} ${_date(context, clinicalEvent!.updatedAt)}',
    ];
    return Material(
      color: selected ? DrAiColors.brandSoft : DrAiColors.white,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: selected ? DrAiColors.brand : DrAiColors.outline,
          width: selected ? 2 : 1,
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: InkWell(
        key: Key('payment-request-event-${event.clinicalEventId}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      event.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                  ),
                  _StatusChip(status: event.status),
                ],
              ),
              if (dates.isNotEmpty) ...<Widget>[
                const SizedBox(height: 4),
                Text(
                  dates.join(' · '),
                  style: const TextStyle(color: DrAiColors.inkSecondary),
                ),
              ],
              const SizedBox(height: DrAiSpacing.sm),
              Wrap(
                spacing: DrAiSpacing.md,
                runSpacing: 4,
                children: <Widget>[
                  Text(
                    '${event.items.length} ${_copy(context, 'items', '个项目')}',
                  ),
                  Text(
                    '${_copy(context, 'Requested', '申请')} ${_money(event.currency, event.payerRequestedTotalMinor)}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  Text(
                    '${_copy(context, 'Patient', '个人承担')} ${_money(event.currency, event.patientResponsibilityTotalMinor)}',
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ItemSelectionStep extends StatelessWidget {
  const _ItemSelectionStep({
    required this.event,
    required this.submittedItemIds,
    required this.selectedItemIds,
    required this.onSelectionChanged,
  });

  final CareCostEventData? event;
  final Set<String> submittedItemIds;
  final Set<String> selectedItemIds;
  final void Function(String id, bool selected) onSelectionChanged;

  @override
  Widget build(BuildContext context) {
    final items = event?.items ?? const <CareCostItemData>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _StepTitle(
          title: _copy(
            context,
            'Select eligible care-cost items',
            '选择符合条件的诊疗费用项目',
          ),
          description: _copy(
            context,
            'Choose each linked clinical service explicitly. Pending, invalid, cancelled, and previously submitted rows cannot be selected.',
            '请逐项选择已关联的临床服务。费用待补、金额无效、已取消或已提交的项目不可选择。',
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        if (items.isEmpty)
          _InlineEmpty(
            icon: Icons.receipt_long_outlined,
            title: _copy(context, 'No care-cost items', '暂无诊疗费用项目'),
            body: _copy(
              context,
              'Add financial details while creating a billable clinical record in Patient Management.',
              '请在患者管理中创建可计费临床记录时填写费用信息。',
            ),
          )
        else ...<Widget>[
          for (final item in items) ...<Widget>[
            _SelectableCareItem(
              item: item,
              selected: selectedItemIds.contains(item.id),
              previouslySubmitted: submittedItemIds.contains(item.id),
              onChanged: (value) => onSelectionChanged(item.id, value ?? false),
            ),
            const SizedBox(height: DrAiSpacing.sm),
          ],
          Container(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            decoration: BoxDecoration(
              color: DrAiColors.brandSoft,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: <Widget>[
                const Icon(Icons.checklist, color: DrAiColors.brandDark),
                const SizedBox(width: DrAiSpacing.sm),
                Expanded(
                  child: Text(
                    _copy(
                      context,
                      '${selectedItemIds.length} item(s) selected. Final totals are reconciled by the server.',
                      '已选择 ${selectedItemIds.length} 个项目。最终金额由服务器核算。',
                    ),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _SelectableCareItem extends StatelessWidget {
  const _SelectableCareItem({
    required this.item,
    required this.selected,
    required this.previouslySubmitted,
    required this.onChanged,
  });

  final CareCostItemData item;
  final bool selected;
  final bool previouslySubmitted;
  final ValueChanged<bool?> onChanged;

  @override
  Widget build(BuildContext context) {
    final cancelled = item.status == 'cancelled';
    final eligible = item.submissionEligible && !previouslySubmitted;
    return Material(
      color: selected ? DrAiColors.brandSoft : DrAiColors.white,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: selected ? DrAiColors.brand : DrAiColors.outline,
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: CheckboxListTile(
        key: Key('payment-request-item-${item.id}'),
        value: selected,
        onChanged: eligible ? onChanged : null,
        controlAffinity: ListTileControlAffinity.leading,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.sm,
          vertical: 4,
        ),
        title: Row(
          children: <Widget>[
            Icon(_itemIcon(item.itemType), size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                item.label,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
            if (previouslySubmitted)
              _SmallLabel(
                text: _copy(context, 'Already submitted', '已提交'),
                color: DrAiColors.inkSecondary,
              )
            else if (cancelled)
              _SmallLabel(
                text: _copy(context, 'Cancelled', '已取消'),
                color: DrAiColors.danger,
              )
            else if (!item.submissionEligible)
              _SmallLabel(
                text: _blockedReason(context, item.ineligibilityReason),
                color: DrAiColors.danger,
              ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 7),
          child: Wrap(
            spacing: DrAiSpacing.md,
            runSpacing: 6,
            children: <Widget>[
              Text(
                '${_copy(context, 'Source', '来源')} '
                '${_statusText(context, item.sourceCategory)}',
              ),
              Text(
                '${_copy(context, 'Service status', '服务状态')} '
                '${_statusText(context, item.sourceStatus)}',
              ),
              Text(
                '${_copy(context, 'Service date', '服务日期')} '
                '${_date(context, item.performedAt ?? item.scheduledAt ?? item.orderedAt ?? item.serviceDate)}',
              ),
              Text(
                '${_copy(context, 'Pricing', '计价状态')} '
                '${_statusText(context, item.pricingState)}',
              ),
              Text(
                '${_copy(context, 'Actual', '实际')} ${_money(item.currency, item.actualCostMinor)}',
              ),
              Text(
                '${_copy(context, 'Requested', '申请')} ${_money(item.currency, item.payerRequestedMinor)}',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              Text(
                '${_copy(context, 'Patient', '个人承担')} ${_money(item.currency, item.patientResponsibilityMinor)}',
              ),
              Text(
                _copy(
                  context,
                  'Versioned AI support is shown in the intelligence artifact',
                  '版本化 AI 支持显示在智能产物中',
                ),
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

String _blockedReason(BuildContext context, String? reason) {
  return switch (reason) {
    'cost_pending' => _copy(context, 'Cost pending', '费用待补'),
    'allocation_incomplete' => _copy(
      context,
      'Allocation incomplete',
      '金额分配不完整',
    ),
    'unsupported_currency' => _copy(context, 'Unsupported currency', '币种不支持'),
    'unlinked_legacy_item' => _copy(context, 'Source link missing', '缺少临床来源关联'),
    'source_mismatch' => _copy(context, 'Source mismatch', '临床来源不一致'),
    'source_ineligible' => _copy(context, 'Source not eligible', '临床来源不可提交'),
    'already_submitted' => _copy(context, 'Already submitted', '已提交'),
    'total_required' => _copy(context, 'Total required', '缺少总费用'),
    'cancelled' => _copy(context, 'Cancelled', '已取消'),
    _ => _copy(context, 'Not eligible', '暂不可提交'),
  };
}

class _PayerAndSummaryStep extends StatelessWidget {
  const _PayerAndSummaryStep({
    required this.organizations,
    required this.selectedOrganizationId,
    required this.summaryController,
    required this.onOrganizationChanged,
    required this.onRetry,
    required this.onSummaryChanged,
  });

  final AsyncValue<List<PayerOrganizationData>> organizations;
  final String? selectedOrganizationId;
  final TextEditingController summaryController;
  final ValueChanged<String?> onOrganizationChanged;
  final VoidCallback onRetry;
  final ValueChanged<String> onSummaryChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _StepTitle(
          title: _copy(
            context,
            'Choose the payer and write your summary',
            '选择支付机构并填写申请说明',
          ),
          description: _copy(
            context,
            'You own the clinical rationale. Dr. AI does not diagnose the patient or determine medical necessity here.',
            '临床理由由医生负责。Dr. AI 不在此诊断患者或判断医疗必要性。',
          ),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        Text(
          _copy(context, 'Payer organization', '支付机构'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        organizations.when(
          loading: () => const LinearProgressIndicator(),
          error: (error, stackTrace) => _InlineError(
            message: _copy(
              context,
              'Payer organizations could not be loaded.',
              '无法加载支付机构。',
            ),
            onRetry: onRetry,
          ),
          data: (items) {
            if (items.isEmpty) {
              return _InlineEmpty(
                icon: Icons.account_balance_outlined,
                title: _copy(
                  context,
                  'No payer organization available',
                  '暂无可用支付机构',
                ),
                body: _copy(
                  context,
                  'A payer organization must be configured before a request can be submitted.',
                  '提交申请前必须先配置支付机构。',
                ),
              );
            }
            return DropdownButtonFormField<String>(
              key: const Key('payment-request-payer'),
              initialValue: selectedOrganizationId,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: _copy(context, 'Select organization', '选择机构'),
                prefixIcon: const Icon(Icons.account_balance_outlined),
              ),
              items: items
                  .map(
                    (organization) => DropdownMenuItem<String>(
                      value: organization.id,
                      child: Text(
                        '${organization.name} · ${_organizationType(context, organization.organizationType)}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  )
                  .toList(),
              onChanged: onOrganizationChanged,
            );
          },
        ),
        const SizedBox(height: DrAiSpacing.lg),
        Text(
          _copy(context, 'Doctor-authored request summary', '医生填写的申请说明'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        TextField(
          key: const Key('payment-request-summary'),
          controller: summaryController,
          onChanged: onSummaryChanged,
          minLines: 5,
          maxLines: 8,
          maxLength: 4000,
          decoration: InputDecoration(
            labelText: _copy(
              context,
              'Clinical context and reason for this request',
              '临床背景与申请理由',
            ),
            helperText: _copy(
              context,
              'At least 20 characters. Include the relevant care context and why these selected services are being submitted.',
              '至少 20 个字符。请说明相关诊疗背景及提交所选服务的原因。',
            ),
            alignLabelWithHint: true,
          ),
        ),
      ],
    );
  }
}

class _ReviewStep extends StatelessWidget {
  const _ReviewStep({
    required this.patient,
    required this.event,
    required this.organization,
    required this.items,
    required this.summary,
    required this.confirmed,
    required this.submitting,
    required this.submissionError,
    required this.createdRequest,
    required this.onConfirmedChanged,
    required this.onSubmit,
    required this.onViewHistory,
  });

  final PatientSummary? patient;
  final CareCostEventData? event;
  final PayerOrganizationData? organization;
  final List<CareCostItemData> items;
  final String summary;
  final bool confirmed;
  final bool submitting;
  final String? submissionError;
  final PayerRequestData? createdRequest;
  final ValueChanged<bool?>? onConfirmedChanged;
  final VoidCallback? onSubmit;
  final VoidCallback onViewHistory;

  @override
  Widget build(BuildContext context) {
    if (createdRequest != null) {
      return _SuccessState(
        request: createdRequest!,
        onViewHistory: onViewHistory,
      );
    }
    final currency = items.isEmpty ? 'CNY' : items.first.currency;
    final requested = items.fold<int>(
      0,
      (total, item) => total + item.payerRequestedMinor,
    );
    final patientResponsibility = items.fold<int>(
      0,
      (total, item) => total + item.patientResponsibilityMinor,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _StepTitle(
          title: _copy(context, 'Review before submitting', '提交前确认'),
          description: _copy(
            context,
            'Submitting creates an immutable line-item snapshot. The server remains authoritative for the final requested total.',
            '提交后将创建不可变更的项目快照。最终申请总额以服务器核算为准。',
          ),
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _ReviewFacts(
          patient: patient,
          event: event,
          organization: organization,
          itemCount: items.length,
        ),
        const SizedBox(height: DrAiSpacing.lg),
        Text(
          _copy(context, 'Selected line items', '所选明细项目'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        for (final item in items)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(_itemIcon(item.itemType)),
            title: Text(item.label),
            subtitle: Text(_date(context, item.serviceDate)),
            trailing: Text(
              _money(item.currency, item.payerRequestedMinor),
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        const Divider(),
        Wrap(
          spacing: DrAiSpacing.xl,
          runSpacing: DrAiSpacing.sm,
          children: <Widget>[
            _ReviewTotal(
              label: _copy(context, 'Requested preview', '申请金额预览'),
              value: _money(currency, requested),
            ),
            _ReviewTotal(
              label: _copy(context, 'Patient responsibility', '个人承担'),
              value: _money(currency, patientResponsibility),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        Text(
          _copy(context, 'Doctor summary', '医生申请说明'),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        SelectableText(summary),
        const SizedBox(height: DrAiSpacing.lg),
        CheckboxListTile(
          key: const Key('payment-request-confirmation'),
          value: confirmed,
          onChanged: onConfirmedChanged,
          controlAffinity: ListTileControlAffinity.leading,
          contentPadding: EdgeInsets.zero,
          title: Text(
            _copy(
              context,
              'I confirm that the patient, Clinical Event, payer, selected items, and doctor-authored summary are correct.',
              '我确认患者、临床事件、支付机构、所选项目及医生填写的说明均正确。',
            ),
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        if (submissionError != null) ...<Widget>[
          const SizedBox(height: DrAiSpacing.sm),
          _InlineError(message: submissionError!, onRetry: onSubmit),
        ],
        const SizedBox(height: DrAiSpacing.md),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            key: const Key('payment-request-submit'),
            onPressed: onSubmit,
            icon: submitting
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: DrAiColors.white,
                    ),
                  )
                : const Icon(Icons.lock_outline),
            label: Text(
              submitting
                  ? _copy(context, 'Submitting…', '正在提交…')
                  : _copy(
                      context,
                      'Confirm and create immutable request',
                      '确认并创建不可变更申请',
                    ),
            ),
          ),
        ),
      ],
    );
  }
}

class _RequestHistory extends StatefulWidget {
  const _RequestHistory({
    required this.requests,
    required this.onRetry,
    this.initialRequestId,
  });

  final AsyncValue<List<PayerRequestData>> requests;
  final VoidCallback onRetry;
  final String? initialRequestId;

  @override
  State<_RequestHistory> createState() => _RequestHistoryState();
}

class _RequestHistoryState extends State<_RequestHistory> {
  _RequestHistoryFilter _filter = _RequestHistoryFilter.all;

  @override
  Widget build(BuildContext context) {
    return widget.requests.when(
      loading: () => const DashboardLoadingView(),
      error: (error, stackTrace) => DashboardErrorView(
        message: error.toString(),
        onRetry: widget.onRetry,
      ),
      data: (items) {
        final filteredItems = items
            .where(
              (request) =>
                  widget.initialRequestId == null ||
                  request.id == widget.initialRequestId,
            )
            .where((request) => _matchesHistoryFilter(request, _filter))
            .toList();
        return RefreshIndicator(
          onRefresh: () async => widget.onRetry(),
          child: ListView(
            key: const ValueKey<String>('payment-request-history'),
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1120),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        _copy(context, 'Request history', '申请记录'),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _copy(
                          context,
                          'Track every submitted request through its current human-review outcome. Accepted or rejected does not mean paid or finally adjudicated.',
                          '跟踪每份已提交申请的当前人工审核结果。“已接受”或“已拒绝”不代表已付款或最终裁定。',
                        ),
                        style: const TextStyle(color: DrAiColors.inkSecondary),
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      if (widget.initialRequestId == null)
                        Wrap(
                          spacing: DrAiSpacing.xs,
                          runSpacing: DrAiSpacing.xs,
                          children: <Widget>[
                            for (final filter in _RequestHistoryFilter.values)
                              ChoiceChip(
                                key: Key(
                                  'payment-request-filter-${filter.name}',
                                ),
                                selected: _filter == filter,
                                label: Text(
                                  '${_historyFilterLabel(context, filter)} '
                                  '(${items.where((request) => _matchesHistoryFilter(request, filter)).length})',
                                ),
                                onSelected: (_) =>
                                    setState(() => _filter = filter),
                              ),
                          ],
                        ),
                      const SizedBox(height: DrAiSpacing.lg),
                      if (filteredItems.isEmpty)
                        _InlineEmpty(
                          icon: Icons.inbox_outlined,
                          title: _copy(
                            context,
                            'No requests in this status',
                            '此状态下暂无申请',
                          ),
                          body: _filter == _RequestHistoryFilter.all
                              ? _copy(
                                  context,
                                  'Create the first payment request from the New request tab.',
                                  '请从“新建申请”标签创建第一份支付申请。',
                                )
                              : _copy(
                                  context,
                                  'Choose another status to continue reviewing the request history.',
                                  '请选择其他状态继续查看申请记录。',
                                ),
                        )
                      else
                        for (final request in filteredItems) ...<Widget>[
                          _HistoryCard(request: request),
                          const SizedBox(height: DrAiSpacing.md),
                        ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _HistoryCard extends ConsumerWidget {
  const _HistoryCard({required this.request});
  final PayerRequestData request;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patientResponsibility = request.lines.fold<int>(
      0,
      (total, line) => total + line.patientResponsibilityMinor,
    );
    final latestReview = request.reviews.isEmpty ? null : request.reviews.last;
    return Material(
      key: Key('payment-request-history-${request.id}'),
      color: DrAiColors.white,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(16),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.md,
          vertical: DrAiSpacing.xs,
        ),
        childrenPadding: const EdgeInsets.fromLTRB(
          DrAiSpacing.md,
          0,
          DrAiSpacing.md,
          DrAiSpacing.md,
        ),
        title: Row(
          children: <Widget>[
            Expanded(
              child: Text(
                request.clinicalEventTitle,
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
            _StatusChip(status: request.status),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 7),
          child: Wrap(
            spacing: DrAiSpacing.md,
            runSpacing: 5,
            children: <Widget>[
              Text(request.patientDisplayName),
              Text(request.payerOrganization.name),
              Text(_date(context, request.createdAt)),
              Text(
                _money(request.currency, request.requestedTotalMinor),
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ],
          ),
        ),
        children: <Widget>[
          if (request.reviewedAt != null ||
              request.status != 'submitted') ...<Widget>[
            _ReviewOutcomeBanner(request: request, latestReview: latestReview),
            const SizedBox(height: DrAiSpacing.md),
          ],
          Align(
            alignment: Alignment.centerLeft,
            child: Text(request.doctorSummary),
          ),
          const SizedBox(height: DrAiSpacing.md),
          for (final line in request.lines)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(_itemIcon(line.itemType), size: 20),
              title: Text(line.label),
              subtitle: Text(_date(context, line.serviceDate)),
              trailing: Text(
                _money(line.currency, line.requestedMinor),
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          const Divider(),
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  '${_copy(context, 'Patient responsibility', '个人承担')} · ${_money(request.currency, patientResponsibility)}',
                ),
              ),
              Text(
                _copy(context, 'AI: Not evaluated', 'AI：尚未评估'),
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Align(
            alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              key: Key('doctor-intelligence-${request.id}'),
              onPressed: () => context.go(
                '/doctor/payer-requests/${request.id}/intelligence'
                '?patient=${request.patientId}&event=${request.clinicalEventId}',
              ),
              icon: const Icon(Icons.fact_check_outlined),
              label: Text(
                _copy(
                  context,
                  'Review Clinical Event intelligence',
                  '审核临床事件智能',
                ),
              ),
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.tonalIcon(
              key: Key('doctor-payer-response-${request.id}'),
              onPressed:
                  request.status == 'accepted' ||
                      request.status == 'rejected' ||
                      request.status == 'closed'
                  ? null
                  : () => _showDoctorResponseDialog(context, ref, request),
              icon: const Icon(Icons.add_comment_outlined),
              label: Text(
                _copy(context, 'Add justification or response', '添加理由或补充说明'),
              ),
            ),
          ),
          if (request.doctorResponses.isNotEmpty) ...<Widget>[
            const Divider(height: DrAiSpacing.lg),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                _copy(context, 'Doctor response history', '医生补充说明记录'),
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
            for (final entry in request.doctorResponses.indexed)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.history_edu_outlined),
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
          if (request.reviews.isNotEmpty) ...<Widget>[
            const Divider(height: DrAiSpacing.lg),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                _copy(context, 'Payer transition history', '支付方状态变更记录'),
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
            ),
            for (final entry in request.reviews.indexed)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.fact_check_outlined),
                title: Text(
                  '${_statusText(context, entry.$2.fromStatus)} → '
                  '${_statusText(context, entry.$2.toStatus)}',
                ),
                subtitle: Text(
                  '${entry.$2.reviewerDisplayName} · ${entry.$2.reviewerTitle} · '
                  '${formatProductHistoryTime(context, entry.$2.createdAt)}\n'
                  '${_copy(context, 'Recorded reason', '记录原因')}: '
                  '${humanizeProductValue(entry.$2.reasonCode)}',
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
        ],
      ),
    );
  }
}

Future<void> _showDoctorResponseDialog(
  BuildContext context,
  WidgetRef ref,
  PayerRequestData request,
) async {
  final controller = TextEditingController();
  var responseType = request.status == 'clarification_requested'
      ? 'clarification_response'
      : 'justification';
  String? error;
  await showDialog<void>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setState) => AlertDialog(
        title: Text(_copy(context, 'Add doctor response', '添加医生补充说明')),
        content: SizedBox(
          width: 520,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              DropdownButtonFormField<String>(
                initialValue: responseType,
                items:
                    const <String>[
                          'justification',
                          'clarification_response',
                          'additional_information',
                        ]
                        .map(
                          (value) => DropdownMenuItem(
                            value: value,
                            child: Text(
                              _doctorResponseTypeText(context, value),
                            ),
                          ),
                        )
                        .toList(),
                onChanged: (value) => responseType = value ?? responseType,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              TextField(
                key: const Key('doctor-payer-response-summary'),
                controller: controller,
                minLines: 4,
                maxLines: 8,
                decoration: InputDecoration(
                  labelText: _copy(
                    context,
                    'Clinical context and justification',
                    '临床背景与理由',
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
                    .appendDoctorPayerResponse(
                      requestId: request.id,
                      expectedVersion: request.version,
                      responseType: responseType,
                      summary: controller.text.trim(),
                      idempotencyKey:
                          'doctor-response-${request.id}-${DateTime.now().microsecondsSinceEpoch}',
                    );
                ref.invalidate(doctorPayerRequestsProvider);
                if (dialogContext.mounted) Navigator.pop(dialogContext);
              } on ApiError catch (apiError) {
                setState(() => error = apiError.message);
              }
            },
            child: Text(_copy(context, 'Save response', '保存补充说明')),
          ),
        ],
      ),
    ),
  );
  controller.dispose();
}

class _ReviewOutcomeBanner extends StatelessWidget {
  const _ReviewOutcomeBanner({
    required this.request,
    required this.latestReview,
  });

  final PayerRequestData request;
  final PayerReviewData? latestReview;

  @override
  Widget build(BuildContext context) {
    final isRejected = request.status == 'rejected';
    final isAccepted = request.status == 'accepted';
    final color = isRejected
        ? DrAiColors.danger
        : isAccepted
        ? DrAiColors.brand
        : DrAiColors.inkSecondary;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(
                isRejected
                    ? Icons.cancel_outlined
                    : isAccepted
                    ? Icons.check_circle_outline
                    : Icons.fact_check_outlined,
                color: color,
                size: 20,
              ),
              const SizedBox(width: DrAiSpacing.xs),
              Expanded(
                child: Text(
                  _reviewOutcomeTitle(context, request.status),
                  style: TextStyle(color: color, fontWeight: FontWeight.w900),
                ),
              ),
              if (request.reviewedAt != null)
                Text(
                  _date(context, request.reviewedAt!),
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            _reviewOutcomeDescription(context, request.status),
            style: const TextStyle(color: DrAiColors.inkSecondary),
          ),
          if (latestReview != null) ...<Widget>[
            const SizedBox(height: 4),
            Text(
              '${_copy(context, 'Recorded reason', '记录原因')} · '
              '${humanizeProductValue(latestReview!.reasonCode)}',
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _StepActions extends StatelessWidget {
  const _StepActions({
    required this.step,
    required this.canContinue,
    required this.onBack,
    required this.onContinue,
  });

  final int step;
  final bool canContinue;
  final VoidCallback? onBack;
  final VoidCallback? onContinue;

  @override
  Widget build(BuildContext context) {
    if (step == 3) return const SizedBox.shrink();
    return Container(
      color: DrAiColors.white,
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      child: SafeArea(
        top: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1120),
            child: Row(
              children: <Widget>[
                if (onBack != null)
                  OutlinedButton.icon(
                    onPressed: onBack,
                    icon: const Icon(Icons.arrow_back),
                    label: Text(_copy(context, 'Back', '上一步')),
                  ),
                const Spacer(),
                FilledButton.icon(
                  key: const Key('payment-request-continue'),
                  onPressed: canContinue ? onContinue : null,
                  icon: const Icon(Icons.arrow_forward),
                  label: Text(_copy(context, 'Continue', '继续')),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ReviewFacts extends StatelessWidget {
  const _ReviewFacts({
    required this.patient,
    required this.event,
    required this.organization,
    required this.itemCount,
  });

  final PatientSummary? patient;
  final CareCostEventData? event;
  final PayerOrganizationData? organization;
  final int itemCount;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: DrAiSpacing.sm,
      runSpacing: DrAiSpacing.sm,
      children: <Widget>[
        _Fact(
          icon: Icons.person_outline,
          label: _copy(context, 'Patient', '患者'),
          value: patient?.displayName ?? '—',
        ),
        _Fact(
          icon: Icons.event_note_outlined,
          label: _copy(context, 'Clinical Event', '临床事件'),
          value: event?.title ?? '—',
        ),
        _Fact(
          icon: Icons.account_balance_outlined,
          label: _copy(context, 'Payer', '支付机构'),
          value: organization?.name ?? '—',
        ),
        _Fact(
          icon: Icons.checklist,
          label: _copy(context, 'Selected items', '所选项目'),
          value: '$itemCount',
        ),
      ],
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minWidth: 210),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: DrAiColors.pageBackground,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, color: DrAiColors.brand),
          const SizedBox(width: 8),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  label,
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
                Text(
                  value,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ReviewTotal extends StatelessWidget {
  const _ReviewTotal({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(label, style: const TextStyle(color: DrAiColors.inkSecondary)),
        Text(
          value,
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
        ),
      ],
    );
  }
}

class _SuccessState extends StatelessWidget {
  const _SuccessState({required this.request, required this.onViewHistory});

  final PayerRequestData request;
  final VoidCallback onViewHistory;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      key: const Key('payment-request-success'),
      liveRegion: true,
      child: Column(
        children: <Widget>[
          const CircleAvatar(
            radius: 34,
            backgroundColor: DrAiColors.brandSoft,
            foregroundColor: DrAiColors.brandDark,
            child: Icon(Icons.check, size: 36),
          ),
          const SizedBox(height: DrAiSpacing.md),
          Text(
            _copy(context, 'Payment request submitted', '支付申请已提交'),
            style: Theme.of(
              context,
            ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          Text(
            _copy(
              context,
              'The immutable snapshot was created successfully. Its server-confirmed requested total is ${_money(request.currency, request.requestedTotalMinor)}.',
              '不可变更快照已成功创建。服务器确认的申请总额为 ${_money(request.currency, request.requestedTotalMinor)}。',
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: DrAiSpacing.lg),
          _StatusChip(status: request.status),
          const SizedBox(height: DrAiSpacing.lg),
          FilledButton.icon(
            onPressed: onViewHistory,
            icon: const Icon(Icons.history),
            label: Text(_copy(context, 'View request history', '查看申请记录')),
          ),
        ],
      ),
    );
  }
}

class _StepTitle extends StatelessWidget {
  const _StepTitle({required this.title, required this.description});
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 4),
        Text(
          description,
          style: const TextStyle(color: DrAiColors.inkSecondary),
        ),
      ],
    );
  }
}

class _InlineEmpty extends StatelessWidget {
  const _InlineEmpty({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.lg),
      decoration: BoxDecoration(
        color: DrAiColors.pageBackground,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: <Widget>[
          Icon(icon, color: DrAiColors.inkSecondary, size: 30),
          const SizedBox(height: 8),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(
            body,
            textAlign: TextAlign.center,
            style: const TextStyle(color: DrAiColors.inkSecondary),
          ),
        ],
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message, required this.onRetry});
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.md),
      decoration: BoxDecoration(
        color: DrAiColors.danger.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.error_outline, color: DrAiColors.danger),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(child: Text(message)),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: Text(_copy(context, 'Retry', '重试')),
            ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'accepted' || 'closed' => DrAiColors.brand,
      'clarification_requested' => Colors.orange.shade800,
      'rejected' || 'escalated' => DrAiColors.danger,
      _ => DrAiColors.brandDark,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        _statusText(context, status),
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w800,
          fontSize: 12,
        ),
      ),
    );
  }
}

class _SmallLabel extends StatelessWidget {
  const _SmallLabel({required this.text, required this.color});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: 11,
        ),
      ),
    );
  }
}

String _copy(BuildContext context, String en, String zh) {
  return Localizations.localeOf(context).languageCode == 'zh' ? zh : en;
}

String _money(String currency, int minor) {
  return NumberFormat.currency(
    symbol: currency == 'CNY' ? '¥' : '$currency ',
    decimalDigits: 2,
  ).format(minor / 100);
}

String _date(BuildContext context, DateTime value) {
  return DateFormat.yMMMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).format(value);
}

String _statusText(BuildContext context, String status) {
  return switch (status) {
    'submitted' => _copy(context, 'Submitted', '已提交'),
    'under_review' => _copy(context, 'Under human review', '人工审核中'),
    'clarification_requested' => _copy(
      context,
      'Clarification requested',
      '需补充说明',
    ),
    'accepted' => _copy(context, 'Accepted', '已接受'),
    'rejected' => _copy(context, 'Rejected', '已拒绝'),
    'escalated' => _copy(context, 'Escalated', '已升级'),
    'closed' => _copy(context, 'Closed', '已关闭'),
    'active' => _copy(context, 'Active', '进行中'),
    'completed' => _copy(context, 'Completed', '已完成'),
    'scheduled' => _copy(context, 'Scheduled', '已安排'),
    'planned' => _copy(context, 'Planned', '计划中'),
    'cancelled' => _copy(context, 'Cancelled', '已取消'),
    _ => status.replaceAll('_', ' '),
  };
}

String _doctorResponseTypeText(BuildContext context, String responseType) {
  return switch (responseType) {
    'justification' => _copy(context, 'Doctor justification', '医生说明'),
    'clarification_response' => _copy(
      context,
      'Clarification response',
      '补充说明答复',
    ),
    'additional_information' => _copy(
      context,
      'Additional information',
      '补充资料',
    ),
    _ => humanizeProductValue(responseType),
  };
}

bool _matchesHistoryFilter(
  PayerRequestData request,
  _RequestHistoryFilter filter,
) {
  return switch (filter) {
    _RequestHistoryFilter.all => true,
    _RequestHistoryFilter.pending => {
      'submitted',
      'clarification_requested',
      'under_review',
      'escalated',
    }.contains(request.status),
    _RequestHistoryFilter.accepted => request.status == 'accepted',
    _RequestHistoryFilter.rejected => request.status == 'rejected',
    _RequestHistoryFilter.closed => request.status == 'closed',
  };
}

String _historyFilterLabel(BuildContext context, _RequestHistoryFilter filter) {
  return switch (filter) {
    _RequestHistoryFilter.all => _copy(context, 'All', '全部'),
    _RequestHistoryFilter.pending => _copy(context, 'Awaiting outcome', '等待结果'),
    _RequestHistoryFilter.accepted => _copy(context, 'Accepted', '已接受'),
    _RequestHistoryFilter.rejected => _copy(context, 'Rejected', '已拒绝'),
    _RequestHistoryFilter.closed => _copy(context, 'Closed', '已关闭'),
  };
}

String _reviewOutcomeTitle(BuildContext context, String status) {
  return switch (status) {
    'accepted' => _copy(context, 'Accepted by payer reviewer', '支付方审核员已接受'),
    'rejected' => _copy(context, 'Rejected by payer reviewer', '支付方审核员已拒绝'),
    'clarification_requested' => _copy(
      context,
      'Clarification requested',
      '需要补充说明',
    ),
    'escalated' => _copy(context, 'Escalated for review', '已升级审核'),
    'closed' => _copy(context, 'Review closed', '审核已关闭'),
    _ => _statusText(context, status),
  };
}

String _reviewOutcomeDescription(BuildContext context, String status) {
  return switch (status) {
    'accepted' => _copy(
      context,
      'This human review outcome does not guarantee reimbursement or payment.',
      '此人工审核结果不保证报销或付款。',
    ),
    'rejected' => _copy(
      context,
      'This human review outcome is not a final adjudicated patient obligation.',
      '此人工审核结果不是患者最终裁定的付款义务。',
    ),
    'clarification_requested' => _copy(
      context,
      'The payer reviewer needs additional information before recording an outcome.',
      '支付方审核员需要更多信息后才能记录结果。',
    ),
    'escalated' => _copy(
      context,
      'The request has been sent for additional human review.',
      '该申请已提交进一步人工审核。',
    ),
    'closed' => _copy(
      context,
      'The human review workflow has been closed with a recorded reason.',
      '人工审核流程已关闭并记录原因。',
    ),
    _ => _copy(
      context,
      'The request is awaiting a human review outcome.',
      '该申请正在等待人工审核结果。',
    ),
  };
}

String _organizationType(BuildContext context, String type) {
  return switch (type) {
    'public_payer' => _copy(context, 'Public payer', '公共支付方'),
    'commercial_payer' => _copy(context, 'Commercial payer', '商业支付方'),
    'observer' => _copy(context, 'Observer', '观察方'),
    _ => type.replaceAll('_', ' '),
  };
}

IconData _itemIcon(String type) => switch (type) {
  'medication' || 'prescription' => Icons.medication_outlined,
  'imaging' => Icons.image_search_outlined,
  'laboratory' => Icons.science_outlined,
  'booking' || 'follow_up' => Icons.event_outlined,
  'procedure' || 'therapy' => Icons.healing_outlined,
  'consultation' => Icons.medical_services_outlined,
  _ => Icons.receipt_long_outlined,
};
