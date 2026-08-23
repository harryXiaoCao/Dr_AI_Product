import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/app/routing/router.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_theme.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/notifications/domain/notification_data.dart';
import 'package:dr_ai_app/features/notifications/presentation/notification_inbox_screen.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fakes.dart';

Future<void> pumpInbox(
  WidgetTester tester, {
  required FakeDrAiRepository repository,
  AppRole role = AppRole.patient,
  Locale locale = const Locale('en'),
  Size size = const Size(900, 1000),
  double textScale = 1,
}) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetDevicePixelRatio();
    tester.view.resetPhysicalSize();
  });
  await tester.pumpWidget(
    ProviderScope(
      overrides: [repositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(
        theme: DrAiTheme.light,
        locale: locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: NotificationInboxScreen(role: role),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUpAll(() async {
    final inter = FontLoader('Inter')
      ..addFont(rootBundle.load('assets/fonts/InterVariable.ttf'));
    final notoSansSc = FontLoader('NotoSansSC')
      ..addFont(rootBundle.load('assets/fonts/NotoSansSC-Variable.ttf'));
    final materialIcons = FontLoader('MaterialIcons')
      ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await Future.wait(<Future<void>>[
      inter.load(),
      notoSansSc.load(),
      materialIcons.load(),
    ]);
  });

  testWidgets('patient doctor and payer share the persisted inbox', (
    tester,
  ) async {
    for (final role in <AppRole>[
      AppRole.patient,
      AppRole.doctor,
      AppRole.payer,
    ]) {
      await pumpInbox(tester, repository: FakeDrAiRepository(), role: role);
      expect(
        find.byKey(Key('${role.wireValue}-notification-inbox')),
        findsOneWidget,
      );
      expect(find.text('Recovery reminder'), findsOneWidget);
      expect(find.text('1 unread'), findsOneWidget);
    }
  });

  testWidgets('read and unread actions use persisted readback', (tester) async {
    final repository = FakeDrAiRepository();
    await pumpInbox(tester, repository: repository);
    final id = notificationInboxFixture.items.single.id;

    await tester.tap(find.byKey(Key('notification-read-$id')));
    await tester.pumpAndSettle();

    expect(repository.notificationInbox.unreadCount, 0);
    expect(find.text('Mark unread'), findsOneWidget);
    expect(find.text('0 unread'), findsOneWidget);

    await tester.tap(find.byKey(Key('notification-read-$id')));
    await tester.pumpAndSettle();
    expect(repository.notificationInbox.unreadCount, 1);
    expect(find.text('Mark read'), findsOneWidget);
  });

  testWidgets('mutation failure leaves the server-backed row visible', (
    tester,
  ) async {
    final repository = FakeDrAiRepository(
      notificationMutationError: const ApiError(
        code: 'conflict',
        message: 'Changed',
        statusCode: 409,
      ),
    );
    await pumpInbox(tester, repository: repository);
    final id = notificationInboxFixture.items.single.id;

    await tester.tap(find.byKey(Key('notification-read-$id')));
    await tester.pumpAndSettle();

    expect(find.text('Recovery reminder'), findsOneWidget);
    expect(
      find.text('The update could not be saved. The inbox was not changed.'),
      findsOneWidget,
    );
    expect(repository.notificationInbox.unreadCount, 1);
  });

  testWidgets('offline load is truthful and retryable', (tester) async {
    await pumpInbox(
      tester,
      repository: FakeDrAiRepository(
        notificationLoadError: const ApiError(
          code: 'service_unavailable',
          message: 'Offline',
        ),
      ),
    );

    expect(
      find.textContaining('Notifications are unavailable offline'),
      findsOneWidget,
    );
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('Chinese enlarged content retains semantics and readiness copy', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    try {
      await pumpInbox(
        tester,
        repository: FakeDrAiRepository(),
        locale: const Locale('zh'),
        size: const Size(412, 917),
        textScale: 1.35,
      );
      await tester.tap(find.byKey(const Key('notification-preferences')));
      await tester.pumpAndSettle();

      expect(find.text('通知'), findsWidgets);
      expect(find.text('1 条未读'), findsOneWidget);
      expect(find.text('尚未配置提供方凭据'), findsWidgets);
      expect(tester.getSemantics(find.text('Recovery reminder')), isNotNull);
    } finally {
      semantics.dispose();
    }
  });

  testWidgets('long Chinese notification remains usable on a narrow viewport', (
    tester,
  ) async {
    final longInbox = NotificationInboxData(
      items: <NotificationInboxItem>[
        notificationFixture(
          title: '人工审核状态已有更新，请打开应用查看当前记录',
          body:
              '这是一条仅包含通用说明的合成通知。请在经过身份验证的 Dr. AI 应用中查看已持久化的最新状态、历史记录和可执行操作；锁屏预览不会显示患者身份、诊断、药物或付款方备注。',
        ),
      ],
      unreadCount: 1,
      generatedAt: DateTime.now().toUtc(),
    );
    await pumpInbox(
      tester,
      repository: FakeDrAiRepository(notificationInbox: longInbox),
      locale: const Locale('zh'),
      size: const Size(412, 917),
      textScale: 1.35,
    );

    expect(tester.takeException(), isNull);
    expect(find.textContaining('人工审核状态'), findsOneWidget);
    expect(
      find.byKey(const Key('notification-category-filter')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('notification-status-filter')), findsOneWidget);
  });

  testWidgets(
    'keyboard traversal reaches notification filters in reading order',
    (tester) async {
      await pumpInbox(tester, repository: FakeDrAiRepository());
      final category = find.byKey(const Key('notification-category-filter'));
      final status = find.byKey(const Key('notification-status-filter'));

      for (var index = 0; index < 12; index += 1) {
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pump();
        if (Focus.of(tester.element(category)).hasFocus) break;
      }
      expect(Focus.of(tester.element(category)).hasFocus, isTrue);
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pump();
      expect(Focus.of(tester.element(status)).hasFocus, isTrue);
    },
  );

  testWidgets(
    'signed-out notification path resumes after role authentication',
    (tester) async {
      const notificationId = '11111111-1111-4111-8111-111111111111';
      final sessionState = RouterSessionState.hydrated(null);
      final signedOutRouter = createRouter(
        null,
        initialLocation: '/patient/notifications/$notificationId/open',
        sessionState: sessionState,
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            repositoryProvider.overrideWithValue(FakeDrAiRepository()),
          ],
          child: MaterialApp.router(
            theme: DrAiTheme.light,
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            routerConfig: signedOutRouter,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(signedOutRouter.routeInformationProvider.value.uri.path, '/login');

      signedOutRouter.dispose();
      sessionState.setSignedIn(AppRole.patient);
      final authenticatedRouter = createRouter(
        AppRole.patient,
        initialLocation: '/login',
        sessionState: sessionState,
      );
      addTearDown(authenticatedRouter.dispose);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            repositoryProvider.overrideWithValue(
              FakeDrAiRepository(
                notificationOpenResult: const NotificationOpenResult(
                  status: 'resolved',
                  destinationPath: '/patient/recovery-plan',
                ),
              ),
            ),
          ],
          child: MaterialApp.router(
            theme: DrAiTheme.light,
            supportedLocales: AppLocalizations.supportedLocales,
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            routerConfig: authenticatedRouter,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        authenticatedRouter.routeInformationProvider.value.uri.path,
        '/patient/recovery-plan',
      );
    },
  );

  test('open result rejects cross-role and absolute destinations', () {
    const patientPath = NotificationOpenResult(
      status: 'resolved',
      destinationPath: '/patient/recovery-plan',
    );
    const externalPath = NotificationOpenResult(
      status: 'resolved',
      destinationPath: 'https://example.invalid/private',
    );

    expect(patientPath.safePathFor(AppRole.patient), '/patient/recovery-plan');
    expect(patientPath.safePathFor(AppRole.doctor), isNull);
    expect(externalPath.safePathFor(AppRole.patient), isNull);
  });
}
