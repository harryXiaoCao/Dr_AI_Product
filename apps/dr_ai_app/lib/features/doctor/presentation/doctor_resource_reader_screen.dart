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

class DoctorResourceReaderScreen extends ConsumerStatefulWidget {
  const DoctorResourceReaderScreen({required this.sourceId, super.key});

  final String sourceId;

  @override
  ConsumerState<DoctorResourceReaderScreen> createState() =>
      _DoctorResourceReaderScreenState();
}

class _DoctorResourceReaderScreenState
    extends ConsumerState<DoctorResourceReaderScreen> {
  late Future<MedicalResourceDetail> _detail;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _detail = ref.read(repositoryProvider).loadMedicalResource(widget.sourceId);
  }

  void _retry() {
    setState(_load);
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 2,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: FutureBuilder<MedicalResourceDetail>(
          future: _detail,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _ReaderFailure(
                notFound:
                    snapshot.error is ApiError &&
                    (snapshot.error! as ApiError).statusCode == 404,
                onRetry: _retry,
              );
            }
            final detail = snapshot.requireData;
            if (detail.resource.rightsStatus !=
                    MedicalRightsStatus.storedTextApproved ||
                detail.sections.isEmpty) {
              return _ReaderUnavailable(detail: detail);
            }
            return _ReaderDocument(detail: detail);
          },
        ),
      ),
    );
  }
}

class _ReaderDocument extends StatefulWidget {
  const _ReaderDocument({required this.detail});

  final MedicalResourceDetail detail;

  @override
  State<_ReaderDocument> createState() => _ReaderDocumentState();
}

class _ReaderDocumentState extends State<_ReaderDocument> {
  bool _languageInitialized = false;
  bool _showChinese = false;

  MedicalResourceTranslation? get _chineseTranslation {
    for (final translation in widget.detail.translations) {
      if (translation.language == 'zh-Hans') return translation;
    }
    return null;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_languageInitialized) {
      _showChinese =
          Localizations.localeOf(context).languageCode == 'zh' &&
          _chineseTranslation != null;
      _languageInitialized = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    final detail = widget.detail;
    final resource = detail.resource;
    final chineseTranslation = _chineseTranslation;
    final showChinese = _showChinese && chineseTranslation != null;
    final title = showChinese
        ? chineseTranslation.title
        : resource.titleEn ?? resource.title;
    final sections = showChinese
        ? chineseTranslation.sections
        : detail.sections;
    return RepaintBoundary(
      key: const Key('resource-reader-golden-boundary'),
      child: CustomScrollView(
        key: const Key('resource-reader-document'),
        slivers: <Widget>[
          SliverToBoxAdapter(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 920),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                    DrAiSpacing.md,
                    DrAiSpacing.md,
                    DrAiSpacing.md,
                    DrAiSpacing.xxl,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          key: const Key('back-to-resources'),
                          onPressed: () => context.go('/doctor/resources'),
                          icon: const Icon(Icons.arrow_back),
                          label: Text(context.l10n.backToResources),
                        ),
                      ),
                      const SizedBox(height: DrAiSpacing.sm),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: DrAiColors.white,
                          borderRadius: BorderRadius.circular(DrAiRadii.xl),
                          border: Border.all(color: DrAiColors.outline),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(DrAiSpacing.xl),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                context.l10n.resourceReaderTitle,
                                style: Theme.of(context).textTheme.labelLarge
                                    ?.copyWith(
                                      color: DrAiColors.brand,
                                      fontWeight: FontWeight.w800,
                                    ),
                              ),
                              const SizedBox(height: DrAiSpacing.sm),
                              SelectableText(
                                title,
                                key: const Key('resource-reader-title'),
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineMedium
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: DrAiSpacing.xs),
                              Text(
                                detail.publisherName,
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(color: DrAiColors.inkSecondary),
                              ),
                              const SizedBox(height: DrAiSpacing.md),
                              if (chineseTranslation != null) ...<Widget>[
                                SegmentedButton<bool>(
                                  key: const Key('resource-reader-language'),
                                  segments: <ButtonSegment<bool>>[
                                    ButtonSegment<bool>(
                                      value: false,
                                      icon: const Icon(Icons.article_outlined),
                                      label: Text(context.l10n.originalEnglish),
                                    ),
                                    ButtonSegment<bool>(
                                      value: true,
                                      icon: const Icon(Icons.translate),
                                      label: Text(
                                        context.l10n.reviewedChineseTranslation,
                                      ),
                                    ),
                                  ],
                                  selected: <bool>{showChinese},
                                  onSelectionChanged: (selection) {
                                    setState(() {
                                      _showChinese = selection.single;
                                    });
                                  },
                                ),
                                const SizedBox(height: DrAiSpacing.md),
                              ],
                              Wrap(
                                spacing: DrAiSpacing.xs,
                                runSpacing: DrAiSpacing.xs,
                                children: <Widget>[
                                  _ReaderBadge(
                                    icon: Icons.translate,
                                    label: showChinese
                                        ? context
                                              .l10n
                                              .reviewedChineseTranslation
                                        : context.l10n.originalEnglish,
                                  ),
                                  _ReaderBadge(
                                    icon: Icons.public,
                                    label: _jurisdictionLabel(
                                      context,
                                      resource.jurisdiction,
                                    ),
                                  ),
                                  _ReaderBadge(
                                    icon:
                                        detail.medicalReviewStatus == 'approved'
                                        ? Icons.verified_outlined
                                        : Icons.pending_actions_outlined,
                                    label:
                                        detail.medicalReviewStatus == 'approved'
                                        ? context
                                              .l10n
                                              .resourceReaderReviewApproved
                                        : context
                                              .l10n
                                              .resourceReaderReviewPending,
                                    warning:
                                        detail.medicalReviewStatus !=
                                        'approved',
                                  ),
                                ],
                              ),
                              const SizedBox(height: DrAiSpacing.lg),
                              _ReaderNotice(
                                text: showChinese
                                    ? context.l10n.unofficialAiTranslationNotice
                                    : context.l10n.resourceReaderNotice,
                              ),
                              const SizedBox(height: DrAiSpacing.lg),
                              Wrap(
                                spacing: DrAiSpacing.sm,
                                runSpacing: DrAiSpacing.sm,
                                children: <Widget>[
                                  FilledButton.icon(
                                    key: const Key('open-official-source'),
                                    onPressed: () => _openOfficialSource(
                                      context,
                                      resource.officialLocator,
                                    ),
                                    icon: const Icon(Icons.open_in_new),
                                    label: Text(
                                      context.l10n.openOfficialSource,
                                    ),
                                  ),
                                  OutlinedButton.icon(
                                    key: const Key('copy-document-citation'),
                                    onPressed: () =>
                                        _copyCitation(context, title, detail),
                                    icon: const Icon(Icons.content_copy),
                                    label: Text(
                                      context.l10n.copyDocumentCitation,
                                    ),
                                  ),
                                ],
                              ),
                              const Divider(height: DrAiSpacing.xxl),
                              _DocumentMetadata(detail: detail),
                              const SizedBox(height: DrAiSpacing.xl),
                              for (final section in sections)
                                _DocumentSection(section: section),
                              const Divider(height: DrAiSpacing.xxl),
                              Text(
                                context.l10n.rightsAndAttribution,
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: DrAiSpacing.xs),
                              SelectableText(
                                <String>[
                                  if (resource.licenseName != null)
                                    resource.licenseName!,
                                  if (resource.attributionRequirements != null)
                                    resource.attributionRequirements!,
                                ].join('\n\n'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  static Future<void> _openOfficialSource(
    BuildContext context,
    String locator,
  ) async {
    final opened = await launchUrl(
      Uri.parse(locator),
      mode: LaunchMode.externalApplication,
    );
    if (!opened && context.mounted) {
      await Clipboard.setData(ClipboardData(text: locator));
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.l10n.officialLocatorCopied)),
      );
    }
  }

  static Future<void> _copyCitation(
    BuildContext context,
    String title,
    MedicalResourceDetail detail,
  ) async {
    final resource = detail.resource;
    await Clipboard.setData(
      ClipboardData(
        text: context.l10n.resourceCitation(
          title,
          detail.publisherName,
          (detail.publicationDate ?? resource.catalogVerifiedAt).year
              .toString(),
          resource.officialLocator,
        ),
      ),
    );
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(context.l10n.citationCopied)));
  }
}

class _DocumentMetadata extends StatelessWidget {
  const _DocumentMetadata({required this.detail});

  final MedicalResourceDetail detail;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: DrAiSpacing.xl,
      runSpacing: DrAiSpacing.md,
      children: <Widget>[
        if (detail.publicationDate case final date?)
          _MetadataItem(
            label: context.l10n.publicationDateLabel,
            value: _formatDate(context, date),
          ),
        _MetadataItem(
          label: context.l10n.captureDateLabel,
          value: _formatDate(context, detail.resource.catalogVerifiedAt),
        ),
        _MetadataItem(
          label: context.l10n.stableInternalReference,
          value: detail.resource.stableReference,
        ),
      ],
    );
  }
}

class _MetadataItem extends StatelessWidget {
  const _MetadataItem({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 280),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: DrAiColors.inkSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: DrAiSpacing.xxs),
          SelectableText(value),
        ],
      ),
    );
  }
}

class _DocumentSection extends StatelessWidget {
  const _DocumentSection({required this.section});

  final MedicalResourceSection section;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (section.heading.isNotEmpty) ...<Widget>[
            SelectableText(
              section.heading,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: DrAiColors.inkStrong,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
          ],
          SelectableText(
            section.originalText,
            key: ValueKey<String>('resource-section-${section.heading}'),
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(height: 1.65),
          ),
        ],
      ),
    );
  }
}

class _ReaderNotice extends StatelessWidget {
  const _ReaderNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7DA),
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: const Color(0xFFE8CF72)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Icon(Icons.info_outline, color: Color(0xFF6A4C00)),
            const SizedBox(width: DrAiSpacing.sm),
            Expanded(child: Text(text)),
          ],
        ),
      ),
    );
  }
}

class _ReaderBadge extends StatelessWidget {
  const _ReaderBadge({
    required this.icon,
    required this.label,
    this.warning = false,
  });

  final IconData icon;
  final String label;
  final bool warning;

  @override
  Widget build(BuildContext context) {
    final foreground = warning ? const Color(0xFF6A4C00) : DrAiColors.brand;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: warning ? const Color(0xFFFFF3C4) : DrAiColors.brandSoft,
        borderRadius: BorderRadius.circular(DrAiRadii.pill),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: DrAiSpacing.sm,
          vertical: DrAiSpacing.xs,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(icon, size: 17, color: foreground),
            const SizedBox(width: DrAiSpacing.xs),
            Text(
              label,
              style: TextStyle(color: foreground, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReaderFailure extends StatelessWidget {
  const _ReaderFailure({required this.notFound, required this.onRetry});

  final bool notFound;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _ReaderState(
      icon: notFound ? Icons.menu_book_outlined : Icons.cloud_off_outlined,
      title: notFound
          ? context.l10n.resourceReaderUnavailableTitle
          : context.l10n.resourceReaderLoadFailedTitle,
      body: notFound
          ? context.l10n.resourceReaderUnavailableBody
          : context.l10n.resourceReaderLoadFailedBody,
      action: notFound
          ? null
          : OutlinedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: Text(context.l10n.resourceReaderRetry),
            ),
    );
  }
}

class _ReaderUnavailable extends StatelessWidget {
  const _ReaderUnavailable({required this.detail});

  final MedicalResourceDetail detail;

  @override
  Widget build(BuildContext context) {
    return _ReaderState(
      icon: Icons.link,
      title: context.l10n.resourceReaderUnavailableTitle,
      body: context.l10n.resourceReaderUnavailableBody,
      action: FilledButton.icon(
        key: const Key('open-official-source'),
        onPressed: () => _ReaderDocumentState._openOfficialSource(
          context,
          detail.resource.officialLocator,
        ),
        icon: const Icon(Icons.open_in_new),
        label: Text(context.l10n.openOfficialSource),
      ),
    );
  }
}

class _ReaderState extends StatelessWidget {
  const _ReaderState({
    required this.icon,
    required this.title,
    required this.body,
    this.action,
  });

  final IconData icon;
  final String title;
  final String body;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Column(
            children: <Widget>[
              Icon(icon, size: 52, color: DrAiColors.brand),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                body,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              if (action != null) ...<Widget>[
                const SizedBox(height: DrAiSpacing.lg),
                action!,
              ],
              const SizedBox(height: DrAiSpacing.md),
              TextButton.icon(
                onPressed: () => context.go('/doctor/resources'),
                icon: const Icon(Icons.arrow_back),
                label: Text(context.l10n.backToResources),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

String _jurisdictionLabel(
  BuildContext context,
  MedicalJurisdiction jurisdiction,
) => switch (jurisdiction) {
  MedicalJurisdiction.unitedStates =>
    Localizations.localeOf(context).languageCode == 'zh'
        ? '美国'
        : 'United States',
  MedicalJurisdiction.china => context.l10n.jurisdictionChina,
  MedicalJurisdiction.international => context.l10n.jurisdictionInternational,
};

String _formatDate(BuildContext context, DateTime date) {
  return DateFormat.yMMMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).format(date);
}
