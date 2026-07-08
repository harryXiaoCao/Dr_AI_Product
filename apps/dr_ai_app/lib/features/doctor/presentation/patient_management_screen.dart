import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
      selectedIndex: 4,
      child: ColoredBox(
        color: DrAiColors.brandSoft,
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.sm),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final wide = constraints.maxWidth >= 980;
              final list = _PatientSearchPane(
                controller: _searchController,
                patients: patients,
                selectedPatientId: _selectedPatientId,
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
                onOpenPatientPicker: () =>
                    _showPatientPicker(context, patients),
              );
              if (wide) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    SizedBox(width: 320, child: list),
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
  overview(
    label: 'Overview',
    icon: Icons.space_dashboard_outlined,
    summary: 'Patient snapshot and active event context',
  ),
  profile(
    label: 'Profile',
    icon: Icons.badge_outlined,
    summary: 'Patient-controlled information for doctor review',
  ),
  medicalHistory(
    label: 'Medical history',
    icon: Icons.description_outlined,
    summary: 'Patient-entered history with clinician review context',
  ),
  clinicalEvents(
    label: 'Clinical Events',
    icon: Icons.fact_check_outlined,
    summary: 'Problems over time with visits, diagnosis, and linked care',
  ),
  medicationPrescriptions(
    label: 'Medications & Prescriptions',
    icon: Icons.medication_outlined,
    summary: 'Event-linked orders, schedules, and generated reminders',
  ),
  recoveryPlans(
    label: 'Recovery Plans',
    icon: Icons.assignment_turned_in_outlined,
    summary: 'Event-linked timeline creation, review, and completion',
  ),
  imaging(
    label: 'Imaging',
    icon: Icons.image_search_outlined,
    summary: 'Event-linked upload metadata and manual review status',
  ),
  consultationActivity(
    label: 'Consultation & Activity',
    icon: Icons.edit_note_outlined,
    summary: 'Notes, specialist review, and supporting timeline',
  );

  const _DoctorPatientSection({
    required this.label,
    required this.icon,
    required this.summary,
  });

  final String label;
  final IconData icon;
  final String summary;
}

class _PatientSearchPane extends StatelessWidget {
  const _PatientSearchPane({
    required this.controller,
    required this.patients,
    required this.selectedPatientId,
    required this.onSearchChanged,
    required this.onSelect,
    required this.onRetry,
  });

  final TextEditingController controller;
  final AsyncValue<PatientListData> patients;
  final String? selectedPatientId;
  final ValueChanged<String> onSearchChanged;
  final ValueChanged<String> onSelect;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _CarePanel(
      title: 'Patient Management',
      icon: Icons.people_outline,
      child: Column(
        children: <Widget>[
          const _PatientConnectPanel(),
          const SizedBox(height: DrAiSpacing.sm),
          TextField(
            key: const Key('patient-search-field'),
            controller: controller,
            onChanged: onSearchChanged,
            maxLength: 80,
            decoration: const InputDecoration(
              counterText: '',
              prefixIcon: Icon(Icons.search),
              labelText: 'Search synthetic patients',
              helperText: 'Name or synthetic identifier',
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          Expanded(
            child: patients.when(
              loading: () => const DashboardLoadingView(
                label: 'Loading synthetic patients',
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(error),
                onRetry: onRetry,
              ),
              data: (data) {
                if (data.items.isEmpty) {
                  return const _EmptyState(
                    key: Key('patient-list-empty'),
                    icon: Icons.person_add_alt_1_outlined,
                    title: 'No connected patients yet',
                    body:
                        'Ask the patient for their code, connect them here, then build the care workspace from zero.',
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
            const Text(
              'Connect patient by code',
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
                labelText: 'Patient code',
                helperText: 'Shown on the patient dashboard after sign-up',
                errorText: _validationError,
                prefixIcon: const Icon(Icons.badge_outlined),
              ),
              onSubmitted: (_) => _connect(),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            FilledButton.icon(
              key: const Key('patient-connect-button'),
              onPressed: state.isLoading ? null : _connect,
              icon: state.isLoading
                  ? const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.person_add_alt_1_outlined),
              label: const Text('Connect'),
            ),
            state.when(
              data: (_) => connected == null
                  ? const SizedBox.shrink()
                  : Padding(
                      padding: const EdgeInsets.only(top: DrAiSpacing.xs),
                      child: Text(
                        'Connected ${connected.displayName}.',
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
                  _safeErrorMessage(error),
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
      setState(() => _validationError = 'Enter the patient code.');
      return;
    }
    setState(() => _validationError = null);
    await ref.read(patientConnectionControllerProvider.notifier).connect(code);
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
    required this.onOpenPatientPicker,
  });

  final String? patientId;
  final _DoctorPatientSection selectedSection;
  final String? selectedClinicalEventId;
  final bool compact;
  final ValueChanged<_DoctorPatientSection> onSectionChanged;
  final ValueChanged<String?> onClinicalEventChanged;
  final VoidCallback onOpenPatientPicker;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = patientId;
    if (id == null) {
      return _CarePanel(
        title: 'Patient Profile',
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
                  label: const Text('Choose patient'),
                ),
              ),
            const Expanded(
              child: _EmptyState(
                key: Key('patient-detail-empty'),
                icon: Icons.touch_app_outlined,
                title: 'Select a synthetic patient',
                body: 'Open an assigned patient to review core records.',
              ),
            ),
          ],
        ),
      );
    }
    final bundle = ref.watch(patientCareBundleProvider(id));
    return _CarePanel(
      title: 'Patient Workspace',
      icon: Icons.badge_outlined,
      child: bundle.when(
        loading: () =>
            const DashboardLoadingView(label: 'Loading patient profile'),
        error: (error, stackTrace) => DashboardErrorView(
          message: _safeErrorMessage(error),
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
    this.onOpenPatientPicker,
  });

  final PatientCareBundle bundle;
  final bool showNotes;
  final _DoctorPatientSection selectedSection;
  final String? selectedClinicalEventId;
  final bool compact;
  final ValueChanged<_DoctorPatientSection>? onSectionChanged;
  final ValueChanged<String?>? onClinicalEventChanged;
  final VoidCallback? onOpenPatientPicker;

  @override
  Widget build(BuildContext context) {
    if (!showNotes) {
      return ListView(
        key: const Key('patient-care-bundle-list'),
        children: <Widget>[
          _ProfileHeader(bundle: bundle),
          const SizedBox(height: DrAiSpacing.sm),
          _medicalRecordsSection(bundle),
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
      onClinicalEventChanged: onClinicalEventChanged,
    );
    return Column(
      key: const Key('patient-care-bundle-list'),
      children: <Widget>[
        if (compact)
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              key: const Key('open-patient-picker-button'),
              onPressed: onOpenPatientPicker,
              icon: const Icon(Icons.people_outline),
              label: const Text('Change patient'),
            ),
          ),
        if (compact) const SizedBox(height: DrAiSpacing.xs),
        _SelectedPatientSummaryHeader(bundle: bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _ActiveClinicalEventBar(
          bundle: bundle,
          selectedEvent: selectedEvent,
          compact: compact,
          onChanged: onClinicalEventChanged,
        ),
        SizedBox(height: compact ? DrAiSpacing.xs : DrAiSpacing.sm),
        if (compact)
          _CompactSectionPicker(
            selectedSection: selectedSection,
            onChanged: onSectionChanged,
          )
        else
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                SizedBox(
                  width: 214,
                  child: _SectionNavigation(
                    selectedSection: selectedSection,
                    onChanged: onSectionChanged,
                  ),
                ),
                const SizedBox(width: DrAiSpacing.sm),
                Expanded(child: content),
              ],
            ),
          ),
        if (compact) ...<Widget>[
          const SizedBox(height: DrAiSpacing.sm),
          Expanded(child: content),
        ],
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
    final lastVisit = _lastVisitLabel(bundle.visitHistory);
    final workflowStatus = _workflowStatus(bundle);
    return DecoratedBox(
      key: const Key('selected-patient-summary-header'),
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Wrap(
              spacing: DrAiSpacing.sm,
              runSpacing: DrAiSpacing.xs,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: <Widget>[
                Text(
                  patient.displayName,
                  style: const TextStyle(
                    color: DrAiColors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                _DarkStatusChip(label: _ageSexLabel(patient)),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                _DarkStatusChip(
                  label: plans.when(
                    loading: () => 'Recovery plan loading',
                    error: (error, stackTrace) => 'Recovery plan unavailable',
                    data: _activePlanLabel,
                  ),
                ),
                _DarkStatusChip(label: 'Last visit: $lastVisit'),
                _DarkStatusChip(label: workflowStatus),
              ],
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
                    'Active Clinical Event',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                _LightMetricChip(
                  label: event == null ? 'setup needed' : event.status,
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (compact)
              Text(
                event == null
                    ? 'Create a Clinical Event before event-linked care work.'
                    : '${event.title} - ${event.chiefComplaint}',
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              )
            else if (events.isEmpty)
              const Text(
                'Create a Clinical Event before authoring event-linked prescriptions, recovery plans, imaging, notes, or consultation.',
                style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
              )
            else
              DropdownButtonFormField<String>(
                key: const Key('clinical-event-selector'),
                initialValue: event?.id,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Selected care episode',
                  prefixIcon: Icon(Icons.fact_check_outlined),
                ),
                items: <DropdownMenuItem<String>>[
                  for (final event in events)
                    DropdownMenuItem<String>(
                      value: event.id,
                      child: Text(
                        '${event.title} - ${event.status}',
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
                    ? 'Linked sections will show legacy patient-wide records until an event is selected.'
                    : '${event.chiefComplaint} | ${_eventLinkSummary(event)}',
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

class _DarkStatusChip extends StatelessWidget {
  const _DarkStatusChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.brandDark,
        borderRadius: BorderRadius.circular(DrAiRadii.sm),
        border: Border.all(color: DrAiColors.outlineMuted),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.xs,
          vertical: 6,
        ),
        child: Text(
          label,
          style: const TextStyle(color: DrAiColors.white, fontSize: 12),
        ),
      ),
    );
  }
}

class _SectionNavigation extends StatelessWidget {
  const _SectionNavigation({
    required this.selectedSection,
    required this.onChanged,
  });

  final _DoctorPatientSection selectedSection;
  final ValueChanged<_DoctorPatientSection>? onChanged;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: ListView(
        key: const Key('doctor-workspace-section-nav'),
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        children: <Widget>[
          for (final section in _DoctorPatientSection.values)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Material(
                color: section == selectedSection
                    ? DrAiColors.patientAccent
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(DrAiRadii.sm),
                child: ListTile(
                  key: Key('doctor-section-${section.name}'),
                  dense: true,
                  selected: section == selectedSection,
                  leading: Icon(section.icon, color: DrAiColors.brand),
                  title: Text(section.label, maxLines: 2),
                  onTap: onChanged == null ? null : () => onChanged!(section),
                ),
              ),
            ),
        ],
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
      decoration: const InputDecoration(
        labelText: 'Workspace section',
        prefixIcon: Icon(Icons.view_list_outlined),
      ),
      items: <DropdownMenuItem<_DoctorPatientSection>>[
        for (final section in _DoctorPatientSection.values)
          DropdownMenuItem<_DoctorPatientSection>(
            value: section,
            child: Text(section.label, overflow: TextOverflow.ellipsis),
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
    required this.onClinicalEventChanged,
  });

  final PatientCareBundle bundle;
  final _DoctorPatientSection selectedSection;
  final ClinicalEventItem? selectedEvent;
  final ValueChanged<String?>? onClinicalEventChanged;

  @override
  Widget build(BuildContext context) {
    return _SectionScaffold(
      section: selectedSection,
      child: ListView(
        key: Key('doctor-section-list-${selectedSection.name}'),
        children: <Widget>[
          switch (selectedSection) {
            _DoctorPatientSection.overview => _OverviewSection(
              bundle: bundle,
              selectedEvent: selectedEvent,
            ),
            _DoctorPatientSection.profile => _ProfileReviewSection(
              bundle: bundle,
            ),
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
          },
        ],
      ),
    );
  }
}

class _SectionScaffold extends StatelessWidget {
  const _SectionScaffold({required this.section, required this.child});

  final _DoctorPatientSection section;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
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
                Icon(section.icon, color: DrAiColors.brand),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        section.label,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        section.summary,
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
            const SizedBox(height: DrAiSpacing.sm),
            Expanded(child: child),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        _ProfileHeader(bundle: bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _InfoTile(
          title: 'Clinical event readiness',
          subtitle: selectedEvent == null
              ? _workflowStatus(bundle)
              : 'Active event: ${selectedEvent!.status}',
          body: selectedEvent == null
              ? 'Create or select a Clinical Event to organize prescriptions, medication schedules, recovery plans, imaging, notes, and consultation around one care episode.'
              : '${selectedEvent!.title} links ${_eventLinkSummary(selectedEvent!)}.',
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ClinicalEventContextCard(bundle: bundle, selectedEvent: selectedEvent),
      ],
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
              '${_demographicsLine(patient)}\n'
              'Doctor review only: patient-controlled profile fields are not edited from this workspace.',
        ),
        const SizedBox(height: DrAiSpacing.sm),
        const _InlineMessage(
          key: Key('doctor-profile-read-only-notice'),
          message:
              'Profile corrections should be requested from the patient; direct doctor editing is intentionally out of this Phase 2 slice.',
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
        const _InlineMessage(
          key: Key('medical-history-patient-entered-notice'),
          message:
              'Medical history is patient-entered. Doctor verification, correction requests, and amendments are stored as visible audited overlays.',
          icon: Icons.verified_user_outlined,
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _MedicalHistoryReviewPanel(bundle: bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _medicalHistoryReviewsSection(bundle),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<PatientAllergyItem>(
          key: const Key('allergies-section'),
          title: 'Allergies',
          icon: Icons.warning_amber_outlined,
          items: bundle.allergies,
          emptyTitle: 'No allergies recorded',
          itemBuilder: (item) => _InfoTile(
            title: item.label,
            subtitle: '${item.severity} - ${item.status}',
            body: item.reaction ?? 'No reaction detail recorded.',
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<ChronicDiseaseItem>(
          key: const Key('chronic-diseases-section'),
          title: 'Chronic diseases',
          icon: Icons.monitor_heart_outlined,
          items: bundle.chronicDiseases,
          emptyTitle: 'No chronic diseases recorded',
          itemBuilder: (item) => _InfoTile(
            title: item.name,
            subtitle: '${item.status} - ${item.diagnosedOn ?? 'date unknown'}',
            body: item.notes ?? 'No condition note recorded.',
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _medicalRecordsSection(bundle),
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
  final _amendmentController = TextEditingController(
    text: 'Doctor amendment: synthetic reviewed history context.',
  );
  final _correctionController = TextEditingController(
    text: 'Please confirm this synthetic history item in your profile.',
  );
  String? _validationError;

  @override
  void dispose() {
    _amendmentController.dispose();
    _correctionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final targets = _historyReviewTargets(widget.bundle);
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
              'Medical History Review',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (targets.isEmpty)
              const _InlineMessage(
                message:
                    'No patient-entered allergy, chronic disease, or record is available for doctor review yet.',
                icon: Icons.info_outline,
              )
            else ...<Widget>[
              DropdownButtonFormField<String>(
                key: const Key('medical-history-review-target-field'),
                initialValue: _targetKey,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Patient-entered item',
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
                decoration: const InputDecoration(
                  labelText: 'Review action',
                  prefixIcon: Icon(Icons.verified_outlined),
                ),
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'verified',
                    child: Text('Mark verified'),
                  ),
                  DropdownMenuItem(
                    value: 'amendment',
                    child: Text('Add doctor amendment'),
                  ),
                  DropdownMenuItem(
                    value: 'correction_requested',
                    child: Text('Request patient correction'),
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
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Doctor amendment',
                  prefixIcon: Icon(Icons.edit_note_outlined),
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              TextField(
                key: const Key('medical-history-correction-field'),
                controller: _correctionController,
                maxLength: 1200,
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Patient correction request',
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
                label: const Text('Save audited review'),
              ),
            ],
            state.when(
              loading: () => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: LinearProgressIndicator(),
              ),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(error)),
              data: (review) {
                if (review == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  message: 'Medical history review saved: ${review.action}.',
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
    final targets = _historyReviewTargets(widget.bundle);
    final selected = targets
        .where((target) => target.key == _targetKey)
        .firstOrNull;
    if (selected == null) {
      setState(() => _validationError = 'Select a patient-entered item first.');
      return;
    }
    if (_action == 'amendment' && _amendmentController.text.trim().length < 3) {
      setState(() => _validationError = 'Enter a doctor amendment.');
      return;
    }
    if (_action == 'correction_requested' &&
        _correctionController.text.trim().length < 3) {
      setState(() => _validationError = 'Enter a patient correction request.');
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
          title: 'Encounter updates',
          icon: Icons.event_note_outlined,
          items: _eventVisitHistory(bundle, selectedEvent),
          emptyTitle: 'No encounter updates recorded',
          itemBuilder: (item) => _InfoTile(
            title: item.title,
            subtitle: '${item.visitType} - ${_dateLabel(item.occurredAt)}',
            body:
                '${item.summary}\nClinician: ${item.clinicianLabel}\n'
                'Clinical Event link: ${_eventTitle(bundle, selectedEvent)}',
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<DiagnosisItem>(
          key: const Key('diagnoses-section'),
          title: 'Doctor diagnosis record',
          icon: Icons.fact_check_outlined,
          items: _eventDiagnoses(bundle, selectedEvent),
          emptyTitle: 'No diagnoses recorded',
          itemBuilder: (item) => _InfoTile(
            title: item.label,
            subtitle: '${item.status} - ${item.diagnosedOn ?? 'date unknown'}',
            body:
                '${item.notes ?? 'No diagnosis note recorded.'}\n'
                'Patient can read this record but cannot edit doctor diagnosis.',
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
          text:
              'Prescription orders and active medication schedules are shown under ${_eventTitle(bundle, selectedEvent)}. '
              'Reminder rows below are generated schedule outputs, not a standalone doctor workspace.',
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _medicationsListSection(bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _prescriptionsListSection(bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _remindersListSection(bundle, selectedEvent),
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
          text:
              'Imaging is reviewed as supporting evidence for ${_eventTitle(bundle, selectedEvent)}. Findings remain doctor-entered; the app does not make automated clinical claims.',
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _imagingListSection(bundle, selectedEvent),
        const SizedBox(height: DrAiSpacing.sm),
        _DemoAssessmentWorkflow(
          patientId: bundle.patient.patientId,
          clinicalEventId: selectedEvent?.id,
        ),
      ],
    );
  }
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
          title: 'Doctor notes',
          icon: Icons.edit_note_outlined,
          items: _eventDoctorNotes(bundle, selectedEvent),
          emptyTitle: 'No doctor notes',
          itemBuilder: (item) => _InfoTile(
            title: item.title,
            subtitle: 'Linked to ${_eventTitle(bundle, selectedEvent)}',
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
    final eventTitle = _eventTitle(bundle, selectedEvent);
    final visits = _eventVisitHistory(bundle, selectedEvent);
    final diagnoses = _eventDiagnoses(bundle, selectedEvent);
    final prescriptions = _eventPrescriptions(bundle, selectedEvent);
    final reminders = _eventMedicationReminders(bundle, selectedEvent);
    final imagingAssets = _eventImagingAssets(bundle, selectedEvent);
    final doctorNotes = _eventDoctorNotes(bundle, selectedEvent);
    final latestUpdate = visits.isEmpty
        ? 'No encounter update recorded'
        : _dateLabel(
            ([...visits]..sort((a, b) => b.occurredAt.compareTo(a.occurredAt)))
                .first
                .occurredAt,
          );
    final diagnosisStatus = diagnoses.isEmpty
        ? 'Diagnosis not recorded'
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
            const Text(
              'Clinical Event groups one medical problem over time. Doctors create and update it; patients can read it but cannot edit doctor diagnosis.',
              style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Wrap(
              spacing: DrAiSpacing.xs,
              runSpacing: DrAiSpacing.xs,
              children: <Widget>[
                _LightMetricChip(label: diagnosisStatus),
                _LightMetricChip(label: 'Latest update: $latestUpdate'),
                _LightMetricChip(
                  label: '${prescriptions.length} prescription(s)',
                ),
                _LightMetricChip(
                  label: '${reminders.length} generated reminder(s)',
                ),
                _LightMetricChip(
                  label: '${imagingAssets.length} imaging asset(s)',
                ),
                _LightMetricChip(label: '${doctorNotes.length} note(s)'),
              ],
            ),
            if (selectedEvent != null &&
                selectedEvent!.timeline.isNotEmpty) ...<Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Text(
                'Event timeline',
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
                          '${entry.title} - ${_dateLabel(entry.occurredAt)}',
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

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _chiefComplaintController = TextEditingController();
    _symptomSummaryController = TextEditingController();
    _diagnosisSummaryController = TextEditingController();
    _onsetDateController = TextEditingController();
    _loadEvent(widget.selectedEvent);
  }

  @override
  void didUpdateWidget(covariant _ClinicalEventEditor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedEvent?.id != widget.selectedEvent?.id) {
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
                    'Clinical Event Editor',
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
                        ? 'Create Clinical Event'
                        : 'Update Clinical Event',
                  ),
                ),
                OutlinedButton.icon(
                  key: const Key('clinical-event-new-button'),
                  onPressed: state.isLoading ? null : _startNewEvent,
                  icon: const Icon(Icons.add_circle_outline),
                  label: const Text('New event'),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (widget.bundle.clinicalEvents.isEmpty)
              const _InlineMessage(
                message:
                    'No Clinical Event exists yet. Create one before authoring linked care outputs.',
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
                      label: Text('${event.title} - ${event.status}'),
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
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Clinical Event title',
                prefixIcon: Icon(Icons.fact_check_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('clinical-event-chief-complaint-field'),
              controller: _chiefComplaintController,
              maxLength: 240,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Chief complaint',
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
                    decoration: const InputDecoration(
                      counterText: '',
                      labelText: 'Onset date',
                      helperText: 'YYYY-MM-DD or blank',
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: const Key('clinical-event-status-field'),
                    initialValue: _status,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Status'),
                    items: const <DropdownMenuItem<String>>[
                      DropdownMenuItem(value: 'active', child: Text('active')),
                      DropdownMenuItem(
                        value: 'monitoring',
                        child: Text('monitoring'),
                      ),
                      DropdownMenuItem(
                        value: 'resolved',
                        child: Text('resolved'),
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
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Symptom/update summary',
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
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Doctor diagnosis or provisional diagnosis',
                prefixIcon: Icon(Icons.medical_information_outlined),
              ),
            ),
            const _InlineMessage(
              key: Key('clinical-event-doctor-owned-notice'),
              message:
                  'Patients can read Clinical Events, but doctor diagnosis fields are doctor-managed and audited.',
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
                  _InlineMessage(message: _safeErrorMessage(error)),
              data: (event) {
                if (event == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  key: const Key('clinical-event-save-success'),
                  message:
                      '${event.title} saved as ${event.status}. ${event.safetyLabel}',
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
    _titleController.text = event?.title ?? 'Synthetic care episode';
    _chiefComplaintController.text =
        event?.chiefComplaint ?? 'Synthetic chief complaint';
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
      _validationError = valid
          ? null
          : 'Use a title, chief complaint, and optional YYYY-MM-DD onset date.';
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
            subtitle: _dateLabel(entry.occurredAt),
            body: 'Clinical Event timeline entry: ${entry.entryType}.',
          ),
      for (final prescription in _eventPrescriptions(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: 'Prescription ${prescription.status}',
          subtitle: _dateLabel(prescription.issuedAt),
          body:
              '${prescription.medications.length} medication line(s) linked to ${_eventTitle(bundle, selectedEvent)}.',
        ),
      for (final reminder in _eventMedicationReminders(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: reminder.reminderType == 'refill'
              ? 'Generated refill reminder'
              : 'Generated medication reminder',
          subtitle: '${reminder.status} - ${_dateLabel(reminder.nextDueAt)}',
          body:
              '${reminder.scheduleLabel}\nCreated from medication schedule context.',
        ),
      for (final asset in _eventImagingAssets(bundle, selectedEvent))
        _ActivityDisplayItem(
          title: 'Imaging ${asset.reviewStatus}',
          subtitle: '${asset.uploadStatus} - ${asset.storageProvider}',
          body:
              'Manual review status for ${_eventTitle(bundle, selectedEvent)}.',
        ),
    ];
    return _ItemSection<_ActivityDisplayItem>(
      key: const Key('consultation-activity-timeline-section'),
      title: 'Activity timeline',
      icon: Icons.timeline_outlined,
      items: items,
      emptyTitle: 'No activity yet',
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

Widget _medicalRecordsSection(PatientCareBundle bundle) {
  return _ItemSection<MedicalRecordItem>(
    key: const Key('medical-history-section'),
    title: 'Medical History',
    icon: Icons.description_outlined,
    items: bundle.records,
    emptyTitle: 'No Medical Records',
    itemBuilder: (item) => _InfoTile(
      title: item.title,
      subtitle: item.category,
      body: item.summary,
    ),
  );
}

Widget _medicalHistoryReviewsSection(PatientCareBundle bundle) {
  return _ItemSection<MedicalHistoryReviewItem>(
    key: const Key('medical-history-reviews-section'),
    title: 'Doctor review and amendments',
    icon: Icons.verified_user_outlined,
    items: bundle.medicalHistoryReviews,
    emptyTitle: 'No doctor review records',
    itemBuilder: (item) => _InfoTile(
      title: _historyReviewActionLabel(item.action),
      subtitle: '${item.targetType} - ${_dateLabel(item.createdAt)}',
      body:
          '${item.amendmentSummary ?? item.correctionRequest ?? 'Clinician verified patient-entered history.'}\n'
          'Audit-linked overlay; original patient-entered item is preserved.',
    ),
  );
}

List<_HistoryReviewTarget> _historyReviewTargets(PatientCareBundle bundle) {
  return <_HistoryReviewTarget>[
    for (final allergy in bundle.allergies)
      _HistoryReviewTarget(
        key: 'allergy:${allergy.id}',
        targetType: 'allergy',
        targetId: allergy.id,
        label: 'Allergy: ${allergy.label}',
      ),
    for (final condition in bundle.chronicDiseases)
      _HistoryReviewTarget(
        key: 'chronic_disease:${condition.id}',
        targetType: 'chronic_disease',
        targetId: condition.id,
        label: 'Chronic disease: ${condition.name}',
      ),
    for (final record in bundle.records)
      _HistoryReviewTarget(
        key: 'medical_record:${record.id}',
        targetType: 'medical_record',
        targetId: record.id,
        label: 'Medical record: ${record.title}',
      ),
  ];
}

String _historyReviewActionLabel(String action) {
  return switch (action) {
    'verified' => 'Clinician verified',
    'amendment' => 'Doctor amendment',
    'correction_requested' => 'Patient correction requested',
    _ => action,
  };
}

Widget _imagingListSection(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<MedicalImagingAsset>(
    key: const Key('imaging-assets-section'),
    title: 'Imaging',
    icon: Icons.image_search_outlined,
    items: _eventImagingAssets(bundle, selectedEvent),
    emptyTitle: 'No imaging assets',
    itemBuilder: (item) => _InfoTile(
      title: '${item.contentType} asset',
      subtitle: '${item.uploadStatus} - ${item.reviewStatus}',
      body:
          '${item.sizeBytes} bytes via ${item.storageProvider}\n'
          'Uploaded: ${_dateLabel(item.uploadedAt)}\n'
          'Finding/result: ${item.findingSummary ?? 'Pending manual doctor review'}\n'
          'Measurement/observation: ${item.measurementSummary ?? 'Not recorded'}',
    ),
  );
}

Widget _medicationsListSection(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<MedicationItem>(
    key: const Key('medications-section'),
    title: 'Medications',
    icon: Icons.medication_outlined,
    items: _eventMedications(bundle, selectedEvent),
    emptyTitle: 'No synthetic medications',
    itemBuilder: (item) => _InfoTile(
      title: item.name,
      subtitle: '${item.dosage} - ${item.status}',
      body: '${item.schedule}\n${item.note}',
    ),
  );
}

Widget _prescriptionsListSection(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<PrescriptionItem>(
    key: const Key('prescriptions-section'),
    title: 'Prescriptions',
    icon: Icons.receipt_long_outlined,
    items: _eventPrescriptions(bundle, selectedEvent),
    emptyTitle: 'No prescriptions',
    itemBuilder: (item) => _InfoTile(
      title: '${item.status} prescription',
      subtitle: '${item.medications.length} medication line(s)',
      body: _prescriptionSummary(item),
    ),
  );
}

Widget _remindersListSection(
  PatientCareBundle bundle,
  ClinicalEventItem? selectedEvent,
) {
  return _ItemSection<MedicationReminderItem>(
    key: const Key('medication-reminders-section'),
    title: 'Medication Reminders',
    icon: Icons.notifications_active_outlined,
    items: _eventMedicationReminders(bundle, selectedEvent),
    emptyTitle: 'No medication reminders',
    itemBuilder: (item) => _InfoTile(
      title: item.reminderType == 'refill'
          ? 'Refill reminder'
          : 'Medication reminder',
      subtitle: '${item.status} - ${item.channel}',
      body: '${item.scheduleLabel}\nNext: ${_dateLabel(item.nextDueAt)}',
    ),
  );
}

enum _MedicationWorkflowMode {
  medication(
    title: 'Medication Schedule Editor',
    icon: Icons.medication_liquid_outlined,
  ),
  prescription(
    title: 'Prescription Order Workflow',
    icon: Icons.receipt_long_outlined,
  );

  const _MedicationWorkflowMode({required this.title, required this.icon});

  final String title;
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
  late final TextEditingController _nameController;
  late final TextEditingController _dosageController;
  late final TextEditingController _scheduleController;
  late final TextEditingController _noteController;
  late final TextEditingController _prescriptionNoteController;
  String _status = 'active';
  String? _validationMessage;

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
    _nameController = TextEditingController(
      text: medication?.name ?? 'Synthetic medication',
    );
    _dosageController = TextEditingController(
      text: medication?.dosage ?? '10 mg',
    );
    _scheduleController = TextEditingController(
      text: medication?.schedule ?? 'Every demo morning',
    );
    _noteController = TextEditingController(
      text: medication?.note ?? 'Synthetic medication workflow only.',
    );
    _prescriptionNoteController = TextEditingController(
      text: 'Synthetic prescription workflow only.',
    );
    _status = medication?.status ?? 'active';
  }

  @override
  void dispose() {
    _nameController.dispose();
    _dosageController.dispose();
    _scheduleController.dispose();
    _noteController.dispose();
    _prescriptionNoteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(medicationWorkflowControllerProvider);
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
                    widget.mode.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.sm),
            if (widget.mode == _MedicationWorkflowMode.prescription)
              _InlineMessage(
                message: _selectedMedication == null
                    ? 'Save a medication before issuing a prescription.'
                    : 'Prescription lines use the selected event medication values and feed the patient medication schedule.',
                icon: Icons.info_outline,
              ),
            if (widget.clinicalEventId == null)
              const _InlineMessage(
                message:
                    'Select or create a Clinical Event before saving new event-linked medication work.',
                icon: Icons.account_tree_outlined,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('medication-name-field'),
              controller: _nameController,
              maxLength: 160,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Medication name',
                prefixIcon: Icon(Icons.medication_outlined),
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
                    decoration: const InputDecoration(
                      counterText: '',
                      labelText: 'Dosage',
                    ),
                  ),
                ),
                const SizedBox(width: DrAiSpacing.xs),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: const Key('medication-status-field'),
                    initialValue: _status,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Status'),
                    items: const <DropdownMenuItem<String>>[
                      DropdownMenuItem(value: 'active', child: Text('active')),
                      DropdownMenuItem(value: 'paused', child: Text('paused')),
                      DropdownMenuItem(
                        value: 'stopped',
                        child: Text('stopped'),
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
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Schedule',
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
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Medication note',
                ),
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
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Prescription note',
                  prefixIcon: Icon(Icons.notes_outlined),
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
                  _InlineMessage(message: _safeErrorMessage(error)),
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
                          ? 'Add medication'
                          : 'Update medication',
                    ),
                  ),
                if (widget.mode == _MedicationWorkflowMode.prescription)
                  FilledButton.icon(
                    key: const Key('create-prescription-button'),
                    onPressed: state.isLoading || widget.clinicalEventId == null
                        ? null
                        : _createPrescription,
                    icon: const Icon(Icons.receipt_long_outlined),
                    label: const Text('Issue prescription'),
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
      _validationMessage = valid
          ? null
          : 'Medication name, dosage, and schedule are required.';
    });
    return valid;
  }

  Future<void> _saveMedication() async {
    if (!_validateMedicationFields()) {
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
        );
  }

  Future<void> _createPrescription() async {
    if (!_validateMedicationFields()) {
      return;
    }
    final medication = _selectedMedication;
    if (medication == null) {
      setState(() {
        _validationMessage = 'Save a medication before issuing a prescription.';
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

class _DemoAssessmentWorkflow extends ConsumerStatefulWidget {
  const _DemoAssessmentWorkflow({
    required this.patientId,
    required this.clinicalEventId,
  });

  final String patientId;
  final String? clinicalEventId;

  @override
  ConsumerState<_DemoAssessmentWorkflow> createState() =>
      _DemoAssessmentWorkflowState();
}

class _DemoAssessmentWorkflowState
    extends ConsumerState<_DemoAssessmentWorkflow> {
  final _filenameController = TextEditingController(
    text: 'synthetic-ct-demo.png',
  );
  final _sizeController = TextEditingController(text: '2048');
  final _findingController = TextEditingController(
    text: 'Manual demo finding entered by doctor after imaging review.',
  );
  final _measurementController = TextEditingController(
    text: 'Demo measurement note: no automated interpretation.',
  );
  String _contentType = 'image/png';
  String _fixtureId = 'synthetic_lung_case_001';
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
              'Demo Image Upload',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('demo-upload-filename-field'),
              controller: _filenameController,
              maxLength: 160,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Synthetic image filename',
                helperText: 'PNG, JPEG, or DICOM demo metadata only',
                prefixIcon: Icon(Icons.image_outlined),
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
                    decoration: const InputDecoration(
                      labelText: 'Content type',
                      prefixIcon: Icon(Icons.tune_outlined),
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
                    decoration: const InputDecoration(
                      labelText: 'Size bytes',
                      prefixIcon: Icon(Icons.straighten_outlined),
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
              label: const Text('Prepare demo upload'),
            ),
            uploadState.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(error)),
              data: (presign) {
                if (presign == null) {
                  return const SizedBox.shrink();
                }
                return _UploadPreparedCard(presign: presign);
              },
            ),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              'Phase 2 Imaging Workflow',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-finding-field'),
              controller: _findingController,
              maxLength: 1200,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Manual doctor-entered finding/result',
                prefixIcon: Icon(Icons.fact_check_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('imaging-measurement-field'),
              controller: _measurementController,
              maxLength: 240,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Manual measurement or observation',
                prefixIcon: Icon(Icons.straighten_outlined),
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
                  label: const Text('Prepare imaging'),
                ),
                imagingState.when(
                  loading: () => const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  error: (error, stackTrace) =>
                      _InlineMessage(message: _safeErrorMessage(error)),
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
                          label: const Text('Finalize upload'),
                        ),
                        OutlinedButton.icon(
                          key: const Key('imaging-review-button'),
                          onPressed: canReview ? _reviewImaging : null,
                          icon: const Icon(Icons.fact_check_outlined),
                          label: const Text('Mark reviewed'),
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
              const _InlineMessage(
                message:
                    'Select or create a Clinical Event before preparing event-linked imaging metadata.',
                icon: Icons.account_tree_outlined,
              ),
            Text(
              'Assessment Form',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('assessment-fixture-field'),
              initialValue: _fixtureId,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Synthetic fixture',
                prefixIcon: Icon(Icons.science_outlined),
              ),
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem(
                  value: 'synthetic_lung_case_001',
                  child: Text('synthetic_lung_case_001'),
                ),
                DropdownMenuItem(
                  value: 'synthetic_lung_case_002',
                  child: Text('synthetic_lung_case_002'),
                ),
              ],
              onChanged: (value) => setState(
                () => _fixtureId = value ?? 'synthetic_lung_case_001',
              ),
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
              label: const Text('Run simulated assessment'),
            ),
            createState.when(
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) =>
                  _InlineMessage(message: _safeErrorMessage(error)),
              data: (result) {
                if (result == null) {
                  return const SizedBox.shrink();
                }
                return _AssessmentResultCard(result: result);
              },
            ),
            const SizedBox(height: DrAiSpacing.sm),
            assessments.when(
              loading: () => const DashboardLoadingView(
                label: 'Loading simulated assessment history',
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(error),
                onRetry: () =>
                    ref.invalidate(assessmentListProvider(widget.patientId)),
              ),
              data: (data) {
                if (data.items.isEmpty) {
                  return const _EmptyState(
                    icon: Icons.analytics_outlined,
                    title: 'No simulated results yet',
                    body: 'Run a synthetic fixture to create a demo result.',
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
        _uploadValidationError =
            'Enter a demo filename and a positive byte size.';
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
        _uploadValidationError =
            'Enter an imaging filename and a positive byte size.';
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
        _uploadValidationError = 'Enter the uploaded byte size to finalize.';
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
        _uploadValidationError =
            'Enter a manual imaging finding/result before review.';
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
        _assessmentValidationError = 'Select a synthetic fixture.';
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
  final _titleController = TextEditingController(
    text: 'Synthetic Week 3 Recovery Plan',
  );
  final _instructionsController = TextEditingController(
    text:
        'Demo-only recovery plan for invited beta workflow validation. '
        'This is not diagnosis, treatment, or medical advice.',
  );
  final _medicationController = TextEditingController(
    text: 'Demo medication reminder',
  );
  final _exerciseController = TextEditingController(
    text: 'Light demo mobility',
  );
  final _dietController = TextEditingController(text: 'Demo hydration check');
  final _followUpController = TextEditingController(
    text: 'Synthetic follow-up preparation',
  );
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
              'Recovery Plan Editor',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (widget.clinicalEventId == null)
              const _InlineMessage(
                message:
                    'Select or create a Clinical Event before creating an event-linked recovery plan.',
                icon: Icons.account_tree_outlined,
              ),
            plans.when(
              loading: () =>
                  const DashboardLoadingView(label: 'Loading recovery plans'),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(error),
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
                      const _InlineMessage(
                        message:
                            'No recovery plan for this Clinical Event yet. Save a synthetic draft first.',
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
                                '${plan.title} - ${plan.status} / ${plan.reviewStatus}',
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
                        message:
                            'Plan ${selectedPlan.status}; review ${selectedPlan.reviewStatus}; '
                            '${selectedPlan.progressSummary.completedTaskCount}/'
                            '${selectedPlan.progressSummary.taskCount} tasks complete.',
                        icon: Icons.fact_check_outlined,
                      ),
                    ],
                    const SizedBox(height: DrAiSpacing.xs),
                    _InlineMessage(
                      key: const Key('recovery-plan-active-event-guardrail'),
                      message: activeEventPlans.isEmpty
                          ? 'No active Recovery Plan for this Clinical Event.'
                          : activeEventPlans.length == 1
                          ? 'One active Recovery Plan is linked to this Clinical Event.'
                          : 'Multiple active plans are visible for this event; approve a replacement to resolve the workflow.',
                      icon: Icons.assignment_turned_in_outlined,
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                    TextField(
                      key: const Key('recovery-plan-title-field'),
                      controller: _titleController,
                      maxLength: 160,
                      decoration: const InputDecoration(
                        counterText: '',
                        labelText: 'Synthetic plan title',
                        prefixIcon: Icon(Icons.assignment_outlined),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    TextField(
                      key: const Key('recovery-plan-instructions-field'),
                      controller: _instructionsController,
                      maxLength: 1200,
                      minLines: 2,
                      maxLines: 4,
                      decoration: const InputDecoration(
                        counterText: '',
                        labelText: 'Synthetic instructions',
                        prefixIcon: Icon(Icons.notes_outlined),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    _taskField(
                      key: const Key('recovery-medication-task-field'),
                      controller: _medicationController,
                      label: 'Medication task',
                      icon: Icons.medication_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-exercise-task-field'),
                      controller: _exerciseController,
                      label: 'Exercise task',
                      icon: Icons.directions_walk_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-diet-task-field'),
                      controller: _dietController,
                      label: 'Diet task',
                      icon: Icons.restaurant_outlined,
                    ),
                    _taskField(
                      key: const Key('recovery-follow-up-task-field'),
                      controller: _followUpController,
                      label: 'Follow-up task',
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
                      error: (error, stackTrace) =>
                          _InlineMessage(message: _safeErrorMessage(error)),
                      data: (plan) {
                        if (plan == null) {
                          return const SizedBox.shrink();
                        }
                        return _InlineMessage(
                          message:
                              '${plan.title} saved as ${plan.status}. '
                              'Review ${plan.reviewStatus}. '
                              '${plan.safetyLabel}',
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
                          label: const Text('Save draft'),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-submit-review-button'),
                          onPressed: editorState.isLoading
                              ? null
                              : _submitReview,
                          icon: const Icon(Icons.outgoing_mail),
                          label: const Text('Submit review'),
                        ),
                        OutlinedButton.icon(
                          key: const Key(
                            'recovery-plan-request-changes-button',
                          ),
                          onPressed: editorState.isLoading
                              ? null
                              : _requestChanges,
                          icon: const Icon(Icons.edit_note_outlined),
                          label: const Text('Request changes'),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-activate-button'),
                          onPressed: editorState.isLoading ? null : _approve,
                          icon: const Icon(Icons.task_alt_outlined),
                          label: const Text('Approve for patient'),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-complete-button'),
                          onPressed: editorState.isLoading
                              ? null
                              : _completePlan,
                          icon: const Icon(Icons.done_all_outlined),
                          label: const Text('Complete plan'),
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
        detail: 'Synthetic medication reminder for demo notification testing.',
        dueLabel: 'Today',
        notificationTime: '09:00',
      ),
      RecoveryTaskInput(
        category: 'exercise',
        title: _exerciseController.text.trim(),
        detail: 'Synthetic exercise task for recovery-plan UI validation.',
        dueLabel: 'Today',
      ),
      RecoveryTaskInput(
        category: 'diet',
        title: _dietController.text.trim(),
        detail: 'Synthetic diet task for recovery-plan UI validation.',
        dueLabel: 'Today',
      ),
      RecoveryTaskInput(
        category: 'follow_up',
        title: _followUpController.text.trim(),
        detail: 'Synthetic follow-up task for recovery-plan UI validation.',
        dueLabel: 'Today',
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
        _validationError =
            'Use at least three characters for every synthetic plan field.';
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
      _validationError =
          'Save the synthetic recovery plan before $actionLabel.';
    });
    return false;
  }

  void _submitReview() {
    if (!_requireSelectedPlan('review submission')) {
      return;
    }
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .submitForReview(patientId: widget.patientId, planId: _latestPlanId()!);
  }

  void _requestChanges() {
    if (!_requireSelectedPlan('requesting changes')) {
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
        _validationError = 'Save and submit the synthetic recovery plan first.';
      });
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .approve(patientId: widget.patientId, planId: planId);
  }

  void _completePlan() {
    if (!_requireSelectedPlan('completion')) {
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
  final _specialtyController = TextEditingController(
    text: 'Pulmonology demo review',
  );
  final _summaryController = TextEditingController(
    text: 'Synthetic review of recovery-plan education questions.',
  );
  String _priority = 'routine';
  String? _validationError;

  @override
  void dispose() {
    _specialtyController.dispose();
    _summaryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final list = ref.watch(consultationListProvider);
    final createState = ref.watch(consultationRequestControllerProvider);
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
              'Specialist Consultation',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            const Text(
              'Synthetic asynchronous request only. No appointments, billing, video, voice, or clinical assessment.',
              style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
            ),
            if (widget.clinicalEventId == null)
              const _InlineMessage(
                message:
                    'Select or create a Clinical Event before requesting event-linked specialist review.',
                icon: Icons.account_tree_outlined,
              ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('consultation-specialty-field'),
              controller: _specialtyController,
              maxLength: 120,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Synthetic specialty',
                prefixIcon: Icon(Icons.groups_2_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            TextField(
              key: const Key('consultation-summary-field'),
              controller: _summaryController,
              maxLength: 240,
              minLines: 2,
              maxLines: 3,
              decoration: const InputDecoration(
                counterText: '',
                labelText: 'Non-identifying synthetic question summary',
                prefixIcon: Icon(Icons.forum_outlined),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            SegmentedButton<String>(
              segments: const <ButtonSegment<String>>[
                ButtonSegment<String>(
                  value: 'routine',
                  icon: Icon(Icons.schedule_outlined),
                  label: Text('Routine'),
                ),
                ButtonSegment<String>(
                  value: 'soon',
                  icon: Icon(Icons.priority_high_outlined),
                  label: Text('Soon'),
                ),
              ],
              selected: <String>{_priority},
              onSelectionChanged: (values) =>
                  setState(() => _priority = values.first),
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
                  _InlineMessage(message: _safeErrorMessage(error)),
              data: (request) {
                if (request == null) {
                  return const SizedBox.shrink();
                }
                return _InlineMessage(
                  message:
                      '${request.specialty} consultation ${request.status}. '
                      '${request.safetyLabel}',
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
              label: const Text('Request specialist review'),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            list.when(
              loading: () => const DashboardLoadingView(
                label: 'Loading consultation requests',
              ),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(error),
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
                  return const _EmptyState(
                    icon: Icons.support_agent_outlined,
                    title: 'No specialist request yet',
                    body:
                        'Submit a synthetic request for asynchronous status tracking.',
                  );
                }
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    for (final item in items)
                      _InfoTile(
                        title: '${item.specialty} - ${item.status}',
                        subtitle: 'Priority: ${item.priority}',
                        body: '${item.questionSummary}\n${item.safetyLabel}',
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
        _validationError =
            'Use a synthetic specialty and a non-identifying summary.';
      });
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(consultationRequestControllerProvider.notifier)
        .create(
          patientId: widget.patientId,
          clinicalEventId: widget.clinicalEventId,
          specialty: specialty,
          questionSummary: summary,
          priority: _priority,
        );
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
              _demographicsLine(patient),
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _historyLine(bundle),
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

String _demographicsLine(PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null) 'Born ${patient.birthYear}',
    if (patient.sex != null) patient.sex!,
    if (patient.preferredLanguage != null) patient.preferredLanguage!,
    if (patient.contactPreference != null) patient.contactPreference!,
  ];
  return values.isEmpty ? 'Demographics not recorded' : values.join(' - ');
}

String _ageSexLabel(PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null)
      'Age ${DateTime.now().year - patient.birthYear!}',
    if (patient.sex != null && patient.sex!.trim().isNotEmpty) patient.sex!,
  ];
  return values.isEmpty ? 'Age/sex not recorded' : values.join(' - ');
}

String _activePlanLabel(RecoveryPlanListData data) {
  RecoveryPlanData? activePlan;
  for (final plan in data.items) {
    if (plan.status == 'active') {
      activePlan = plan;
      break;
    }
  }
  activePlan ??= data.items.isEmpty ? null : data.items.first;
  if (activePlan == null) {
    return 'Recovery plan: none';
  }
  return 'Recovery plan: ${activePlan.status} / ${activePlan.reviewStatus}';
}

String _lastVisitLabel(List<VisitHistoryItem> visits) {
  if (visits.isEmpty) {
    return 'none recorded';
  }
  final sorted = [...visits]
    ..sort((a, b) => b.occurredAt.compareTo(a.occurredAt));
  return _dateLabel(sorted.first.occurredAt);
}

String _workflowStatus(PatientCareBundle bundle) {
  final hasActivity =
      bundle.records.isNotEmpty ||
      bundle.visitHistory.isNotEmpty ||
      bundle.diagnoses.isNotEmpty ||
      bundle.medications.isNotEmpty ||
      bundle.prescriptions.isNotEmpty ||
      bundle.imagingAssets.isNotEmpty ||
      bundle.doctorNotes.isNotEmpty;
  return hasActivity ? 'Workflow: review ready' : 'Workflow: setup needed';
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

String _eventTitle(PatientCareBundle bundle, ClinicalEventItem? selectedEvent) {
  if (selectedEvent != null) {
    return 'Clinical Event: ${selectedEvent.title}';
  }
  if (bundle.diagnoses.isNotEmpty) {
    return 'Clinical Event: ${bundle.diagnoses.first.label}';
  }
  if (bundle.visitHistory.isNotEmpty) {
    return 'Clinical Event: ${bundle.visitHistory.first.title}';
  }
  return 'Clinical Event: setup needed';
}

String _eventLinkSummary(ClinicalEventItem event) {
  final counts = event.linkedResourceCounts;
  return '${counts['prescriptions'] ?? 0} prescription(s), '
      '${counts['medications'] ?? 0} medication schedule item(s), '
      '${counts['recovery_plans'] ?? 0} recovery plan(s), '
      '${counts['imaging_assets'] ?? 0} imaging asset(s), '
      '${counts['doctor_notes'] ?? 0} note(s)';
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

String _historyLine(PatientCareBundle bundle) {
  return 'Allergies: ${_labelsOrEmpty(bundle.allergies)} | '
      'Chronic diseases: ${_namesOrEmpty(bundle.chronicDiseases)} | '
      'Visits: ${_visitsOrEmpty(bundle.visitHistory)} | '
      'Diagnoses: ${_diagnosesOrEmpty(bundle.diagnoses)}';
}

String _labelsOrEmpty(List<PatientAllergyItem> items) {
  if (items.isEmpty) {
    return 'None recorded';
  }
  return items.map((item) => item.label).join(', ');
}

String _namesOrEmpty(List<ChronicDiseaseItem> items) {
  if (items.isEmpty) {
    return 'None recorded';
  }
  return items.map((item) => item.name).join(', ');
}

String _visitsOrEmpty(List<VisitHistoryItem> items) {
  if (items.isEmpty) {
    return 'None recorded';
  }
  return items.map((item) => item.title).join(', ');
}

String _diagnosesOrEmpty(List<DiagnosisItem> items) {
  if (items.isEmpty) {
    return 'None recorded';
  }
  return items.map((item) => item.label).join(', ');
}

String _prescriptionSummary(PrescriptionItem item) {
  final lines = item.medications
      .map((line) => '${line.name}: ${line.dosage} - ${line.schedule}')
      .join('\n');
  final notes = item.notes == null || item.notes!.isEmpty
      ? 'No prescription note'
      : item.notes!;
  return '$lines\n$notes';
}

String _dateLabel(DateTime? value) {
  if (value == null) {
    return 'not scheduled';
  }
  return '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
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
                body: 'Synthetic content has not been seeded for this section.',
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
      child: const Padding(
        padding: EdgeInsets.all(DrAiSpacing.sm),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(Icons.info_outline, color: DrAiColors.ink),
            SizedBox(width: DrAiSpacing.xs),
            Expanded(
              child: Text(
                'Research simulation - not for diagnosis.\n'
                'Synthetic demonstration data only. Do not enter real patient data.',
                style: TextStyle(fontWeight: FontWeight.w700),
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
        title: 'Demo upload prepared',
        subtitle: 'Synthetic-only ${presign.method} metadata',
        body:
            'Object key: ${presign.objectKey}\n'
            'Expires: ${presign.expiresAt.toUtc().toIso8601String()}\n'
            '${presign.safetyLabel}',
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
    final title = asset == null ? 'Imaging upload prepared' : 'Imaging status';
    final subtitle = asset == null
        ? '${presign?.storageProvider ?? 'tencent_cos'} metadata'
        : '${asset.uploadStatus} - ${asset.reviewStatus}';
    final body = asset == null
        ? 'Expires: ${presign?.expiresAt.toUtc().toIso8601String()}\n'
              '${presign?.safetyLabel ?? ''}'
        : '${asset.contentType}, ${asset.uploadedSizeBytes ?? asset.sizeBytes} bytes\n'
              'Reviewed: ${_dateLabel(asset.reviewedAt)}\n'
              'Finding/result: ${asset.findingSummary ?? 'Pending manual doctor review'}\n'
              'Measurement/observation: ${asset.measurementSummary ?? 'Not recorded'}\n'
              '${asset.safetyLabel}';
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
                result.safetyLabel,
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
                  _ResultChip(label: 'Risk: ${result.riskBand}'),
                  _ResultChip(label: 'Demo score: $score'),
                  _ResultChip(label: result.inputCompleteness),
                ],
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text('Fixture model: ${result.modelVersion}'),
              const SizedBox(height: DrAiSpacing.xs),
              for (final limitation in result.limitations)
                Text('- $limitation'),
              const SizedBox(height: DrAiSpacing.xs),
              for (final step in result.recommendedNextSteps) Text('- $step'),
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
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: DrAiColors.white,
                      fontSize: 18,
                    ),
                  ),
                ),
                Icon(icon, color: DrAiColors.white),
              ],
            ),
          ),
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

String _safeErrorMessage(Object error) {
  if (error is ApiError) {
    if (error.code == 'unauthenticated') {
      return 'Your session has ended. Please sign in again.';
    }
    if (error.code == 'not_found') {
      return 'This synthetic patient record is not available.';
    }
    if (error.code == 'validation_failed') {
      return 'Check the entered synthetic data and try again.';
    }
    if (error.code == 'unsupported_media_type') {
      return error.message;
    }
    if (error.code == 'payload_too_large') {
      return error.message;
    }
    if (error.code == 'service_unavailable') {
      return 'Unable to reach Dr. AI. Check your connection and try again.';
    }
    return error.message;
  }
  return 'Unable to reach Dr. AI. Check your connection and try again.';
}
