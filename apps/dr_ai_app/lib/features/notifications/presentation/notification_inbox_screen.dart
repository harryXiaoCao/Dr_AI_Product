import 'dart:math';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/notifications/application/notification_providers.dart';
import 'package:dr_ai_app/features/notifications/domain/notification_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/navigation_back_button.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class NotificationInboxScreen extends ConsumerStatefulWidget {
  const NotificationInboxScreen({
    required this.role,
    this.originIndex,
    super.key,
  });

  final AppRole role;
  final int? originIndex;

  @override
  ConsumerState<NotificationInboxScreen> createState() =>
      _NotificationInboxScreenState();
}

class _NotificationInboxScreenState
    extends ConsumerState<NotificationInboxScreen> {
  String _category = 'all';
  String _status = 'all';
  final Map<String, FocusNode> _rowFocus = <String, FocusNode>{};
  Future<void> Function()? _retryAction;
  String? _actionError;

  @override
  void dispose() {
    for (final node in _rowFocus.values) {
      node.dispose();
    }
    super.dispose();
  }

  int get _selectedIndex => widget.originIndex ?? 0;

  @override
  Widget build(BuildContext context) {
    final inbox = ref.watch(notificationInboxProvider);
    return ResponsiveAppShell(
      role: widget.role,
      selectedIndex: _selectedIndex,
      child: NavigationPageFrame(
        fallbackPath: '/${widget.role.wireValue}',
        child: ColoredBox(
          color: DrAiColors.pageBackground,
          child: inbox.when(
            loading: () => DashboardLoadingView(
              label: _copy(context, 'Loading notifications', '正在加载通知'),
            ),
            error: (error, stackTrace) => DashboardErrorView(
              message: _loadError(context, error),
              onRetry: () => ref.invalidate(notificationInboxProvider),
            ),
            data: (data) => _inbox(context, data),
          ),
        ),
      ),
    );
  }

  Widget _inbox(BuildContext context, NotificationInboxData data) {
    final categories = <String>{
      'all',
      ...data.items.map((item) => item.category),
    }.toList();
    final visible = data.items.where((item) {
      if (_category != 'all' && item.category != _category) return false;
      return switch (_status) {
        'unread' => item.isUnread,
        'read' => !item.isUnread && !item.isDismissed,
        'dismissed' => item.isDismissed,
        'expired' => item.isExpired,
        'superseded' => item.isSuperseded,
        _ => true,
      };
    }).toList();
    final stale =
        DateTime.now().toUtc().difference(data.generatedAt) >
        const Duration(minutes: 5);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(notificationInboxProvider);
        await ref.read(notificationInboxProvider.future);
      },
      child: ListView(
        key: Key('${widget.role.wireValue}-notification-inbox'),
        padding: const EdgeInsets.all(DrAiSpacing.md),
        children: <Widget>[
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 920),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Semantics(
                    header: true,
                    child: Text(
                      _copy(context, 'Notifications', '通知'),
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  Text(
                    _copy(
                      context,
                      'Persisted reminders, warnings, and account updates. External delivery never replaces this inbox.',
                      '这里显示已持久化的提醒、警告和账户更新。外部投递不会替代此收件箱。',
                    ),
                    style: const TextStyle(color: DrAiColors.inkSecondary),
                  ),
                  const SizedBox(height: DrAiSpacing.md),
                  _InboxSummary(unreadCount: data.unreadCount, stale: stale),
                  const SizedBox(height: DrAiSpacing.md),
                  _filters(context, categories),
                  if (_actionError != null) ...<Widget>[
                    const SizedBox(height: DrAiSpacing.sm),
                    _ActionFailure(
                      message: _actionError!,
                      onRetry: _retryAction,
                    ),
                  ],
                  const SizedBox(height: DrAiSpacing.md),
                  if (data.items.isEmpty)
                    _EmptyInbox(role: widget.role)
                  else if (visible.isEmpty)
                    _EmptyFilter(onClear: _clearFilters)
                  else
                    for (final item in visible) ...<Widget>[
                      _notificationCard(context, item),
                      const SizedBox(height: DrAiSpacing.sm),
                    ],
                  const SizedBox(height: DrAiSpacing.sm),
                  _PreferencesAndReadiness(role: widget.role),
                  const SizedBox(height: DrAiSpacing.xl),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _filters(BuildContext context, List<String> categories) {
    return FocusTraversalGroup(
      child: Wrap(
        spacing: DrAiSpacing.sm,
        runSpacing: DrAiSpacing.sm,
        children: <Widget>[
          SizedBox(
            width: 220,
            child: DropdownButtonFormField<String>(
              key: const Key('notification-category-filter'),
              initialValue: _category,
              decoration: InputDecoration(
                labelText: _copy(context, 'Category', '类别'),
              ),
              items: categories
                  .map(
                    (value) => DropdownMenuItem<String>(
                      value: value,
                      child: Text(_categoryLabel(context, value)),
                    ),
                  )
                  .toList(),
              onChanged: (value) => setState(() => _category = value ?? 'all'),
            ),
          ),
          SizedBox(
            width: 220,
            child: DropdownButtonFormField<String>(
              key: const Key('notification-status-filter'),
              initialValue: _status,
              decoration: InputDecoration(
                labelText: _copy(context, 'Status', '状态'),
              ),
              items:
                  const <String>[
                        'all',
                        'unread',
                        'read',
                        'dismissed',
                        'expired',
                        'superseded',
                      ]
                      .map(
                        (value) => DropdownMenuItem<String>(
                          value: value,
                          child: Text(_statusLabel(context, value)),
                        ),
                      )
                      .toList(),
              onChanged: (value) => setState(() => _status = value ?? 'all'),
            ),
          ),
          if (_category != 'all' || _status != 'all')
            TextButton.icon(
              onPressed: _clearFilters,
              icon: const Icon(Icons.filter_alt_off_outlined),
              label: Text(_copy(context, 'Clear filters', '清除筛选')),
            ),
        ],
      ),
    );
  }

  Widget _notificationCard(BuildContext context, NotificationInboxItem item) {
    final focus = _rowFocus.putIfAbsent(item.id, FocusNode.new);
    final busy = ref.watch(notificationMutationControllerProvider).isLoading;
    return Semantics(
      container: true,
      label: [
        item.isUnread
            ? _copy(context, 'Unread notification', '未读通知')
            : _copy(context, 'Read notification', '已读通知'),
        _notificationTitle(context, item),
        _statusLabel(context, _effectiveStatus(item)),
      ].join('. '),
      child: Card(
        color: item.isUnread ? const Color(0xFFF4F6FF) : DrAiColors.white,
        child: Focus(
          focusNode: focus,
          child: Padding(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Icon(
                      _severityIcon(item.severity),
                      color: _severityColor(item.severity),
                      semanticLabel: _severityLabel(context, item.severity),
                    ),
                    const SizedBox(width: DrAiSpacing.sm),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            _notificationTitle(context, item),
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _notificationBody(context, item),
                            style: const TextStyle(height: 1.45),
                          ),
                        ],
                      ),
                    ),
                    if (item.isUnread)
                      Tooltip(
                        message: _copy(context, 'Unread', '未读'),
                        child: const Icon(
                          Icons.circle,
                          size: 10,
                          color: DrAiColors.brand,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: DrAiSpacing.sm),
                Wrap(
                  spacing: DrAiSpacing.xs,
                  runSpacing: DrAiSpacing.xs,
                  children: <Widget>[
                    _StatusChip(
                      label: _statusLabel(context, _effectiveStatus(item)),
                    ),
                    _StatusChip(label: _categoryLabel(context, item.category)),
                    _StatusChip(
                      label: _deliveryLabel(context, item.deliveryState),
                    ),
                  ],
                ),
                const SizedBox(height: DrAiSpacing.sm),
                Text(
                  '${_actorLabel(context, item.actorKind)} · '
                  '${_dateLabel(context, item.occurredAt)}',
                  style: const TextStyle(
                    color: DrAiColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
                if (item.scheduledFor != null)
                  Text(
                    '${_copy(context, 'Scheduled', '计划时间')}: '
                    '${_dateLabel(context, item.scheduledFor!)}',
                    style: const TextStyle(
                      color: DrAiColors.inkSecondary,
                      fontSize: 12,
                    ),
                  ),
                const SizedBox(height: DrAiSpacing.sm),
                Wrap(
                  spacing: DrAiSpacing.xs,
                  runSpacing: DrAiSpacing.xs,
                  children: <Widget>[
                    if (item.isActionable)
                      FilledButton.icon(
                        key: Key('notification-open-${item.id}'),
                        onPressed: busy ? null : () => _open(item, focus),
                        icon: const Icon(Icons.open_in_new_outlined),
                        label: Text(_copy(context, 'Open', '打开')),
                      ),
                    if (!item.isDismissed &&
                        !item.isExpired &&
                        !item.isSuperseded)
                      OutlinedButton(
                        key: Key('notification-read-${item.id}'),
                        onPressed: busy
                            ? null
                            : () => _setRead(item, read: item.isUnread),
                        child: Text(
                          item.isUnread
                              ? _copy(context, 'Mark read', '标记为已读')
                              : _copy(context, 'Mark unread', '标记为未读'),
                        ),
                      ),
                    if (item.canDismiss && !item.isDismissed)
                      TextButton(
                        key: Key('notification-dismiss-${item.id}'),
                        onPressed: busy ? null : () => _dismiss(item),
                        child: Text(_copy(context, 'Dismiss', '忽略')),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _setRead(
    NotificationInboxItem item, {
    required bool read,
  }) async {
    final idempotencyKey = _opaqueUuid();
    Future<void> action() => ref
        .read(notificationMutationControllerProvider.notifier)
        .setRead(item: item, read: read, idempotencyKey: idempotencyKey);
    await _runAction(action);
  }

  Future<void> _dismiss(NotificationInboxItem item) async {
    final idempotencyKey = _opaqueUuid();
    Future<void> action() => ref
        .read(notificationMutationControllerProvider.notifier)
        .dismiss(item: item, idempotencyKey: idempotencyKey);
    await _runAction(action);
  }

  Future<void> _runAction(Future<void> Function() action) async {
    setState(() {
      _actionError = null;
      _retryAction = null;
    });
    await action();
    final result = ref.read(notificationMutationControllerProvider);
    if (result.hasError && mounted) {
      setState(() {
        _actionError = _copy(
          context,
          'The update could not be saved. The inbox was not changed.',
          '无法保存更新，收件箱未发生更改。',
        );
        _retryAction = () => _runAction(action);
      });
    }
  }

  Future<void> _open(NotificationInboxItem item, FocusNode returnFocus) async {
    try {
      final result = await ref
          .read(repositoryProvider)
          .resolveNotificationOpen(item.id);
      if (!mounted) return;
      final safePath = result.safePathFor(widget.role);
      if (safePath == null) {
        context.push(
          '/${widget.role.wireValue}/notifications/${item.id}/unavailable'
          '?reason=${Uri.encodeQueryComponent(result.status)}',
        );
        return;
      }
      // The server-owned open transition marks the item read atomically.
      // Reusing the pre-open version here would create a false 409 conflict.
      await context.push(safePath);
      if (mounted) {
        ref.invalidate(notificationInboxProvider);
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (returnFocus.canRequestFocus) returnFocus.requestFocus();
        });
      }
    } on Exception {
      if (!mounted) return;
      setState(() {
        _actionError = _copy(
          context,
          'The destination could not be verified. No private content was shown.',
          '无法验证目标位置，未显示任何私密内容。',
        );
      });
    }
  }

  void _clearFilters() {
    setState(() {
      _category = 'all';
      _status = 'all';
    });
  }
}

class NotificationOpenScreen extends ConsumerStatefulWidget {
  const NotificationOpenScreen({
    required this.role,
    required this.notificationId,
    super.key,
  });

  final AppRole role;
  final String notificationId;

  @override
  ConsumerState<NotificationOpenScreen> createState() =>
      _NotificationOpenScreenState();
}

class _NotificationOpenScreenState
    extends ConsumerState<NotificationOpenScreen> {
  String? _failure;

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(_resolve);
  }

  Future<void> _resolve() async {
    try {
      final result = await ref
          .read(repositoryProvider)
          .resolveNotificationOpen(widget.notificationId);
      if (!mounted) return;
      final path = result.safePathFor(widget.role);
      if (path != null) {
        context.go(path);
        return;
      }
      setState(() => _failure = result.status);
    } on Exception {
      if (mounted) setState(() => _failure = 'denied');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: widget.role,
      child: _failure == null
          ? DashboardLoadingView(
              label: _copy(context, 'Verifying destination', '正在验证目标位置'),
            )
          : NotificationUnavailableScreen(role: widget.role, reason: _failure!),
    );
  }
}

class NotificationUnavailableScreen extends StatelessWidget {
  const NotificationUnavailableScreen({
    required this.role,
    required this.reason,
    super.key,
  });

  final AppRole role;
  final String reason;

  @override
  Widget build(BuildContext context) {
    final message = switch (reason) {
      'expired' => _copy(
        context,
        'This notification has expired and is no longer actionable.',
        '此通知已过期，无法继续操作。',
      ),
      'superseded' => _copy(
        context,
        'A newer update replaced this notification.',
        '此通知已被更新的内容替代。',
      ),
      'revoked' || 'denied' => _copy(
        context,
        'This destination is not available for the current signed-in account.',
        '当前登录账户无法访问此目标位置。',
      ),
      _ => _copy(
        context,
        'This destination is currently unavailable.',
        '此目标位置当前不可用。',
      ),
    };
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xl),
        child: Semantics(
          liveRegion: true,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const Icon(
                Icons.link_off_outlined,
                size: 48,
                color: DrAiColors.inkSecondary,
              ),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                _copy(context, 'Notification unavailable', '通知不可用'),
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: DrAiSpacing.md),
              FilledButton(
                onPressed: () => context.go('/${role.wireValue}/notifications'),
                child: Text(_copy(context, 'Return to inbox', '返回收件箱')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InboxSummary extends StatelessWidget {
  const _InboxSummary({required this.unreadCount, required this.stale});

  final int unreadCount;
  final bool stale;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      label: _copy(
        context,
        '$unreadCount unread notifications',
        '$unreadCount 条未读通知',
      ),
      child: Wrap(
        spacing: DrAiSpacing.sm,
        runSpacing: DrAiSpacing.sm,
        children: <Widget>[
          Chip(
            avatar: const Icon(Icons.mark_email_unread_outlined, size: 18),
            label: Text(
              _copy(context, '$unreadCount unread', '$unreadCount 条未读'),
            ),
          ),
          if (stale)
            Chip(
              avatar: const Icon(Icons.sync_problem_outlined, size: 18),
              label: Text(
                _copy(context, 'May be out of date — refresh', '内容可能已过时，请刷新'),
              ),
            ),
        ],
      ),
    );
  }
}

class _PreferencesAndReadiness extends ConsumerStatefulWidget {
  const _PreferencesAndReadiness({required this.role});

  final AppRole role;

  @override
  ConsumerState<_PreferencesAndReadiness> createState() =>
      _PreferencesAndReadinessState();
}

class _PreferencesAndReadinessState
    extends ConsumerState<_PreferencesAndReadiness> {
  final _timeZone = TextEditingController();
  final _quietStart = TextEditingController();
  final _quietEnd = TextEditingController();
  bool _initialized = false;
  String _locale = 'en';
  String _preview = 'generic';
  String? _preferenceIdempotencyKey;
  String? _saveError;

  @override
  void dispose() {
    _timeZone.dispose();
    _quietStart.dispose();
    _quietEnd.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final preferences = ref.watch(notificationPreferencesProvider);
    final readiness = ref.watch(notificationReadinessProvider);
    return Card(
      child: ExpansionTile(
        key: const Key('notification-preferences'),
        leading: const Icon(Icons.tune_outlined),
        title: Text(_copy(context, 'Preferences and delivery', '偏好与投递')),
        subtitle: Text(
          _copy(
            context,
            'In-product records stay available when external delivery is unavailable.',
            '外部投递不可用时，应用内记录仍然可见。',
          ),
        ),
        childrenPadding: const EdgeInsets.fromLTRB(
          DrAiSpacing.md,
          0,
          DrAiSpacing.md,
          DrAiSpacing.md,
        ),
        children: <Widget>[
          preferences.when(
            loading: () => const LinearProgressIndicator(),
            error: (error, stackTrace) => _InlineUnavailable(
              message: _copy(
                context,
                'Preferences are unavailable. Existing server settings were not changed.',
                '偏好设置当前不可用，服务器现有设置未被更改。',
              ),
              onRetry: () => ref.invalidate(notificationPreferencesProvider),
            ),
            data: (value) {
              _initialize(value);
              return _preferenceForm(context, value);
            },
          ),
          const Divider(height: DrAiSpacing.xl),
          readiness.when(
            loading: () => const LinearProgressIndicator(),
            error: (error, stackTrace) => _InlineUnavailable(
              message: _copy(
                context,
                'External delivery readiness could not be verified, so external controls remain unavailable.',
                '无法验证外部投递就绪状态，因此外部控制保持不可用。',
              ),
              onRetry: () => ref.invalidate(notificationReadinessProvider),
            ),
            data: (value) => _readiness(context, value),
          ),
        ],
      ),
    );
  }

  void _initialize(NotificationPreferences value) {
    if (_initialized) return;
    _initialized = true;
    _locale = value.locale;
    _preview = value.previewLevel;
    _timeZone.text = value.timeZone;
    _quietStart.text = value.quietHoursStart ?? '';
    _quietEnd.text = value.quietHoursEnd ?? '';
  }

  Widget _preferenceForm(
    BuildContext context,
    NotificationPreferences original,
  ) {
    final busy = ref.watch(notificationMutationControllerProvider).isLoading;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        SwitchListTile(
          key: const Key('notification-in-product-toggle'),
          contentPadding: EdgeInsets.zero,
          value: true,
          onChanged: null,
          title: Text(_copy(context, 'In-product notifications', '应用内通知')),
          subtitle: Text(
            _copy(
              context,
              'Safety-critical records remain visible even when optional categories are disabled.',
              '即使关闭可选类别，安全关键记录仍会保持可见。',
            ),
          ),
        ),
        Wrap(
          spacing: DrAiSpacing.sm,
          runSpacing: DrAiSpacing.sm,
          children: <Widget>[
            SizedBox(
              width: 210,
              child: DropdownButtonFormField<String>(
                initialValue: _locale,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Notification language', '通知语言'),
                ),
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(value: 'en', child: Text('English')),
                  DropdownMenuItem(value: 'zh-Hans', child: Text('简体中文')),
                ],
                onChanged: busy
                    ? null
                    : (value) => setState(() => _locale = value ?? 'en'),
              ),
            ),
            SizedBox(
              width: 250,
              child: TextFormField(
                key: const Key('notification-time-zone'),
                controller: _timeZone,
                enabled: !busy,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Time zone', '时区'),
                  helperText: 'Asia/Shanghai',
                ),
              ),
            ),
            SizedBox(
              width: 180,
              child: TextFormField(
                key: const Key('notification-quiet-start'),
                controller: _quietStart,
                enabled: !busy,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Quiet hours start', '免打扰开始'),
                  hintText: '22:00',
                ),
              ),
            ),
            SizedBox(
              width: 180,
              child: TextFormField(
                key: const Key('notification-quiet-end'),
                controller: _quietEnd,
                enabled: !busy,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Quiet hours end', '免打扰结束'),
                  hintText: '07:00',
                ),
              ),
            ),
            SizedBox(
              width: 250,
              child: DropdownButtonFormField<String>(
                initialValue: _preview,
                decoration: InputDecoration(
                  labelText: _copy(context, 'Lock-screen preview', '锁屏预览'),
                ),
                items: <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'generic',
                    child: Text(_copy(context, 'Generic only', '仅通用提示')),
                  ),
                  DropdownMenuItem(
                    value: 'private_in_app',
                    child: Text(
                      _copy(context, 'Hide details externally', '外部隐藏详情'),
                    ),
                  ),
                ],
                onChanged: busy
                    ? null
                    : (value) => setState(() => _preview = value ?? 'generic'),
              ),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.md),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton.icon(
            key: const Key('notification-preferences-save'),
            onPressed: busy ? null : () => _save(original),
            icon: busy
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.save_outlined),
            label: Text(_copy(context, 'Save preferences', '保存偏好')),
          ),
        ),
        if (_saveError != null) ...<Widget>[
          const SizedBox(height: DrAiSpacing.sm),
          _InlineUnavailable(
            message: _saveError!,
            onRetry: busy ? null : () => _save(original),
          ),
        ],
      ],
    );
  }

  Widget _readiness(BuildContext context, NotificationReadiness readiness) {
    if (readiness.channels.isEmpty) {
      return _InlineUnavailable(
        message: _copy(
          context,
          'External notification delivery is not configured. The persisted inbox remains available.',
          '外部通知投递尚未配置，已持久化的应用内收件箱仍可使用。',
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          _copy(context, 'External channel readiness', '外部渠道就绪状态'),
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        for (final channel in readiness.channels)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(
              channel.enabled
                  ? Icons.check_circle_outline
                  : Icons.block_outlined,
              color: channel.enabled
                  ? DrAiColors.accentMint
                  : DrAiColors.inkSecondary,
            ),
            title: Text(_channelLabel(context, channel.channel)),
            subtitle: Text(
              _readinessLabel(context, channel.status, channel.readinessCode),
            ),
            trailing: _StatusChip(
              label: channel.enabled
                  ? _copy(context, 'Ready', '已就绪')
                  : _copy(context, 'Unavailable', '不可用'),
            ),
          ),
      ],
    );
  }

  Future<void> _save(NotificationPreferences original) async {
    if (mounted) {
      setState(() => _saveError = null);
    }
    final idempotencyKey = _preferenceIdempotencyKey ??= _opaqueUuid();
    await ref
        .read(notificationMutationControllerProvider.notifier)
        .savePreferences(
          NotificationPreferences(
            allowedCategories: original.allowedCategories,
            inProductEnabled: true,
            externalChannels: original.externalChannels,
            quietHoursStart: _emptyToNull(_quietStart.text),
            quietHoursEnd: _emptyToNull(_quietEnd.text),
            locale: _locale,
            timeZone: _timeZone.text.trim(),
            previewLevel: _preview,
            version: original.version,
          ),
          idempotencyKey: idempotencyKey,
        );
    final result = ref.read(notificationMutationControllerProvider);
    if (!mounted) return;
    if (result.hasError) {
      setState(() {
        _saveError = _copy(
          context,
          'The preferences were not saved. Retry will safely reuse the same request.',
          '偏好未保存。重试将安全地复用同一请求。',
        );
      });
      return;
    }
    _preferenceIdempotencyKey = null;
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Text(label, style: const TextStyle(fontSize: 12)),
    );
  }
}

class _ActionFailure extends StatelessWidget {
  const _ActionFailure({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function()? onRetry;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Card(
        color: const Color(0xFFFFF4F4),
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.sm),
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
        ),
      ),
    );
  }
}

class _InlineUnavailable extends StatelessWidget {
  const _InlineUnavailable({required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.info_outline, color: DrAiColors.inkSecondary),
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

class _EmptyInbox extends StatelessWidget {
  const _EmptyInbox({required this.role});

  final AppRole role;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: _copy(context, 'No notifications', '暂无通知'),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.xl),
          child: Column(
            children: <Widget>[
              const Icon(
                Icons.notifications_none_outlined,
                size: 44,
                color: DrAiColors.inkSecondary,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              Text(
                _copy(context, 'No notifications yet', '暂无通知'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                _copy(
                  context,
                  'New authorized updates will appear here after the server persists them.',
                  '服务器持久化新的已授权更新后，它们会显示在这里。',
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyFilter extends StatelessWidget {
  const _EmptyFilter({required this.onClear});

  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: Column(
          children: <Widget>[
            Text(
              _copy(
                context,
                'No notifications match these filters.',
                '没有符合这些筛选条件的通知。',
              ),
            ),
            TextButton(
              onPressed: onClear,
              child: Text(_copy(context, 'Clear filters', '清除筛选')),
            ),
          ],
        ),
      ),
    );
  }
}

typedef _NotificationTemplate = ({
  String enTitle,
  String enBody,
  String zhTitle,
  String zhBody,
});

// Mirrors the fixed system copy in services/api/app/notification_contracts.py.
// Match stored text exactly so authored notification content stays untouched.
const _notificationTemplates = <String, _NotificationTemplate>{
  "care_relationship_approval_requested": (
    enTitle: "Doctor connection request",
    enBody: "Open Dr. AI to review a doctor connection request.",
    zhTitle: "医生连接请求",
    zhBody: "打开 Dr. AI 查看医生连接请求。",
  ),
  "medication_reminder": (
    enTitle: "Care reminder",
    enBody: "Open Dr. AI to review your scheduled care reminder.",
    zhTitle: "护理提醒",
    zhBody: "打开 Dr. AI 查看您的计划护理提醒。",
  ),
  "refill_reminder": (
    enTitle: "Refill reminder",
    enBody: "Open Dr. AI to review a refill reminder.",
    zhTitle: "续药提醒",
    zhBody: "打开 Dr. AI 查看续药提醒。",
  ),
  "recovery_task_due": (
    enTitle: "Recovery reminder",
    enBody: "Open Dr. AI to review a recovery task.",
    zhTitle: "康复提醒",
    zhBody: "打开 Dr. AI 查看康复任务。",
  ),
  "follow_up_milestone": (
    enTitle: "Follow-up reminder",
    enBody: "Open Dr. AI to review a follow-up milestone.",
    zhTitle: "随访提醒",
    zhBody: "打开 Dr. AI 查看随访节点。",
  ),
  "consultation_milestone": (
    enTitle: "Consultation update",
    enBody: "Open Dr. AI to review a consultation update.",
    zhTitle: "会诊更新",
    zhBody: "打开 Dr. AI 查看会诊更新。",
  ),
  "care_service_milestone": (
    enTitle: "Care milestone",
    enBody: "Open Dr. AI to review a scheduled care milestone.",
    zhTitle: "医疗服务节点",
    zhBody: "打开 Dr. AI 查看计划医疗服务节点。",
  ),
  "imaging_action_available": (
    enTitle: "Imaging update",
    enBody: "Open Dr. AI to review an available imaging action.",
    zhTitle: "影像更新",
    zhBody: "打开 Dr. AI 查看可执行的影像操作。",
  ),
  "missing_information_warning": (
    enTitle: "Information needs review",
    enBody: "Required information has not been recorded.",
    zhTitle: "信息需要审核",
    zhBody: "尚未记录所需信息。",
  ),
  "incomplete_allocation_warning": (
    enTitle: "Cost allocation incomplete",
    enBody:
        "A deterministic allocation check is incomplete. Review is recommended.",
    zhTitle: "费用分配不完整",
    zhBody: "确定性分配检查尚未完成，建议审核。",
  ),
  "payer_clarification_requested": (
    enTitle: "Clarification requested",
    enBody: "Open Dr. AI to review the payer clarification request.",
    zhTitle: "需要澄清",
    zhBody: "打开 Dr. AI 查看付款方的澄清请求。",
  ),
  "adherence_evidence_available": (
    enTitle: "Recorded care evidence updated",
    enBody: "Open Dr. AI to review newly recorded completion evidence.",
    zhTitle: "护理记录已更新",
    zhBody: "打开 Dr. AI 查看新记录的完成证据。",
  ),
  "imaging_status_warning": (
    enTitle: "Imaging status updated",
    enBody: "Open Dr. AI to review the recorded imaging status.",
    zhTitle: "影像状态已更新",
    zhBody: "打开 Dr. AI 查看已记录的影像状态。",
  ),
  "consultation_follow_up_warning": (
    enTitle: "Consultation status updated",
    enBody: "Open Dr. AI to review the consultation status.",
    zhTitle: "会诊状态已更新",
    zhBody: "打开 Dr. AI 查看会诊状态。",
  ),
  "payer_request_submitted": (
    enTitle: "Review request available",
    enBody: "Open Dr. AI to review a newly submitted request.",
    zhTitle: "有新的审核请求",
    zhBody: "打开 Dr. AI 查看新提交的请求。",
  ),
  "payer_doctor_response_added": (
    enTitle: "Additional information available",
    enBody: "Open Dr. AI to review an attributable response.",
    zhTitle: "有补充信息",
    zhBody: "打开 Dr. AI 查看可追溯的回复。",
  ),
  "payer_manual_review_transition": (
    enTitle: "Request status updated",
    enBody: "Open Dr. AI to review the latest human review status.",
    zhTitle: "请求状态已更新",
    zhBody: "打开 Dr. AI 查看最新的人工审核状态。",
  ),
  "payer_final_outcome": (
    enTitle: "Human review outcome recorded",
    enBody: "Open Dr. AI to review the recorded outcome.",
    zhTitle: "已记录人工审核结果",
    zhBody: "打开 Dr. AI 查看已记录的审核结果。",
  ),
  "payer_request_closed": (
    enTitle: "Review request closed",
    enBody: "Open Dr. AI to review the closed request history.",
    zhTitle: "审核请求已关闭",
    zhBody: "打开 Dr. AI 查看已关闭请求的历史记录。",
  ),
  "cost_variance_warning": (
    enTitle: "Cost comparison needs review",
    enBody:
        "A deterministic comparison is outside the published range. Review is recommended.",
    zhTitle: "费用比较需要审核",
    zhBody: "确定性比较结果超出已发布范围，建议进行审核。",
  ),
};

String _notificationTitle(BuildContext context, NotificationInboxItem item) {
  final template = _notificationTemplates[item.eventType];
  if (template == null ||
      (item.title != template.enTitle && item.title != template.zhTitle)) {
    return item.title;
  }
  return Localizations.localeOf(context).languageCode == 'zh'
      ? template.zhTitle
      : template.enTitle;
}

String _notificationBody(BuildContext context, NotificationInboxItem item) {
  final template = _notificationTemplates[item.eventType];
  if (template == null ||
      (item.body != template.enBody && item.body != template.zhBody)) {
    return item.body;
  }
  return Localizations.localeOf(context).languageCode == 'zh'
      ? template.zhBody
      : template.enBody;
}

String _loadError(BuildContext context, Object error) {
  if (error is ApiError &&
      (error.code == 'service_unavailable' || error.statusCode == null)) {
    return _copy(
      context,
      'Notifications are unavailable offline. Reconnect and retry; persisted server state was not changed.',
      '离线时无法获取通知。请重新连接后重试；服务器持久化状态未被更改。',
    );
  }
  return _copy(
    context,
    'Notifications are temporarily unavailable. Retry to read the persisted inbox.',
    '通知暂时不可用。请重试以读取已持久化的收件箱。',
  );
}

String _effectiveStatus(NotificationInboxItem item) {
  if (item.isDismissed) return 'dismissed';
  if (item.isExpired) return 'expired';
  if (item.isSuperseded) return 'superseded';
  return item.isUnread ? 'unread' : 'read';
}

String _statusLabel(BuildContext context, String value) => switch (value) {
  'all' => _copy(context, 'All statuses', '全部状态'),
  'unread' => _copy(context, 'Unread', '未读'),
  'read' => _copy(context, 'Read', '已读'),
  'dismissed' => _copy(context, 'Dismissed', '已忽略'),
  'expired' => _copy(context, 'Expired', '已过期'),
  'superseded' => _copy(context, 'Superseded', '已被替代'),
  'scheduled' => _copy(context, 'Scheduled', '已计划'),
  'retrying' => _copy(context, 'Retrying', '正在重试'),
  'failed' => _copy(context, 'Failed', '失败'),
  'cancelled' => _copy(context, 'Cancelled', '已取消'),
  _ => context.l10n.stableValue(value),
};

String _categoryLabel(BuildContext context, String value) => switch (value) {
  'all' => _copy(context, 'All categories', '全部类别'),
  'medication_reminder' => _copy(context, 'Medication', '用药'),
  'recovery_task' => _copy(context, 'Recovery', '康复'),
  'payer_request' => _copy(context, 'Payer review', '支付方审核'),
  'expected_care_comparison' => _copy(context, 'Cost comparison', '费用比较'),
  'consultation' => _copy(context, 'Consultation', '会诊'),
  'imaging' => _copy(context, 'Imaging', '影像'),
  'system' || 'legacy' => _copy(context, 'System', '系统'),
  _ => context.l10n.stableValue(value),
};

String _deliveryLabel(BuildContext context, String value) => switch (value) {
  'accepted' => _copy(context, 'Provider accepted', '提供方已接受'),
  'sent' => _copy(context, 'Sent', '已发送'),
  'delivered' => _copy(context, 'Delivered', '已送达'),
  'failed' => _copy(context, 'Delivery failed', '投递失败'),
  'retrying' => _copy(context, 'Retrying delivery', '正在重试投递'),
  'expired' => _copy(context, 'Delivery expired', '投递已过期'),
  'unknown' => _copy(context, 'Delivery unknown', '投递状态未知'),
  'quiet_hours' => _copy(context, 'Held for quiet hours', '免打扰期间暂缓'),
  'not_requested' => _copy(context, 'In-product only', '仅应用内'),
  'in_product_only' => _copy(context, 'In-product only', '仅应用内'),
  _ => context.l10n.stableValue(value),
};

String _severityLabel(BuildContext context, String value) => switch (value) {
  'warning' => _copy(context, 'Warning', '警告'),
  'action' => _copy(context, 'Action requested', '需要操作'),
  _ => _copy(context, 'Information', '信息'),
};

IconData _severityIcon(String value) => switch (value) {
  'warning' => Icons.warning_amber_rounded,
  'action' => Icons.task_alt_outlined,
  _ => Icons.info_outline,
};

Color _severityColor(String value) => switch (value) {
  'warning' => DrAiColors.accentOrange,
  'action' => DrAiColors.brand,
  _ => DrAiColors.inkSecondary,
};

String _actorLabel(BuildContext context, String value) => switch (value) {
  'doctor' => _copy(context, 'Doctor', '医生'),
  'payer_reviewer' || 'payer' => _copy(context, 'Payer reviewer', '支付方审核员'),
  _ => _copy(context, 'Dr. AI system', 'Dr. AI 系统'),
};

String _channelLabel(BuildContext context, String value) => switch (value) {
  'in_app' => _copy(context, 'In-product inbox', '应用内收件箱'),
  'apns' => 'Apple Push Notification service',
  'android_emas' => _copy(context, 'Android push', 'Android 推送'),
  'web_push' => 'Web Push',
  _ => value,
};

String _readinessLabel(BuildContext context, String status, String readiness) {
  if (status == 'permission_denied' || status == 'permission_revoked') {
    return _copy(context, 'Permission denied or revoked', '权限已拒绝或撤销');
  }
  if (status == 'permission_not_requested') {
    return _copy(context, 'Permission not requested', '尚未请求权限');
  }
  return switch (readiness) {
    'ready' => _copy(context, 'Ready', '已就绪'),
    'unsupported_platform' => _copy(context, 'Unsupported platform', '平台不支持'),
    'missing_provider_credentials' => _copy(
      context,
      'Provider credentials are not configured',
      '尚未配置提供方凭据',
    ),
    'stale_endpoint' => _copy(context, 'Device endpoint is stale', '设备端点已过期'),
    'signed_out' => _copy(context, 'Device is signed out', '设备已退出登录'),
    _ => _copy(context, 'Unavailable', '不可用'),
  };
}

String _dateLabel(BuildContext context, DateTime value) {
  return DateFormat.yMMMd(
    Localizations.localeOf(context).toLanguageTag(),
  ).add_jm().format(value.toLocal());
}

String _copy(BuildContext context, String en, String zh) {
  return Localizations.localeOf(context).languageCode == 'zh' ? zh : en;
}

String _opaqueUuid() {
  final bytes = List<int>.generate(16, (_) => Random.secure().nextInt(256));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  final hex = bytes.map((value) => value.toRadixString(16).padLeft(2, '0'));
  final value = hex.join();
  return '${value.substring(0, 8)}-${value.substring(8, 12)}-'
      '${value.substring(12, 16)}-${value.substring(16, 20)}-'
      '${value.substring(20)}';
}

String? _emptyToNull(String value) {
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}
