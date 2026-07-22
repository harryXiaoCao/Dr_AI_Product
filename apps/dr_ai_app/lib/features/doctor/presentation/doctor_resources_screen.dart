import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/doctor/domain/medical_resource_fixture.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

enum ResourceCatalogAvailability {
  ready,
  loading,
  partialIndex,
  offline,
  serviceFailure,
}

enum _ResourceTab { search, saved, recentUpdates, sourceRegistry }

enum _ResourceDateWindow { any, past12Months, past24Months }

class DoctorResourcesScreen extends ConsumerStatefulWidget {
  const DoctorResourcesScreen({
    this.initialAvailability = ResourceCatalogAvailability.ready,
    this.loadFromApi = true,
    super.key,
  });

  final ResourceCatalogAvailability initialAvailability;
  final bool loadFromApi;

  @override
  ConsumerState<DoctorResourcesScreen> createState() =>
      _DoctorResourcesScreenState();
}

class _DoctorResourcesScreenState extends ConsumerState<DoctorResourcesScreen> {
  late ResourceCatalogAvailability _availability;
  List<MedicalResourceFixture> _resources = authoritativeMedicalResourceCatalog;
  final TextEditingController _searchController = TextEditingController();
  final Set<String> _saved = <String>{};
  _ResourceTab _tab = _ResourceTab.search;
  bool _showFilters = true;
  bool _filterVisibilityInitialized = false;
  String _query = '';
  MedicalResourceTopic? _topic;
  MedicalDocumentType? _documentType;
  MedicalOrganization? _organization;
  MedicalJurisdiction? _jurisdiction;
  MedicalResourceLanguage? _language;
  MedicalAudience? _audience;
  _ResourceDateWindow _dateWindow = _ResourceDateWindow.any;
  MedicalVersionStatus? _versionStatus;
  int _resultLimit = 20;

  @override
  void initState() {
    super.initState();
    _availability = widget.initialAvailability;
    if (widget.loadFromApi &&
        widget.initialAvailability == ResourceCatalogAvailability.ready) {
      _availability = ResourceCatalogAvailability.loading;
      Future<void>.microtask(_loadResources);
    }
  }

  Future<void> _loadResources() async {
    if (mounted) {
      setState(() => _availability = ResourceCatalogAvailability.loading);
    }
    try {
      final resources = await ref
          .read(repositoryProvider)
          .loadMedicalResources();
      if (!mounted) return;
      setState(() {
        _resources = resources;
        _availability = ResourceCatalogAvailability.ready;
        _resultLimit = 20;
      });
    } on ApiError catch (error) {
      if (!mounted) return;
      setState(() {
        _availability = error.statusCode == 0
            ? ResourceCatalogAvailability.offline
            : ResourceCatalogAvailability.serviceFailure;
      });
    } on Exception {
      if (!mounted) return;
      setState(() => _availability = ResourceCatalogAvailability.offline);
    }
  }

  void _retryCatalog() {
    if (widget.loadFromApi) {
      _loadResources();
    } else {
      setState(() => _availability = ResourceCatalogAvailability.ready);
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_filterVisibilityInitialized) {
      _showFilters = MediaQuery.sizeOf(context).width >= 700;
      _filterVisibilityInitialized = true;
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  bool get _hasFilters =>
      _topic != null ||
      _documentType != null ||
      _organization != null ||
      _jurisdiction != null ||
      _language != null ||
      _audience != null ||
      _dateWindow != _ResourceDateWindow.any ||
      _versionStatus != null;

  List<MedicalResourceFixture> _filteredResources(BuildContext context) {
    final normalizedQuery = _query.trim().toLowerCase();
    final cutoff = switch (_dateWindow) {
      _ResourceDateWindow.any => null,
      _ResourceDateWindow.past12Months => DateTime(2025, 7, 13),
      _ResourceDateWindow.past24Months => DateTime(2024, 7, 13),
    };
    return _resources.where((resource) {
      final matchesQuery =
          normalizedQuery.isEmpty ||
          resource.title.toLowerCase().contains(normalizedQuery) ||
          (resource.titleEn?.toLowerCase().contains(normalizedQuery) ??
              false) ||
          resource.catalogSummary.toLowerCase().contains(normalizedQuery) ||
          resource.searchKeywords.any(
            (keyword) => keyword.toLowerCase().contains(normalizedQuery),
          ) ||
          _topicLabel(
            context,
            resource.topic,
          ).toLowerCase().contains(normalizedQuery);
      return matchesQuery &&
          (_topic == null || resource.topic == _topic) &&
          (_documentType == null || resource.documentType == _documentType) &&
          (_organization == null || resource.organization == _organization) &&
          (_jurisdiction == null || resource.jurisdiction == _jurisdiction) &&
          (_language == null || resource.language == _language) &&
          (_audience == null || resource.audience == _audience) &&
          (_versionStatus == null ||
              resource.versionStatus == _versionStatus) &&
          (cutoff == null || resource.catalogVerifiedAt.isAfter(cutoff));
    }).toList();
  }

  void _clearFilters() {
    setState(() {
      _topic = null;
      _documentType = null;
      _organization = null;
      _jurisdiction = null;
      _language = null;
      _audience = null;
      _dateWindow = _ResourceDateWindow.any;
      _versionStatus = null;
    });
  }

  void _selectSuggestion(String suggestion) {
    _searchController.text = suggestion;
    _searchController.selection = TextSelection.collapsed(
      offset: suggestion.length,
    );
    setState(() => _query = suggestion);
  }

  void _toggleSaved(MedicalResourceFixture resource) {
    final adding = !_saved.contains(resource.id);
    setState(() {
      if (adding) {
        _saved.add(resource.id);
      } else {
        _saved.remove(resource.id);
      }
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            adding
                ? context.l10n.resourceSavedConfirmation
                : context.l10n.resourceRemovedConfirmation,
          ),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 700;
            return ListView(
              key: const Key('doctor-resources-page'),
              padding: EdgeInsets.fromLTRB(
                compact ? DrAiSpacing.sm : DrAiSpacing.lg,
                DrAiSpacing.lg,
                compact ? DrAiSpacing.sm : DrAiSpacing.lg,
                DrAiSpacing.xxl,
              ),
              children: <Widget>[
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1240),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        _PageHeading(compact: compact),
                        const SizedBox(height: DrAiSpacing.md),
                        _CatalogPreviewNotice(
                          total: _resources.length,
                          liveCatalog: widget.loadFromApi,
                        ),
                        const SizedBox(height: DrAiSpacing.lg),
                        _SearchField(
                          controller: _searchController,
                          query: _query,
                          onChanged: (value) => setState(() => _query = value),
                          onClear: () {
                            _searchController.clear();
                            setState(() => _query = '');
                          },
                        ),
                        const SizedBox(height: DrAiSpacing.sm),
                        _SearchSuggestions(onSelected: _selectSuggestion),
                        const SizedBox(height: DrAiSpacing.lg),
                        _ResourceTabs(
                          selected: _tab,
                          onSelected: (tab) => setState(() => _tab = tab),
                        ),
                        const SizedBox(height: DrAiSpacing.md),
                        if (_tab == _ResourceTab.search) ...<Widget>[
                          _FilterHeader(
                            expanded: _showFilters,
                            hasFilters: _hasFilters,
                            onToggle: () =>
                                setState(() => _showFilters = !_showFilters),
                            onClear: _clearFilters,
                          ),
                          if (_showFilters) ...<Widget>[
                            const SizedBox(height: DrAiSpacing.sm),
                            _buildFilters(),
                          ],
                          const SizedBox(height: DrAiSpacing.lg),
                        ],
                        _buildCatalogBody(),
                      ],
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildFilters() {
    return Card(
      key: const Key('resource-filter-panel'),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 980
                ? 4
                : constraints.maxWidth >= 560
                ? 2
                : 1;
            final width =
                (constraints.maxWidth - (columns - 1) * DrAiSpacing.sm) /
                columns;
            return Wrap(
              spacing: DrAiSpacing.sm,
              runSpacing: DrAiSpacing.sm,
              children: <Widget>[
                _FilterField<MedicalResourceTopic>(
                  width: width,
                  label: context.l10n.topicFilter,
                  value: _topic,
                  values: MedicalResourceTopic.values,
                  valueLabel: (value) => _topicLabel(context, value),
                  onChanged: (value) => setState(() => _topic = value),
                ),
                _FilterField<MedicalDocumentType>(
                  width: width,
                  label: context.l10n.documentTypeFilter,
                  value: _documentType,
                  values: MedicalDocumentType.values,
                  valueLabel: (value) => _documentTypeLabel(context, value),
                  onChanged: (value) => setState(() => _documentType = value),
                ),
                _FilterField<MedicalOrganization>(
                  width: width,
                  label: context.l10n.organizationFilter,
                  value: _organization,
                  values: MedicalOrganization.values,
                  valueLabel: (value) => _organizationLabel(context, value),
                  onChanged: (value) => setState(() => _organization = value),
                ),
                _FilterField<MedicalJurisdiction>(
                  width: width,
                  label: context.l10n.jurisdictionFilter,
                  value: _jurisdiction,
                  values: MedicalJurisdiction.values,
                  valueLabel: (value) => _jurisdictionLabel(context, value),
                  onChanged: (value) => setState(() => _jurisdiction = value),
                ),
                _FilterField<MedicalResourceLanguage>(
                  width: width,
                  label: context.l10n.originalLanguageFilter,
                  value: _language,
                  values: MedicalResourceLanguage.values,
                  valueLabel: (value) => _languageLabel(context, value),
                  onChanged: (value) => setState(() => _language = value),
                ),
                _FilterField<MedicalAudience>(
                  width: width,
                  label: context.l10n.intendedAudienceFilter,
                  value: _audience,
                  values: MedicalAudience.values,
                  valueLabel: (value) => _audienceLabel(context, value),
                  onChanged: (value) => setState(() => _audience = value),
                ),
                _FilterField<_ResourceDateWindow>(
                  width: width,
                  label: context.l10n.publicationReviewDateFilter,
                  value: _dateWindow,
                  includeAll: false,
                  values: _ResourceDateWindow.values,
                  valueLabel: (value) => _dateWindowLabel(context, value),
                  onChanged: (value) => setState(
                    () => _dateWindow = value ?? _ResourceDateWindow.any,
                  ),
                ),
                _FilterField<MedicalVersionStatus>(
                  width: width,
                  label: context.l10n.versionStatusFilter,
                  value: _versionStatus,
                  values: MedicalVersionStatus.values,
                  valueLabel: (value) => _versionLabel(context, value),
                  onChanged: (value) => setState(() => _versionStatus = value),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildCatalogBody() {
    if (_availability == ResourceCatalogAvailability.loading) {
      return _ResourceStateCard(
        key: const Key('resources-loading-state'),
        icon: Icons.hourglass_top_rounded,
        title: context.l10n.loadingMedicalResources,
        loading: true,
      );
    }
    if (_availability == ResourceCatalogAvailability.offline) {
      return _ResourceStateCard(
        key: const Key('resources-offline-state'),
        icon: Icons.cloud_off_outlined,
        title: context.l10n.resourceOfflineTitle,
        body: context.l10n.resourceOfflineBody,
        actionLabel: context.l10n.resourceRetry,
        onAction: _retryCatalog,
      );
    }
    if (_availability == ResourceCatalogAvailability.serviceFailure) {
      return _ResourceStateCard(
        key: const Key('resources-service-failure-state'),
        icon: Icons.sync_problem_outlined,
        title: context.l10n.resourceServiceFailureTitle,
        body: context.l10n.resourceServiceFailureBody,
        actionLabel: context.l10n.resourceRetry,
        onAction: _retryCatalog,
      );
    }

    final children = <Widget>[];
    if (_availability == ResourceCatalogAvailability.partialIndex) {
      children.add(
        _InlineStatusBanner(
          key: const Key('resources-partial-index-state'),
          title: context.l10n.resourcePartialIndexTitle,
          body: context.l10n.resourcePartialIndexBody,
        ),
      );
      children.add(const SizedBox(height: DrAiSpacing.md));
    }
    children.add(switch (_tab) {
      _ResourceTab.search => _buildResults(_filteredResources(context)),
      _ResourceTab.saved => _buildSaved(),
      _ResourceTab.recentUpdates => _buildRecentUpdates(),
      _ResourceTab.sourceRegistry => _buildRegistry(),
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: children,
    );
  }

  Widget _buildSaved() {
    final resources = _resources
        .where((resource) => _saved.contains(resource.id))
        .toList();
    if (resources.isEmpty) {
      return _ResourceStateCard(
        key: const Key('resources-saved-empty-state'),
        icon: Icons.bookmark_border,
        title: context.l10n.noSavedResourcesTitle,
        body: context.l10n.noSavedResourcesBody,
        actionLabel: context.l10n.resourceSearchTab,
        onAction: () => setState(() => _tab = _ResourceTab.search),
      );
    }
    return _buildResults(resources, showCount: false);
  }

  Widget _buildRecentUpdates() {
    final resources =
        _resources
            .where(
              (resource) =>
                  resource.catalogVerifiedAt.isAfter(DateTime(2026, 6, 1)),
            )
            .toList()
          ..sort(
            (left, right) =>
                right.catalogVerifiedAt.compareTo(left.catalogVerifiedAt),
          );
    if (resources.isEmpty) {
      return _ResourceStateCard(
        key: const Key('resources-recent-empty-state'),
        icon: Icons.update,
        title: context.l10n.noRecentUpdatesTitle,
        body: context.l10n.noRecentUpdatesBody,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        for (final resource in resources) ...<Widget>[
          Text(
            context.l10n.resourceUpdatedLabel(
              _formatDate(context, resource.catalogVerifiedAt),
            ),
            style: const TextStyle(
              color: DrAiColors.inkSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: DrAiSpacing.xs),
          _resourceCard(resource),
          const SizedBox(height: DrAiSpacing.md),
        ],
      ],
    );
  }

  Widget _buildRegistry() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          context.l10n.sourceRegistrySubtitle,
          style: const TextStyle(color: DrAiColors.inkSecondary),
        ),
        const SizedBox(height: DrAiSpacing.md),
        LayoutBuilder(
          builder: (context, constraints) {
            final cardWidth = constraints.maxWidth >= 780
                ? (constraints.maxWidth - DrAiSpacing.md) / 2
                : constraints.maxWidth;
            return Wrap(
              spacing: DrAiSpacing.md,
              runSpacing: DrAiSpacing.md,
              children: <Widget>[
                for (final organization in MedicalOrganization.values)
                  SizedBox(
                    width: cardWidth,
                    child: Card(
                      key: Key('source-registry-${organization.name}'),
                      child: Padding(
                        padding: const EdgeInsets.all(DrAiSpacing.md),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            const CircleAvatar(
                              backgroundColor: DrAiColors.brandSoft,
                              child: Icon(
                                Icons.account_balance_outlined,
                                color: DrAiColors.brand,
                              ),
                            ),
                            const SizedBox(height: DrAiSpacing.sm),
                            Text(
                              _organizationLabel(context, organization),
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: DrAiSpacing.xs),
                            Text(
                              context.l10n.reviewedSourceCount(
                                _resources
                                    .where(
                                      (resource) =>
                                          resource.organization == organization,
                                    )
                                    .length,
                              ),
                              style: const TextStyle(
                                color: DrAiColors.inkSecondary,
                              ),
                            ),
                            const SizedBox(height: DrAiSpacing.sm),
                            TextButton.icon(
                              onPressed: () {
                                setState(() {
                                  _organization = organization;
                                  _tab = _ResourceTab.search;
                                });
                              },
                              icon: const Icon(Icons.arrow_forward, size: 18),
                              label: Text(context.l10n.viewOrganizationSources),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }

  Widget _buildResults(
    List<MedicalResourceFixture> resources, {
    bool showCount = true,
  }) {
    if (resources.isEmpty) {
      return _ResourceStateCard(
        key: const Key('resources-no-results-state'),
        icon: Icons.search_off_outlined,
        title: context.l10n.noResourceResultsTitle,
        body: context.l10n.noResourceResultsBody,
        actionLabel: context.l10n.clearFilters,
        onAction: () {
          _searchController.clear();
          _clearFilters();
          setState(() => _query = '');
        },
      );
    }
    final visibleResources = resources.take(_resultLimit).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        if (showCount) ...<Widget>[
          Text(
            context.l10n.resourceResultCount(resources.length),
            key: const Key('resource-result-count'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: DrAiSpacing.sm),
        ],
        for (final resource in visibleResources) ...<Widget>[
          _resourceCard(resource),
          const SizedBox(height: DrAiSpacing.md),
        ],
        if (visibleResources.length < resources.length)
          Center(
            child: OutlinedButton.icon(
              key: const Key('show-more-resources'),
              onPressed: () => setState(() => _resultLimit += 20),
              icon: const Icon(Icons.expand_more),
              label: Text(context.l10n.showMoreResources),
            ),
          ),
      ],
    );
  }

  Widget _resourceCard(MedicalResourceFixture resource) {
    return _ResourceResultCard(
      key: Key('resource-card-${resource.stableReference}'),
      resource: resource,
      saved: _saved.contains(resource.id),
      onToggleSaved: () => _toggleSaved(resource),
      onOpen: () => _showSourceDetails(resource),
    );
  }

  Future<void> _showSourceDetails(MedicalResourceFixture resource) async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _ResourceDetailDialog(
        resource: resource,
        saved: _saved.contains(resource.id),
        onReadOriginal:
            resource.rightsStatus == MedicalRightsStatus.storedTextApproved
            ? () {
                Navigator.of(dialogContext).pop();
                context.go(
                  '/doctor/resources/${Uri.encodeComponent(resource.id)}/read',
                );
              }
            : null,
        onOpenOfficial: () => _openOfficialSource(
          dialogContext,
          _resourceLocator(dialogContext, resource),
        ),
        onToggleSaved: () {
          _toggleSaved(resource);
          Navigator.of(dialogContext).pop();
        },
      ),
    );
  }
}

class _PageHeading extends StatelessWidget {
  const _PageHeading({required this.compact});
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        if (!compact) ...<Widget>[
          const CircleAvatar(
            radius: 25,
            backgroundColor: DrAiColors.brandSoft,
            child: Icon(Icons.menu_book_outlined, color: DrAiColors.brand),
          ),
          const SizedBox(width: DrAiSpacing.md),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                context.l10n.medicalResources,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: DrAiColors.ink,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                context.l10n.medicalResourcesSubtitle,
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CatalogPreviewNotice extends StatelessWidget {
  const _CatalogPreviewNotice({required this.total, required this.liveCatalog});

  final int total;
  final bool liveCatalog;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('resource-catalog-preview-notice'),
      decoration: BoxDecoration(
        color: const Color(0xFFF0F4FF),
        border: Border.all(color: const Color(0xFFC9D5F2)),
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
      ),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.verified_user_outlined, color: DrAiColors.brand),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  context.l10n.resourceCatalogPreviewTitle,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: DrAiSpacing.xxs),
                Text(
                  liveCatalog
                      ? _isChinese(context)
                            ? '当前从受治理 API 加载 $total 项资源，涵盖台湾卫生福利部国民健康署、国家卫健委、世界卫生组织、MedlinePlus、NCI、NIMH 与 MyHealthfinder。每项均显示其版权和审核状态。'
                            : 'The governed API currently provides $total resources from Taiwan HPA, NHC, WHO, MedlinePlus, NCI, NIMH, and MyHealthfinder. Each item shows its rights and review state.'
                      : context.l10n.resourceCatalogPreviewBody,
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

class _SearchField extends StatelessWidget {
  const _SearchField({
    required this.controller,
    required this.query,
    required this.onChanged,
    required this.onClear,
  });
  final TextEditingController controller;
  final String query;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return TextField(
      key: const Key('medical-resource-search-field'),
      controller: controller,
      onChanged: onChanged,
      textInputAction: TextInputAction.search,
      decoration: InputDecoration(
        hintText: context.l10n.resourceSearchHint,
        prefixIcon: const Icon(Icons.search),
        suffixIcon: query.isEmpty
            ? null
            : IconButton(
                key: const Key('clear-resource-search'),
                tooltip: context.l10n.clearFilters,
                onPressed: onClear,
                icon: const Icon(Icons.close),
              ),
        contentPadding: const EdgeInsets.symmetric(vertical: 18),
      ),
    );
  }
}

class _SearchSuggestions extends StatelessWidget {
  const _SearchSuggestions({required this.onSelected});
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    final suggestions = <String>[
      context.l10n.resourceSuggestionOne,
      context.l10n.resourceSuggestionTwo,
      context.l10n.resourceSuggestionThree,
    ];
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: DrAiSpacing.xs,
      runSpacing: DrAiSpacing.xs,
      children: <Widget>[
        Text(
          context.l10n.searchSuggestions,
          style: const TextStyle(
            color: DrAiColors.inkSecondary,
            fontWeight: FontWeight.w700,
          ),
        ),
        for (final suggestion in suggestions)
          ActionChip(
            label: Text(suggestion),
            onPressed: () => onSelected(suggestion),
          ),
      ],
    );
  }
}

class _ResourceTabs extends StatelessWidget {
  const _ResourceTabs({required this.selected, required this.onSelected});
  final _ResourceTab selected;
  final ValueChanged<_ResourceTab> onSelected;

  @override
  Widget build(BuildContext context) {
    final tabs = <(_ResourceTab, IconData, String)>[
      (_ResourceTab.search, Icons.search, context.l10n.resourceSearchTab),
      (
        _ResourceTab.saved,
        Icons.bookmark_outline,
        context.l10n.savedResourcesTab,
      ),
      (_ResourceTab.recentUpdates, Icons.update, context.l10n.recentUpdatesTab),
      (
        _ResourceTab.sourceRegistry,
        Icons.account_balance_outlined,
        context.l10n.sourceRegistryTab,
      ),
    ];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        key: const Key('resource-tabs'),
        children: <Widget>[
          for (final tab in tabs) ...<Widget>[
            ChoiceChip(
              key: Key('resource-tab-${tab.$1.name}'),
              avatar: Icon(tab.$2, size: 18),
              label: Text(tab.$3),
              selected: selected == tab.$1,
              onSelected: (_) => onSelected(tab.$1),
            ),
            const SizedBox(width: DrAiSpacing.xs),
          ],
        ],
      ),
    );
  }
}

class _FilterHeader extends StatelessWidget {
  const _FilterHeader({
    required this.expanded,
    required this.hasFilters,
    required this.onToggle,
    required this.onClear,
  });
  final bool expanded;
  final bool hasFilters;
  final VoidCallback onToggle;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        TextButton.icon(
          key: const Key('resource-filter-toggle'),
          onPressed: onToggle,
          icon: Icon(expanded ? Icons.tune : Icons.tune_outlined),
          label: Text(
            expanded ? context.l10n.hideFilters : context.l10n.showFilters,
          ),
        ),
        const Spacer(),
        if (hasFilters)
          TextButton(
            key: const Key('clear-resource-filters'),
            onPressed: onClear,
            child: Text(context.l10n.clearFilters),
          ),
      ],
    );
  }
}

class _FilterField<T> extends StatelessWidget {
  const _FilterField({
    required this.width,
    required this.label,
    required this.value,
    required this.values,
    required this.valueLabel,
    required this.onChanged,
    this.includeAll = true,
  });
  final double width;
  final String label;
  final T? value;
  final List<T> values;
  final String Function(T value) valueLabel;
  final ValueChanged<T?> onChanged;
  final bool includeAll;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: DropdownButtonFormField<T?>(
        key: Key('resource-filter-${T.toString()}'),
        initialValue: value,
        isExpanded: true,
        decoration: InputDecoration(labelText: label),
        items: <DropdownMenuItem<T?>>[
          if (includeAll)
            DropdownMenuItem<T?>(
              value: null,
              child: Text(context.l10n.allOptions),
            ),
          for (final option in values)
            DropdownMenuItem<T?>(
              value: option,
              child: Text(valueLabel(option), overflow: TextOverflow.ellipsis),
            ),
        ],
        onChanged: onChanged,
      ),
    );
  }
}

class _ResourceResultCard extends StatelessWidget {
  const _ResourceResultCard({
    required this.resource,
    required this.saved,
    required this.onToggleSaved,
    required this.onOpen,
    super.key,
  });
  final MedicalResourceFixture resource;
  final bool saved;
  final VoidCallback onToggleSaved;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final superseded =
        resource.versionStatus == MedicalVersionStatus.superseded;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(
                    child: Text(
                      _resourceTitle(context, resource),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  IconButton(
                    key: Key('save-resource-${resource.stableReference}'),
                    tooltip: saved
                        ? context.l10n.removeSavedResource
                        : context.l10n.saveResource,
                    onPressed: onToggleSaved,
                    icon: Icon(
                      saved ? Icons.bookmark : Icons.bookmark_border,
                      color: DrAiColors.brand,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _StatusBadges(resource: resource),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                resource.catalogSummary,
                key: Key('resource-summary-${resource.stableReference}'),
                style: const TextStyle(
                  color: DrAiColors.ink,
                  fontWeight: FontWeight.w600,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                _catalogUseNote(context, resource),
                style: const TextStyle(
                  color: DrAiColors.inkSecondary,
                  height: 1.5,
                ),
              ),
              if (superseded) ...<Widget>[
                const SizedBox(height: DrAiSpacing.sm),
                _WarningStrip(text: context.l10n.supersededDoNotRely),
              ],
              const SizedBox(height: DrAiSpacing.md),
              Wrap(
                spacing: DrAiSpacing.lg,
                runSpacing: DrAiSpacing.xs,
                children: <Widget>[
                  _Metadata(
                    label: context.l10n.publisherLabel,
                    value: _organizationLabel(context, resource.organization),
                  ),
                  _Metadata(
                    label: context.l10n.sourceTypeLabel,
                    value: _documentTypeLabel(context, resource.documentType),
                  ),
                  _Metadata(
                    label: context.l10n.jurisdictionFilter,
                    value: _jurisdictionLabel(context, resource.jurisdiction),
                  ),
                  _Metadata(
                    label: context.l10n.originalLanguageFilter,
                    value: _languageLabel(context, resource.language),
                  ),
                  _Metadata(
                    label: context.l10n.catalogVerifiedLabel,
                    value: _formatDate(context, resource.catalogVerifiedAt),
                  ),
                ],
              ),
              const SizedBox(height: DrAiSpacing.md),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  key: Key('open-resource-${resource.stableReference}'),
                  onPressed: onOpen,
                  icon: const Icon(Icons.open_in_new, size: 18),
                  label: Text(context.l10n.openSourceDetails),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusBadges extends StatelessWidget {
  const _StatusBadges({required this.resource});
  final MedicalResourceFixture resource;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: DrAiSpacing.xs,
      runSpacing: DrAiSpacing.xs,
      children: <Widget>[
        _Badge(
          icon: Icons.verified_outlined,
          label: context.l10n.resourceOfficialMetadataStatus,
          foreground: const Color(0xFF17633A),
          background: const Color(0xFFE7F6ED),
        ),
        _Badge(
          icon: resource.patientUseEligible
              ? Icons.family_restroom_outlined
              : Icons.medical_services_outlined,
          label: resource.patientUseEligible
              ? context.l10n.patientEducationApproved
              : context.l10n.doctorOnlyResource,
          foreground: DrAiColors.brand,
          background: DrAiColors.brandSoft,
        ),
        _Badge(
          icon: Icons.translate,
          label: _languageLabel(context, resource.language),
          foreground: const Color(0xFF315C78),
          background: const Color(0xFFE6F3FA),
        ),
        _Badge(
          icon: resource.rightsStatus == MedicalRightsStatus.storedTextApproved
              ? Icons.library_books_outlined
              : Icons.link,
          label: _rightsStatusLabel(context, resource.rightsStatus),
          foreground:
              resource.rightsStatus == MedicalRightsStatus.storedTextApproved
              ? const Color(0xFF17633A)
              : const Color(0xFF6A4C00),
          background:
              resource.rightsStatus == MedicalRightsStatus.storedTextApproved
              ? const Color(0xFFE7F6ED)
              : const Color(0xFFFFF3C4),
        ),
      ],
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({
    required this.icon,
    required this.label,
    required this.foreground,
    required this.background,
  });
  final IconData icon;
  final String label;
  final Color foreground;
  final Color background;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(DrAiRadii.pill),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 15, color: foreground),
          const SizedBox(width: DrAiSpacing.xxs),
          Flexible(
            child: Text(
              label,
              style: TextStyle(
                color: foreground,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Metadata extends StatelessWidget {
  const _Metadata({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 145, maxWidth: 280),
      child: Text.rich(
        TextSpan(
          children: <InlineSpan>[
            TextSpan(
              text: '$label  ',
              style: const TextStyle(
                color: DrAiColors.mutedInk,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            TextSpan(
              text: value,
              style: const TextStyle(color: DrAiColors.ink, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _WarningStrip extends StatelessWidget {
  const _WarningStrip({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF1E8),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      child: Row(
        children: <Widget>[
          const Icon(Icons.warning_amber_rounded, color: Color(0xFF8A3B12)),
          const SizedBox(width: DrAiSpacing.xs),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: Color(0xFF69300F),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ResourceDetailDialog extends StatelessWidget {
  const _ResourceDetailDialog({
    required this.resource,
    required this.saved,
    required this.onToggleSaved,
    required this.onReadOriginal,
    required this.onOpenOfficial,
  });
  final MedicalResourceFixture resource;
  final bool saved;
  final VoidCallback onToggleSaved;
  final VoidCallback? onReadOriginal;
  final VoidCallback onOpenOfficial;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      key: const Key('resource-detail-dialog'),
      insetPadding: const EdgeInsets.all(DrAiSpacing.sm),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760, maxHeight: 760),
        child: Column(
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(
                DrAiSpacing.lg,
                DrAiSpacing.lg,
                DrAiSpacing.sm,
                DrAiSpacing.sm,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(
                    child: Text(
                      _resourceTitle(context, resource),
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                  ),
                  IconButton(
                    tooltip: context.l10n.close,
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(DrAiSpacing.lg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    _StatusBadges(resource: resource),
                    const SizedBox(height: DrAiSpacing.lg),
                    _DetailSection(
                      title: context.l10n.resourceOfficialMetadataStatus,
                      child: SelectableText(
                        resource.catalogSummary,
                        key: const Key('resource-detail-summary'),
                      ),
                    ),
                    _DetailSection(
                      title: context.l10n.provenance,
                      child: Text(_provenanceBody(context, resource)),
                    ),
                    _DetailSection(
                      title: context.l10n.officialLocator,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            resource.language == MedicalResourceLanguage.english
                                ? context.l10n.englishOfficialSource
                                : context.l10n.chineseOfficialSource,
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: DrAiSpacing.xxs),
                          SelectableText(resource.officialLocator),
                          const SizedBox(height: DrAiSpacing.xs),
                          TextButton.icon(
                            key: const Key('copy-official-locator'),
                            onPressed: () => _copy(
                              context,
                              resource.officialLocator,
                              context.l10n.officialLocatorCopied,
                            ),
                            icon: const Icon(Icons.copy, size: 18),
                            label: Text(context.l10n.copyOfficialLocator),
                          ),
                          if (resource.englishOfficialLocator
                              case final locator?) ...<Widget>[
                            const SizedBox(height: DrAiSpacing.sm),
                            Text(
                              context.l10n.englishOfficialSource,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: DrAiSpacing.xxs),
                            SelectableText(locator),
                            const SizedBox(height: DrAiSpacing.xs),
                            TextButton.icon(
                              key: const Key('copy-english-official-locator'),
                              onPressed: () => _copy(
                                context,
                                locator,
                                context.l10n.englishOfficialLocatorCopied,
                              ),
                              icon: const Icon(Icons.copy, size: 18),
                              label: Text(
                                context.l10n.copyEnglishOfficialLocator,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    _DetailSection(
                      title: context.l10n.stableInternalReference,
                      child: SelectableText(resource.stableReference),
                    ),
                    _DetailSection(
                      title: context.l10n.publicationReviewDateFilter,
                      child: Wrap(
                        spacing: DrAiSpacing.lg,
                        runSpacing: DrAiSpacing.sm,
                        children: <Widget>[
                          _Metadata(
                            label: context.l10n.catalogVerifiedLabel,
                            value: _formatDate(
                              context,
                              resource.catalogVerifiedAt,
                            ),
                          ),
                          if (resource.publisherDateText != null)
                            _Metadata(
                              label: _isChinese(context)
                                  ? '发布方日期'
                                  : 'Publisher date',
                              value: resource.publisherDateText!,
                            ),
                        ],
                      ),
                    ),
                    if (resource.licenseName != null)
                      _DetailSection(
                        title: _isChinese(context)
                            ? '版权与署名'
                            : 'Rights and attribution',
                        child: _Passage(
                          text: <String>[
                            resource.licenseName!,
                            if (resource.attributionRequirements != null)
                              resource.attributionRequirements!,
                          ].join('\n\n'),
                        ),
                      ),
                    _DetailSection(
                      title: context.l10n.catalogUseStatus,
                      child: _Passage(text: _catalogUseNote(context, resource)),
                    ),
                  ],
                ),
              ),
            ),
            const Divider(height: 1),
            SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                child: Wrap(
                  spacing: DrAiSpacing.sm,
                  runSpacing: DrAiSpacing.sm,
                  alignment: WrapAlignment.end,
                  children: <Widget>[
                    OutlinedButton.icon(
                      key: const Key('open-official-source'),
                      onPressed: onOpenOfficial,
                      icon: const Icon(Icons.open_in_new, size: 18),
                      label: Text(context.l10n.openOfficialSource),
                    ),
                    if (onReadOriginal != null)
                      FilledButton.icon(
                        key: const Key('read-original-text'),
                        onPressed: onReadOriginal,
                        icon: const Icon(Icons.article_outlined, size: 18),
                        label: Text(context.l10n.readOriginalText),
                      ),
                    OutlinedButton.icon(
                      onPressed: onToggleSaved,
                      icon: Icon(
                        saved ? Icons.bookmark : Icons.bookmark_border,
                      ),
                      label: Text(
                        saved
                            ? context.l10n.removeSavedResource
                            : context.l10n.saveResource,
                      ),
                    ),
                    FilledButton.icon(
                      key: const Key('copy-resource-citation'),
                      onPressed: () => _copy(
                        context,
                        context.l10n.resourceCitation(
                          _resourceTitle(context, resource),
                          _organizationLabel(context, resource.organization),
                          resource.catalogVerifiedAt.year.toString(),
                          _resourceLocator(context, resource),
                        ),
                        context.l10n.citationCopied,
                      ),
                      icon: const Icon(Icons.content_copy, size: 18),
                      label: Text(context.l10n.copyCitation),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> _copy(
    BuildContext context,
    String value,
    String confirmation,
  ) async {
    await Clipboard.setData(ClipboardData(text: value));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(confirmation)));
  }
}

Future<void> _openOfficialSource(BuildContext context, String locator) async {
  final opened = await launchUrl(
    Uri.parse(locator),
    mode: LaunchMode.externalApplication,
  );
  if (!opened && context.mounted) {
    await Clipboard.setData(ClipboardData(text: locator));
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(context.l10n.officialLocatorCopied)));
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(color: DrAiColors.brand),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          child,
        ],
      ),
    );
  }
}

class _Passage extends StatelessWidget {
  const _Passage({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      child: Text(text),
    );
  }
}

class _InlineStatusBanner extends StatelessWidget {
  const _InlineStatusBanner({
    required this.title,
    required this.body,
    super.key,
  });
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF3D7),
        border: Border.all(color: const Color(0xFFEBCF8D)),
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
      ),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.info_outline, color: Color(0xFF6A4C00)),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: DrAiSpacing.xxs),
                Text(body),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ResourceStateCard extends StatelessWidget {
  const _ResourceStateCard({
    required this.icon,
    required this.title,
    this.body,
    this.actionLabel,
    this.onAction,
    this.loading = false,
    super.key,
  });
  final IconData icon;
  final String title;
  final String? body;
  final String? actionLabel;
  final VoidCallback? onAction;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xl),
        child: Column(
          children: <Widget>[
            if (loading)
              const CircularProgressIndicator()
            else
              Icon(icon, size: 46, color: DrAiColors.mutedInk),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              title,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            if (body != null) ...<Widget>[
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                body!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: DrAiColors.inkSecondary),
              ),
            ],
            if (actionLabel != null && onAction != null) ...<Widget>[
              const SizedBox(height: DrAiSpacing.md),
              OutlinedButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}

String _topicLabel(BuildContext context, MedicalResourceTopic value) =>
    switch (value) {
      MedicalResourceTopic.infectiousDisease =>
        context.l10n.topicInfectiousDisease,
      MedicalResourceTopic.chronicDisease => context.l10n.topicChronicDisease,
      MedicalResourceTopic.maternalChildHealth =>
        context.l10n.topicMaternalChildHealth,
      MedicalResourceTopic.mentalHealth => context.l10n.topicMentalHealth,
      MedicalResourceTopic.injuryEmergency => context.l10n.topicInjuryEmergency,
      MedicalResourceTopic.environmentalHealth =>
        context.l10n.topicEnvironmentalHealth,
      MedicalResourceTopic.nutritionLifestyle =>
        context.l10n.topicNutritionLifestyle,
      MedicalResourceTopic.healthSystems => context.l10n.topicHealthSystems,
    };

String _documentTypeLabel(BuildContext context, MedicalDocumentType value) =>
    switch (value) {
      MedicalDocumentType.factSheet => context.l10n.documentFactSheet,
      MedicalDocumentType.healthTopicSummary =>
        _isChinese(context) ? '健康主题摘要' : 'Health-topic summary',
      MedicalDocumentType.medicalTestExplanation =>
        _isChinese(context) ? '医学检验说明' : 'Medical-test explanation',
      MedicalDocumentType.patientEducation =>
        _isChinese(context) ? '患者教育资料' : 'Patient education',
      MedicalDocumentType.preventiveHealth =>
        _isChinese(context) ? '预防保健资料' : 'Preventive health',
      MedicalDocumentType.clinicalGuideline =>
        context.l10n.documentClinicalGuideline,
      MedicalDocumentType.clinicalProtocol =>
        context.l10n.documentClinicalProtocol,
      MedicalDocumentType.practiceGuideline =>
        context.l10n.documentPracticeGuideline,
      MedicalDocumentType.guidance => context.l10n.documentGuidance,
    };

String _organizationLabel(BuildContext context, MedicalOrganization value) =>
    switch (value) {
      MedicalOrganization.worldHealthOrganization =>
        context.l10n.organizationWorldHealthOrganization,
      MedicalOrganization.nationalHealthCommission =>
        context.l10n.organizationNationalHealthCommission,
      MedicalOrganization.healthPromotionAdministration =>
        _isChinese(context)
            ? '台湾卫生福利部国民健康署'
            : 'Health Promotion Administration, Taiwan',
      MedicalOrganization.medlinePlus => 'MedlinePlus',
      MedicalOrganization.nationalCancerInstitute =>
        _isChinese(context) ? '美国国家癌症研究所' : 'National Cancer Institute',
      MedicalOrganization.nationalInstituteOfMentalHealth =>
        _isChinese(context)
            ? '美国国家精神卫生研究所'
            : 'National Institute of Mental Health',
      MedicalOrganization.officeOfDiseasePreventionAndHealthPromotion =>
        _isChinese(context)
            ? '美国疾病预防与健康促进办公室'
            : 'Office of Disease Prevention and Health Promotion',
    };

String _jurisdictionLabel(BuildContext context, MedicalJurisdiction value) =>
    switch (value) {
      MedicalJurisdiction.international =>
        context.l10n.jurisdictionInternational,
      MedicalJurisdiction.china => context.l10n.jurisdictionChina,
      MedicalJurisdiction.taiwan => _isChinese(context) ? '台湾' : 'Taiwan',
      MedicalJurisdiction.unitedStates =>
        _isChinese(context) ? '美国' : 'United States',
    };

String _rightsStatusLabel(BuildContext context, MedicalRightsStatus value) =>
    switch (value) {
      MedicalRightsStatus.linkOnlyPending => context.l10n.rightsReviewPending,
      MedicalRightsStatus.storedTextApproved =>
        _isChinese(context) ? '原文已获准存储' : 'Original text storage approved',
    };

String _catalogUseNote(BuildContext context, MedicalResourceFixture resource) {
  if (resource.rightsStatus == MedicalRightsStatus.storedTextApproved) {
    return _isChinese(context)
        ? '已存储发布方英文原文。医学审核、中文翻译和患者可读性审核仍待完成；当前不用于 AI 检索。'
        : 'The publisher’s original English text is stored. Medical review, Chinese translation, and patient-readability review remain pending; it is not used for AI retrieval.';
  }
  return context.l10n.resourceCatalogMetadataNote;
}

String _provenanceBody(BuildContext context, MedicalResourceFixture resource) {
  if (resource.rightsStatus == MedicalRightsStatus.storedTextApproved) {
    return _isChinese(context)
        ? '该条目于 ${_formatDate(context, resource.catalogVerifiedAt)} 从发布方官方网站采集，保留英文原文、规范来源定位、内容校验和版权证据。其属于境外证据，医学审核与中文本地化审核仍待完成。'
        : 'Captured from the publisher’s official website on ${_formatDate(context, resource.catalogVerifiedAt)}, preserving the original English text, canonical locator, content checksums, and rights evidence. It remains foreign-jurisdiction evidence pending medical and Chinese-localization review.';
  }
  return _isChinese(context)
      ? '该条目从发布方官方网站目录采集，仅保留已核验的目录元数据与官方定位；正文存储和 AI 检索仍未获准。'
      : 'Captured from the publisher’s official catalog. Only verified catalog metadata and official locators are retained; article storage and AI retrieval are not approved.';
}

bool _isChinese(BuildContext context) =>
    Localizations.localeOf(context).languageCode == 'zh';

String _languageLabel(BuildContext context, MedicalResourceLanguage value) =>
    switch (value) {
      MedicalResourceLanguage.bilingualChineseEnglish =>
        context.l10n.bilingualChineseEnglish,
      MedicalResourceLanguage.chinese => context.l10n.languageChinese,
      MedicalResourceLanguage.english => context.l10n.languageEnglish,
    };

String _resourceTitle(BuildContext context, MedicalResourceFixture resource) =>
    Localizations.localeOf(context).languageCode == 'zh'
    ? resource.title
    : resource.titleEn ?? resource.title;

String _resourceLocator(
  BuildContext context,
  MedicalResourceFixture resource,
) => Localizations.localeOf(context).languageCode == 'zh'
    ? resource.officialLocator
    : resource.englishOfficialLocator ?? resource.officialLocator;

String _audienceLabel(BuildContext context, MedicalAudience value) =>
    switch (value) {
      MedicalAudience.doctors => context.l10n.audienceDoctors,
    };

String _dateWindowLabel(BuildContext context, _ResourceDateWindow value) =>
    switch (value) {
      _ResourceDateWindow.any => context.l10n.dateAny,
      _ResourceDateWindow.past12Months => context.l10n.datePast12Months,
      _ResourceDateWindow.past24Months => context.l10n.datePast24Months,
    };

String _versionLabel(BuildContext context, MedicalVersionStatus value) =>
    switch (value) {
      MedicalVersionStatus.current => context.l10n.statusCurrent,
      MedicalVersionStatus.superseded => context.l10n.statusSuperseded,
    };

String _formatDate(BuildContext context, DateTime date) {
  final locale = Localizations.localeOf(context).toLanguageTag();
  return DateFormat.yMMMd(locale).format(date);
}
