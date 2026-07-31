import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/notifications/domain/notification_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final notificationInboxProvider =
    FutureProvider.autoDispose<NotificationInboxData>((ref) async {
      return ref.read(repositoryProvider).loadNotificationInbox();
    });

final notificationPreferencesProvider =
    FutureProvider.autoDispose<NotificationPreferences>((ref) async {
      return ref.read(repositoryProvider).loadNotificationPreferences();
    });

final notificationReadinessProvider =
    FutureProvider.autoDispose<NotificationReadiness>((ref) async {
      return ref.read(repositoryProvider).loadNotificationReadiness();
    });

final notificationMutationControllerProvider =
    AsyncNotifierProvider<
      NotificationMutationController,
      NotificationInboxItem?
    >(NotificationMutationController.new);

class NotificationMutationController
    extends AsyncNotifier<NotificationInboxItem?> {
  @override
  Future<NotificationInboxItem?> build() async => null;

  Future<void> setRead({
    required NotificationInboxItem item,
    required bool read,
    required String idempotencyKey,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(repositoryProvider)
          .setNotificationReadStatus(
            notificationId: item.id,
            read: read,
            expectedVersion: item.version,
            idempotencyKey: idempotencyKey,
          ),
    );
    if (!state.hasError) ref.invalidate(notificationInboxProvider);
  }

  Future<void> dismiss({
    required NotificationInboxItem item,
    required String idempotencyKey,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(repositoryProvider)
          .dismissNotification(
            notificationId: item.id,
            expectedVersion: item.version,
            idempotencyKey: idempotencyKey,
          ),
    );
    if (!state.hasError) ref.invalidate(notificationInboxProvider);
  }

  Future<void> savePreferences(
    NotificationPreferences preferences, {
    required String idempotencyKey,
  }) async {
    state = const AsyncLoading();
    final result = await AsyncValue.guard(() async {
      await ref
          .read(repositoryProvider)
          .updateNotificationPreferences(
            preferences,
            idempotencyKey: idempotencyKey,
          );
      return null;
    });
    state = result;
    if (!state.hasError) {
      ref
        ..invalidate(notificationPreferencesProvider)
        ..invalidate(notificationReadinessProvider)
        ..invalidate(notificationInboxProvider);
    }
  }
}
