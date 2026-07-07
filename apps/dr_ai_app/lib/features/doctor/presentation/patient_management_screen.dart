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
                onSelect: (patientId) =>
                    setState(() => _selectedPatientId = patientId),
                onRetry: () => ref.invalidate(patientListProvider),
              );
              final detail = _PatientDetailPane(patientId: _selectedPatientId);
              if (wide) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    SizedBox(width: 360, child: list),
                    const SizedBox(width: DrAiSpacing.sm),
                    Expanded(child: detail),
                  ],
                );
              }
              return ListView(
                children: <Widget>[
                  SizedBox(height: 430, child: list),
                  const SizedBox(height: DrAiSpacing.sm),
                  SizedBox(height: 720, child: detail),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
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
                    icon: Icons.person_search_outlined,
                    title: 'No synthetic patients found',
                    body: 'Adjust the search term or clear the field.',
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

class _PatientDetailPane extends ConsumerWidget {
  const _PatientDetailPane({required this.patientId});

  final String? patientId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = patientId;
    if (id == null) {
      return const _CarePanel(
        title: 'Patient Profile',
        icon: Icons.badge_outlined,
        child: _EmptyState(
          key: Key('patient-detail-empty'),
          icon: Icons.touch_app_outlined,
          title: 'Select a synthetic patient',
          body: 'Open an assigned patient to review Week 2 records.',
        ),
      );
    }
    final bundle = ref.watch(patientCareBundleProvider(id));
    return _CarePanel(
      title: 'Patient Profile',
      icon: Icons.badge_outlined,
      child: bundle.when(
        loading: () =>
            const DashboardLoadingView(label: 'Loading patient profile'),
        error: (error, stackTrace) => DashboardErrorView(
          message: _safeErrorMessage(error),
          onRetry: () => ref.invalidate(patientCareBundleProvider(id)),
        ),
        data: (data) => _PatientCareBundleView(bundle: data, showNotes: true),
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
  const _PatientCareBundleView({required this.bundle, required this.showNotes});

  final PatientCareBundle bundle;
  final bool showNotes;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('patient-care-bundle-list'),
      children: <Widget>[
        _ProfileHeader(patient: bundle.patient),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<MedicalRecordItem>(
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
        ),
        const SizedBox(height: DrAiSpacing.sm),
        _ItemSection<MedicationItem>(
          key: const Key('medications-section'),
          title: 'Medications',
          icon: Icons.medication_outlined,
          items: bundle.medications,
          emptyTitle: 'No synthetic medications',
          itemBuilder: (item) => _InfoTile(
            title: item.name,
            subtitle: '${item.dosage} - ${item.status}',
            body: '${item.schedule}\n${item.note}',
          ),
        ),
        if (showNotes) ...<Widget>[
          const SizedBox(height: DrAiSpacing.sm),
          _ItemSection<DoctorNoteItem>(
            key: const Key('doctor-notes-section'),
            title: 'Doctor Notes',
            icon: Icons.edit_note_outlined,
            items: bundle.doctorNotes,
            emptyTitle: 'No doctor notes',
            itemBuilder: (item) => _InfoTile(
              title: item.title,
              subtitle: 'Doctor-facing synthetic note',
              body: item.body,
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          _DemoAssessmentWorkflow(patientId: bundle.patient.patientId),
          const SizedBox(height: DrAiSpacing.sm),
          _RecoveryPlanEditor(patientId: bundle.patient.patientId),
          const SizedBox(height: DrAiSpacing.sm),
          _ConsultationRequestPanel(patientId: bundle.patient.patientId),
        ],
      ],
    );
  }
}

class _DemoAssessmentWorkflow extends ConsumerStatefulWidget {
  const _DemoAssessmentWorkflow({required this.patientId});

  final String patientId;

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
  String _contentType = 'image/png';
  String _fixtureId = 'synthetic_lung_case_001';
  String? _uploadValidationError;
  String? _assessmentValidationError;

  @override
  void dispose() {
    _filenameController.dispose();
    _sizeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(demoAssetPresignControllerProvider);
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
              'Assessment Form',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            DropdownButtonFormField<String>(
              key: const Key('assessment-fixture-field'),
              initialValue: _fixtureId,
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
  const _RecoveryPlanEditor({required this.patientId});

  final String patientId;

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
            plans.when(
              loading: () =>
                  const DashboardLoadingView(label: 'Loading recovery plans'),
              error: (error, stackTrace) => DashboardErrorView(
                message: _safeErrorMessage(error),
                onRetry: () =>
                    ref.invalidate(recoveryPlanListProvider(widget.patientId)),
              ),
              data: (data) {
                _selectInitialPlan(data.items);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    if (data.items.isEmpty)
                      const _InlineMessage(
                        message:
                            'No recovery plan yet. Save a synthetic draft first.',
                        icon: Icons.info_outline,
                      )
                    else
                      Wrap(
                        spacing: DrAiSpacing.xs,
                        runSpacing: DrAiSpacing.xs,
                        children: <Widget>[
                          for (final plan in data.items)
                            ChoiceChip(
                              label: Text('${plan.title} - ${plan.status}'),
                              selected: plan.planId == _selectedPlanId,
                              onSelected: (_) => _loadPlan(plan),
                            ),
                        ],
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
                          onPressed: editorState.isLoading ? null : _save,
                          icon: const Icon(Icons.save_outlined),
                          label: const Text('Save recovery plan'),
                        ),
                        OutlinedButton.icon(
                          key: const Key('recovery-plan-activate-button'),
                          onPressed: editorState.isLoading ? null : _activate,
                          icon: const Icon(Icons.task_alt_outlined),
                          label: const Text('Activate for patient'),
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
          planId: _selectedPlanId,
          title: _titleController.text.trim(),
          instructions: _instructionsController.text.trim(),
          tasks: _taskInputs(),
        );
  }

  void _activate() {
    final latest = ref.read(recoveryPlanEditorControllerProvider);
    final planId =
        (latest.hasValue ? latest.value?.planId : null) ?? _selectedPlanId;
    if (planId == null) {
      setState(() {
        _validationError =
            'Save the synthetic recovery plan before activation.';
      });
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(recoveryPlanEditorControllerProvider.notifier)
        .activate(patientId: widget.patientId, planId: planId);
  }
}

class _ConsultationRequestPanel extends ConsumerStatefulWidget {
  const _ConsultationRequestPanel({required this.patientId});

  final String patientId;

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
              onPressed: createState.isLoading ? null : _submit,
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
                    .where((item) => item.patientId == widget.patientId)
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
          specialty: specialty,
          questionSummary: summary,
          priority: _priority,
        );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.patient});

  final PatientProfile patient;

  @override
  Widget build(BuildContext context) {
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
              patient.overview,
              style: const TextStyle(color: DrAiColors.outlineMuted),
            ),
          ],
        ),
      ),
    );
  }
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
