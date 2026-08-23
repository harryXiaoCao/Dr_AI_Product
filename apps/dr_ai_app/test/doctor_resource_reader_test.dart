import 'dart:io';

import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/doctor/domain/medical_resource_fixture.dart';
import 'package:dr_ai_app/features/doctor/presentation/doctor_resource_reader_screen.dart';
import 'package:dr_ai_app/l10n/generated/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

const sourceId = 'KBS-MEDLINEPLUS-HIGH-BLOOD-PRESSURE';

final resource = MedicalResourceFixture(
  id: sourceId,
  stableReference: sourceId,
  title: 'High Blood Pressure',
  titleEn: 'High Blood Pressure',
  catalogSummary: 'Publisher-authored description.',
  searchKeywords: const <String>['High Blood Pressure'],
  officialLocator: 'https://medlineplus.gov/highbloodpressure.html',
  documentType: MedicalDocumentType.healthTopicSummary,
  organization: MedicalOrganization.medlinePlus,
  jurisdiction: MedicalJurisdiction.unitedStates,
  language: MedicalResourceLanguage.english,
  topic: MedicalResourceTopic.chronicDisease,
  catalogVerifiedAt: DateTime(2026, 7, 15),
  publisherDateText: 'Date created: 11/14/1998',
  licenseName: 'U.S. Government public domain',
  rightsEvidenceLocator: 'https://medlineplus.gov/about/using/usingcontent/',
  attributionRequirements: 'Credit MedlinePlus.',
  rightsStatus: MedicalRightsStatus.storedTextApproved,
);

final detail = MedicalResourceDetail(
  resource: resource,
  publisherName: 'MedlinePlus',
  originalLanguage: 'en',
  medicalReviewStatus: 'pending',
  publicationDate: DateTime(2024, 5, 1),
  sections: const <MedicalResourceSection>[
    MedicalResourceSection(
      heading: 'Overview',
      originalText:
          'High blood pressure can affect people over time. This is publisher-authored original text used only in this doctor-reader test.',
    ),
  ],
);

final bilingualDetail = MedicalResourceDetail(
  resource: resource,
  publisherName: 'MedlinePlus',
  originalLanguage: 'en',
  medicalReviewStatus: 'pending',
  publicationDate: DateTime(2024, 5, 1),
  sections: detail.sections,
  translations: const <MedicalResourceTranslation>[
    MedicalResourceTranslation(
      language: 'zh-Hans',
      title: '高血压',
      translationType: 'ai_generated_unofficial',
      reviewStatus: 'medical_and_native_chinese_approved',
      sections: <MedicalResourceSection>[
        MedicalResourceSection(
          heading: '概述',
          originalText: '高血压可能会随时间影响患者的健康。',
        ),
      ],
    ),
  ],
);

final whoDetail = MedicalResourceDetail(
  resource: MedicalResourceFixture(
    id: 'KBS-WHO-ZH-22F9C005D13537AE',
    stableReference: 'KBS-WHO-ZH-22F9C005D13537AE',
    title: '高血压',
    titleEn: 'Hypertension',
    catalogSummary: 'WHO 官方事实清单原文。',
    searchKeywords: const <String>['高血压', 'Hypertension'],
    officialLocator:
        'https://www.who.int/zh/news-room/fact-sheets/detail/hypertension',
    englishOfficialLocator:
        'https://www.who.int/news-room/fact-sheets/detail/hypertension',
    documentType: MedicalDocumentType.factSheet,
    organization: MedicalOrganization.worldHealthOrganization,
    jurisdiction: MedicalJurisdiction.international,
    language: MedicalResourceLanguage.bilingualChineseEnglish,
    topic: MedicalResourceTopic.chronicDisease,
    catalogVerifiedAt: DateTime(2026, 8, 13),
    licenseName: 'WHO non-exclusive permission, request 202609681',
    attributionRequirements: 'Credit WHO without implying endorsement.',
    rightsStatus: MedicalRightsStatus.storedTextApproved,
  ),
  publisherName: '世界卫生组织',
  originalLanguage: 'zh-Hans',
  medicalReviewStatus: 'pending',
  sections: const <MedicalResourceSection>[
    MedicalResourceSection(heading: '概述', originalText: '高血压是血管内压力过高。'),
  ],
  translations: const <MedicalResourceTranslation>[
    MedicalResourceTranslation(
      language: 'en',
      title: 'Hypertension',
      translationType: 'official_publisher_version',
      reviewStatus: 'official_text_medical_review_pending',
      sections: <MedicalResourceSection>[
        MedicalResourceSection(
          heading: 'Overview',
          originalText:
              'Hypertension is when blood vessel pressure is too high.',
        ),
      ],
    ),
  ],
);

final hpaDetail = MedicalResourceDetail(
  resource: MedicalResourceFixture(
    id: 'KBV-HPA-TEST-1',
    stableReference: 'KBV-HPA-TEST-1',
    title: '喝水可以预防慢性病吗？',
    catalogSummary: '国民健康署保健辟谣问答。',
    searchKeywords: const <String>['喝水'],
    officialLocator: 'https://data.gov.tw/dataset/43338',
    documentType: MedicalDocumentType.factSheet,
    organization: MedicalOrganization.healthPromotionAdministration,
    jurisdiction: MedicalJurisdiction.taiwan,
    language: MedicalResourceLanguage.chinese,
    topic: MedicalResourceTopic.chronicDisease,
    catalogVerifiedAt: DateTime(2026, 7, 17),
    licenseName: '政府资料开放授权条款第1版',
    rightsStatus: MedicalRightsStatus.storedTextApproved,
  ),
  publisherName: '卫生福利部国民健康署',
  originalLanguage: 'zh-Hant',
  medicalReviewStatus: 'pending',
  sections: const <MedicalResourceSection>[
    MedicalResourceSection(heading: '喝水可以預防慢性病嗎？', originalText: '這是繁體中文原文。'),
  ],
  translations: const <MedicalResourceTranslation>[
    MedicalResourceTranslation(
      language: 'zh-Hans',
      title: '喝水可以预防慢性病吗？',
      translationType: 'deterministic_script_conversion',
      reviewStatus: 'pending_medical_and_native_simplified_chinese_review',
      sections: <MedicalResourceSection>[
        MedicalResourceSection(
          heading: '喝水可以预防慢性病吗？',
          originalText: '这是简体中文内容。',
        ),
      ],
    ),
  ],
);

final skipReaderGoldenOnCi =
    Platform.environment['CI'] == 'true' ||
    Directory.current.path.contains('dr_ai_flutter_verify');

Future<void> pumpReader(
  WidgetTester tester, {
  required MedicalResourceDetail resourceDetail,
}) async {
  tester.view.physicalSize = const Size(1280, 832);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        repositoryProvider.overrideWithValue(
          FakeDrAiRepository(
            medicalResourceDetails: <String, MedicalResourceDetail>{
              sourceId: resourceDetail,
            },
          ),
        ),
      ],
      child: MaterialApp(
        localizationsDelegates: <LocalizationsDelegate<dynamic>>[
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: const DoctorResourceReaderScreen(sourceId: sourceId),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('doctor reader displays approved original text and provenance', (
    tester,
  ) async {
    await pumpReader(tester, resourceDetail: detail);

    expect(find.byKey(const Key('resource-reader-document')), findsOneWidget);
    expect(find.byKey(const Key('resource-reader-title')), findsOneWidget);
    expect(find.text('Original English'), findsOneWidget);
    expect(find.text('Medical review pending'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(
      find.textContaining('publisher-authored original text'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('open-official-source')), findsOneWidget);
    expect(find.byKey(const Key('copy-document-citation')), findsOneWidget);
  });

  testWidgets(
    'doctor reader switches to a reviewed unofficial Chinese translation',
    (tester) async {
      await pumpReader(tester, resourceDetail: bilingualDetail);

      expect(find.byKey(const Key('resource-reader-language')), findsOneWidget);
      await tester.tap(find.text('Reviewed Chinese translation').first);
      await tester.pumpAndSettle();

      expect(find.text('高血压'), findsOneWidget);
      expect(find.text('概述'), findsOneWidget);
      expect(find.textContaining('高血压可能'), findsOneWidget);
      expect(find.textContaining('unofficial AI-generated'), findsOneWidget);
      expect(
        find.textContaining('publisher-authored original text'),
        findsNothing,
      );
    },
  );

  testWidgets('doctor reader switches between official WHO language versions', (
    tester,
  ) async {
    await pumpReader(tester, resourceDetail: whoDetail);

    expect(find.text('Official English version'), findsWidgets);
    expect(find.text('Hypertension'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(find.textContaining('unofficial AI-generated'), findsNothing);

    await tester.tap(find.text('Official Chinese original').first);
    await tester.pumpAndSettle();

    expect(find.text('高血压'), findsOneWidget);
    expect(find.text('概述'), findsOneWidget);
  });

  testWidgets(
    'reader refuses a direct link when display-approved text is absent',
    (tester) async {
      final unavailable = MedicalResourceDetail(
        resource: MedicalResourceFixture(
          id: resource.id,
          stableReference: resource.stableReference,
          title: resource.title,
          titleEn: resource.titleEn,
          catalogSummary: resource.catalogSummary,
          searchKeywords: resource.searchKeywords,
          officialLocator: resource.officialLocator,
          documentType: resource.documentType,
          organization: resource.organization,
          jurisdiction: resource.jurisdiction,
          language: resource.language,
          topic: resource.topic,
          catalogVerifiedAt: resource.catalogVerifiedAt,
        ),
        publisherName: 'MedlinePlus',
        originalLanguage: 'en',
        medicalReviewStatus: 'pending',
        sections: const <MedicalResourceSection>[],
      );

      await pumpReader(tester, resourceDetail: unavailable);

      expect(find.byKey(const Key('resource-reader-document')), findsNothing);
      expect(find.text('Original text is not available'), findsOneWidget);
      expect(find.byKey(const Key('open-official-source')), findsOneWidget);
    },
  );

  testWidgets(
    'doctor reader exposes HPA Simplified-Chinese Q&A with provenance',
    (tester) async {
      await pumpReader(tester, resourceDetail: hpaDetail);

      expect(find.text('卫生福利部国民健康署'), findsOneWidget);
      expect(
        find.text('Simplified Chinese conversion (review pending)'),
        findsWidgets,
      );
      expect(find.text('这是简体中文内容。'), findsOneWidget);
      expect(find.text('Taiwan'), findsOneWidget);
      expect(
        find.textContaining('deterministic Simplified-Chinese'),
        findsOneWidget,
      );
      expect(find.text('这是繁体中文原文。'), findsNothing);
    },
  );

  testWidgets('doctor reader matches the desktop visual target', (
    tester,
  ) async {
    await pumpReader(tester, resourceDetail: detail);

    await expectLater(
      find.byKey(const Key('resource-reader-golden-boundary')),
      matchesGoldenFile('goldens/doctor_resource_reader_1280x832.png'),
    );
  }, skip: skipReaderGoldenOnCi);
}
