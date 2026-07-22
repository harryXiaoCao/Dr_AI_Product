import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/doctor/domain/medical_resource_fixture.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_resources_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

void setResourcesViewport(WidgetTester tester, Size size) {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

Future<void> pumpResources(
  WidgetTester tester, {
  ResourceCatalogAvailability availability = ResourceCatalogAvailability.ready,
  Locale locale = const Locale('en'),
  bool settle = true,
  bool loadFromApi = false,
  DrAiRepository? repository,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        if (repository != null)
          repositoryProvider.overrideWithValue(repository),
      ],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: DoctorResourcesScreen(
          key: ValueKey<ResourceCatalogAvailability>(availability),
          initialAvailability: availability,
          loadFromApi: loadFromApi,
        ),
      ),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
  }
}

void main() {
  test('HPA API records keep Taiwan publisher and jurisdiction provenance', () {
    final resource = MedicalResourceFixture.fromApiJson(<String, dynamic>{
      'source_id': 'KBV-HPA-TEST-1',
      'title': '保健辟谣测试',
      'title_en': null,
      'catalog_summary': '国民健康署官方问答。',
      'search_keywords': <String>['保健辟谣'],
      'official_locator': 'https://data.gov.tw/dataset/43338',
      'english_official_locator': null,
      'available_languages': <String>['zh-Hant', 'zh-Hans'],
      'publisher_id': 'KBP-TW-HPA',
      'source_type': 'health_myth_qa',
      'topic': 'health_education',
      'jurisdiction': 'TW',
      'catalog_verified_at': '2026-07-17T00:00:00Z',
      'publisher_date_text': '17-Jul-26',
      'license_name': '政府资料开放授权条款第1版',
      'rights_evidence_locator': 'https://data.gov.tw/license',
      'attribution_requirements': '注明来源。',
      'rights_mode': 'stored_text',
    });

    expect(
      resource.organization,
      MedicalOrganization.healthPromotionAdministration,
    );
    expect(resource.jurisdiction, MedicalJurisdiction.taiwan);
    expect(resource.language, MedicalResourceLanguage.chinese);
  });

  testWidgets('doctor resources visually lists rights-cleared API records', (
    tester,
  ) async {
    final medlinePlus = MedicalResourceFixture.fromApiJson(<String, dynamic>{
      'source_id': 'KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE',
      'title': 'High Blood Pressure',
      'title_en': 'High Blood Pressure',
      'catalog_summary': 'Publisher-authored description.',
      'search_keywords': <String>['High Blood Pressure'],
      'official_locator': 'https://medlineplus.gov/highbloodpressure.html',
      'english_official_locator':
          'https://medlineplus.gov/highbloodpressure.html',
      'available_languages': <String>['en'],
      'publisher_id': 'KBP-MEDLINEPLUS',
      'source_type': 'health_topic_summary',
      'topic': 'High Blood Pressure',
      'jurisdiction': 'US',
      'catalog_verified_at': '2026-07-15T00:00:00Z',
      'publisher_date_text': 'Date created: 11/14/1998',
      'license_name': 'U.S. Government public domain',
      'rights_evidence_locator':
          'https://medlineplus.gov/about/using/usingcontent/',
      'attribution_requirements': 'Credit MedlinePlus.',
      'rights_mode': 'stored_text',
    });
    setResourcesViewport(tester, const Size(1280, 832));
    await pumpResources(
      tester,
      loadFromApi: true,
      repository: FakeDrAiRepository(
        medicalResources: <MedicalResourceFixture>[medlinePlus],
      ),
    );

    expect(medlinePlus.organization, MedicalOrganization.medlinePlus);
    expect(find.text('1 resource'), findsOneWidget);
    expect(find.text('High Blood Pressure'), findsWidgets);
    final resourceTitle = find.text('High Blood Pressure');
    await tester.ensureVisible(resourceTitle.first);
    await tester.tap(resourceTitle.first);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('resource-detail-dialog')), findsOneWidget);
    expect(
      find.textContaining('MedlinePlus', findRichText: true),
      findsWidgets,
    );
    expect(find.text('Original text storage approved'), findsWidgets);
    expect(find.byKey(const Key('read-original-text')), findsOneWidget);
    expect(find.byKey(const Key('open-official-source')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor resources search, save, details, and citation work', (
    tester,
  ) async {
    String? copiedText;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          copiedText =
              (call.arguments as Map<Object?, Object?>)['text'] as String?;
        }
        return null;
      },
    );
    addTearDown(
      () => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        null,
      ),
    );
    setResourcesViewport(tester, const Size(1280, 832));
    await pumpResources(tester);

    expect(find.byKey(const Key('doctor-resources-page')), findsOneWidget);
    expect(
      find.byKey(const Key('medical-resource-search-field')),
      findsOneWidget,
    );
    expect(find.text('298 resources'), findsOneWidget);
    expect(find.text('Official catalog metadata'), findsNWidgets(20));
    expect(
      find.byKey(const Key('resource-summary-KBS-WHO-ZH-22F9C005D13537AE')),
      findsOneWidget,
    );
    expect(find.textContaining('此目录摘要仅描述已核验的元数据'), findsWidgets);

    await tester.enterText(
      find.byKey(const Key('medical-resource-search-field')),
      'no matching governed source',
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('resources-no-results-state')), findsOneWidget);

    await tester.tap(find.byKey(const Key('clear-resource-search')));
    await tester.pumpAndSettle();
    expect(find.text('298 resources'), findsOneWidget);

    final saveButton = find.byKey(
      const Key('save-resource-KBS-WHO-ZH-22F9C005D13537AE'),
    );
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
    await tester.pumpAndSettle();
    final savedTab = find.byKey(const Key('resource-tab-saved'));
    await tester.fling(
      find.byKey(const Key('doctor-resources-page')),
      const Offset(0, 1800),
      1800,
    );
    await tester.pumpAndSettle();
    await tester.tap(savedTab);
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('resource-card-KBS-WHO-ZH-22F9C005D13537AE')),
      findsOneWidget,
    );

    final resourceTitle = find.text('Hypertension');
    await tester.ensureVisible(resourceTitle);
    await tester.tap(resourceTitle);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('resource-detail-dialog')), findsOneWidget);
    expect(find.byKey(const Key('resource-detail-summary')), findsOneWidget);
    expect(find.text('Provenance'), findsOneWidget);
    expect(find.text('Catalog and retrieval status'), findsOneWidget);
    expect(find.text('Official Chinese page'), findsOneWidget);
    expect(find.text('Official English page'), findsOneWidget);

    final citationButton = find.byKey(const Key('copy-resource-citation'));
    await tester.tap(citationButton);
    await tester.pumpAndSettle();
    expect(copiedText, contains('Hypertension'));
    expect(copiedText, contains('/news-room/fact-sheets/detail/hypertension'));
    expect(find.text('Citation copied.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor resources is localized and usable at phone width', (
    tester,
  ) async {
    setResourcesViewport(tester, const Size(412, 917));
    await pumpResources(tester, locale: const Locale('zh'));

    expect(find.text('医疗资源'), findsWidgets);
    expect(find.text('搜索'), findsWidgets);
    expect(find.text('已保存'), findsOneWidget);
    expect(find.text('近期更新'), findsOneWidget);
    expect(find.text('来源登记'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.enterText(
      find.byKey(const Key('medical-resource-search-field')),
      '高血压',
    );
    await tester.pumpAndSettle();
    expect(find.text('1 项资源'), findsOneWidget);
    expect(
      find.byKey(const Key('resource-card-KBS-WHO-ZH-22F9C005D13537AE')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'doctor resources matches catalog aliases beyond article titles',
    (tester) async {
      setResourcesViewport(tester, const Size(1280, 832));
      await pumpResources(tester, locale: const Locale('zh'));

      await tester.enterText(
        find.byKey(const Key('medical-resource-search-field')),
        '血压高',
      );
      await tester.pumpAndSettle();

      expect(find.text('1 项资源'), findsOneWidget);
      expect(
        find.byKey(const Key('resource-card-KBS-WHO-ZH-22F9C005D13537AE')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('resource filters and registry tabs change local results', (
    tester,
  ) async {
    setResourcesViewport(tester, const Size(1280, 900));
    await pumpResources(tester);

    await tester.tap(
      find.byKey(const Key('resource-filter-MedicalResourceTopic')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Chronic diseases').last);
    await tester.pumpAndSettle();

    expect(find.text('45 resources'), findsOneWidget);
    expect(find.text('Rights review pending—official link only'), findsWidgets);

    await tester.tap(find.byKey(const Key('clear-resource-filters')));
    await tester.pumpAndSettle();
    expect(find.text('298 resources'), findsOneWidget);

    await tester.tap(find.byKey(const Key('resource-tab-sourceRegistry')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('source-registry-worldHealthOrganization')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('source-registry-nationalHealthCommission')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('resource-tab-recentUpdates')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Catalog verified'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('monolingual WHO and NHC sources keep accurate language labels', (
    tester,
  ) async {
    setResourcesViewport(tester, const Size(1280, 900));
    await pumpResources(tester);

    await tester.enterText(
      find.byKey(const Key('medical-resource-search-field')),
      '原发性肝癌诊疗指南',
    );
    await tester.pumpAndSettle();
    expect(find.text('1 resource'), findsOneWidget);
    expect(find.text('Chinese'), findsWidgets);
    final nhcTitle = find.descendant(
      of: find.byKey(const Key('resource-card-KBS-NHC-ZH-4F83ED3828B7739E')),
      matching: find.text('原发性肝癌诊疗指南（2024年版）'),
    );
    await tester.ensureVisible(nhcTitle);
    await tester.tap(nhcTitle);
    await tester.pumpAndSettle();
    expect(find.text('Official Chinese page'), findsOneWidget);
    expect(find.text('Official English page'), findsNothing);
    await tester.tap(find.byTooltip('Close'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('medical-resource-search-field')),
      'Commercial determinants of health',
    );
    await tester.pumpAndSettle();
    expect(find.text('1 resource'), findsOneWidget);
    expect(find.text('English'), findsWidgets);
    final englishTitle = find.descendant(
      of: find.byKey(const Key('resource-card-KBS-WHO-EN-9449D2BF3E710188')),
      matching: find.text('Commercial determinants of health'),
    );
    await tester.ensureVisible(englishTitle);
    await tester.tap(englishTitle);
    await tester.pumpAndSettle();
    expect(find.text('Official English page'), findsOneWidget);
    expect(find.text('Official Chinese page'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('doctor resources implements operational catalog states', (
    tester,
  ) async {
    setResourcesViewport(tester, const Size(900, 900));

    await pumpResources(
      tester,
      availability: ResourceCatalogAvailability.loading,
      settle: false,
    );
    expect(find.byKey(const Key('resources-loading-state')), findsOneWidget);

    await pumpResources(
      tester,
      availability: ResourceCatalogAvailability.offline,
    );
    expect(find.byKey(const Key('resources-offline-state')), findsOneWidget);

    await pumpResources(
      tester,
      availability: ResourceCatalogAvailability.serviceFailure,
    );
    expect(
      find.byKey(const Key('resources-service-failure-state')),
      findsOneWidget,
    );

    await pumpResources(
      tester,
      availability: ResourceCatalogAvailability.partialIndex,
    );
    expect(
      find.byKey(const Key('resources-partial-index-state')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
