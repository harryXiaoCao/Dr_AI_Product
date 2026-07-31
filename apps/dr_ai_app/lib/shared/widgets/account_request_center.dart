import 'dart:async';
import 'dart:math';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/account/application/support_request_providers.dart';
import 'package:dr_ai_app/features/account/domain/support_request_data.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AccountRequestCenter extends ConsumerStatefulWidget {
  const AccountRequestCenter({required this.role, super.key});

  final AppRole role;

  @override
  ConsumerState<AccountRequestCenter> createState() =>
      _AccountRequestCenterState();
}

class _AccountRequestCenterState extends ConsumerState<AccountRequestCenter> {
  final _formKey = GlobalKey<FormState>();
  final _subjectController = TextEditingController();
  final _messageController = TextEditingController();
  final _formFocus = FocusNode();
  String _requestType = 'support';
  bool _understandsDeletionBoundary = false;
  bool _submitting = false;
  String? _submissionKey;
  String? _submissionSignature;
  int _submissionAttempts = 0;
  String? _statusMessage;
  bool _statusIsError = false;
  final Map<String, String> _withdrawalKeys = <String, String>{};
  final Set<String> _withdrawing = <String>{};

  @override
  void dispose() {
    _subjectController.dispose();
    _messageController.dispose();
    _formFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final requests = ref.watch(supportRequestsProvider);
    return Container(
      key: Key('${widget.role.wireValue}-account-request-center'),
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.lg),
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.lg),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: FocusTraversalGroup(
        policy: OrderedTraversalPolicy(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(
                  Icons.support_agent_outlined,
                  color: DrAiColors.brand,
                ),
                const SizedBox(width: DrAiSpacing.sm),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        context.l10n.accountRequestsTitle,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: DrAiColors.brandDark,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        context.l10n.accountRequestsDescription,
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          height: 1.45,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: DrAiSpacing.md),
            _requestForm(),
            const SizedBox(height: DrAiSpacing.lg),
            const Divider(color: DrAiColors.outline),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.requestHistoryTitle,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: DrAiColors.brandDark,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            requests.when(
              loading: () => Semantics(
                liveRegion: true,
                label: context.l10n.loadingAccountRequests,
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: DrAiSpacing.md),
                  child: LinearProgressIndicator(),
                ),
              ),
              error: (error, stackTrace) => _RequestLoadError(
                message: context.l10n.loadAccountRequestsFailed,
                onRetry: () {
                  _recordEvent(
                    eventName: 'workflow_retried',
                    outcome: 'retried',
                    failureCategory: null,
                  );
                  ref.invalidate(supportRequestsProvider);
                },
              ),
              data: (items) => items.isEmpty
                  ? _EmptyRequestHistory(onStart: _focusForm)
                  : Column(
                      children: <Widget>[
                        for (final request in items)
                          Padding(
                            padding: const EdgeInsets.only(
                              bottom: DrAiSpacing.sm,
                            ),
                            child: _requestHistoryCard(request),
                          ),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _requestForm() {
    final isDeletion = _requestType == 'deletion';
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          FocusTraversalOrder(
            order: const NumericFocusOrder(1),
            child: DropdownButtonFormField<String>(
              key: const Key('account-request-type'),
              focusNode: _formFocus,
              initialValue: _requestType,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: context.l10n.requestTypeLabel,
              ),
              items: <DropdownMenuItem<String>>[
                DropdownMenuItem(
                  value: 'support',
                  child: Text(context.l10n.supportRequestType),
                ),
                DropdownMenuItem(
                  value: 'feedback',
                  child: Text(context.l10n.feedbackRequestType),
                ),
                DropdownMenuItem(
                  value: 'deletion',
                  child: Text(context.l10n.deletionRequestType),
                ),
              ],
              onChanged: _submitting
                  ? null
                  : (value) {
                      setState(() {
                        _requestType = value ?? 'support';
                        _understandsDeletionBoundary = false;
                        _clearSubmissionIdentity();
                      });
                    },
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          FocusTraversalOrder(
            order: const NumericFocusOrder(2),
            child: TextFormField(
              key: const Key('account-request-subject'),
              controller: _subjectController,
              maxLength: 160,
              textInputAction: TextInputAction.next,
              decoration: InputDecoration(
                labelText: context.l10n.requestSubjectLabel,
                counterText: '',
              ),
              onChanged: (_) => _contentChanged(),
              validator: (value) {
                final length = value?.trim().length ?? 0;
                return length < 3
                    ? context.l10n.requestSubjectValidation
                    : null;
              },
            ),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          FocusTraversalOrder(
            order: const NumericFocusOrder(3),
            child: TextFormField(
              key: const Key('account-request-message'),
              controller: _messageController,
              minLines: 3,
              maxLines: 6,
              maxLength: 2000,
              decoration: InputDecoration(
                labelText: context.l10n.requestMessageLabel,
                helperText: context.l10n.requestPrivacyHelper,
              ),
              onChanged: (_) => _contentChanged(),
              validator: (value) {
                final length = value?.trim().length ?? 0;
                return length < 8
                    ? context.l10n.requestMessageValidation
                    : null;
              },
            ),
          ),
          if (isDeletion) ...<Widget>[
            const SizedBox(height: DrAiSpacing.xs),
            Material(
              color: DrAiColors.pageBackground,
              clipBehavior: Clip.antiAlias,
              shape: RoundedRectangleBorder(
                side: const BorderSide(color: DrAiColors.outline),
                borderRadius: BorderRadius.circular(DrAiRadii.md),
              ),
              child: Padding(
                padding: const EdgeInsets.all(DrAiSpacing.sm),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Text(
                      context.l10n.deletionRetentionBoundary,
                      style: const TextStyle(height: 1.45),
                    ),
                    FocusTraversalOrder(
                      order: const NumericFocusOrder(4),
                      child: CheckboxListTile(
                        key: const Key('account-request-deletion-boundary'),
                        contentPadding: EdgeInsets.zero,
                        controlAffinity: ListTileControlAffinity.leading,
                        value: _understandsDeletionBoundary,
                        onChanged: _submitting
                            ? null
                            : (value) => setState(
                                () => _understandsDeletionBoundary =
                                    value ?? false,
                              ),
                        title: Text(context.l10n.deletionBoundaryConfirmation),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          if (_statusMessage != null) ...<Widget>[
            const SizedBox(height: DrAiSpacing.sm),
            Semantics(
              liveRegion: true,
              child: Container(
                key: const Key('account-request-status'),
                padding: const EdgeInsets.all(DrAiSpacing.sm),
                decoration: BoxDecoration(
                  color: _statusIsError
                      ? const Color(0xFFFFEDEA)
                      : const Color(0xFFEAF8F3),
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Text(
                  _statusMessage!,
                  style: TextStyle(
                    color: _statusIsError
                        ? DrAiColors.danger
                        : const Color(0xFF08614F),
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ],
          const SizedBox(height: DrAiSpacing.sm),
          Align(
            alignment: Alignment.centerRight,
            child: FocusTraversalOrder(
              order: const NumericFocusOrder(5),
              child: FilledButton.icon(
                key: const Key('account-request-submit'),
                onPressed:
                    _submitting || (isDeletion && !_understandsDeletionBoundary)
                    ? null
                    : _submit,
                icon: _submitting
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: DrAiColors.white,
                        ),
                      )
                    : Icon(
                        _submissionAttempts > 0
                            ? Icons.refresh_outlined
                            : Icons.send_outlined,
                      ),
                label: Text(
                  _submitting
                      ? context.l10n.submittingRequest
                      : _submissionAttempts > 0
                      ? context.l10n.retryRequest
                      : context.l10n.submitRequest,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _requestHistoryCard(SupportRequestData request) {
    final withdrawing = _withdrawing.contains(request.id);
    return Material(
      key: Key('account-request-${request.publicReference}'),
      color: DrAiColors.white,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        side: const BorderSide(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: ExpansionTile(
        childrenPadding: const EdgeInsets.fromLTRB(
          DrAiSpacing.md,
          0,
          DrAiSpacing.md,
          DrAiSpacing.md,
        ),
        title: Row(
          children: <Widget>[
            Expanded(
              child: Text(
                request.subject,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
            const SizedBox(width: DrAiSpacing.xs),
            _RequestStatusBadge(status: request.status),
          ],
        ),
        subtitle: Text(
          '${_requestTypeLabel(request.requestType)} · '
          '${request.publicReference} · ${_date(request.updatedAt)}',
        ),
        children: <Widget>[
          Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              context.l10n.requestReceipt(request.publicReference),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          const SizedBox(height: DrAiSpacing.xs),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(_nextAction(request)),
          ),
          const SizedBox(height: DrAiSpacing.sm),
          _LifecycleNotice(
            text:
                '${_retentionBoundary(request.retentionBoundaryCode)}\n'
                '${_deletionEffect(request.deletionEffectCode)}',
          ),
          const SizedBox(height: DrAiSpacing.md),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              context.l10n.requestTimelineTitle,
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
          ),
          const SizedBox(height: DrAiSpacing.xs),
          if (request.timeline.isEmpty)
            Align(
              alignment: Alignment.centerLeft,
              child: Text(context.l10n.requestTimelineUnavailable),
            )
          else
            for (final entry in request.timeline)
              _RequestTimelineTile(
                entry: entry,
                summary: _timelineSummary(entry),
                actor: _actorLabel(entry.actorKind),
                date: _date(entry.occurredAt),
              ),
          if (request.canWithdraw) ...<Widget>[
            const SizedBox(height: DrAiSpacing.sm),
            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                key: Key('account-request-withdraw-${request.publicReference}'),
                onPressed: withdrawing ? null : () => _confirmWithdraw(request),
                icon: withdrawing
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.undo_outlined),
                label: Text(context.l10n.withdrawRequest),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      _recordEvent(
        eventName: 'workflow_failed',
        outcome: 'failed',
        failureCategory: 'validation',
      );
      return;
    }
    final signature =
        '$_requestType|${_subjectController.text.trim()}|'
        '${_messageController.text.trim()}';
    if (_submissionSignature != signature || _submissionKey == null) {
      _submissionSignature = signature;
      _submissionKey = _newKey('submit');
      _submissionAttempts = 0;
      _recordEvent(
        eventName: 'journey_started',
        outcome: 'started',
        failureCategory: null,
      );
    } else {
      _recordEvent(
        eventName: 'workflow_retried',
        outcome: 'retried',
        failureCategory: null,
      );
    }
    final startedAt = DateTime.now();
    setState(() {
      _submitting = true;
      _statusMessage = null;
      _statusIsError = false;
      _submissionAttempts += 1;
    });
    try {
      final created = await ref
          .read(repositoryProvider)
          .createSupportRequest(
            requestType: _requestType,
            subject: _subjectController.text,
            message: _messageController.text,
            idempotencyKey: _submissionKey!,
          );
      if (!mounted) return;
      _recordEvent(
        eventName: created.replay ? 'workflow_replayed' : 'journey_completed',
        outcome: created.replay ? 'replayed' : 'completed',
        failureCategory: null,
        latency: DateTime.now().difference(startedAt),
      );
      setState(() {
        _submitting = false;
        _statusIsError = false;
        _statusMessage = created.replay
            ? context.l10n.requestReplayConfirmed(created.publicReference)
            : context.l10n.requestSubmitted(created.publicReference);
        _subjectController.clear();
        _messageController.clear();
        _understandsDeletionBoundary = false;
        _submissionAttempts = 0;
        _clearSubmissionIdentity(clearStatus: false);
      });
      ref.invalidate(supportRequestsProvider);
    } on ApiError catch (error) {
      if (!mounted) return;
      final conflict = error.statusCode == 409 || error.code == 'conflict';
      _recordEvent(
        eventName: conflict ? 'workflow_conflict' : 'workflow_failed',
        outcome: conflict ? 'conflict' : 'failed',
        failureCategory: conflict ? null : _failureCategory(error),
        latency: DateTime.now().difference(startedAt),
      );
      setState(() {
        _submitting = false;
        _statusIsError = true;
        _statusMessage = conflict
            ? context.l10n.requestConflict
            : _safeError(error);
        if (conflict) {
          // The server has proved that this key belongs to different content.
          // Keep ambiguous transport failures on the original key, but rotate
          // after a confirmed 409 so an unchanged retry can be submitted.
          _submissionKey = _newKey('submit');
        }
      });
      if (conflict) ref.invalidate(supportRequestsProvider);
    } on Exception {
      if (!mounted) return;
      _recordEvent(
        eventName: 'workflow_failed',
        outcome: 'failed',
        failureCategory: 'network',
        latency: DateTime.now().difference(startedAt),
      );
      setState(() {
        _submitting = false;
        _statusIsError = true;
        _statusMessage = context.l10n.requestNetworkFailure;
      });
    }
  }

  Future<void> _confirmWithdraw(SupportRequestData request) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.withdrawRequestQuestion),
        content: Text(context.l10n.withdrawRequestDescription),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            key: const Key('account-request-withdraw-confirm'),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(context.l10n.withdrawRequest),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    final key = _withdrawalKeys.putIfAbsent(
      request.id,
      () => _newKey('withdraw'),
    );
    setState(() => _withdrawing.add(request.id));
    try {
      final updated = await ref
          .read(repositoryProvider)
          .withdrawSupportRequest(
            requestId: request.id,
            expectedVersion: request.version,
            idempotencyKey: key,
          );
      if (!mounted) return;
      _recordEvent(
        eventName: updated.replay ? 'workflow_replayed' : 'task_completed',
        outcome: updated.replay ? 'replayed' : 'completed',
        failureCategory: null,
      );
      setState(() {
        _withdrawing.remove(request.id);
        _withdrawalKeys.remove(request.id);
        _statusIsError = false;
        _statusMessage = updated.replay
            ? context.l10n.withdrawalReplayConfirmed
            : context.l10n.requestWithdrawn(updated.publicReference);
      });
      ref.invalidate(supportRequestsProvider);
    } on ApiError catch (error) {
      if (!mounted) return;
      final conflict = error.statusCode == 409 || error.code == 'conflict';
      _recordEvent(
        eventName: conflict ? 'workflow_conflict' : 'workflow_failed',
        outcome: conflict ? 'conflict' : 'failed',
        failureCategory: conflict ? null : _failureCategory(error),
      );
      setState(() {
        _withdrawing.remove(request.id);
        _statusIsError = true;
        _statusMessage = conflict
            ? context.l10n.withdrawalConflict
            : _safeError(error);
      });
      if (conflict) ref.invalidate(supportRequestsProvider);
    } on Exception {
      if (!mounted) return;
      _recordEvent(
        eventName: 'workflow_failed',
        outcome: 'failed',
        failureCategory: 'network',
      );
      setState(() {
        _withdrawing.remove(request.id);
        _statusIsError = true;
        _statusMessage = context.l10n.requestNetworkFailure;
      });
    }
  }

  void _contentChanged() {
    if (_submissionSignature == null &&
        _statusMessage == null &&
        _submissionAttempts == 0) {
      return;
    }
    setState(() {
      _clearSubmissionIdentity();
      _statusMessage = null;
      _statusIsError = false;
    });
  }

  void _clearSubmissionIdentity({bool clearStatus = true}) {
    _submissionKey = null;
    _submissionSignature = null;
    _submissionAttempts = 0;
    if (clearStatus) _statusMessage = null;
  }

  void _focusForm() {
    _formFocus.requestFocus();
    Scrollable.ensureVisible(
      _formFocus.context!,
      duration: const Duration(milliseconds: 180),
    );
  }

  String _newKey(String action) => '$action-${_opaqueUuid()}';

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

  void _recordEvent({
    required String eventName,
    required String outcome,
    required String? failureCategory,
    Duration? latency,
  }) {
    final width = MediaQuery.sizeOf(context).width;
    final locale = Localizations.localeOf(context).languageCode == 'zh'
        ? 'zh-Hans'
        : 'en';
    final platform = kIsWeb
        ? 'web'
        : switch (defaultTargetPlatform) {
            TargetPlatform.android => 'android',
            TargetPlatform.iOS => 'ios',
            TargetPlatform.macOS => 'macos',
            TargetPlatform.windows => 'windows',
            TargetPlatform.linux => 'linux',
            TargetPlatform.fuchsia => 'unknown',
          };
    unawaited(
      ref
          .read(repositoryProvider)
          .recordProductEvent(
            ProductEventInput(
              eventName: eventName,
              journeyCode: 'account_$_requestType',
              surfaceCode: 'account',
              outcome: outcome,
              failureCategory: failureCategory,
              latencyBucket: _latencyBucket(latency),
              locale: locale,
              platform: platform,
              layout: width < 600
                  ? 'mobile'
                  : width < 1024
                  ? 'tablet'
                  : 'desktop',
              // One opaque observation identifier. Never derive analytics
              // identity from a receipt, request id, user, or form content.
              deduplicationKey: _opaqueUuid(),
            ),
          ),
    );
  }

  String _requestTypeLabel(String value) => switch (value) {
    'feedback' => context.l10n.feedbackRequestType,
    'deletion' => context.l10n.deletionRequestType,
    _ => context.l10n.supportRequestType,
  };

  String _nextAction(SupportRequestData request) => switch (request.status) {
    'queued' => context.l10n.requestNextQueued,
    'reviewing' => context.l10n.requestNextReviewing,
    'resolved' => context.l10n.requestNextResolved,
    'failed' => context.l10n.requestNextFailed,
    'cancelled' => context.l10n.requestNextCancelled,
    _ => context.l10n.requestNextUnavailable,
  };

  String _retentionBoundary(String code) => switch (code) {
    'regulated_and_audit_retention_applies' =>
      context.l10n.deletionRetentionBoundary,
    'standard_support_retention' =>
      context.l10n.standardSupportRetentionBoundary,
    _ => context.l10n.unknownRetentionBoundary,
  };

  String _deletionEffect(String code) => switch (code) {
    'request_only_no_immediate_deletion' =>
      context.l10n.deletionRequestOnlyEffect,
    'not_a_deletion_request' => context.l10n.notDeletionRequestEffect,
    _ => context.l10n.unknownDeletionEffect,
  };

  String _timelineSummary(SupportRequestTimelineEntry entry) {
    return switch (entry.summaryCode) {
      'request_submitted' => context.l10n.timelineRequestSubmitted,
      'request_withdrawn_by_requester' => context.l10n.timelineRequestWithdrawn,
      'review_started' => context.l10n.timelineReviewStarted,
      'request_resolved' => context.l10n.timelineRequestResolved,
      _ => _statusLabel(entry.status),
    };
  }

  String _actorLabel(String actorKind) => switch (actorKind) {
    'requester' => context.l10n.timelineActorYou,
    'support_team' => context.l10n.timelineActorAuthorizedOperator,
    _ => context.l10n.timelineActorSystem,
  };

  String _statusLabel(String status) => switch (status) {
    'queued' => context.l10n.requestStatusQueued,
    'reviewing' => context.l10n.requestStatusReviewing,
    'resolved' => context.l10n.requestStatusResolved,
    'failed' => context.l10n.requestStatusFailed,
    'cancelled' => context.l10n.requestStatusCancelled,
    _ => context.l10n.requestStatusUnavailable,
  };

  String _date(DateTime value) {
    final local = value.toLocal();
    return '${MaterialLocalizations.of(context).formatShortDate(local)} '
        '${MaterialLocalizations.of(context).formatTimeOfDay(TimeOfDay.fromDateTime(local))}';
  }

  String _safeError(ApiError error) => switch (error.code) {
    'validation_failed' => context.l10n.requestSafeContentFailure,
    'forbidden' || 'unauthorized' => context.l10n.requestAuthorizationFailure,
    'service_unavailable' => context.l10n.requestNetworkFailure,
    _ => context.l10n.requestGenericFailure,
  };

  String _failureCategory(ApiError error) => switch (error.code) {
    'validation_failed' => 'validation',
    'forbidden' || 'unauthorized' => 'authorization',
    'not_found' => 'not_found',
    'conflict' => 'conflict',
    'service_unavailable' => 'network',
    _ => 'unknown',
  };

  String _latencyBucket(Duration? duration) {
    if (duration == null) return 'not_measured';
    final milliseconds = duration.inMilliseconds;
    if (milliseconds < 250) return 'lt_250ms';
    if (milliseconds < 1000) return '250_999ms';
    if (milliseconds < 3000) return '1_2_99s';
    if (milliseconds < 10000) return '3_9_99s';
    if (milliseconds < 30000) return '10_29_99s';
    return '30s_plus';
  }
}

class _RequestStatusBadge extends StatelessWidget {
  const _RequestStatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final (label, color, background) = switch (status) {
      'reviewing' => (
        context.l10n.requestStatusReviewing,
        const Color(0xFF6A4A00),
        const Color(0xFFFFF4D6),
      ),
      'resolved' => (
        context.l10n.requestStatusResolved,
        const Color(0xFF08614F),
        const Color(0xFFEAF8F3),
      ),
      'cancelled' => (
        context.l10n.requestStatusCancelled,
        DrAiColors.inkSecondary,
        DrAiColors.pageBackground,
      ),
      'failed' => (
        context.l10n.requestStatusFailed,
        DrAiColors.danger,
        const Color(0xFFFFEDEA),
      ),
      _ => (
        context.l10n.requestStatusQueued,
        DrAiColors.brandDark,
        DrAiColors.brandSoft,
      ),
    };
    return Semantics(
      label: label,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        decoration: BoxDecoration(
          color: background,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}

class _RequestTimelineTile extends StatelessWidget {
  const _RequestTimelineTile({
    required this.entry,
    required this.summary,
    required this.actor,
    required this.date,
  });

  final SupportRequestTimelineEntry entry;
  final String summary;
  final String actor;
  final String date;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: '$summary. $actor. $date.',
      child: Padding(
        padding: const EdgeInsets.only(bottom: DrAiSpacing.sm),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Padding(
              padding: EdgeInsets.only(top: 5),
              child: Icon(Icons.circle, size: 9, color: DrAiColors.brand),
            ),
            const SizedBox(width: DrAiSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    summary,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  Text(
                    '$actor · $date',
                    style: const TextStyle(color: DrAiColors.inkSecondary),
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

class _LifecycleNotice extends StatelessWidget {
  const _LifecycleNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E6),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: const Color(0xFFE4C36C)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.policy_outlined, size: 20),
          const SizedBox(width: DrAiSpacing.xs),
          Expanded(child: Text(text, style: const TextStyle(height: 1.45))),
        ],
      ),
    );
  }
}

class _RequestLoadError extends StatelessWidget {
  const _RequestLoadError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.md),
        child: Column(
          children: <Widget>[
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: DrAiSpacing.sm),
            OutlinedButton.icon(
              key: const Key('account-request-load-retry'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_outlined),
              label: Text(context.l10n.tryAgain),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyRequestHistory extends StatelessWidget {
  const _EmptyRequestHistory({required this.onStart});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: context.l10n.noAccountRequests,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.lg),
        child: Column(
          children: <Widget>[
            const Icon(
              Icons.inbox_outlined,
              size: 36,
              color: DrAiColors.inkSecondary,
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.noAccountRequests,
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            TextButton(
              key: const Key('account-request-empty-start'),
              onPressed: onStart,
              child: Text(context.l10n.startAccountRequest),
            ),
          ],
        ),
      ),
    );
  }
}
