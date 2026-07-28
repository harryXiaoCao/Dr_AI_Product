import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/care_cost/application/care_cost_providers.dart';
import 'package:dr_ai_app/features/care_cost/domain/care_cost_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

class PatientManagementScreen extends ConsumerStatefulWidget {
  const PatientManagementScreen({super.key});

  @override
  ConsumerState<PatientManagementScreen> createState() =>
      _PatientManagementScreenState();
}

class _PatientManagementScreenState
    extends ConsumerState<PatientManagementScreen> {
  final _searchController = TextEditingController();
  String? _selectedPatientId;
  String? _selectedClinicalEventId;
  _DoctorPatientSection _selectedSection = _DoctorPatientSection.overview;
  bool _patientPaneCollapsed = false;
  bool _sectionRailCollapsed = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final patients = ref.watch(patientListProvider);
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 1,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.sm),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final wide = constraints.maxWidth >= 980;
              final list = _PatientSearchPane(
                controller: _searchController,
                patients: patients,
                selectedPatientId: _selectedPatientId,
                collapsed: wide && _patientPaneCollapsed,
                onToggle: wide
                    ? () => setState(
                        () => _patientPaneCollapsed = !_patientPaneCollapsed,
                      )
                    : null,
                onSearchChanged: (value) =>
                    ref.read(patientSearchQueryProvider.notifier).state = value,
                onSelect: (patientId) => setState(() {
                  _selectedPatientId = patientId;
                  _selectedClinicalEventId = null;
                  _selectedSection = _DoctorPatientSection.overview;
                }),
                onRetry: () => ref.invalidate(patientListProvider),
              );
              final detail = _PatientDetailPane(
                patientId: _selectedPatientId,
                selectedSection: _selectedSection,
                selectedClinicalEventId: _selectedClinicalEventId,
                compact: !wide,
                onSectionChanged: (section) =>
                    setState(() => _selectedSection = section),
                onClinicalEventChanged: (eventId) =>
                    setState(() => _selectedClinicalEventId = eventId),
                sectionRailCollapsed: _sectionRailCollapsed,
                onToggleSectionRail: () => setState(
                  () => _sectionRailCollapsed = !_sectionRailCollapsed,
                ),
                onOpenPatientPicker: () =>
                    _showPatientPicker(context, patients),
              );
              if (wide) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    SizedBox(
                      width: _patientPaneCollapsed ? 68 : 300,
                      child: list,
                    ),
                    const SizedBox(width: DrAiSpacing.sm),
                    Expanded(child: detail),
                  ],
                );
              }
              return detail;
            },
          ),
        ),
      ),
    );
  }

  Future<void> _showPatientPicker(
    BuildContext context,
    AsyncValue<PatientListData> patients,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => SafeArea(
        child: SizedBox(
          height: MediaQuery.sizeOf(sheetContext).height * 0.82,
          child: Padding(
            padding: const EdgeInsets.all(DrAiSpacing.sm),
            child: _PatientSearchPane(
              controller: _searchController,
              patients: patients,
              selectedPatientId: _selectedPatientId,
              collapsed: false,
              onToggle: null,
              onSearchChanged: (value) =>
                  ref.read(patientSearchQueryProvider.notifier).state = value,
              onSelect: (patientId) {
                setState(() {
                  _selectedPatientId = patientId;
                  _selectedClinicalEventId = null;
                  _selectedSection = _DoctorPatientSection.overview;
                });
                Navigator.of(sheetContext).pop();
              },
              onRetry: () => ref.invalidate(patientListProvider),
            ),
          ),
        ),
      ),
    );
  }
}

enum _DoctorPatientSection {
  overview(icon: Icons.space_dashboard_outlined),
  profile(icon: Icons.badge_outlined),
  medicalHistory(icon: Icons.description_outlined),
  clinicalEvents(icon: Icons.fact_check_outlined),
  medicationPrescriptions(icon: Icons.medication_outlined),
  recoveryPlans(icon: Icons.assignment_turned_in_outlined),
  imaging(icon: Icons.image_search_outlined),
  consultationActivity(icon: Icons.edit_note_outlined);

  const _DoctorPatientSection({required this.icon});

  final IconData icon;
}

extension _LocalizedDoctorPatientSection on _DoctorPatientSection {
  String localizedLabel(BuildContext context) => switch (this) {
    _DoctorPatientSection.overview => context.l10n.overview,
    _DoctorPatientSection.profile => context.l10n.profile,
    _DoctorPatientSection.medicalHistory => context.l10n.medicalHistoryLower,
    _DoctorPatientSection.clinicalEvents => context.l10n.clinicalEvents,
    _DoctorPatientSection.medicationPrescriptions =>
      context.l10n.medicationsPrescriptions,
    _DoctorPatientSection.recoveryPlans => context.l10n.recoveryPlans,
    _DoctorPatientSection.imaging => context.l10n.imaging,
    _DoctorPatientSection.consultationActivity =>
      context.l10n.consultationActivity,
  };

  String localizedSummary(BuildContext context) => switch (this) {
    _DoctorPatientSection.overview => context.l10n.overviewSummary,
    _DoctorPatientSection.profile => context.l10n.profileSummary,
    _DoctorPatientSection.medicalHistory => context.l10n.medicalHistorySummary,
    _DoctorPatientSection.clinicalEvents => context.l10n.clinicalEventsSummary,
    _DoctorPatientSection.medicationPrescriptions =>
      context.l10n.medicationsSummary,
    _DoctorPatientSection.recoveryPlans => context.l10n.recoveryPlansSummary,
    _DoctorPatientSection.imaging => context.l10n.imagingSummary,
    _DoctorPatientSection.consultationActivity =>
      context.l10n.consultationActivitySummary,
  };
}

class _PatientSearchPane extends StatelessWidget {
  const _PatientSearchPane({
    required this.controller,
    required this.patients,
    required this.selectedPatientId,
    required this.collapsed,
    required this.onToggle,
    required this.onSearchChanged,
    required this.onSelect,
    required this.onRetry,
  });

  final TextEditingController controller;
  final AsyncValue<PatientListData> patients;
  final String? selectedPatientId;
  final bool collapsed;
  final VoidCallback? onToggle;
  final ValueChanged<String> onSearchChanged;
  final ValueChanged<String> onSelect;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    if (collapsed) {
      return DecoratedBox(
        key: const Key('collapsed-patient-pane'),
        decoration: BoxDecoration(
          color: DrAiColors.white,
          borderRadius: BorderRadius.circular(DrAiRadii.lg),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Column(
          children: <Widget>[
            IconButton(
              key: const Key('expand-patient-pane-button'),
              tooltip: context.l10n.expandPatientList,
              onPressed: onToggle,
              icon: const Icon(Icons.keyboard_double_arrow_right_rounded),
            ),
            const Divider(height: 1),
            const SizedBox(height: DrAiSpacing.sm),
            const Icon(Icons.people_outline, color: DrAiColors.brand),
          ],
        ),
      );
    }
    return _CarePanel(
      title: context.l10n.patientManagement,
      icon: Icons.people_outline,
      trailing: IconButton(
        key: const Key('collapse-patient-pane-button'),
        tooltip: context.l10n.collapsePatientList,
        onPressed: onToggle,
        icon: const Icon(Icons.keyboard_double_arrow_left_rounded),
      ),
      child: Column(
        children: <Widget>[
          const _PatientConnectPanel(),
          const SizedBox(height: DrAiSpacing.sm),
          TextField(
            key: const Key('patient-search-field'),
            controller: controller,
            onChanged: onSearchChanged,
            maxLength: 80,
            decoration: InputDecoration(
              counterText: '',
              prefixIcon: Icon(Icons.search),
              labelText: context.l10n.searchPatients,
              helperText: context.l10n.namePatientId,
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Expanded(
            child: patients.when(
              loading: () =>
                  DashboardLoadingView(label: context.l10n.loadingPatients),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(context, error),
                onRetry: onRetry,
              ),
              data: (data) {
                if (data.items.isEmpty) {
                  return _EmptyState(
                    key: Key('patient-list-empty'),
                    icon: Icons.person_add_alt_1_outlined,
                    title: context.l10n.noConnectedPatients,
                    body: context.l10n.connectPatientEmpty,
                  );
                }
                return ListView.separated(
                  itemCount: data.items.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: DrAiSpacing.xs),
                  itemBuilder: (context, index) {
                    final patient = data.items[index];
                    final selected = patient.patientId == selectedPatientId;
                    return Material(
                      color: Colors.transparent,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                      child: ListTile(
                        key: Key('patient-row-${patient.syntheticIdentifier}'),
                        selected: selected,
                        selectedTileColor: DrAiColors.patientAccent,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(DrAiRadii.md),
                        ),
                        leading: const CircleAvatar(
                          backgroundColor: DrAiColors.brand,
                          child: Icon(Icons.person, color: DrAiColors.white),
                        ),
                        title: Text(patient.displayName),
                        subtitle: Text(patient.syntheticIdentifier),
                        onTap: () => onSelect(patient.patientId),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _PatientConnectPanel extends ConsumerStatefulWidget {
  const _PatientConnectPanel();

  @override
  ConsumerState<_PatientConnectPanel> createState() =>
      _PatientConnectPanelState();
}

class _PatientConnectPanelState extends ConsumerState<_PatientConnectPanel> {
  final _patientCodeController = TextEditingController();
  String? _validationError;
  bool _previewing = false;

  @override
  void dispose() {
    _patientCodeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(patientConnectionControllerProvider);
    final connected = state.asData?.value;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.connectPatientByCode,
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('patient-connect-code-field'),
              controller: _patientCodeController,
              maxLength: 80,
              textCapitalization: TextCapitalization.characters,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.patientCode,
                helperText: context.l10n.patientCodeHelper,
                errorText: _validationError,
                prefixIcon: const Icon(Icons.badge_outlined),
              ),
              onSubmitted: (_) => _connect(),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            FilledButton.icon(
              key: const Key('patient-connect-button'),
              onPressed: state.isLoading || _previewing ? null : _connect,
              icon: state.isLoading || _previewing
                  ? const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.person_add_alt_1_outlined),
              label: Text(context.l10n.reviewPatientMatch),
            ),
            state.when(
              data: (_) => connected == null
                  ? const SizedBox.shrink()
                  : Padding(
                      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
                      child: Text(
                        context.l10n.connectedPatient(connected.displayName),
                        key: const Key('patient-connect-success'),
                        style: const TextStyle(
                          color: DrAiColors.brand,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) => Padding(
                padding: const EdgeInsets.only(top: DrAiSpacing.xs),
                child: Text(
                  _safeErrorMessage(context, error),
                  key: const Key('patient-connect-error'),
                  style: const TextStyle(
                    color: DrAiColors.danger,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _connect() async {
    final code = _patientCodeController.text.trim();
    if (code.length < 6) {
      setState(() => _validationError = context.l10n.enterPatientCode);
      return;
    }
    setState(() {
      _validationError = null;
      _previewing = true;
    });
    try {
      final controller = ref.read(patientConnectionControllerProvider.notifier);
      final preview = await controller.preview(code);
      if (!mounted) {
        return;
      }
      setState(() => _previewing = false);
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(context.l10n.confirmPatientConnection),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(context.l10n.confirmPatientDescription),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                preview.displayName,
                key: const Key('patient-match-preview-name'),
                style: const TextStyle(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(preview.maskedPatientCode),
            ],
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(context.l10n.cancel),
            ),
            FilledButton(
              key: const Key('patient-match-confirm-button'),
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(context.l10n.confirmConnect),
            ),
          ],
        ),
      );
      if (confirmed == true) {
        await controller.connect(code);
      }
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _previewing = false;
          _validationError = error.statusCode == 404
              ? context.l10n.patientNotFound
              : error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _previewing = false;
          _validationError = context.l10n.reviewPatientFailed;
        });
      }
    }
  }
}

class _PatientDetailPane extends ConsumerWidget {
  const _PatientDetailPane({
    required this.patientId,
    required this.selectedSection,
    required this.selectedClinicalEventId,
    required this.compact,
    required this.onSectionChanged,
    required this.onClinicalEventChanged,
    required this.sectionRailCollapsed,
    required this.onToggleSectionRail,
    required this.onOpenPatientPicker,
  });

  final String? patientId;
  final _DoctorPatientSection selectedSection;
  final String? selectedClinicalEventId;
  final bool compact;
  final ValueChanged<_DoctorPatientSection> onSectionChanged;
  final ValueChanged<String?> onClinicalEventChanged;
  final bool sectionRailCollapsed;
  final VoidCallback onToggleSectionRail;
  final VoidCallback onOpenPatientPicker;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = patientId;
    if (id == null) {
      return _CarePanel(
        title: context.l10n.patientProfile,
        icon: Icons.badge_outlined,
        child: Column(
          children: <Widget>[
            if (compact)
              Align(
                alignment: Alignment.centerLeft,
                child: OutlinedButton.icon(
                  key: const Key('open-patient-picker-button'),
                  onPressed: onOpenPatientPicker,
                  icon: const Icon(Icons.people_outline),
                  label: Text(context.l10n.choosePatient),
                ),
              ),
            Expanded(
              child: _EmptyState(
                key: Key('patient-detail-empty'),
                icon: Icons.touch_app_outlined,
                title: context.l10n.selectPatient,
                body: context.l10n.selectPatientDescription,
              ),
            ),
          ],
        ),
      );
    }
    final bundle = ref.watch(patientCareBundleProvider(id));
    return _CarePanel(
      title: context.l10n.patientWorkspaceTitle,
      icon: Icons.badge_outlined,
      child: bundle.when(
        loading: () =>
            DashboardLoadingView(label: context.l10n.loadingPatientProfile),
        error: (error, stackTrace) => DashboardErrorView(
          message: _safeErrorMessage(context, error),
          onRetry: () => ref.invalidate(patientCareBundleProvider(id)),
        ),
        data: (data) => _PatientCareBundleView(
          bundle: data,
          showNotes: true,
          selectedSection: selectedSection,
          selectedClinicalEventId: selectedClinicalEventId,
          compact: compact,
          onSectionChanged: onSectionChanged,
          onClinicalEventChanged: onClinicalEventChanged,
          sectionRailCollapsed: sectionRailCollapsed,
          onToggleSectionRail: onToggleSectionRail,
          onOpenPatientPicker: onOpenPatientPicker,
        ),
      ),
    );
  }
}

class PatientCareBundleSummary extends StatelessWidget {
  const PatientCareBundleSummary({
    required this.bundle,
    this.showNotes = false,
    super.key,
  });

  final PatientCareBundle bundle;
  final bool showNotes;

  @override
  Widget build(BuildContext context) {
    return _PatientCareBundleView(bundle: bundle, showNotes: showNotes);
  }
}

class _PatientCareBundleView extends StatelessWidget {
  const _PatientCareBundleView({
    required this.bundle,
    required this.showNotes,
    this.selectedSection = _DoctorPatientSection.overview,
    this.selectedClinicalEventId,
    this.compact = false,
    this.onSectionChanged,
    this.onClinicalEventChanged,
    this.sectionRailCollapsed = false,
    this.onToggleSectionRail,
    this.onOpenPatientPicker,
  });

  final PatientCareBundle bundle;
  final bool showNotes;
  final _DoctorPatientSection selectedSection;
  final String? selectedClinicalEventId;
  final bool compact;
  final ValueChanged<_DoctorPatientSection>? onSectionChanged;
  final ValueChanged<String?>? onClinicalEventChanged;
  final bool sectionRailCollapsed;
  final VoidCallback? onToggleSectionRail;
  final VoidCallback? onOpenPatientPicker;

  @override
  Widget build(BuildContext context) {
    if (!showNotes) {
      return ListView(
        key: const Key('patient-care-bundle-list'),
        children: <Widget>[
          _ProfileHeader(bundle: bundle),
          const SizedBox(height: DrAiSpacing.sm),
          _medicalRecordsSection(context, bundle),
        ],
      );
    }
    final selectedEvent = _selectedClinicalEvent(
      bundle,
      selectedClinicalEventId,
    );
    final content = _WorkspaceSectionContent(
      bundle: bundle,
      selectedSection: selectedSection,
      selectedEvent: selectedEvent,
      compact: compact,
      onClinicalEventChanged: onClinicalEventChanged,
    );
    if (compact) {
      return ListView(
        key: const Key('patient-care-bundle-list'),
        children: <Widget>[
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              key: const Key('open-patient-picker-button'),
              onPressed: onOpenPatientPicker,
              icon: const Icon(Icons.people_outline),
              label: Text(context.l10n.changePatient),
            ),
          ),
          const SizedBox(height: DrAiSpacing.xs),
          _SelectedPatientSummaryHeader(bundle: bundle),
          const SizedBox(height: DrAiSpacing.sm),
          _ActiveClinicalEventBar(
            bundle: bundle,
            selectedEvent: selectedEvent,
            compact: true,
            onChanged: onClinicalEventChanged,
          ),
          const SizedBox(height: DrAiSpacing.xs),
          _CompactSectionPicker(
            selectedSection: selectedSection,
            onChanged: onSectionChanged,
          ),
          const SizedBox(height: DrAiSpacing.sm),
          content,
          const SizedBox(height: DrAiSpacing.sm),
        ],
      );
    }
    return Column(
      key: const Key('patient-care-bundle-list'),
      children: <Widget>[
        _SelectedPatientSummaryHeader(bundle: bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _ActiveClinicalEventBar(
          bundle: bundle,
          selectedEvent: selectedEvent,
          compact: false,
          onChanged: onClinicalEventChanged,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              SizedBox(
                width: sectionRailCollapsed ? 72 : 214,
                child: _SectionNavigation(
                  selectedSection: selectedSection,
                  collapsed: sectionRailCollapsed,
                  onToggle: onToggleSectionRail,
                  onChanged: onSectionChanged,
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(child: content),
            ],
          ),
        ),
      ],
    );
  }
}

class _SelectedPatientSummaryHeader extends ConsumerWidget {
  const _SelectedPatientSummaryHeader({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = bundle.patient;
    final plans = ref.watch(recoveryPlanListProvider(patient.patientId));
    final lastVisit = _lastVisitLabel(context, bundle.visitHistory);
    final workflowStatus = _workflowStatus(context, bundle);
    return DecoratedBox(
      key: const Key('selected-patient-summary-header'),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: <Widget>[
            const CircleAvatar(
              radius: 28,
              backgroundColor: DrAiColors.brandSoft,
              child: Icon(
                Icons.person_outline_rounded,
                color: DrAiColors.brand,
                size: 28,
              ),
            ),
            const SizedBox(width: DrAiSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    patient.displayName,
                    style: const TextStyle(
                      color: DrAiColors.ink,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  Wrap(
                    spacing: DrAiSpacing.xs,
                    runSpacing: DrAiSpacing.xs,
                    children: <Widget>[
                      _LightMetricChip(label: patient.syntheticIdentifier),
                      _LightMetricChip(label: _ageSexLabel(context, patient)),
                      _LightMetricChip(
                        label: plans.when(
                          loading: () => context.l10n.recoveryPlanLoading,
                          error: (error, stackTrace) =>
                              context.l10n.recoveryPlanUnavailable,
                          data: (data) => _activePlanLabel(context, data),
                        ),
                      ),
                      _LightMetricChip(
                        label: context.l10n.lastVisit(lastVisit),
                      ),
                      _LightMetricChip(label: workflowStatus),
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

class _ActiveClinicalEventBar extends StatelessWidget {
  const _ActiveClinicalEventBar({
    required this.bundle,
    required this.selectedEvent,
    required this.compact,
    required this.onChanged,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;
  final bool compact;
  final ValueChanged<String?>? onChanged;

  @override
  Widget build(BuildContext context) {
    final events = bundle.clinicalEvents;
    final event = selectedEvent;
    return DecoratedBox(
      key: const Key('active-clinical-event-bar'),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(
                  Icons.account_tree_outlined,
                  color: DrAiColors.brand,
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    context.l10n.activeClinicalEvent,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                _LightMetricChip(
                  label: event == null
                      ? context.l10n.setupNeeded
                      : context.l10n.stableValue(event.status),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (events.isEmpty)
              Text(
                context.l10n.createEventBeforeCare,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              )
            else
              DropdownButtonFormField<String>(
                key: const Key('clinical-event-selector'),
                initialValue: event?.id,
                isExpanded: true,
                decoration: InputDecoration(
                  labelText: context.l10n.selectedCareEpisode,
                  prefixIcon: const Icon(Icons.fact_check_outlined),
                  isDense: compact,
                ),
                items: <DropdownMenuItem<String>>[
                  for (final event in events)
                    DropdownMenuItem<String>(
                      value: event.id,
                      child: Text(
                        '${event.title} - ${context.l10n.stableValue(event.status)}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: onChanged,
              ),
            if (!compact) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                event == null
                    ? context.l10n.legacyRecordsNotice
                    : '${event.chiefComplaint} | ${_eventLinkSummary(context, event)}',
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SectionNavigation extends StatelessWidget {
  const _SectionNavigation({
    required this.selectedSection,
    required this.collapsed,
    required this.onToggle,
    required this.onChanged,
  });

  final _DoctorPatientSection selectedSection;
  final bool collapsed;
  final VoidCallback? onToggle;
  final ValueChanged<_DoctorPatientSection>? onChanged;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: SingleChildScrollView(
        key: const Key('doctor-workspace-section-nav'),
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Column(
          children: <Widget>[
            Align(
              alignment: collapsed ? Alignment.center : Alignment.centerRight,
              child: IconButton(
                key: const Key('toggle-section-rail-button'),
                tooltip: collapsed
                    ? context.l10n.expandSectionNavigation
                    : context.l10n.collapseSectionNavigation,
                onPressed: onToggle,
                icon: Icon(
                  collapsed
                      ? Icons.keyboard_double_arrow_right_rounded
                      : Icons.keyboard_double_arrow_left_rounded,
                ),
              ),
            ),
            const Divider(height: 1),
            const SizedBox(height: DrAiSpacing.xs),
            for (final section in _DoctorPatientSection.values)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Material(
                  color: section == selectedSection
                      ? DrAiColors.brandSoft
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                  child: ListTile(
                    key: Key('doctor-section-${section.name}'),
                    dense: true,
                    minLeadingWidth: 20,
                    contentPadding: collapsed
                        ? const EdgeInsets.symmetric(horizontal: 12)
                        : const EdgeInsets.symmetric(horizontal: 10),
                    selected: section == selectedSection,
                    leading: Icon(section.icon, color: DrAiColors.brand),
                    title: collapsed
                        ? null
                        : Text(section.localizedLabel(context), maxLines: 2),
                    titleTextStyle: const TextStyle(
                      color: DrAiColors.ink,
                      fontWeight: FontWeight.w600,
                    ),
                    onTap: onChanged == null ? null : () => onChanged!(section),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _CompactSectionPicker extends StatelessWidget {
  const _CompactSectionPicker({
    required this.selectedSection,
    required this.onChanged,
  });

  final _DoctorPatientSection selectedSection;
  final ValueChanged<_DoctorPatientSection>? onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<_DoctorPatientSection>(
      key: const Key('doctor-compact-section-picker'),
      initialValue: selectedSection,
      isExpanded: true,
      decoration: InputDecoration(
        labelText: context.l10n.workspaceSection,
        prefixIcon: Icon(Icons.view_list_outlined),
      ),
      items: <DropdownMenuItem<_DoctorPatientSection>>[
        for (final section in _DoctorPatientSection.values)
          DropdownMenuItem<_DoctorPatientSection>(
            value: section,
            child: Text(
              section.localizedLabel(context),
              overflow: TextOverflow.ellipsis,
            ),
          ),
      ],
      onChanged: onChanged == null
          ? null
          : (value) {
              if (value != null) {
                onChanged!(value);
              }
            },
    );
  }
}

class _WorkspaceSectionContent extends StatelessWidget {
  const _WorkspaceSectionContent({
    required this.bundle,
    required this.selectedSection,
    required this.selectedEvent,
    required this.compact,
    required this.onClinicalEventChanged,
  });

  final PatientCareBundle bundle;
  final _DoctorPatientSection selectedSection;
  final ClinicalEventItem? selectedEvent;
  final bool compact;
  final ValueChanged<String?>? onClinicalEventChanged;

  @override
  Widget build(BuildContext context) {
    final sectionContent = switch (selectedSection) {
      _DoctorPatientSection.overview => _OverviewSection(
        bundle: bundle,
        selectedEvent: selectedEvent,
      ),
      _DoctorPatientSection.profile => _ProfileReviewSection(bundle: bundle),
      _DoctorPatientSection.medicalHistory => _MedicalHistorySection(
        bundle: bundle,
      ),
      _DoctorPatientSection.clinicalEvents => _ClinicalEventsSection(
        bundle: bundle,
        selectedEvent: selectedEvent,
        onEventChanged: onClinicalEventChanged,
      ),
      _DoctorPatientSection.medicationPrescriptions =>
        _MedicationPrescriptionsSection(
          bundle: bundle,
          selectedEvent: selectedEvent,
        ),
      _DoctorPatientSection.recoveryPlans => _RecoveryPlanEditor(
        patientId: bundle.patient.patientId,
        clinicalEventId: selectedEvent?.id,
      ),
      _DoctorPatientSection.imaging => _ImagingSection(
        bundle: bundle,
        selectedEvent: selectedEvent,
      ),
      _DoctorPatientSection.consultationActivity =>
        _ConsultationActivitySection(
          bundle: bundle,
          selectedEvent: selectedEvent,
        ),
    };
    return _SectionScaffold(
      section: selectedSection,
      expandBody: !compact,
      child: compact
          ? KeyedSubtree(
              key: Key('doctor-section-list-${selectedSection.name}'),
              child: sectionContent,
            )
          : ListView(
              key: Key('doctor-section-list-${selectedSection.name}'),
              children: <Widget>[sectionContent],
            ),
    );
  }
}

class _SectionScaffold extends StatelessWidget {
  const _SectionScaffold({
    required this.section,
    required this.child,
    this.expandBody = true,
  });

  final _DoctorPatientSection section;
  final Widget child;
  final bool expandBody;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.all(DrAiSpacing.md),
              child: Row(
                children: <Widget>[
                  DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.brandSoft,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.xs),
                      child: Icon(section.icon, color: DrAiColors.brand),
                    ),
                  ),
                  const SizedBox(width: DrAiSpacing.sm),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          section.localizedLabel(context),
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(
                                color: DrAiColors.ink,
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                        Text(
                          section.localizedSummary(context),
                          style: const TextStyle(
                            color: DrAiColors.mutedInk,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            if (expandBody)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(DrAiSpacing.sm),
                  child: child,
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.all(DrAiSpacing.sm),
                child: child,
              ),
          ],
        ),
      ),
    );
  }
}

class _OverviewSection extends StatelessWidget {
  const _OverviewSection({required this.bundle, required this.selectedEvent});

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    final plans = _eventRecoveryPlansById(
      bundle.recoveryPlans,
      selectedEvent?.id,
    );
    final medications = _eventMedications(bundle, selectedEvent);
    return LayoutBuilder(
      builder: (context, constraints) {
        final twoColumns = constraints.maxWidth >= 760;
        final cardWidth = twoColumns
            ? (constraints.maxWidth - DrAiSpacing.sm) / 2
            : constraints.maxWidth;
        return Wrap(
          spacing: DrAiSpacing.sm,
          runSpacing: DrAiSpacing.sm,
          children: <Widget>[
            SizedBox(
              width: cardWidth,
              child: _OverviewSummaryCard(
                icon: Icons.verified_user_outlined,
                title: context.l10n.verifiedHistory,
                body: _historyLine(context, bundle),
                bodyKey: const Key('medical-history-overview-section'),
              ),
            ),
            SizedBox(
              width: cardWidth,
              child: _OverviewSummaryCard(
                icon: Icons.event_note_outlined,
                title: context.l10n.activeClinicalEvents,
                body: selectedEvent == null
                    ? context.l10n.noClinicalEvent
                    : '${selectedEvent!.title}\n${selectedEvent!.chiefComplaint}\n${_eventLinkSummary(context, selectedEvent!)}',
              ),
            ),
            SizedBox(
              width: cardWidth,
              child: _OverviewSummaryCard(
                icon: Icons.favorite_border_rounded,
                title: context.l10n.activeRecoveryPlan,
                body: plans.isEmpty
                    ? context.l10n.noEventRecoveryPlan
                    : '${plans.first.title}\n${context.l10n.stableValue(plans.first.status)}',
              ),
            ),
            SizedBox(
              width: cardWidth,
              child: _OverviewSummaryCard(
                icon: Icons.medication_outlined,
                title: context.l10n.currentMedications,
                body: medications.isEmpty
                    ? context.l10n.noMedications
                    : medications
                          .take(4)
                          .map((item) => '${item.name} · ${item.dosage}')
                          .join('\n'),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _OverviewSummaryCard extends StatelessWidget {
  const _OverviewSummaryCard({
    required this.icon,
    required this.title,
    required this.body,
    this.bodyKey,
  });

  final IconData icon;
  final String title;
  final String body;
  final Key? bodyKey;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.brandSoft,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(DrAiSpacing.xs),
                    child: Icon(icon, color: DrAiColors.brand, size: 20),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.sm),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: DrAiColors.ink,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              body,
              key: bodyKey,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileReviewSection extends StatelessWidget {
  const _ProfileReviewSection({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context) {
    final patient = bundle.patient;
    return Column(
      children: <Widget>[
        _InfoTile(
          title: patient.displayName,
          subtitle: patient.syntheticIdentifier,
          body:
              '${patient.relationshipLabel}\n'
              '${_demographicsLine(context, patient)}\n'
              '${context.l10n.doctorReviewOnly}',
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _InlineMessage(
          key: Key('doctor-profile-read-only-notice'),
          message: context.l10n.profileCorrectionNotice,
          icon: Icons.lock_outline,
        ),
      ],
    );
  }
}

class _MedicalHistorySection extends StatelessWidget {
  const _MedicalHistorySection({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        _InlineMessage(
          key: Key('medical-history-patient-entered-notice'),
          message: context.l10n.historyAuditNotice,
          icon: Icons.verified_user_outlined,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _MedicalHistoryReviewPanel(bundle: bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _medicalHistoryReviewsSection(context, bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<PatientAllergyItem>(
          key: const Key('allergies-section'),
          title: context.l10n.allergies,
          icon: Icons.warning_amber_outlined,
          items: bundle.allergies,
          emptyTitle: context.l10n.noAllergies,
          itemBuilder: (item) => _InfoTile(
            title: item.label,
            subtitle:
                '${context.l10n.stableValue(item.severity)} - ${context.l10n.stableValue(item.status)}',
            body: item.reaction ?? context.l10n.noReaction,
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<ChronicDiseaseItem>(
          key: const Key('chronic-diseases-section'),
          title: context.l10n.chronicDiseases,
          icon: Icons.monitor_heart_outlined,
          items: bundle.chronicDiseases,
          emptyTitle: context.l10n.noChronicDiseases,
          itemBuilder: (item) => _InfoTile(
            title: item.name,
            subtitle:
                '${context.l10n.stableValue(item.status)} - ${item.diagnosedOn ?? context.l10n.dateUnknown}',
            body: item.notes ?? context.l10n.noConditionNote,
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _medicalRecordsSection(context, bundle),
      ],
    );
  }
}

class _MedicalHistoryReviewPanel extends ConsumerStatefulWidget {
  const _MedicalHistoryReviewPanel({required this.bundle});

  final PatientCareBundle bundle;

  @override
  ConsumerState<_MedicalHistoryReviewPanel> createState() =>
      _MedicalHistoryReviewPanelState();
}

class _MedicalHistoryReviewPanelState
    extends ConsumerState<_MedicalHistoryReviewPanel> {
  String _action = 'verified';
  String? _targetKey;
  final _amendmentController = TextEditingController();
  final _correctionController = TextEditingController();
  String? _validationError;

  @override
  void dispose() {
    _amendmentController.dispose();
    _correctionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final targets = _historyReviewTargets(context, widget.bundle);
    _targetKey ??= targets.isEmpty ? null : targets.first.key;
    final state = ref.watch(medicalHistoryReviewControllerProvider);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.medicalHistoryReview,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (targets.isEmpty)
              _InlineMessage(
                message: context.l10n.noPatientHistoryItem,
                icon: Icons.info_outline,
              )
            else ...<Widget>[
              DropdownButtonFormField<String>(
                key: const Key('medical-history-review-target-field'),
                initialValue: _targetKey,
                isExpanded: true,
                decoration: InputDecoration(
                  labelText: context.l10n.patientEnteredItem,
                  prefixIcon: Icon(Icons.history_edu_outlined),
                ),
                items: <DropdownMenuItem<String>>[
                  for (final target in targets)
                    DropdownMenuItem<String>(
                      value: target.key,
                      child: Text(target.label),
                    ),
                ],
                onChanged: (value) => setState(() => _targetKey = value),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              DropdownButtonFormField<String>(
                key: const Key('medical-history-review-action-field'),
                initialValue: _action,
                decoration: InputDecoration(
                  labelText: context.l10n.reviewAction,
                  prefixIcon: Icon(Icons.verified_outlined),
                ),
                items: <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'verified',
                    child: Text(context.l10n.markVerified),
                  ),
                  DropdownMenuItem(
                    value: 'amendment',
                    child: Text(context.l10n.addDoctorAmendment),
                  ),
                  DropdownMenuItem(
                    value: 'correction_requested',
                    child: Text(context.l10n.requestPatientCorrection),
                  ),
                ],
                onChanged: (value) =>
                    setState(() => _action = value ?? 'verified'),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              TextField(
                key: const Key('medical-history-amendment-field'),
                controller: _amendmentController,
                maxLength: 1200,
                decoration: InputDecoration(
                  counterText: '',
                  labelText: context.l10n.doctorAmendment,
                  prefixIcon: Icon(Icons.edit_note_outlined),
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              TextField(
                key: const Key('medical-history-correction-field'),
                controller: _correctionController,
                maxLength: 1200,
                decoration: InputDecoration(
                  counterText: '',
                  labelText: context.l10n.patientCorrectionRequest,
                  prefixIcon: Icon(Icons.outgoing_mail),
                ),
              ),
              if (_validationError != null)
                _InlineMessage(
                  message: _validationError!,
                  icon: Icons.error_outline,
                ),
              const SizedBox(height: DrAiSpacing.xs),
              FilledButton.icon(
                key: const Key('medical-history-review-save-button'),
                onPressed: state.isLoading ? null : _save,
                icon: const Icon(Icons.save_outlined),
                label: Text(context.l10n.saveAuditedReview),
              ),
            ],
            state.when(
              loading: () => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: LinearProgressIndicator(),
              ),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (review) {
                if (review == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  message: context.l10n.historyReviewSaved(
                    context.l10n.stableValue(review.action),
                  ),
                  icon: Icons.check_circle_outline,
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _save() {
    final targets = _historyReviewTargets(context, widget.bundle);
    final selected = targets
        .where((target) => target.key == _targetKey)
        .firstOrNull;
    if (selected == null) {
      setState(() => _validationError = context.l10n.selectHistoryItem);
      return;
    }
    if (_action == 'amendment' && _amendmentController.text.trim().length < 3) {
      setState(() => _validationError = context.l10n.enterDoctorAmendment);
      return;
    }
    if (_action == 'correction_requested' &&
        _correctionController.text.trim().length < 3) {
      setState(() => _validationError = context.l10n.enterPatientCorrection);
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(medicalHistoryReviewControllerProvider.notifier)
        .create(
          patientId: widget.bundle.patient.patientId,
          targetType: selected.targetType,
          targetId: selected.targetId,
          action: _action,
          amendmentSummary: _action == 'amendment'
              ? _amendmentController.text.trim()
              : '',
          correctionRequest: _action == 'correction_requested'
              ? _correctionController.text.trim()
              : '',
        );
  }
}

class _HistoryReviewTarget {
  const _HistoryReviewTarget({
    required this.key,
    required this.targetType,
    required this.targetId,
    required this.label,
  });

  final String key;
  final String targetType;
  final String targetId;
  final String label;
}

class _ClinicalEventsSection extends StatelessWidget {
  const _ClinicalEventsSection({
    required this.bundle,
    required this.selectedEvent,
    required this.onEventChanged,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;
  final ValueChanged<String?>? onEventChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        _ClinicalEventEditor(
          bundle: bundle,
          selectedEvent: selectedEvent,
          onEventChanged: onEventChanged,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ClinicalEventContextCard(bundle: bundle, selectedEvent: selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<VisitHistoryItem>(
          key: const Key('visit-history-section'),
          title: context.l10n.encounterUpdates,
          icon: Icons.event_note_outlined,
          items: _eventVisitHistory(bundle, selectedEvent),
          emptyTitle: context.l10n.noEncounterUpdates,
          itemBuilder: (item) => _InfoTile(
            title: item.title,
            subtitle:
                '${item.visitType} - ${_dateLabel(context, item.occurredAt)}',
            body:
                '${item.summary}\n${context.l10n.clinicianNamed(item.clinicianLabel ?? context.l10n.notRecorded)}\n'
                '${context.l10n.clinicalEventLink(_eventTitle(context, bundle, selectedEvent))}',
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<DiagnosisItem>(
          key: const Key('diagnoses-section'),
          title: context.l10n.doctorDiagnosisRecord,
          icon: Icons.fact_check_outlined,
          items: _eventDiagnoses(bundle, selectedEvent),
          emptyTitle: context.l10n.noDiagnoses,
          itemBuilder: (item) => _InfoTile(
            title: item.label,
            subtitle:
                '${context.l10n.stableValue(item.status)} - ${item.diagnosedOn ?? context.l10n.dateUnknown}',
            body:
                '${item.notes ?? context.l10n.noDiagnosisNote}\n'
                '${context.l10n.diagnosisReadOnly}',
          ),
        ),
      ],
    );
  }
}

class _MedicationPrescriptionsSection extends StatelessWidget {
  const _MedicationPrescriptionsSection({
    required this.bundle,
    required this.selectedEvent,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        _EventLinkNotice(
          text: context.l10n.prescriptionContextNotice(
            _eventTitle(context, bundle, selectedEvent),
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _medicationsListSection(context, bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _prescriptionsListSection(context, bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _remindersListSection(context, bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _MedicationWorkflowPanel(
          bundle: bundle,
          clinicalEventId: selectedEvent?.id,
          mode: _MedicationWorkflowMode.prescription,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _MedicationWorkflowPanel(
          bundle: bundle,
          clinicalEventId: selectedEvent?.id,
          mode: _MedicationWorkflowMode.medication,
        ),
      ],
    );
  }
}

class _ImagingSection extends StatelessWidget {
  const _ImagingSection({required this.bundle, required this.selectedEvent});

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        _EventLinkNotice(
          text: context.l10n.imagingEvidenceNotice(
            _eventTitle(context, bundle, selectedEvent),
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        _InlineMessage(
          message: context.l10n.imagingArtifactNotBillable,
          icon: Icons.info_outline,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ImagingClinicalServicePanel(
          bundle: bundle,
          selectedEvent: selectedEvent,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _imagingListSection(context, bundle, selectedEvent),
      ],
    );
  }
}

class _ImagingClinicalServicePanel extends ConsumerStatefulWidget {
  const _ImagingClinicalServicePanel({
    required this.bundle,
    required this.selectedEvent,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  ConsumerState<_ImagingClinicalServicePanel> createState() =>
      _ImagingClinicalServicePanelState();
}

class _ImagingClinicalServicePanelState
    extends ConsumerState<_ImagingClinicalServicePanel> {
  final _nameController = TextEditingController();
  final _modalityController = TextEditingController();
  final _bodyRegionController = TextEditingController();
  final _scheduledController = TextEditingController();
  final _performedController = TextEditingController();
  final _indicationController = TextEditingController();
  final _totalController = TextEditingController();
  final _payerController = TextEditingController();
  final _patientController = TextEditingController();
  final _filenameController = TextEditingController();
  final _sizeController = TextEditingController();
  final _findingController = TextEditingController();
  String _category = 'imaging';
  String _status = 'ordered';
  String _pricingState = 'pending_cost';
  String _contentType = 'application/dicom';
  bool _recordCost = true;
  String? _editingServiceId;
  String? _evidenceServiceId;
  String? _validationError;
  List<int>? _selectedEvidenceBytes;

  List<ClinicalServiceItem> get _services => widget.bundle.clinicalServices
      .where((item) => item.clinicalEventId == widget.selectedEvent?.id)
      .toList();

  List<ClinicalServiceItem> get _imagingServices =>
      _services.where((item) => item.category == 'imaging').toList();

  @override
  void dispose() {
    _nameController.dispose();
    _modalityController.dispose();
    _bodyRegionController.dispose();
    _scheduledController.dispose();
    _performedController.dispose();
    _indicationController.dispose();
    _totalController.dispose();
    _payerController.dispose();
    _patientController.dispose();
    _filenameController.dispose();
    _sizeController.dispose();
    _findingController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final serviceState = ref.watch(clinicalServiceWorkflowControllerProvider);
    final imagingState = ref.watch(medicalImagingWorkflowControllerProvider);
    final ledger = ref
        .watch(patientCareCostLedgerProvider(widget.bundle.patient.patientId))
        .asData
        ?.value;
    final services = _services;
    if (_evidenceServiceId != null &&
        !services.any((item) => item.id == _evidenceServiceId)) {
      _evidenceServiceId = null;
    }
    return DecoratedBox(
      key: const Key('imaging-clinical-service-panel'),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.imagingProcedure,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.imagingProcedureDescription,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              context.l10n.clinicalDetails,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('clinical-service-category'),
              initialValue: _category,
              decoration: const InputDecoration(labelText: 'Service category'),
              items: <DropdownMenuItem<String>>[
                for (final value in const <String>[
                  'imaging',
                  'laboratory',
                  'consultation',
                  'treatment',
                  'rehabilitation',
                  'other_service',
                ])
                  DropdownMenuItem(value: value, child: Text(value)),
              ],
              onChanged: (value) =>
                  setState(() => _category = value ?? 'imaging'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-procedure-name'),
              controller: _nameController,
              decoration: InputDecoration(
                labelText: context.l10n.procedureName,
                prefixIcon: const Icon(Icons.medical_information_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('imaging-modality'),
                    controller: _modalityController,
                    decoration: InputDecoration(
                      labelText: context.l10n.modality,
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: TextField(
                    key: const Key('imaging-body-region'),
                    controller: _bodyRegionController,
                    decoration: InputDecoration(
                      labelText: context.l10n.bodyRegion,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-indication'),
              controller: _indicationController,
              minLines: 2,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: context.l10n.clinicalIndication,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              context.l10n.schedulingServiceDetails,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('imaging-service-status'),
              initialValue: _status,
              decoration: InputDecoration(labelText: context.l10n.status),
              items: <DropdownMenuItem<String>>[
                for (final value in <String>[
                  'ordered',
                  'requested',
                  'scheduled',
                  'in_progress',
                  'performed',
                  'completed',
                  'cancelled',
                  'not_completed',
                ])
                  DropdownMenuItem(
                    value: value,
                    child: Text(context.l10n.stableValue(value)),
                  ),
              ],
              onChanged: (value) =>
                  setState(() => _status = value ?? 'ordered'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('imaging-scheduled-at'),
                    controller: _scheduledController,
                    decoration: InputDecoration(
                      labelText: context.l10n.scheduledDateTime,
                      hintText: '2026-07-25 09:30',
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: TextField(
                    key: const Key('imaging-performed-at'),
                    controller: _performedController,
                    decoration: InputDecoration(
                      labelText: context.l10n.performedDateTime,
                      hintText: '2026-07-25 10:00',
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _ClinicalFinancialSection(
              billable: _recordCost,
              pricingState: _pricingState,
              totalController: _totalController,
              payerController: _payerController,
              patientController: _patientController,
              onBillableChanged: (value) => setState(() => _recordCost = value),
              onPricingStateChanged: (value) =>
                  setState(() => _pricingState = value),
            ),
            if (_validationError != null)
              _InlineMessage(
                message: _validationError!,
                icon: Icons.error_outline,
              ),
            serviceState.when(
              loading: () => const LinearProgressIndicator(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (service) => service == null
                  ? const SizedBox.shrink()
                  : _InlineMessage(
                      message: context.l10n.imagingProcedureSaved(service.name),
                      icon: Icons.check_circle_outline,
                    ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            FilledButton.icon(
              key: const Key('save-imaging-procedure'),
              onPressed: serviceState.isLoading || widget.selectedEvent == null
                  ? null
                  : _saveService,
              icon: const Icon(Icons.save_outlined),
              label: Text(
                _editingServiceId == null
                    ? context.l10n.createImagingProcedure
                    : context.l10n.updateImagingProcedure,
              ),
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.imagingProcedures,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            if (services.isEmpty)
              _InlineMessage(
                message: context.l10n.noImagingProcedures,
                icon: Icons.medical_information_outlined,
              )
            else
              for (final service in services)
                _serviceCard(context, service, ledger),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.imagingEvidence,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('imaging-evidence-service'),
              initialValue: _evidenceServiceId,
              decoration: InputDecoration(
                labelText: context.l10n.selectImagingProcedure,
              ),
              items: <DropdownMenuItem<String>>[
                for (final service in _imagingServices)
                  DropdownMenuItem(
                    value: service.id,
                    child: Text(service.name),
                  ),
              ],
              onChanged: (value) => setState(() => _evidenceServiceId = value),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  flex: 2,
                  child: TextField(
                    key: const Key('imaging-evidence-filename'),
                    controller: _filenameController,
                    decoration: InputDecoration(
                      labelText: context.l10n.imageFilename,
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: TextField(
                    key: const Key('imaging-evidence-size'),
                    controller: _sizeController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: context.l10n.sizeBytes,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              initialValue: _contentType,
              decoration: InputDecoration(labelText: context.l10n.contentType),
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem(
                  value: 'application/dicom',
                  child: Text('application/dicom'),
                ),
                DropdownMenuItem(
                  value: 'application/pdf',
                  child: Text('application/pdf'),
                ),
                DropdownMenuItem(value: 'image/png', child: Text('image/png')),
                DropdownMenuItem(
                  value: 'image/jpeg',
                  child: Text('image/jpeg'),
                ),
              ],
              onChanged: (value) =>
                  setState(() => _contentType = value ?? 'application/dicom'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-evidence-finding'),
              controller: _findingController,
              minLines: 2,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: context.l10n.manualFinding,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                OutlinedButton.icon(
                  key: const Key('choose-imaging-evidence'),
                  onPressed: imagingState.isLoading ? null : _chooseEvidence,
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Choose synthetic image'),
                ),
                OutlinedButton.icon(
                  key: const Key('prepare-imaging-evidence'),
                  onPressed:
                      imagingState.isLoading || _evidenceServiceId == null
                      ? null
                      : _prepareEvidence,
                  icon: const Icon(Icons.attach_file_outlined),
                  label: Text(context.l10n.attachEvidence),
                ),
                OutlinedButton.icon(
                  key: const Key('complete-imaging-evidence'),
                  onPressed:
                      imagingState.isLoading ||
                          imagingState.asData?.value.presign == null ||
                          _selectedEvidenceBytes == null
                      ? null
                      : _completeEvidence,
                  icon: const Icon(Icons.cloud_done_outlined),
                  label: Text(context.l10n.finalizeUpload),
                ),
                OutlinedButton.icon(
                  key: const Key('review-imaging-evidence'),
                  onPressed:
                      imagingState.isLoading ||
                          imagingState.asData?.value.asset?.uploadStatus !=
                              'uploaded'
                      ? null
                      : _reviewEvidence,
                  icon: const Icon(Icons.fact_check_outlined),
                  label: Text(context.l10n.markReviewed),
                ),
              ],
            ),
            imagingState.when(
              loading: () => const LinearProgressIndicator(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (state) => state.message == null
                  ? const SizedBox.shrink()
                  : _InlineMessage(
                      message: state.message!,
                      icon: Icons.check_circle_outline,
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _serviceCard(
    BuildContext context,
    ClinicalServiceItem service,
    CareCostLedgerData? ledger,
  ) {
    final companion = _sourceFinancialCompanion(
      ledger,
      sourceType: 'imaging',
      sourceRecordId: service.id,
    );
    return Padding(
      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: DrAiColors.white,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.sm),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(service.name, style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 4),
              Text(
                '${service.category} · ${service.serviceSubtype ?? ''} · '
                '${service.bodyRegion ?? ''} · '
                '${context.l10n.stableValue(service.status)}',
              ),
              Text(
                '${context.l10n.financialStatus}: '
                '${_financialStatusText(context, companion)}',
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
              Text(
                context.l10n.evidenceFileCount(service.imagingAssetIds.length),
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
              Wrap(
                alignment: WrapAlignment.end,
                spacing: DrAiSpacing.xs,
                children: <Widget>[
                  TextButton(
                    onPressed: () => _editService(service, companion),
                    child: Text(context.l10n.editClinicalService),
                  ),
                  TextButton.icon(
                    onPressed: () async {
                      final financial = await _showFinancialDialog(
                        context,
                        companion,
                      );
                      if (financial == null) return;
                      await ref
                          .read(
                            clinicalServiceWorkflowControllerProvider.notifier,
                          )
                          .updateFinancial(
                            patientId: widget.bundle.patient.patientId,
                            serviceId: service.id,
                            financial: financial,
                          );
                    },
                    icon: const Icon(Icons.price_change_outlined),
                    label: Text(_financialActionText(context, companion)),
                  ),
                  if (service.category == 'imaging')
                    TextButton.icon(
                      onPressed: () =>
                          setState(() => _evidenceServiceId = service.id),
                      icon: const Icon(Icons.attach_file_outlined),
                      label: Text(context.l10n.attachEvidence),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _saveService() async {
    final event = widget.selectedEvent;
    final scheduled = _parseDateTime(_scheduledController.text);
    final performed = _parseDateTime(_performedController.text);
    if (event == null ||
        _nameController.text.trim().length < 2 ||
        _modalityController.text.trim().length < 2 ||
        (_category == 'imaging' &&
            _bodyRegionController.text.trim().length < 2) ||
        (_status == 'scheduled' && scheduled == null) ||
        ({'performed', 'completed'}.contains(_status) && performed == null)) {
      setState(
        () => _validationError = context.l10n.imagingProcedureValidation,
      );
      return;
    }
    final financial = _financialDraft(performed ?? scheduled);
    if (_recordCost && financial == null) return;
    setState(() => _validationError = null);
    await ref
        .read(clinicalServiceWorkflowControllerProvider.notifier)
        .save(
          patientId: widget.bundle.patient.patientId,
          serviceId: _editingServiceId,
          clinicalEventId: event.id,
          category: _category,
          name: _nameController.text.trim(),
          serviceSubtype: _modalityController.text.trim(),
          bodyRegion: _bodyRegionController.text.trim().isEmpty
              ? null
              : _bodyRegionController.text.trim(),
          status: _status,
          scheduledAt: scheduled,
          performedAt: performed,
          indicationSummary: _indicationController.text.trim(),
          financial: financial,
        );
    final saved = ref
        .read(clinicalServiceWorkflowControllerProvider)
        .asData
        ?.value;
    if (mounted && saved != null) {
      setState(() {
        _editingServiceId = saved.id;
        _evidenceServiceId = saved.id;
      });
    }
  }

  ClinicalFinancialDraft? _financialDraft(DateTime? serviceDate) {
    if (!_recordCost) return null;
    if (_pricingState == 'pending_cost') {
      return ClinicalFinancialDraft(
        pricingState: 'pending_cost',
        totalCostMinor: 0,
        payerRequestedMinor: 0,
        patientResponsibilityMinor: 0,
        serviceDate: serviceDate,
      );
    }
    final total = _moneyMinor(_totalController.text);
    final payer = _moneyMinor(_payerController.text);
    final patient = _moneyMinor(_patientController.text);
    if (total == null ||
        total <= 0 ||
        payer == null ||
        patient == null ||
        payer + patient != total) {
      setState(
        () => _validationError = context.l10n.financialAllocationValidation,
      );
      return null;
    }
    return ClinicalFinancialDraft(
      pricingState: _pricingState,
      totalCostMinor: total,
      payerRequestedMinor: payer,
      patientResponsibilityMinor: patient,
      serviceDate: serviceDate,
    );
  }

  void _editService(ClinicalServiceItem service, CareCostItemData? companion) {
    setState(() {
      _editingServiceId = service.id;
      _category = service.category;
      _nameController.text = service.name;
      _modalityController.text = service.serviceSubtype ?? '';
      _bodyRegionController.text = service.bodyRegion ?? '';
      _scheduledController.text = _dateTimeInput(service.scheduledAt);
      _performedController.text = _dateTimeInput(service.performedAt);
      _indicationController.text = service.indicationSummary ?? '';
      _status = service.status;
      _recordCost = companion != null;
      _pricingState = companion?.pricingState ?? 'pending_cost';
      _totalController.text = companion == null
          ? ''
          : _yuanText(companion.actualCostMinor);
      _payerController.text = companion == null
          ? ''
          : _yuanText(companion.payerRequestedMinor);
      _patientController.text = companion == null
          ? ''
          : _yuanText(companion.patientResponsibilityMinor);
    });
  }

  Future<void> _prepareEvidence() async {
    final size =
        _selectedEvidenceBytes?.length ??
        int.tryParse(_sizeController.text.trim());
    if (_filenameController.text.trim().length < 3 ||
        size == null ||
        size < 1) {
      setState(() => _validationError = context.l10n.imageUploadValidation);
      return;
    }
    setState(() => _validationError = null);
    await ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .prepare(
          patientId: widget.bundle.patient.patientId,
          clinicalEventId: widget.selectedEvent?.id,
          clinicalServiceId: _evidenceServiceId,
          filename: _filenameController.text.trim(),
          contentType: _contentType,
          sizeBytes: size,
        );
  }

  Future<void> _chooseEvidence() async {
    final file = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (file == null) return;
    final bytes = await file.readAsBytes();
    final lowerName = file.name.toLowerCase();
    final contentType = lowerName.endsWith('.png') ? 'image/png' : 'image/jpeg';
    if (!mounted) return;
    setState(() {
      _selectedEvidenceBytes = bytes;
      _filenameController.text = file.name;
      _sizeController.text = bytes.length.toString();
      _contentType = contentType;
      _validationError = null;
    });
  }

  Future<void> _completeEvidence() async {
    final bytes = _selectedEvidenceBytes;
    if (bytes == null || bytes.isEmpty) return;
    await ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .uploadAndComplete(
          patientId: widget.bundle.patient.patientId,
          contentType: _contentType,
          bytes: bytes,
        );
  }

  Future<void> _reviewEvidence() async {
    if (_findingController.text.trim().length < 3) {
      setState(() => _validationError = context.l10n.manualFindingValidation);
      return;
    }
    await ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .review(
          patientId: widget.bundle.patient.patientId,
          reviewStatus: 'reviewed',
          findingSummary: _findingController.text.trim(),
          measurementSummary: '',
        );
  }
}

DateTime? _parseDateTime(String value) {
  final normalized = value.trim().replaceFirst(' ', 'T');
  if (normalized.isEmpty) return null;
  return DateTime.tryParse(normalized);
}

String _dateTimeInput(DateTime? value) {
  if (value == null) return '';
  return value
      .toLocal()
      .toIso8601String()
      .substring(0, 16)
      .replaceFirst('T', ' ');
}

class _ConsultationActivitySection extends StatelessWidget {
  const _ConsultationActivitySection({
    required this.bundle,
    required this.selectedEvent,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        _ItemSection<DoctorNoteItem>(
          key: const Key('doctor-notes-section'),
          title: context.l10n.doctorNotes,
          icon: Icons.edit_note_outlined,
          items: _eventDoctorNotes(bundle, selectedEvent),
          emptyTitle: context.l10n.noDoctorNotes,
          itemBuilder: (item) => _InfoTile(
            title: item.title,
            subtitle: context.l10n.linkedToEvent(
              _eventTitle(context, bundle, selectedEvent),
            ),
            body:
                '${item.body}\nPrivate doctor-facing note; hidden from the patient care bundle.',
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _SystemActivitySection(bundle: bundle, selectedEvent: selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _ConsultationRequestPanel(
          patientId: bundle.patient.patientId,
          clinicalEventId: selectedEvent?.id,
        ),
      ],
    );
  }
}

class _ClinicalEventContextCard extends StatelessWidget {
  const _ClinicalEventContextCard({
    required this.bundle,
    required this.selectedEvent,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    final eventTitle = _eventTitle(context, bundle, selectedEvent);
    final visits = _eventVisitHistory(bundle, selectedEvent);
    final diagnoses = _eventDiagnoses(bundle, selectedEvent);
    final prescriptions = _eventPrescriptions(bundle, selectedEvent);
    final reminders = _eventMedicationReminders(bundle, selectedEvent);
    final imagingAssets = _eventImagingAssets(bundle, selectedEvent);
    final doctorNotes = _eventDoctorNotes(bundle, selectedEvent);
    final latestUpdate = visits.isEmpty
        ? context.l10n.noEncounterUpdate
        : _dateLabel(
            context,
            ([...visits]..sort((a, b) => b.occurredAt.compareTo(a.occurredAt)))
                .first
                .occurredAt,
          );
    final diagnosisStatus = diagnoses.isEmpty
        ? context.l10n.diagnosisNotRecorded
        : '${diagnoses.first.status} diagnosis';
    return DecoratedBox(
      key: const Key('clinical-event-context-card'),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(
                  Icons.account_tree_outlined,
                  color: DrAiColors.brand,
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    eventTitle,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.clinicalEventDescription,
              style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                _LightMetricChip(label: diagnosisStatus),
                _LightMetricChip(
                  label: context.l10n.latestUpdate(latestUpdate),
                ),
                _LightMetricChip(
                  label: context.l10n.prescriptionCount(prescriptions.length),
                ),
                _LightMetricChip(
                  label: context.l10n.generatedReminderCount(reminders.length),
                ),
                _LightMetricChip(
                  label: context.l10n.imagingAssetCount(imagingAssets.length),
                ),
                _LightMetricChip(
                  label: context.l10n.noteCount(doctorNotes.length),
                ),
              ],
            ),
            if (selectedEvent != null &&
                selectedEvent!.timeline.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Text(
                context.l10n.eventTimeline,
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              for (final entry in selectedEvent!.timeline.take(4))
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Icon(
                        Icons.timeline_outlined,
                        size: 16,
                        color: DrAiColors.mutedInk,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '${entry.title} - ${_dateLabel(context, entry.occurredAt)}',
                          style: const TextStyle(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ClinicalEventEditor extends ConsumerStatefulWidget {
  const _ClinicalEventEditor({
    required this.bundle,
    required this.selectedEvent,
    required this.onEventChanged,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;
  final ValueChanged<String?>? onEventChanged;

  @override
  ConsumerState<_ClinicalEventEditor> createState() =>
      _ClinicalEventEditorState();
}

class _ClinicalEventEditorState extends ConsumerState<_ClinicalEventEditor> {
  late final TextEditingController _titleController;
  late final TextEditingController _chiefComplaintController;
  late final TextEditingController _symptomSummaryController;
  late final TextEditingController _diagnosisSummaryController;
  late final TextEditingController _onsetDateController;
  String _status = 'active';
  String? _editingEventId;
  String? _validationError;
  bool _localizedDefaultsApplied = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _chiefComplaintController = TextEditingController();
    _symptomSummaryController = TextEditingController();
    _diagnosisSummaryController = TextEditingController();
    _onsetDateController = TextEditingController();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_localizedDefaultsApplied) {
      return;
    }
    _localizedDefaultsApplied = true;
    _loadEvent(widget.selectedEvent);
  }

  @override
  void didUpdateWidget(covariant _ClinicalEventEditor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_localizedDefaultsApplied &&
        oldWidget.selectedEvent?.id != widget.selectedEvent?.id) {
      _loadEvent(widget.selectedEvent);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _chiefComplaintController.dispose();
    _symptomSummaryController.dispose();
    _diagnosisSummaryController.dispose();
    _onsetDateController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(clinicalEventWorkflowControllerProvider);
    return DecoratedBox(
      key: const Key('clinical-event-editor'),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(
                  Icons.edit_calendar_outlined,
                  color: DrAiColors.brand,
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    context.l10n.clinicalEventEditor,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                FilledButton.icon(
                  key: const Key('clinical-event-save-button'),
                  onPressed: state.isLoading ? null : _save,
                  icon: const Icon(Icons.save_outlined),
                  label: Text(
                    _editingEventId == null
                        ? context.l10n.createClinicalEvent
                        : context.l10n.updateClinicalEvent,
                  ),
                ),
                OutlinedButton.icon(
                  key: const Key('clinical-event-new-button'),
                  onPressed: state.isLoading ? null : _startNewEvent,
                  icon: const Icon(Icons.add_circle_outline),
                  label: Text(context.l10n.newEvent),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (widget.bundle.clinicalEvents.isEmpty)
              _InlineMessage(
                message: context.l10n.noClinicalEvent,
                icon: Icons.info_outline,
              )
            else
              Wrap(
                spacing: DrAiSpacing.xs,
                runSpacing: DrAiSpacing.xs,
                children: <Widget>[
                  for (final event in widget.bundle.clinicalEvents)
                    ChoiceChip(
                      key: Key('clinical-event-chip-${event.id}'),
                      label: Text(
                        '${event.title} - ${context.l10n.stableValue(event.status)}',
                      ),
                      selected: event.id == _editingEventId,
                      onSelected: state.isLoading
                          ? null
                          : (_) {
                              widget.onEventChanged?.call(event.id);
                              setState(() => _loadEvent(event));
                            },
                    ),
                ],
              ),
            const SizedBox(height: DrAiSpacing.sm),
            TextField(
              key: const Key('clinical-event-title-field'),
              controller: _titleController,
              maxLength: 160,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.clinicalEventTitle,
                prefixIcon: Icon(Icons.fact_check_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('clinical-event-chief-complaint-field'),
              controller: _chiefComplaintController,
              maxLength: 240,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.chiefComplaint,
                prefixIcon: Icon(Icons.assignment_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('clinical-event-onset-date-field'),
                    controller: _onsetDateController,
                    maxLength: 10,
                    decoration: InputDecoration(
                      counterText: '',
                      labelText: context.l10n.onsetDate,
                      helperText: context.l10n.dateOptional,
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: const Key('clinical-event-status-field'),
                    initialValue: _status,
                    isExpanded: true,
                    decoration: InputDecoration(labelText: context.l10n.status),
                    items: <DropdownMenuItem<String>>[
                      DropdownMenuItem(
                        value: 'active',
                        child: Text(context.l10n.active),
                      ),
                      DropdownMenuItem(
                        value: 'monitoring',
                        child: Text(context.l10n.monitoring),
                      ),
                      DropdownMenuItem(
                        value: 'resolved',
                        child: Text(context.l10n.resolved),
                      ),
                    ],
                    onChanged: (value) =>
                        setState(() => _status = value ?? 'active'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('clinical-event-symptom-summary-field'),
              controller: _symptomSummaryController,
              maxLength: 1200,
              minLines: 2,
              maxLines: 3,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.symptomSummary,
                prefixIcon: Icon(Icons.notes_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('clinical-event-diagnosis-summary-field'),
              controller: _diagnosisSummaryController,
              maxLength: 1200,
              minLines: 2,
              maxLines: 3,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.doctorDiagnosis,
                prefixIcon: Icon(Icons.medical_information_outlined),
              ),
            ),
            _InlineMessage(
              key: Key('clinical-event-doctor-owned-notice'),
              message: context.l10n.eventDiagnosisNotice,
              icon: Icons.lock_outline,
            ),
            if (_validationError != null)
              _InlineMessage(
                message: _validationError!,
                icon: Icons.error_outline,
              ),
            state.when(
              loading: () => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: LinearProgressIndicator(),
              ),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (event) {
                if (event == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  key: const Key('clinical-event-save-success'),
                  message: context.l10n.eventSaved(
                    event.title,
                    context.l10n.stableValue(event.status),
                  ),
                  icon: Icons.check_circle_outline,
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _loadEvent(ClinicalEventItem? event) {
    _editingEventId = event?.id;
    _titleController.text = event?.title ?? context.l10n.newCareEpisode;
    _chiefComplaintController.text =
        event?.chiefComplaint ?? context.l10n.chiefComplaintMissing;
    _symptomSummaryController.text = event?.symptomSummary ?? '';
    _diagnosisSummaryController.text = event?.diagnosisSummary ?? '';
    _onsetDateController.text = event?.onsetDate ?? '';
    _status = event?.status ?? 'active';
  }

  void _startNewEvent() {
    setState(() {
      widget.onEventChanged?.call(null);
      _loadEvent(null);
      _validationError = null;
    });
  }

  bool _validate() {
    final valid =
        _titleController.text.trim().length >= 3 &&
        _chiefComplaintController.text.trim().length >= 3 &&
        (_onsetDateController.text.trim().isEmpty ||
            RegExp(
              r'^\d{4}-\d{2}-\d{2}$',
            ).hasMatch(_onsetDateController.text.trim()));
    setState(() {
      _validationError = valid ? null : context.l10n.eventValidation;
    });
    return valid;
  }

  Future<void> _save() async {
    if (!_validate()) {
      return;
    }
    await ref
        .read(clinicalEventWorkflowControllerProvider.notifier)
        .save(
          patientId: widget.bundle.patient.patientId,
          clinicalEventId: _editingEventId,
          title: _titleController.text.trim(),
          chiefComplaint: _chiefComplaintController.text.trim(),
          symptomSummary: _symptomSummaryController.text.trim(),
          diagnosisSummary: _diagnosisSummaryController.text.trim(),
          onsetDate: _onsetDateController.text.trim(),
          status: _status,
        );
    final saved = ref.read(clinicalEventWorkflowControllerProvider);
    if (saved.hasValue && saved.value != null) {
      widget.onEventChanged?.call(saved.value!.id);
      setState(() => _loadEvent(saved.value));
    }
  }
}

class _EventLinkNotice extends StatelessWidget {
  const _EventLinkNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return _InlineMessage(
      key: const Key('clinical-event-link-notice'),
      message: text,
      icon: Icons.account_tree_outlined,
    );
  }
}

class _SystemActivitySection extends StatelessWidget {
  const _SystemActivitySection({
    required this.bundle,
    required this.selectedEvent,
  });

  final PatientCareBundle bundle;
  final ClinicalEventItem? selectedEvent;

  @override
  Widget build(BuildContext context) {
    final items = <_ActivityDisplayItem>[
      if (selectedEvent != null)
        for (final entry in selectedEvent!.timeline)
          _ActivityDisplayItem(
            title: entry.title,
            subtitle: _dateLabel(context, entry.occurredAt),
            body: context.l10n.timelineEntry(
              context.l10n.stableValue(entry.entryType),
            ),
          ),
      for (final prescription in _eventPrescriptions(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: context.l10n.prescriptionStatus(
            context.l10n.stableValue(prescription.status),
          ),
          subtitle: _dateLabel(context, prescription.issuedAt),
          body: context.l10n.medicationLinesLinked(
            prescription.medications.length,
            _eventTitle(context, bundle, selectedEvent),
          ),
        ),
      for (final reminder in _eventMedicationReminders(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: reminder.reminderType == 'refill'
              ? context.l10n.generatedRefillReminder
              : context.l10n.generatedMedicationReminder,
          subtitle:
              '${context.l10n.stableValue(reminder.status)} - ${_dateLabel(context, reminder.nextDueAt)}',
          body:
              '${reminder.scheduleLabel}\n${context.l10n.createdFromMedicationSchedule}',
        ),
      for (final asset in _eventImagingAssets(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: context.l10n.imagingStatusTitle(
            context.l10n.stableValue(asset.reviewStatus),
          ),
          subtitle:
              '${context.l10n.stableValue(asset.uploadStatus)} - ${asset.storageProvider}',
          body: context.l10n.manualReviewStatus(
            _eventTitle(context, bundle, selectedEvent),
          ),
        ),
    ];
    return _ItemSection<_ActivityDisplayItem>(
      key: const Key('consultation-activity-timeline-section'),
      title: context.l10n.activityTimeline,
      icon: Icons.timeline_outlined,
      items: items,
      emptyTitle: context.l10n.noActivity,
      itemBuilder: (item) => _InfoTile(
        title: item.title,
        subtitle: item.subtitle,
        body: item.body,
      ),
    );
  }
}

class _ActivityDisplayItem {
  const _ActivityDisplayItem({
    required this.title,
    required this.subtitle,
    required this.body,
  });

  final String title;
  final String subtitle;
  final String body;
}

class _LightMetricChip extends StatelessWidget {
  const _LightMetricChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.sm),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.xs,
          vertical: 6,
        ),
        child: Text(label, style: const TextStyle(fontSize: 12)),
      ),
    );
  }
}

Widget _medicalRecordsSection(BuildContext context, PatientCareBundle bundle) {
  return _ItemSection<MedicalRecordItem>(
    key: const Key('medical-history-section'),
    title: context.l10n.medicalHistory,
    icon: Icons.description_outlined,
    items: bundle.records,
    emptyTitle: context.l10n.noMedicalRecords,
    itemBuilder: (item) => _InfoTile(
      title: item.title,
      subtitle: item.category,
      body: item.summary,
    ),
  );
}

Widget _medicalHistoryReviewsSection(
  BuildContext context,
  PatientCareBundle bundle,
) {
  return _ItemSection<MedicalHistoryReviewItem>(
    key: const Key('medical-history-reviews-section'),
    title: context.l10n.doctorReviewAmendments,
    icon: Icons.verified_user_outlined,
    items: bundle.medicalHistoryReviews,
    emptyTitle: context.l10n.noDoctorReviews,
    itemBuilder: (item) => _InfoTile(
      title: _historyReviewActionLabel(context, item.action),
      subtitle:
          '${context.l10n.stableValue(item.targetType)} - ${_dateLabel(context, item.createdAt)}',
      body:
          '${item.amendmentSummary ?? item.correctionRequest ?? context.l10n.clinicianVerifiedHistory}\n'
          '${context.l10n.auditOverlayNotice}',
    ),
  );
}

List<_HistoryReviewTarget> _historyReviewTargets(
  BuildContext context,
  PatientCareBundle bundle,
) {
  return <_HistoryReviewTarget>[
    for (final allergy in bundle.allergies)
      _HistoryReviewTarget(
        key: 'allergy:${allergy.id}',
        targetType: 'allergy',
        targetId: allergy.id,
        label: context.l10n.allergyLabel(allergy.label),
      ),
    for (final condition in bundle.chronicDiseases)
      _HistoryReviewTarget(
        key: 'chronic_disease:${condition.id}',
        targetType: 'chronic_disease',
        targetId: condition.id,
        label: context.l10n.chronicDiseaseLabel(condition.name),
      ),
    for (final record in bundle.records)
      _HistoryReviewTarget(
        key: 'medical_record:${record.id}',
        targetType: 'medical_record',
        targetId: record.id,
        label: context.l10n.medicalRecordLabel(record.title),
      ),
  ];
}

String _historyReviewActionLabel(BuildContext context, String action) {
  return switch (action) {
    'verified' => context.l10n.clinicianVerified,
    'amendment' => context.l10n.doctorAmendment,
    'correction_requested' => context.l10n.patientCorrectionRequested,
    _ => action,
  };
}

Widget _imagingListSection(
  BuildContext context,
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<MedicalImagingAsset>(
    key: const Key('imaging-assets-section'),
    title: context.l10n.imaging,
    icon: Icons.image_search_outlined,
    items: _eventImagingAssets(bundle, selectedEvent),
    emptyTitle: context.l10n.noImagingAssets,
    itemBuilder: (item) => _InfoTile(
      title: context.l10n.contentAsset(item.contentType),
      subtitle:
          '${context.l10n.stableValue(item.uploadStatus)} - ${context.l10n.stableValue(item.reviewStatus)}',
      body:
          '${item.sizeBytes} bytes via ${item.storageProvider}\n'
          '${context.l10n.uploaded(_dateLabel(context, item.uploadedAt))}\n'
          '${context.l10n.findingResult(item.findingSummary ?? context.l10n.pendingManualReview)}\n'
          '${context.l10n.measurementObservation(item.measurementSummary ?? context.l10n.notRecorded)}',
    ),
  );
}

Widget _medicationsListSection(
  BuildContext context,
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return Consumer(
    builder: (context, ref, child) {
      final ledger = ref
          .watch(patientCareCostLedgerProvider(bundle.patient.patientId))
          .asData
          ?.value;
      return _ItemSection<MedicationItem>(
        key: const Key('medications-section'),
        title: context.l10n.medications,
        icon: Icons.medication_outlined,
        items: _eventMedications(bundle, selectedEvent),
        emptyTitle: context.l10n.noMedicationsRecorded,
        itemBuilder: (item) {
          final companion = _sourceFinancialCompanion(
            ledger,
            sourceType: 'medication',
            sourceRecordId: item.id,
          );
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _InfoTile(
                title: item.name,
                subtitle:
                    '${item.dosage} - ${context.l10n.stableValue(item.status)}',
                body:
                    '${item.schedule}\n${item.note}\n'
                    '${context.l10n.financialStatus}: '
                    '${_financialStatusText(context, companion)}',
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  key: Key('medication-cost-${item.id}'),
                  onPressed: () async {
                    final financial = await _showFinancialDialog(
                      context,
                      companion,
                    );
                    if (financial == null) return;
                    await ref
                        .read(medicationWorkflowControllerProvider.notifier)
                        .saveMedication(
                          patientId: bundle.patient.patientId,
                          clinicalEventId: item.clinicalEventId,
                          medicationId: item.id,
                          name: item.name,
                          dosage: item.dosage,
                          schedule: item.schedule,
                          status: item.status,
                          note: item.note,
                          financial: financial,
                        );
                  },
                  icon: const Icon(Icons.price_change_outlined),
                  label: Text(_financialActionText(context, companion)),
                ),
              ),
            ],
          );
        },
      );
    },
  );
}

Widget _prescriptionsListSection(
  BuildContext context,
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<PrescriptionItem>(
    key: const Key('prescriptions-section'),
    title: context.l10n.prescriptions,
    icon: Icons.receipt_long_outlined,
    items: _eventPrescriptions(bundle, selectedEvent),
    emptyTitle: context.l10n.noPrescriptions,
    itemBuilder: (item) => _InfoTile(
      title: context.l10n.prescriptionStatus(
        context.l10n.stableValue(item.status),
      ),
      subtitle: context.l10n.medicationLines(item.medications.length),
      body: _prescriptionSummary(context, item),
    ),
  );
}

Widget _remindersListSection(
  BuildContext context,
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<MedicationReminderItem>(
    key: const Key('medication-reminders-section'),
    title: context.l10n.medicationRemindersTitle,
    icon: Icons.notifications_active_outlined,
    items: _eventMedicationReminders(bundle, selectedEvent),
    emptyTitle: context.l10n.noMedicationReminderRecords,
    itemBuilder: (item) => _InfoTile(
      title: item.reminderType == 'refill'
          ? context.l10n.refillReminder
          : context.l10n.medicationReminder,
      subtitle:
          '${context.l10n.stableValue(item.status)} - ${context.l10n.stableValue(item.channel)}',
      body:
          '${item.scheduleLabel}\n${context.l10n.nextDue(_dateLabel(context, item.nextDueAt))}',
    ),
  );
}

enum _MedicationWorkflowMode {
  medication(icon: Icons.medication_liquid_outlined),
  prescription(icon: Icons.receipt_long_outlined);

  const _MedicationWorkflowMode({required this.icon});

  final IconData icon;
}

class _MedicationWorkflowPanel extends ConsumerStatefulWidget {
  const _MedicationWorkflowPanel({
    required this.bundle,
    required this.clinicalEventId,
    required this.mode,
  });

  final PatientCareBundle bundle;
  final String? clinicalEventId;
  final _MedicationWorkflowMode mode;

  @override
  ConsumerState<_MedicationWorkflowPanel> createState() =>
      _MedicationWorkflowPanelState();
}

class _MedicationWorkflowPanelState
    extends ConsumerState<_MedicationWorkflowPanel> {
  late TextEditingController _nameController;
  late final TextEditingController _dosageController;
  late TextEditingController _scheduleController;
  late final TextEditingController _noteController;
  late final TextEditingController _prescriptionNoteController;
  late final TextEditingController _totalCostController;
  late final TextEditingController _payerRequestedController;
  late final TextEditingController _patientResponsibilityController;
  String _status = 'active';
  String _pricingState = 'pending_cost';
  bool _billable = false;
  bool _financialLoaded = false;
  String? _validationMessage;
  bool _localizedDefaultsApplied = false;

  MedicationItem? get _selectedMedication {
    final medications = _eventMedicationsById(
      widget.bundle.medications,
      widget.clinicalEventId,
    );
    return medications.isEmpty ? null : medications.first;
  }

  @override
  void initState() {
    super.initState();
    final medication = _selectedMedication;
    _nameController = TextEditingController(text: medication?.name ?? '');
    _dosageController = TextEditingController(
      text: medication?.dosage ?? '10 mg',
    );
    _scheduleController = TextEditingController(
      text: medication?.schedule ?? '',
    );
    _noteController = TextEditingController(text: medication?.note ?? '');
    _prescriptionNoteController = TextEditingController(text: '');
    _totalCostController = TextEditingController();
    _payerRequestedController = TextEditingController();
    _patientResponsibilityController = TextEditingController();
    _status = medication?.status ?? 'active';
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_localizedDefaultsApplied || _selectedMedication != null) {
      return;
    }
    _localizedDefaultsApplied = true;
    _nameController.text = context.l10n.medication;
    _scheduleController.text = context.l10n.scheduleNotRecorded;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _dosageController.dispose();
    _scheduleController.dispose();
    _noteController.dispose();
    _prescriptionNoteController.dispose();
    _totalCostController.dispose();
    _payerRequestedController.dispose();
    _patientResponsibilityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(medicationWorkflowControllerProvider);
    if (widget.mode == _MedicationWorkflowMode.medication) {
      final ledger = ref.watch(
        patientCareCostLedgerProvider(widget.bundle.patient.patientId),
      );
      _loadFinancialCompanion(ledger.asData?.value);
    }
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(widget.mode.icon, color: DrAiColors.brand),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    widget.mode == _MedicationWorkflowMode.medication
                        ? context.l10n.medicationScheduleEditor
                        : context.l10n.prescriptionOrderWorkflow,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            if (widget.mode == _MedicationWorkflowMode.prescription)
              _InlineMessage(
                message: _selectedMedication == null
                    ? context.l10n.saveMedicationFirst
                    : context.l10n.prescriptionWorkflowDescription,
                icon: Icons.info_outline,
              ),
            if (widget.clinicalEventId == null)
              _InlineMessage(
                message: context.l10n.selectEventMedication,
                icon: Icons.account_tree_outlined,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('medication-name-field'),
              controller: _nameController,
              maxLength: 160,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.medicationName,
                prefixIcon: const Icon(Icons.medication_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('medication-dosage-field'),
                    controller: _dosageController,
                    maxLength: 120,
                    decoration: InputDecoration(
                      counterText: '',
                      labelText: context.l10n.dosage,
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: const Key('medication-status-field'),
                    initialValue: _status,
                    isExpanded: true,
                    decoration: InputDecoration(labelText: context.l10n.status),
                    items: <DropdownMenuItem<String>>[
                      DropdownMenuItem(
                        value: 'active',
                        child: Text(context.l10n.active),
                      ),
                      DropdownMenuItem(
                        value: 'paused',
                        child: Text(context.l10n.paused),
                      ),
                      DropdownMenuItem(
                        value: 'stopped',
                        child: Text(context.l10n.stopped),
                      ),
                    ],
                    onChanged: (value) =>
                        setState(() => _status = value ?? 'active'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('medication-schedule-field'),
              controller: _scheduleController,
              maxLength: 160,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.schedule,
              ),
            ),
            if (widget.mode == _MedicationWorkflowMode.medication) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              TextField(
                key: const Key('medication-note-field'),
                controller: _noteController,
                maxLength: 800,
                minLines: 2,
                maxLines: 3,
                decoration: InputDecoration(
                  counterText: '',
                  labelText: context.l10n.medicationNote,
                ),
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _ClinicalFinancialSection(
                billable: _billable,
                pricingState: _pricingState,
                totalController: _totalCostController,
                payerController: _payerRequestedController,
                patientController: _patientResponsibilityController,
                onBillableChanged: (value) => setState(() => _billable = value),
                onPricingStateChanged: (value) =>
                    setState(() => _pricingState = value),
              ),
            ],
            if (widget.mode ==
                _MedicationWorkflowMode.prescription) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              TextField(
                key: const Key('prescription-note-field'),
                controller: _prescriptionNoteController,
                maxLength: 400,
                minLines: 2,
                maxLines: 3,
                decoration: InputDecoration(
                  counterText: '',
                  labelText: context.l10n.prescriptionNote,
                  prefixIcon: const Icon(Icons.notes_outlined),
                ),
              ),
            ],
            if (_validationMessage != null)
              _InlineMessage(message: _validationMessage!),
            state.when(
              data: (message) => message == null
                  ? const SizedBox.shrink()
                  : _InlineMessage(
                      key: const Key('medication-workflow-success'),
                      message: message,
                      icon: Icons.check_circle_outline,
                    ),
              loading: () => const LinearProgressIndicator(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                if (widget.mode == _MedicationWorkflowMode.medication)
                  FilledButton.icon(
                    key: const Key('save-medication-button'),
                    onPressed: state.isLoading || widget.clinicalEventId == null
                        ? null
                        : _saveMedication,
                    icon: const Icon(Icons.save_outlined),
                    label: Text(
                      _selectedMedication == null
                          ? context.l10n.addMedication
                          : context.l10n.updateMedication,
                    ),
                  ),
                if (widget.mode == _MedicationWorkflowMode.prescription)
                  FilledButton.icon(
                    key: const Key('create-prescription-button'),
                    onPressed: state.isLoading || widget.clinicalEventId == null
                        ? null
                        : _createPrescription,
                    icon: const Icon(Icons.receipt_long_outlined),
                    label: Text(context.l10n.issuePrescription),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  bool _validateMedicationFields() {
    final valid =
        _nameController.text.trim().length >= 2 &&
        _dosageController.text.trim().isNotEmpty &&
        _scheduleController.text.trim().length >= 2;
    setState(() {
      _validationMessage = valid ? null : context.l10n.medicationValidation;
    });
    return valid;
  }

  Future<void> _saveMedication() async {
    if (!_validateMedicationFields()) {
      return;
    }
    final financial = _financialDraft();
    if (_billable && financial == null) {
      return;
    }
    await ref
        .read(medicationWorkflowControllerProvider.notifier)
        .saveMedication(
          patientId: widget.bundle.patient.patientId,
          clinicalEventId: widget.clinicalEventId,
          medicationId: _selectedMedication?.id,
          name: _nameController.text.trim(),
          dosage: _dosageController.text.trim(),
          schedule: _scheduleController.text.trim(),
          status: _status,
          note: _noteController.text.trim(),
          financial: financial,
        );
  }

  void _loadFinancialCompanion(CareCostLedgerData? ledger) {
    if (_financialLoaded || ledger == null) return;
    _financialLoaded = true;
    final medication = _selectedMedication;
    if (medication == null) return;
    CareCostItemData? companion;
    for (final event in ledger.events) {
      for (final item in event.items) {
        if (item.sourceType == 'medication' &&
            item.sourceRecordId == medication.id) {
          companion = item;
          break;
        }
      }
    }
    if (companion == null) return;
    _billable = true;
    _pricingState = companion.pricingState;
    _totalCostController.text = _yuanText(companion.actualCostMinor);
    _payerRequestedController.text = _yuanText(companion.payerRequestedMinor);
    _patientResponsibilityController.text = _yuanText(
      companion.patientResponsibilityMinor,
    );
  }

  ClinicalFinancialDraft? _financialDraft() {
    if (!_billable) return null;
    if (_pricingState == 'pending_cost') {
      return const ClinicalFinancialDraft(
        pricingState: 'pending_cost',
        totalCostMinor: 0,
        payerRequestedMinor: 0,
        patientResponsibilityMinor: 0,
      );
    }
    final total = _moneyMinor(_totalCostController.text);
    final payer = _moneyMinor(_payerRequestedController.text);
    final patient = _moneyMinor(_patientResponsibilityController.text);
    if (total == null ||
        total <= 0 ||
        payer == null ||
        patient == null ||
        payer + patient != total) {
      setState(() {
        _validationMessage = context.l10n.financialAllocationValidation;
      });
      return null;
    }
    return ClinicalFinancialDraft(
      pricingState: _pricingState,
      totalCostMinor: total,
      payerRequestedMinor: payer,
      patientResponsibilityMinor: patient,
    );
  }

  Future<void> _createPrescription() async {
    if (!_validateMedicationFields()) {
      return;
    }
    final medication = _selectedMedication;
    if (medication == null) {
      setState(() {
        _validationMessage = context.l10n.saveMedicationFirst;
      });
      return;
    }
    await ref
        .read(medicationWorkflowControllerProvider.notifier)
        .createPrescription(
          patientId: widget.bundle.patient.patientId,
          clinicalEventId: widget.clinicalEventId,
          medicationId: medication.id,
          name: _nameController.text.trim(),
          dosage: _dosageController.text.trim(),
          schedule: _scheduleController.text.trim(),
          notes: _prescriptionNoteController.text.trim(),
        );
  }
}

class _ClinicalFinancialSection extends StatelessWidget {
  const _ClinicalFinancialSection({
    required this.billable,
    required this.pricingState,
    required this.totalController,
    required this.payerController,
    required this.patientController,
    required this.onBillableChanged,
    required this.onPricingStateChanged,
  });

  final bool billable;
  final String pricingState;
  final TextEditingController totalController;
  final TextEditingController payerController;
  final TextEditingController patientController;
  final ValueChanged<bool> onBillableChanged;
  final ValueChanged<String> onPricingStateChanged;

  @override
  Widget build(BuildContext context) {
    final amountsEnabled = billable && pricingState != 'pending_cost';
    return Material(
      key: const Key('clinical-financial-section'),
      color: DrAiColors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(DrAiRadii.sm),
        side: const BorderSide(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.financialDetails,
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
            ),
            Text(
              context.l10n.financialDetailsDescription,
              style: const TextStyle(
                color: DrAiColors.inkSecondary,
                fontSize: 12,
              ),
            ),
            CheckboxListTile(
              key: const Key('billable-clinical-item-checkbox'),
              contentPadding: EdgeInsets.zero,
              value: billable,
              onChanged: (value) => onBillableChanged(value ?? false),
              title: Text(context.l10n.billableClinicalItem),
              subtitle: Text(context.l10n.billableClinicalItemDescription),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            if (billable) ...<Widget>[
              DropdownButtonFormField<String>(
                key: const Key('pricing-state-field'),
                initialValue: pricingState,
                decoration: InputDecoration(labelText: context.l10n.costStatus),
                items: <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'pending_cost',
                    child: Text(context.l10n.costPending),
                  ),
                  DropdownMenuItem(
                    value: 'estimated',
                    child: Text(context.l10n.costEstimate),
                  ),
                  DropdownMenuItem(
                    value: 'final',
                    child: Text(context.l10n.costFinal),
                  ),
                ],
                onChanged: (value) =>
                    onPricingStateChanged(value ?? 'pending_cost'),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              InputDecorator(
                decoration: InputDecoration(labelText: context.l10n.currency),
                child: const Text('CNY'),
              ),
              if (!amountsEnabled)
                Padding(
                  padding: const EdgeInsets.only(top: DrAiSpacing.xs),
                  child: Text(
                    context.l10n.pendingCostSubmissionBlocked,
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      fontSize: 12,
                    ),
                  ),
                ),
              if (amountsEnabled) ...<Widget>[
                const SizedBox(height: DrAiSpacing.xs),
                _MoneyField(
                  key: const Key('total-cost-field'),
                  controller: totalController,
                  label: context.l10n.totalCostCny,
                ),
                const SizedBox(height: DrAiSpacing.xs),
                _MoneyField(
                  key: const Key('payer-requested-field'),
                  controller: payerController,
                  label: context.l10n.requestedFromPayerCny,
                ),
                const SizedBox(height: DrAiSpacing.xs),
                _MoneyField(
                  key: const Key('patient-responsibility-field'),
                  controller: patientController,
                  label: context.l10n.expectedPatientResponsibilityCny,
                ),
                const SizedBox(height: DrAiSpacing.xs),
                Text(
                  context.l10n.financialAllocationNotice,
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _MoneyField extends StatelessWidget {
  const _MoneyField({required this.controller, required this.label, super.key});

  final TextEditingController controller;
  final String label;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, prefixText: '¥ '),
    );
  }
}

int? _moneyMinor(String value) {
  final amount = double.tryParse(value.trim());
  if (amount == null || amount < 0) return null;
  return (amount * 100).round();
}

String _yuanText(int minor) => (minor / 100).toStringAsFixed(2);

CareCostItemData? _sourceFinancialCompanion(
  CareCostLedgerData? ledger, {
  required String sourceType,
  required String? sourceRecordId,
}) {
  if (ledger == null || sourceRecordId == null) return null;
  for (final event in ledger.events) {
    for (final item in event.items) {
      if (item.sourceType == sourceType &&
          item.sourceRecordId == sourceRecordId) {
        return item;
      }
    }
  }
  return null;
}

String _financialStatusText(BuildContext context, CareCostItemData? companion) {
  if (companion == null) return context.l10n.noCostRecorded;
  if (companion.alreadySubmitted) return context.l10n.alreadySubmitted;
  return switch (companion.pricingState) {
    'pending_cost' => context.l10n.costPending,
    'estimated' => context.l10n.estimatedCost(
      _yuanText(companion.actualCostMinor),
    ),
    _ => context.l10n.finalCost(_yuanText(companion.actualCostMinor)),
  };
}

String _financialActionText(BuildContext context, CareCostItemData? companion) {
  if (companion == null) return context.l10n.addCost;
  if (companion.pricingState == 'pending_cost') {
    return context.l10n.completeCost;
  }
  return context.l10n.editCost;
}

Future<ClinicalFinancialDraft?> _showFinancialDialog(
  BuildContext context,
  CareCostItemData? companion,
) {
  return showDialog<ClinicalFinancialDraft>(
    context: context,
    builder: (context) => _ClinicalFinancialDialog(companion: companion),
  );
}

class _ClinicalFinancialDialog extends StatefulWidget {
  const _ClinicalFinancialDialog({this.companion});

  final CareCostItemData? companion;

  @override
  State<_ClinicalFinancialDialog> createState() =>
      _ClinicalFinancialDialogState();
}

class _ClinicalFinancialDialogState extends State<_ClinicalFinancialDialog> {
  late String _pricingState;
  late final TextEditingController _totalController;
  late final TextEditingController _payerController;
  late final TextEditingController _patientController;
  String? _error;

  @override
  void initState() {
    super.initState();
    final companion = widget.companion;
    _pricingState = companion?.pricingState ?? 'pending_cost';
    _totalController = TextEditingController(
      text: companion == null ? '' : _yuanText(companion.actualCostMinor),
    );
    _payerController = TextEditingController(
      text: companion == null ? '' : _yuanText(companion.payerRequestedMinor),
    );
    _patientController = TextEditingController(
      text: companion == null
          ? ''
          : _yuanText(companion.patientResponsibilityMinor),
    );
  }

  @override
  void dispose() {
    _totalController.dispose();
    _payerController.dispose();
    _patientController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final amountsEnabled = _pricingState != 'pending_cost';
    return AlertDialog(
      title: Text(_financialActionText(context, widget.companion)),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            DropdownButtonFormField<String>(
              key: const Key('cost-dialog-pricing-state'),
              initialValue: _pricingState,
              decoration: InputDecoration(labelText: context.l10n.costStatus),
              items: <DropdownMenuItem<String>>[
                DropdownMenuItem(
                  value: 'pending_cost',
                  child: Text(context.l10n.costPending),
                ),
                DropdownMenuItem(
                  value: 'estimated',
                  child: Text(context.l10n.costEstimate),
                ),
                DropdownMenuItem(
                  value: 'final',
                  child: Text(context.l10n.costFinal),
                ),
              ],
              onChanged: (value) =>
                  setState(() => _pricingState = value ?? 'pending_cost'),
            ),
            if (amountsEnabled) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              _MoneyField(
                controller: _totalController,
                label: context.l10n.totalCostCny,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              _MoneyField(
                controller: _payerController,
                label: context.l10n.requestedFromPayerCny,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              _MoneyField(
                controller: _patientController,
                label: context.l10n.expectedPatientResponsibilityCny,
              ),
            ],
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: DrAiSpacing.xs),
                child: Text(
                  _error!,
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(context.l10n.cancel),
        ),
        FilledButton(
          key: const Key('save-cost-dialog'),
          onPressed: _save,
          child: Text(context.l10n.saveCost),
        ),
      ],
    );
  }

  void _save() {
    if (_pricingState == 'pending_cost') {
      Navigator.of(context).pop(
        const ClinicalFinancialDraft(
          pricingState: 'pending_cost',
          totalCostMinor: 0,
          payerRequestedMinor: 0,
          patientResponsibilityMinor: 0,
        ),
      );
      return;
    }
    final total = _moneyMinor(_totalController.text);
    final payer = _moneyMinor(_payerController.text);
    final patient = _moneyMinor(_patientController.text);
    if (total == null ||
        total <= 0 ||
        payer == null ||
        patient == null ||
        payer + patient != total) {
      setState(() => _error = context.l10n.financialAllocationValidation);
      return;
    }
    Navigator.of(context).pop(
      ClinicalFinancialDraft(
        pricingState: _pricingState,
        totalCostMinor: total,
        payerRequestedMinor: payer,
        patientResponsibilityMinor: patient,
      ),
    );
  }
}

class DemoAssessmentWorkflow extends ConsumerStatefulWidget {
  const DemoAssessmentWorkflow({
    required this.patientId,
    required this.clinicalEventId,
    super.key,
  });

  final String patientId;
  final String? clinicalEventId;

  @override
  ConsumerState<DemoAssessmentWorkflow> createState() =>
      _DemoAssessmentWorkflowState();
}

class _DemoAssessmentWorkflowState
    extends ConsumerState<DemoAssessmentWorkflow> {
  final _filenameController = TextEditingController();
  final _sizeController = TextEditingController();
  final _findingController = TextEditingController();
  final _measurementController = TextEditingController();
  String _contentType = 'image/png';
  String _fixtureId = '';
  String? _uploadValidationError;
  String? _assessmentValidationError;

  @override
  void dispose() {
    _filenameController.dispose();
    _sizeController.dispose();
    _findingController.dispose();
    _measurementController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(demoAssetPresignControllerProvider);
    final imagingState = ref.watch(medicalImagingWorkflowControllerProvider);
    final createState = ref.watch(assessmentCreateControllerProvider);
    final assessments = ref.watch(assessmentListProvider(widget.patientId));
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const _SimulationDisclosure(),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              context.l10n.imagingUpload,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('demo-upload-filename-field'),
              controller: _filenameController,
              maxLength: 160,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.imageFilename,
                helperText: context.l10n.imageMetadataHelper,
                prefixIcon: const Icon(Icons.image_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Row(
              children: <Widget>[
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: const Key('demo-upload-content-type-field'),
                    initialValue: _contentType,
                    isExpanded: true,
                    decoration: InputDecoration(
                      labelText: context.l10n.contentType,
                      prefixIcon: const Icon(Icons.tune_outlined),
                    ),
                    items: const <DropdownMenuItem<String>>[
                      DropdownMenuItem(
                        value: 'image/png',
                        child: Text('image/png'),
                      ),
                      DropdownMenuItem(
                        value: 'image/jpeg',
                        child: Text('image/jpeg'),
                      ),
                      DropdownMenuItem(
                        value: 'application/dicom',
                        child: Text('application/dicom'),
                      ),
                    ],
                    onChanged: (value) =>
                        setState(() => _contentType = value ?? 'image/png'),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: TextField(
                    key: const Key('demo-upload-size-field'),
                    controller: _sizeController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: context.l10n.sizeBytes,
                      prefixIcon: const Icon(Icons.straighten_outlined),
                    ),
                  ),
                ),
              ],
            ),
            if (_uploadValidationError != null)
              _InlineMessage(
                message: _uploadValidationError!,
                icon: Icons.error_outline,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            FilledButton.icon(
              key: const Key('demo-upload-presign-button'),
              onPressed: uploadState.isLoading ? null : _presignUpload,
              icon: uploadState.isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.cloud_upload_outlined),
              label: Text(context.l10n.prepareUpload),
            ),
            uploadState.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (presign) {
                if (presign == null) {
                  return const SizedBox.shrink();
                }
                return _UploadPreparedCard(presign: presign);
              },
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.imagingWorkflow,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-finding-field'),
              controller: _findingController,
              maxLength: 1200,
              minLines: 2,
              maxLines: 4,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.manualFinding,
                prefixIcon: const Icon(Icons.fact_check_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-measurement-field'),
              controller: _measurementController,
              maxLength: 240,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.manualMeasurement,
                prefixIcon: const Icon(Icons.straighten_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                OutlinedButton.icon(
                  key: const Key('imaging-prepare-button'),
                  onPressed:
                      imagingState.isLoading || widget.clinicalEventId == null
                      ? null
                      : _prepareImaging,
                  icon: const Icon(Icons.add_photo_alternate_outlined),
                  label: Text(context.l10n.prepareImaging),
                ),
                imagingState.when(
                  loading: () => const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  error: (error, stackTrace) => _InlineMessage(
                    message: _safeErrorMessage(context, error),
                  ),
                  data: (state) {
                    final canComplete =
                        state.presign != null &&
                        state.asset?.uploadStatus != 'uploaded';
                    final canReview =
                        state.asset?.uploadStatus == 'uploaded' &&
                        state.asset?.reviewStatus != 'reviewed';
                    return Wrap(
                      spacing: DrAiSpacing.xs,
                      runSpacing: DrAiSpacing.xs,
                      children: <Widget>[
                        OutlinedButton.icon(
                          key: const Key('imaging-complete-button'),
                          onPressed: canComplete ? _completeImaging : null,
                          icon: const Icon(Icons.cloud_done_outlined),
                          label: Text(context.l10n.finalizeUpload),
                        ),
                        OutlinedButton.icon(
                          key: const Key('imaging-review-button'),
                          onPressed: canReview ? _reviewImaging : null,
                          icon: const Icon(Icons.fact_check_outlined),
                          label: Text(context.l10n.markReviewed),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
            imagingState.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) => const SizedBox.shrink(),
              data: (state) {
                if (state.presign == null && state.asset == null) {
                  return const SizedBox.shrink();
                }
                return _ImagingWorkflowCard(state: state);
              },
            ),
            const SizedBox(height: DrAiSpacing.md),
            if (widget.clinicalEventId == null)
              _InlineMessage(
                message: context.l10n.selectEventImaging,
                icon: Icons.account_tree_outlined,
              ),
            Text(
              context.l10n.assessmentForm,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('assessment-fixture-field'),
              initialValue: _fixtureId,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: context.l10n.assessmentFixture,
                prefixIcon: const Icon(Icons.science_outlined),
              ),
              items: const <DropdownMenuItem<String>>[],
              onChanged: (value) => setState(() => _fixtureId = value ?? ''),
            ),
            if (_assessmentValidationError != null)
              _InlineMessage(
                message: _assessmentValidationError!,
                icon: Icons.error_outline,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            OutlinedButton.icon(
              key: const Key('assessment-run-button'),
              onPressed: createState.isLoading ? null : _runAssessment,
              icon: createState.isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.analytics_outlined),
              label: Text(context.l10n.runAssessment),
            ),
            createState.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (result) {
                if (result == null) {
                  return const SizedBox.shrink();
                }
                return _AssessmentResultCard(result: result);
              },
            ),
            const SizedBox(height: DrAiSpacing.sm),
            assessments.when(
              loading: () => DashboardLoadingView(
                label: context.l10n.loadingAssessmentHistory,
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(context, error),
                onRetry: () =>
                    ref.invalidate(assessmentListProvider(widget.patientId)),
              ),
              data: (data) {
                if (data.items.isEmpty) {
                  return _EmptyState(
                    icon: Icons.analytics_outlined,
                    title: context.l10n.noAssessmentResults,
                    body: context.l10n.assessmentEmptyDescription,
                  );
                }
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    for (final result in data.items)
                      _AssessmentResultCard(result: result),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _presignUpload() {
    final filename = _filenameController.text.trim();
    final size = int.tryParse(_sizeController.text.trim());
    if (filename.length < 3 || size == null || size < 1) {
      setState(() {
        _uploadValidationError = context.l10n.imageUploadValidation;
      });
      return;
    }
    setState(() => _uploadValidationError = null);
    ref
        .read(demoAssetPresignControllerProvider.notifier)
        .presign(
          patientId: widget.patientId,
          filename: filename,
          contentType: _contentType,
          sizeBytes: size,
        );
  }

  void _prepareImaging() {
    final filename = _filenameController.text.trim();
    final size = int.tryParse(_sizeController.text.trim());
    if (filename.length < 3 || size == null || size < 1) {
      setState(() {
        _uploadValidationError = context.l10n.imageUploadValidation;
      });
      return;
    }
    setState(() => _uploadValidationError = null);
    ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .prepare(
          patientId: widget.patientId,
          clinicalEventId: widget.clinicalEventId,
          filename: filename,
          contentType: _contentType,
          sizeBytes: size,
        );
  }

  void _completeImaging() {
    final size = int.tryParse(_sizeController.text.trim());
    if (size == null || size < 1) {
      setState(() {
        _uploadValidationError = context.l10n.uploadedBytesValidation;
      });
      return;
    }
    setState(() => _uploadValidationError = null);
    ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .complete(patientId: widget.patientId, uploadedSizeBytes: size);
  }

  void _reviewImaging() {
    if (_findingController.text.trim().length < 3) {
      setState(() {
        _uploadValidationError = context.l10n.manualFindingValidation;
      });
      return;
    }
    setState(() => _uploadValidationError = null);
    ref
        .read(medicalImagingWorkflowControllerProvider.notifier)
        .review(
          patientId: widget.patientId,
          reviewStatus: 'reviewed',
          findingSummary: _findingController.text.trim(),
          measurementSummary: _measurementController.text.trim(),
        );
  }

  void _runAssessment() {
    if (_fixtureId.trim().isEmpty) {
      setState(() {
        _assessmentValidationError = context.l10n.assessmentSelectionValidation;
      });
      return;
    }
    setState(() => _assessmentValidationError = null);
    ref
        .read(assessmentCreateControllerProvider.notifier)
        .create(
          patientId: widget.patientId,
          fixtureId: _fixtureId,
          idempotencyKey:
              'doctor-${widget.patientId}-$_fixtureId-${DateTime.now().millisecondsSinceEpoch}',
        );
  }
}

class _RecoveryPlanEditor extends ConsumerStatefulWidget {
  const _RecoveryPlanEditor({
    required this.patientId,
    required this.clinicalEventId,
  });

  final String patientId;
  final String? clinicalEventId;

  @override
  ConsumerState<_RecoveryPlanEditor> createState() =>
      _RecoveryPlanEditorState();
}

class _RecoveryPlanEditorState extends ConsumerState<_RecoveryPlanEditor> {
  final _titleController = TextEditingController();
  final _instructionsController = TextEditingController();
  final _medicationController = TextEditingController();
  final _exerciseController = TextEditingController();
  final _dietController = TextEditingController();
  final _followUpController = TextEditingController();
  String? _selectedPlanId;
  String? _validationError;

  @override
  void dispose() {
    _titleController.dispose();
    _instructionsController.dispose();
    _medicationController.dispose();
    _exerciseController.dispose();
    _dietController.dispose();
    _followUpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final plans = ref.watch(recoveryPlanListProvider(widget.patientId));
    final editorState = ref.watch(recoveryPlanEditorControllerProvider);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.recoveryPlanEditor,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (widget.clinicalEventId == null)
              _InlineMessage(
                message: context.l10n.selectEventRecovery,
                icon: Icons.account_tree_outlined,
              ),
            plans.when(
              loading: () => DashboardLoadingView(
                label: context.l10n.loadingRecoveryPlans,
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(context, error),
                onRetry: () =>
                    ref.invalidate(recoveryPlanListProvider(widget.patientId)),
              ),
              data: (data) {
                final eventPlans = _eventRecoveryPlansById(
                  data.items,
                  widget.clinicalEventId,
                );
                final activeEventPlans = eventPlans
                    .where((plan) => plan.status == 'active')
                    .toList();
                _selectInitialPlan(eventPlans);
                final selectedPlan = eventPlans
                    .where((plan) => plan.planId == _selectedPlanId)
                    .firstOrNull;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    if (eventPlans.isEmpty)
                      _InlineMessage(
                        message: context.l10n.noEventRecoveryPlan,
                        icon: Icons.info_outline,
                      )
                    else
                      Wrap(
                        spacing: DrAiSpacing.xs,
                        runSpacing: DrAiSpacing.xs,
                        children: <Widget>[
                          for (final plan in eventPlans)
                            ChoiceChip(
                              label: Text(
                                '${plan.title} - ${context.l10n.stableValue(plan.status)} / ${context.l10n.stableValue(plan.reviewStatus)}',
                              ),
                              selected: plan.planId == _selectedPlanId,
                              onSelected: (_) => _loadPlan(plan),
                            ),
                        ],
                      ),
                    if (selectedPlan != null) ...<Widget>[
                      const SizedBox(height: DrAiSpacing.xs),
                      _InlineMessage(
                        key: const Key('recovery-plan-review-status'),
                        message: context.l10n.planStatusReview(
                          context.l10n.stableValue(selectedPlan.status),
                          context.l10n.stableValue(selectedPlan.reviewStatus),
                          selectedPlan.progressSummary.completedTaskCount,
                          selectedPlan.progressSummary.taskCount,
                        ),
                        icon: Icons.fact_check_outlined,
                      ),
                    ],
                    const SizedBox(height: DrAiSpacing.xs),
                    _InlineMessage(
                      key: const Key('recovery-plan-active-event-guardrail'),
                      message: activeEventPlans.isEmpty
                          ? context.l10n.noActiveEventPlan
                          : activeEventPlans.length == 1
                          ? context.l10n.oneActiveEventPlan
                          : context.l10n.multipleActivePlans,
                      icon: Icons.assignment_turned_in_outlined,
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                    TextField(
                      key: const Key('recovery-plan-title-field'),
                      controller: _titleController,
                      maxLength: 160,
                      decoration: InputDecoration(
                        counterText: '',
                        labelText: context.l10n.planTitle,
                        prefixIcon: const Icon(Icons.assignment_outlined),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    TextField(
                      key: const Key('recovery-plan-instructions-field'),
                      controller: _instructionsController,
                      maxLength: 1200,
                      minLines: 2,
                      maxLines: 4,
                      decoration: InputDecoration(
                        counterText: '',
                        labelText: context.l10n.instructions,
                        prefixIcon: const Icon(Icons.notes_outlined),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    _taskField(
                      key: const Key('recovery-medication-task-field'),
                      controller: _medicationController,
                      label: context.l10n.medicationTask,
                      icon: Icons.medication_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-exercise-task-field'),
                      controller: _exerciseController,
                      label: context.l10n.exerciseTask,
                      icon: Icons.directions_walk_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-diet-task-field'),
                      controller: _dietController,
                      label: context.l10n.dietTask,
                      icon: Icons.restaurant_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-follow-up-task-field'),
                      controller: _followUpController,
                      label: context.l10n.followUpTask,
                      icon: Icons.event_available_outlined,
                    ),
                    if (_validationError != null)
                      _InlineMessage(
                        message: _validationError!,
                        icon: Icons.error_outline,
                      ),
                    editorState.when(
                      loading: () => const Padding(
                        padding: EdgeInsets.only(top: DrAiSpacing.xs),
                        child: LinearProgressIndicator(),
                      ),
                      error: (error, stackTrace) => _InlineMessage(
                        message: _safeErrorMessage(context, error),
                      ),
                      data: (plan) {
                        if (plan == null) {
                          return const SizedBox.shrink();
                        }
                        return _InlineMessage(
                          message:
                              '${plan.title} ${context.l10n.stableValue(plan.status)}. '
                              '${context.l10n.reviewStatus(context.l10n.stableValue(plan.reviewStatus))}',
                          icon: Icons.check_circle_outline,
                        );
                      },
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    Wrap(
                      spacing: DrAiSpacing.xs,
                      runSpacing: DrAiSpacing.xs,
                      children: <Widget>[
                        FilledButton.icon(
                          key: const Key('recovery-plan-save-button'),
                          onPressed:
                              editorState.isLoading ||
                                  widget.clinicalEventId == null
                              ? null
                              : _save,
                          icon: const Icon(Icons.save_outlined),
                          label: Text(context.l10n.saveDraft),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-submit-review-button'),
                          onPressed: editorState.isLoading
                              ? null
                              : _submitReview,
                          icon: const Icon(Icons.outgoing_mail),
                          label: Text(context.l10n.submitReview),
                        ),
                        OutlinedButton.icon(
                          key: const Key(
                            'recovery-plan-request-changes-button',
                          ),
                          onPressed: editorState.isLoading
                              ? null
                              : _requestChanges,
                          icon: const Icon(Icons.edit_note_outlined),
                          label: Text(context.l10n.requestChanges),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-activate-button'),
                          onPressed: editorState.isLoading ? null : _approve,
                          icon: const Icon(Icons.task_alt_outlined),
                          label: Text(context.l10n.approvePatient),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-complete-button'),
                          onPressed: editorState.isLoading
                              ? null
                              : _completePlan,
                          icon: const Icon(Icons.done_all_outlined),
                          label: Text(context.l10n.completePlan),
                        ),
                      ],
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _taskField({
    required Key key,
    required TextEditingController controller,
    required String label,
    required IconData icon,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: TextField(
        key: key,
        controller: controller,
        maxLength: 160,
        decoration: InputDecoration(
          counterText: '',
          labelText: label,
          prefixIcon: Icon(icon),
        ),
      ),
    );
  }

  void _selectInitialPlan(List<RecoveryPlanData> plans) {
    if (_selectedPlanId != null || plans.isEmpty) {
      return;
    }
    final active = plans.where((plan) => plan.status == 'active').firstOrNull;
    _applyPlan(active ?? plans.first);
  }

  void _loadPlan(RecoveryPlanData plan) {
    setState(() {
      _applyPlan(plan);
    });
  }

  void _applyPlan(RecoveryPlanData plan) {
    _selectedPlanId = plan.planId;
    _titleController.text = plan.title;
    _instructionsController.text = plan.instructions;
    for (final task in plan.tasks) {
      switch (task.category) {
        case 'medication':
          _medicationController.text = task.title;
        case 'exercise':
          _exerciseController.text = task.title;
        case 'diet':
          _dietController.text = task.title;
        case 'follow_up':
          _followUpController.text = task.title;
      }
    }
  }

  List<RecoveryTaskInput> _taskInputs() {
    return <RecoveryTaskInput>[
      RecoveryTaskInput(
        category: 'medication',
        title: _medicationController.text.trim(),
        detail: context.l10n.medicationTaskDetail,
        dueLabel: context.l10n.today,
        notificationTime: '09:00',
      ),
      RecoveryTaskInput(
        category: 'exercise',
        title: _exerciseController.text.trim(),
        detail: context.l10n.exerciseTaskDetail,
        dueLabel: context.l10n.today,
      ),
      RecoveryTaskInput(
        category: 'diet',
        title: _dietController.text.trim(),
        detail: context.l10n.dietTaskDetail,
        dueLabel: context.l10n.today,
      ),
      RecoveryTaskInput(
        category: 'follow_up',
        title: _followUpController.text.trim(),
        detail: context.l10n.followUpTaskDetail,
        dueLabel: context.l10n.today,
      ),
    ];
  }

  bool _validate() {
    final fields = <String>[
      _titleController.text,
      _instructionsController.text,
      _medicationController.text,
      _exerciseController.text,
      _dietController.text,
      _followUpController.text,
    ];
    if (fields.any((field) => field.trim().length < 3)) {
      setState(() {
        _validationError = context.l10n.planFieldsValidation;
      });
      return false;
    }
    setState(() => _validationError = null);
    return true;
  }

  void _save() {
    if (!_validate()) {
      return;
    }
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .saveDraft(
          patientId: widget.patientId,
          clinicalEventId: widget.clinicalEventId,
          planId: _selectedPlanId,
          title: _titleController.text.trim(),
          instructions: _instructionsController.text.trim(),
          tasks: _taskInputs(),
        );
  }

  String? _latestPlanId() {
    final latest = ref.read(recoveryPlanEditorControllerProvider);
    return (latest.hasValue ? latest.value?.planId : null) ?? _selectedPlanId;
  }

  bool _requireSelectedPlan(String actionLabel) {
    if (_latestPlanId() != null) {
      setState(() => _validationError = null);
      return true;
    }
    setState(() {
      _validationError = context.l10n.savePlanBeforeAction(actionLabel);
    });
    return false;
  }

  void _submitReview() {
    if (!_requireSelectedPlan(context.l10n.submitReview)) {
      return;
    }
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .submitForReview(patientId: widget.patientId, planId: _latestPlanId()!);
  }

  void _requestChanges() {
    if (!_requireSelectedPlan(context.l10n.requestChanges)) {
      return;
    }
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .requestChanges(patientId: widget.patientId, planId: _latestPlanId()!);
  }

  void _approve() {
    final planId = _latestPlanId();
    if (planId == null) {
      setState(() {
        _validationError = context.l10n.submitPlanFirst;
      });
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .approve(patientId: widget.patientId, planId: planId);
  }

  void _completePlan() {
    if (!_requireSelectedPlan(context.l10n.completePlan)) {
      return;
    }
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .completePlan(patientId: widget.patientId, planId: _latestPlanId()!);
  }
}

class _ConsultationRequestPanel extends ConsumerStatefulWidget {
  const _ConsultationRequestPanel({
    required this.patientId,
    required this.clinicalEventId,
  });

  final String patientId;
  final String? clinicalEventId;

  @override
  ConsumerState<_ConsultationRequestPanel> createState() =>
      _ConsultationRequestPanelState();
}

class _ConsultationRequestPanelState
    extends ConsumerState<_ConsultationRequestPanel> {
  final _specialtyController = TextEditingController();
  final _summaryController = TextEditingController();
  final _totalCostController = TextEditingController();
  final _payerRequestedController = TextEditingController();
  final _patientResponsibilityController = TextEditingController();
  String _priority = 'routine';
  String _pricingState = 'pending_cost';
  bool _billable = false;
  ConsultationRequestItem? _editingConsultation;
  String? _validationError;

  @override
  void dispose() {
    _specialtyController.dispose();
    _summaryController.dispose();
    _totalCostController.dispose();
    _payerRequestedController.dispose();
    _patientResponsibilityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final list = ref.watch(consultationListProvider);
    final createState = ref.watch(consultationRequestControllerProvider);
    final financialLedger = ref
        .watch(patientCareCostLedgerProvider(widget.patientId))
        .asData
        ?.value;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              context.l10n.specialistConsultation,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.specialistDescription,
              style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
            ),
            if (widget.clinicalEventId == null)
              _InlineMessage(
                message: context.l10n.selectEventConsultation,
                icon: Icons.account_tree_outlined,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('consultation-specialty-field'),
              controller: _specialtyController,
              maxLength: 120,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.specialty,
                prefixIcon: const Icon(Icons.groups_2_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('consultation-summary-field'),
              controller: _summaryController,
              maxLength: 240,
              minLines: 2,
              maxLines: 3,
              decoration: InputDecoration(
                counterText: '',
                labelText: context.l10n.questionSummary,
                prefixIcon: const Icon(Icons.forum_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            SegmentedButton<String>(
              segments: <ButtonSegment<String>>[
                ButtonSegment<String>(
                  value: 'routine',
                  icon: const Icon(Icons.schedule_outlined),
                  label: Text(context.l10n.routine),
                ),
                ButtonSegment<String>(
                  value: 'soon',
                  icon: const Icon(Icons.priority_high_outlined),
                  label: Text(context.l10n.soon),
                ),
              ],
              selected: <String>{_priority},
              onSelectionChanged: (values) =>
                  setState(() => _priority = values.first),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _ClinicalFinancialSection(
              billable: _billable,
              pricingState: _pricingState,
              totalController: _totalCostController,
              payerController: _payerRequestedController,
              patientController: _patientResponsibilityController,
              onBillableChanged: (value) => setState(() => _billable = value),
              onPricingStateChanged: (value) =>
                  setState(() => _pricingState = value),
            ),
            if (_validationError != null)
              _InlineMessage(
                message: _validationError!,
                icon: Icons.error_outline,
              ),
            createState.when(
              loading: () => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: LinearProgressIndicator(),
              ),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(context, error)),
              data: (request) {
                if (request == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  message: context.l10n.consultationSubmitted(
                    request.specialty,
                    context.l10n.stableValue(request.status),
                  ),
                  icon: Icons.check_circle_outline,
                );
              },
            ),
            const SizedBox(height: DrAiSpacing.xs),
            FilledButton.icon(
              key: const Key('consultation-request-button'),
              onPressed: createState.isLoading || widget.clinicalEventId == null
                  ? null
                  : _submit,
              icon: const Icon(Icons.outgoing_mail),
              label: Text(
                _editingConsultation == null
                    ? context.l10n.requestSpecialistReview
                    : context.l10n.saveConsultationCost,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            list.when(
              loading: () => DashboardLoadingView(
                label: context.l10n.loadingConsultations,
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(context, error),
                onRetry: () => ref.invalidate(consultationListProvider),
              ),
              data: (data) {
                final items = data.items
                    .where(
                      (item) =>
                          item.patientId == widget.patientId &&
                          (widget.clinicalEventId == null ||
                              item.clinicalEventId == widget.clinicalEventId),
                    )
                    .toList();
                if (items.isEmpty) {
                  return _EmptyState(
                    icon: Icons.support_agent_outlined,
                    title: context.l10n.noSpecialistRequest,
                    body: context.l10n.specialistEmptyDescription,
                  );
                }
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    for (final item in items)
                      Builder(
                        builder: (context) {
                          final companion = _sourceFinancialCompanion(
                            financialLedger,
                            sourceType: 'consultation',
                            sourceRecordId: item.clinicalServiceId,
                          );
                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: <Widget>[
                              _InfoTile(
                                title:
                                    '${item.specialty} - ${context.l10n.stableValue(item.status)}',
                                subtitle: context.l10n.priority(
                                  context.l10n.stableValue(item.priority),
                                ),
                                body:
                                    '${item.questionSummary}\n'
                                    '${context.l10n.financialStatus}: '
                                    '${_financialStatusText(context, companion)}',
                              ),
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton.icon(
                                  key: Key(
                                    'edit-consultation-cost-${item.consultationId}',
                                  ),
                                  onPressed: () => _editConsultationFinancial(
                                    item,
                                    financialLedger,
                                  ),
                                  icon: const Icon(Icons.price_change_outlined),
                                  label: Text(
                                    _financialActionText(context, companion),
                                  ),
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _submit() {
    final specialty = _specialtyController.text.trim();
    final summary = _summaryController.text.trim();
    if (specialty.length < 3 || summary.length < 8) {
      setState(() {
        _validationError = context.l10n.consultationValidation;
      });
      return;
    }
    final financial = _consultationFinancialDraft();
    if (_billable && financial == null) return;
    setState(() => _validationError = null);
    final editing = _editingConsultation;
    final controller = ref.read(consultationRequestControllerProvider.notifier);
    if (editing != null) {
      if (financial == null) {
        setState(() {
          _validationError = context.l10n.financialAllocationValidation;
        });
        return;
      }
      controller.updateFinancial(
        patientId: widget.patientId,
        consultation: editing,
        financial: financial,
      );
    } else {
      controller.create(
        patientId: widget.patientId,
        clinicalEventId: widget.clinicalEventId,
        specialty: specialty,
        questionSummary: summary,
        priority: _priority,
        financial: financial,
      );
    }
  }

  ClinicalFinancialDraft? _consultationFinancialDraft() {
    if (!_billable) return null;
    if (_pricingState == 'pending_cost') {
      return const ClinicalFinancialDraft(
        pricingState: 'pending_cost',
        totalCostMinor: 0,
        payerRequestedMinor: 0,
        patientResponsibilityMinor: 0,
      );
    }
    final total = _moneyMinor(_totalCostController.text);
    final payer = _moneyMinor(_payerRequestedController.text);
    final patient = _moneyMinor(_patientResponsibilityController.text);
    if (total == null ||
        total <= 0 ||
        payer == null ||
        patient == null ||
        payer + patient != total) {
      setState(() {
        _validationError = context.l10n.financialAllocationValidation;
      });
      return null;
    }
    return ClinicalFinancialDraft(
      pricingState: _pricingState,
      totalCostMinor: total,
      payerRequestedMinor: payer,
      patientResponsibilityMinor: patient,
    );
  }

  void _editConsultationFinancial(
    ConsultationRequestItem consultation,
    CareCostLedgerData? ledger,
  ) {
    CareCostItemData? companion;
    for (final event in ledger?.events ?? const <CareCostEventData>[]) {
      for (final item in event.items) {
        if (item.sourceType == 'consultation' &&
            item.sourceRecordId == consultation.clinicalServiceId) {
          companion = item;
          break;
        }
      }
    }
    setState(() {
      _specialtyController.text = consultation.specialty;
      _summaryController.text = consultation.questionSummary;
      _priority = consultation.priority;
      _editingConsultation = consultation;
      _billable = true;
      _pricingState = companion?.pricingState ?? 'pending_cost';
      _totalCostController.text = companion == null
          ? ''
          : _yuanText(companion.actualCostMinor);
      _payerRequestedController.text = companion == null
          ? ''
          : _yuanText(companion.payerRequestedMinor);
      _patientResponsibilityController.text = companion == null
          ? ''
          : _yuanText(companion.patientResponsibilityMinor);
      _validationError = null;
    });
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context) {
    final patient = bundle.patient;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              patient.displayName,
              style: const TextStyle(
                color: DrAiColors.white,
                fontSize: 22,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              patient.syntheticIdentifier,
              style: const TextStyle(color: DrAiColors.patientAccent),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              patient.relationshipLabel,
              style: const TextStyle(color: DrAiColors.white),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _demographicsLine(context, patient),
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _historyLine(context, bundle),
              key: const Key('medical-history-overview-section'),
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              patient.overview,
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
          ],
        ),
      ),
    );
  }
}

String _demographicsLine(BuildContext context, PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null) context.l10n.bornYear(patient.birthYear!),
    if (patient.sex != null) context.l10n.stableValue(patient.sex!),
    if (patient.preferredLanguage != null)
      context.l10n.stableValue(patient.preferredLanguage!),
    if (patient.contactPreference != null)
      context.l10n.stableValue(patient.contactPreference!),
  ];
  return values.isEmpty ? context.l10n.demographicsMissing : values.join(' - ');
}

String _ageSexLabel(BuildContext context, PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null)
      context.l10n.ageYears(DateTime.now().year - patient.birthYear!),
    if (patient.sex != null && patient.sex!.trim().isNotEmpty)
      context.l10n.stableValue(patient.sex!),
  ];
  return values.isEmpty ? context.l10n.ageSexMissing : values.join(' - ');
}

String _activePlanLabel(BuildContext context, RecoveryPlanListData data) {
  RecoveryPlanData? activePlan;
  for (final plan in data.items) {
    if (plan.status == 'active') {
      activePlan = plan;
      break;
    }
  }
  activePlan ??= data.items.isEmpty ? null : data.items.first;
  if (activePlan == null) {
    return context.l10n.recoveryPlanNone;
  }
  return context.l10n.recoveryPlanStatus(
    context.l10n.stableValue(activePlan.status),
    context.l10n.stableValue(activePlan.reviewStatus),
  );
}

String _lastVisitLabel(BuildContext context, List<VisitHistoryItem> visits) {
  if (visits.isEmpty) {
    return context.l10n.noneRecorded;
  }
  final sorted = [...visits]
    ..sort((a, b) => b.occurredAt.compareTo(a.occurredAt));
  return _dateLabel(context, sorted.first.occurredAt);
}

String _workflowStatus(BuildContext context, PatientCareBundle bundle) {
  final hasActivity =
      bundle.records.isNotEmpty ||
      bundle.visitHistory.isNotEmpty ||
      bundle.diagnoses.isNotEmpty ||
      bundle.medications.isNotEmpty ||
      bundle.prescriptions.isNotEmpty ||
      bundle.imagingAssets.isNotEmpty ||
      bundle.doctorNotes.isNotEmpty;
  return hasActivity
      ? context.l10n.workflowReviewReady
      : context.l10n.workflowSetupNeeded;
}

ClinicalEventItem? _selectedClinicalEvent(
  PatientCareBundle bundle,
  String? preferredEventId,
) {
  if (bundle.clinicalEvents.isEmpty) {
    return null;
  }
  if (preferredEventId != null) {
    for (final event in bundle.clinicalEvents) {
      if (event.id == preferredEventId) {
        return event;
      }
    }
  }
  for (final event in bundle.clinicalEvents) {
    if (event.status == 'active' || event.status == 'monitoring') {
      return event;
    }
  }
  return bundle.clinicalEvents.first;
}

String _eventTitle(
  BuildContext context,
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  if (selectedEvent != null) {
    return context.l10n.clinicalEventNamed(selectedEvent.title);
  }
  if (bundle.diagnoses.isNotEmpty) {
    return context.l10n.clinicalEventNamed(bundle.diagnoses.first.label);
  }
  if (bundle.visitHistory.isNotEmpty) {
    return context.l10n.clinicalEventNamed(bundle.visitHistory.first.title);
  }
  return context.l10n.clinicalEventSetup;
}

String _eventLinkSummary(BuildContext context, ClinicalEventItem event) {
  final counts = event.linkedResourceCounts;
  return context.l10n.eventResourceSummary(
    counts['prescriptions'] ?? 0,
    counts['medications'] ?? 0,
    counts['recovery_plans'] ?? 0,
    counts['imaging_assets'] ?? 0,
    counts['doctor_notes'] ?? 0,
  );
}

List<VisitHistoryItem> _eventVisitHistory(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.visitHistory, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<DiagnosisItem> _eventDiagnoses(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.diagnoses, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<MedicationItem> _eventMedications(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventMedicationsById(bundle.medications, selectedEvent?.id);
}

List<MedicationItem> _eventMedicationsById(
  List<MedicationItem> items,
  String? clinicalEventId,
) {
  return _eventItems(items, clinicalEventId, (item) => item.clinicalEventId);
}

List<PrescriptionItem> _eventPrescriptions(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.prescriptions, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<MedicationReminderItem> _eventMedicationReminders(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.medicationReminders, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<RecoveryPlanData> _eventRecoveryPlansById(
  List<RecoveryPlanData> items,
  String? clinicalEventId,
) {
  return _eventItems(items, clinicalEventId, (item) => item.clinicalEventId);
}

List<MedicalImagingAsset> _eventImagingAssets(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.imagingAssets, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<DoctorNoteItem> _eventDoctorNotes(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _eventItems(bundle.doctorNotes, selectedEvent?.id, (item) {
    return item.clinicalEventId;
  });
}

List<T> _eventItems<T>(
  List<T> items,
  String? clinicalEventId,
  String? Function(T item) eventIdForItem,
) {
  if (clinicalEventId == null) {
    return items;
  }
  return items
      .where((item) => eventIdForItem(item) == clinicalEventId)
      .toList();
}

String _historyLine(BuildContext context, PatientCareBundle bundle) {
  return context.l10n.historyOverview(
    _labelsOrEmpty(context, bundle.allergies),
    _namesOrEmpty(context, bundle.chronicDiseases),
    _visitsOrEmpty(context, bundle.visitHistory),
    _diagnosesOrEmpty(context, bundle.diagnoses),
  );
}

String _labelsOrEmpty(BuildContext context, List<PatientAllergyItem> items) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.label).join(', ');
}

String _namesOrEmpty(BuildContext context, List<ChronicDiseaseItem> items) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.name).join(', ');
}

String _visitsOrEmpty(BuildContext context, List<VisitHistoryItem> items) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.title).join(', ');
}

String _diagnosesOrEmpty(BuildContext context, List<DiagnosisItem> items) {
  if (items.isEmpty) {
    return context.l10n.noneRecorded;
  }
  return items.map((item) => item.label).join(', ');
}

String _prescriptionSummary(BuildContext context, PrescriptionItem item) {
  final lines = item.medications
      .map((line) => '${line.name}: ${line.dosage} - ${line.schedule}')
      .join('\n');
  final notes = item.notes == null || item.notes!.isEmpty
      ? context.l10n.noPrescriptionNote
      : item.notes!;
  return '$lines\n$notes';
}

String _dateLabel(BuildContext context, DateTime? value) {
  if (value == null) {
    return context.l10n.notScheduled;
  }
  return DateFormat.yMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).format(value);
}

class _ItemSection<T> extends StatelessWidget {
  const _ItemSection({
    required this.title,
    required this.icon,
    required this.items,
    required this.emptyTitle,
    required this.itemBuilder,
    super.key,
  });

  final String title;
  final IconData icon;
  final List<T> items;
  final String emptyTitle;
  final Widget Function(T item) itemBuilder;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(icon, color: DrAiColors.brand),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (items.isEmpty)
              _EmptyState(
                icon: Icons.inbox_outlined,
                title: emptyTitle,
                body: context.l10n.emptySectionDescription,
              )
            else
              for (final item in items) ...<Widget>[
                itemBuilder(item),
                const SizedBox(height: DrAiSpacing.xs),
              ],
          ],
        ),
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  const _InfoTile({
    required this.title,
    required this.subtitle,
    required this.body,
  });

  final String title;
  final String subtitle;
  final String body;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            Text(
              subtitle,
              style: const TextStyle(color: DrAiColors.brand, fontSize: 12),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(body),
          ],
        ),
      ),
    );
  }
}

class _SimulationDisclosure extends StatelessWidget {
  const _SimulationDisclosure();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.patientAccent,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.sm),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Icon(Icons.info_outline, color: DrAiColors.ink),
            const SizedBox(width: DrAiSpacing.xs),
            Expanded(
              child: Text(
                context.l10n.stagingNotice,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InlineMessage extends StatelessWidget {
  const _InlineMessage({
    required this.message,
    this.icon = Icons.warning_amber_outlined,
    super.key,
  });

  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, size: 18, color: DrAiColors.accentOrange),
          const SizedBox(width: DrAiSpacing.xs),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ),
        ],
      ),
    );
  }
}

class _UploadPreparedCard extends StatelessWidget {
  const _UploadPreparedCard({required this.presign});

  final DemoAssetPresign presign;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
      child: _InfoTile(
        title: context.l10n.uploadPrepared,
        subtitle: context.l10n.uploadMetadata(presign.method),
        body:
            '${context.l10n.objectKey(presign.objectKey)}\n'
            '${context.l10n.expires(presign.expiresAt.toUtc().toIso8601String())}\n'
            '${context.l10n.stableValue(presign.safetyLabel)}',
      ),
    );
  }
}

class _ImagingWorkflowCard extends StatelessWidget {
  const _ImagingWorkflowCard({required this.state});

  final MedicalImagingWorkflowState state;

  @override
  Widget build(BuildContext context) {
    final presign = state.presign;
    final asset = state.asset;
    final title = asset == null
        ? context.l10n.imagingUploadPrepared
        : context.l10n.imagingStatus;
    final subtitle = asset == null
        ? '${presign?.storageProvider ?? 'tencent_cos'} metadata'
        : '${context.l10n.stableValue(asset.uploadStatus)} - ${context.l10n.stableValue(asset.reviewStatus)}';
    final body = asset == null
        ? context.l10n.expires(
            presign?.expiresAt.toUtc().toIso8601String() ?? '',
          )
        : '${asset.contentType}, ${context.l10n.bytesVia(asset.uploadedSizeBytes ?? asset.sizeBytes, asset.storageProvider)}\n'
              '${context.l10n.reviewed(_dateLabel(context, asset.reviewedAt))}\n'
              '${context.l10n.findingResult(asset.findingSummary ?? context.l10n.pendingManualReview)}\n'
              '${context.l10n.measurementObservation(asset.measurementSummary ?? context.l10n.notRecorded)}';
    return Padding(
      key: const Key('imaging-workflow-status'),
      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
      child: _InfoTile(title: title, subtitle: subtitle, body: body),
    );
  }
}

class _AssessmentResultCard extends StatelessWidget {
  const _AssessmentResultCard({required this.result});

  final AssessmentResult result;

  @override
  Widget build(BuildContext context) {
    final score = result.demoScore.toStringAsFixed(2);
    return Padding(
      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
      child: DecoratedBox(
        key: Key('assessment-result-${result.assessmentId}'),
        decoration: BoxDecoration(
          color: DrAiColors.white,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.sm),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                context.l10n.stableValue(result.safetyLabel),
                style: const TextStyle(
                  color: DrAiColors.danger,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Wrap(
                spacing: DrAiSpacing.xs,
                runSpacing: DrAiSpacing.xs,
                children: <Widget>[
                  _ResultChip(
                    label: context.l10n.risk(
                      context.l10n.stableValue(result.riskBand),
                    ),
                  ),
                  _ResultChip(label: context.l10n.assessmentScore(score)),
                  _ResultChip(
                    label: context.l10n.stableValue(result.inputCompleteness),
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(context.l10n.modelVersion(result.modelVersion)),
              const SizedBox(height: DrAiSpacing.xs),
              for (final limitation in result.limitations)
                Text('- ${context.l10n.stableValue(limitation)}'),
              const SizedBox(height: DrAiSpacing.xs),
              for (final step in result.recommendedNextSteps)
                Text('- ${context.l10n.stableValue(step)}'),
            ],
          ),
        ),
      ),
    );
  }
}

class _ResultChip extends StatelessWidget {
  const _ResultChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(label),
      backgroundColor: DrAiColors.brandSoft,
      side: const BorderSide(color: DrAiColors.outline),
    );
  }
}

class _CarePanel extends StatelessWidget {
  const _CarePanel({
    required this.title,
    required this.icon,
    required this.child,
    this.trailing,
  });

  final String title;
  final IconData icon;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.fromLTRB(
              DrAiSpacing.sm,
              DrAiSpacing.xs,
              DrAiSpacing.xs,
              DrAiSpacing.xs,
            ),
            child: Row(
              children: <Widget>[
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.brandSoft,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(DrAiSpacing.xs),
                    child: Icon(icon, color: DrAiColors.brand, size: 20),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: DrAiColors.ink,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                ?trailing,
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(DrAiSpacing.sm),
              child: child,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.title,
    required this.body,
    super.key,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 42, color: DrAiColors.mutedInk),
            const SizedBox(height: DrAiSpacing.sm),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              body,
              textAlign: TextAlign.center,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ],
        ),
      ),
    );
  }
}

String _safeErrorMessage(BuildContext context, Object error) {
  if (error is ApiError) {
    if (error.code == 'unauthenticated') {
      return context.l10n.sessionEnded;
    }
    if (error.code == 'not_found') {
      return context.l10n.patientRecordUnavailable;
    }
    if (error.code == 'validation_failed') {
      return context.l10n.checkInformation;
    }
    if (error.code == 'unsupported_media_type') {
      return error.message;
    }
    if (error.code == 'payload_too_large') {
      return error.message;
    }
    if (error.code == 'service_unavailable') {
      return context.l10n.unableToReachRetry;
    }
    return error.message;
  }
  return context.l10n.unableToReachRetry;
}
