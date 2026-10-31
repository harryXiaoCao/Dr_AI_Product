import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/shared/widgets/sign_out_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

class HospitalAdminScreen extends ConsumerStatefulWidget {
  const HospitalAdminScreen({super.key});

  @override
  ConsumerState<HospitalAdminScreen> createState() =>
      _HospitalAdminScreenState();
}

class _HospitalAdminScreenState extends ConsumerState<HospitalAdminScreen> {
  Map<String, dynamic>? _data;
  Object? _error;
  bool _loading = true;
  String? _clinicId;
  String? _status;
  int _page = 1;
  int _section = 0;

  String _t(String en, String zh) =>
      Localizations.localeOf(context).languageCode == 'zh' ? zh : en;

  String _statusLabel(String status) => switch (status) {
    'requested' => _t('Requested', '待处理'),
    'scheduled' => _t('Scheduled', '已排期'),
    'approved' => _t('Approved', '已批准'),
    'declined' => _t('Declined', '已拒绝'),
    'completed' => _t('Completed', '已完成'),
    'cancelled' => _t('Cancelled', '已取消'),
    'available' => _t('Available', '可用'),
    'limited' => _t('Limited', '受限'),
    'unavailable' => _t('Unavailable', '不可用'),
    'active' => _t('Active', '有效'),
    'revoked' => _t('Revoked', '已撤销'),
    _ => status,
  };

  String _actionLabel(String status) => switch (status) {
    'approved' => _t('Approve', '批准'),
    'declined' => _t('Decline', '拒绝'),
    'completed' => _t('Mark complete', '标记完成'),
    'cancelled' => _t('Cancel', '取消'),
    _ => _statusLabel(status),
  };

  String _typeLabel(String type) => switch (type) {
    'equipment' => _t('Equipment', '设备'),
    _ => type,
  };

  String _time(Object? raw) {
    final value = DateTime.tryParse(raw?.toString() ?? '');
    if (value == null) return '—';
    return DateFormat('yyyy-MM-dd HH:mm').format(value.toLocal());
  }

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(_load);
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ref
          .read(repositoryProvider)
          .loadHospitalWorkspace(
            clinicId: _clinicId,
            status: _status,
            page: _page,
          );
      if (mounted) {
        setState(() {
          _data = data;
          _loading = false;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = error;
          _loading = false;
        });
      }
    }
  }

  Future<String?> _reason(String title) async {
    var reason = '';
    final result = await showDialog<String>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, update) => AlertDialog(
          title: Text(title),
          content: TextField(
            autofocus: true,
            maxLength: 240,
            onChanged: (value) => update(() => reason = value),
            decoration: InputDecoration(
              labelText: _t('Reason for audit record', '操作原因（用于审计）'),
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(_t('Cancel', '取消')),
            ),
            FilledButton(
              onPressed: reason.trim().length < 3
                  ? null
                  : () => Navigator.pop(context, reason.trim()),
              child: Text(_t('Confirm', '确认')),
            ),
          ],
        ),
      ),
    );
    return result;
  }

  Future<void> _act(
    Future<void> Function(String reason) action,
    String title,
  ) async {
    final reason = await _reason(title);
    if (reason == null) return;
    try {
      await action(reason);
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_t('Change saved and audited.', '更改已保存并记录审计。')),
          ),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_t('Change failed: $error', '更改失败：$error'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final hospital = (_data?['hospital'] as Map?)?['name']?.toString() ?? '';
    final clinics = (_data?['clinics'] as List?) ?? const [];
    return Scaffold(
      backgroundColor: DrAiColors.pageBackground,
      appBar: AppBar(
        title: Text(_t('Hospital operations', '医院运营工作台')),
        actions: <Widget>[
          IconButton(
            tooltip: _t('Refresh', '刷新'),
            onPressed: _load,
            icon: const Icon(Icons.refresh),
          ),
          const SignOutButton(),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1280),
          child: ListView(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              Text(hospital, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                _t(
                  'Operational counts only. Clinical quality and coverage decisions belong to clinicians and payers.',
                  '仅显示运营数量。医疗质量与保障范围由临床人员和支付方判断。',
                ),
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                children: <Widget>[
                  DropdownMenu<String?>(
                    key: const Key('admin-department-filter'),
                    label: Text(_t('Department', '科室')),
                    initialSelection: _clinicId,
                    dropdownMenuEntries: <DropdownMenuEntry<String?>>[
                      DropdownMenuEntry(
                        value: null,
                        label: _t('All permitted departments', '所有授权科室'),
                      ),
                      for (final raw in clinics)
                        DropdownMenuEntry(
                          value: (raw as Map)['id'].toString(),
                          label: raw['name'].toString(),
                        ),
                    ],
                    onSelected: (value) {
                      _clinicId = value;
                      _page = 1;
                      _load();
                    },
                  ),
                  SegmentedButton<int>(
                    segments: <ButtonSegment<int>>[
                      ButtonSegment(value: 0, label: Text(_t('Demand', '需求'))),
                      ButtonSegment(
                        value: 1,
                        label: Text(_t('Requests', '申请')),
                      ),
                      ButtonSegment(
                        value: 2,
                        label: Text(_t('Resources', '资源')),
                      ),
                      ButtonSegment(
                        value: 3,
                        label: Text(_t('Staff access', '员工权限')),
                      ),
                    ],
                    selected: <int>{_section},
                    onSelectionChanged: (selection) =>
                        setState(() => _section = selection.first),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (_loading)
                const Center(child: CircularProgressIndicator())
              else if (_error != null)
                _panel(
                  Column(
                    children: <Widget>[
                      Text(_t('Unable to load hospital data.', '无法加载医院数据。')),
                      TextButton(
                        onPressed: _load,
                        child: Text(_t('Retry', '重试')),
                      ),
                    ],
                  ),
                )
              else ...<Widget>[
                if (_section == 0) _demand(),
                if (_section == 1) _requests(),
                if (_section == 2) _resources(),
                if (_section == 3) _staff(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _panel(Widget child) => Card(
    child: Padding(padding: const EdgeInsets.all(DrAiSpacing.md), child: child),
  );

  Widget _demand() {
    final counts = (_data?['counts'] as Map?) ?? const {};
    final bookings = (counts['equipment_requests'] as Map?) ?? const {};
    final appointments = (counts['appointments'] as Map?) ?? const {};
    return _panel(
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            _t('Operational demand and recorded outcomes', '运营需求与已记录结果'),
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Text(
            _t('Equipment requests', '设备申请'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          Text(_counts(bookings)),
          const SizedBox(height: 12),
          Text(
            _t('Appointments', '预约'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          Text(_counts(appointments)),
          const SizedBox(height: 12),
          Text(
            _t(
              'Completed means the workflow was marked complete; it does not measure treatment success.',
              '“已完成”仅表示工作流程已标记完成，不代表治疗成功。',
            ),
          ),
        ],
      ),
    );
  }

  String _counts(Map<dynamic, dynamic> counts) => counts.isEmpty
      ? _t('No recorded activity', '暂无记录')
      : counts.entries
            .map(
              (entry) =>
                  '${_statusLabel(entry.key.toString())}: ${entry.value}',
            )
            .join('  ·  ');

  Widget _requests() {
    final rows = (_data?['bookings'] as List?) ?? const [];
    final total = (_data?['total'] as num?)?.toInt() ?? 0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        _panel(
          Wrap(
            spacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: <Widget>[
              Text(_t('Equipment booking queue ($total)', '设备预约队列（$total）')),
              DropdownMenu<String?>(
                key: const Key('admin-status-filter'),
                label: Text(_t('Status', '状态')),
                initialSelection: _status,
                dropdownMenuEntries: <DropdownMenuEntry<String?>>[
                  DropdownMenuEntry(
                    value: null,
                    label: _t('All statuses', '全部状态'),
                  ),
                  for (final status in <String>[
                    'requested',
                    'approved',
                    'declined',
                    'completed',
                    'cancelled',
                  ])
                    DropdownMenuEntry(
                      value: status,
                      label: _statusLabel(status),
                    ),
                ],
                onSelected: (value) {
                  _status = value;
                  _page = 1;
                  _load();
                },
              ),
            ],
          ),
        ),
        if (rows.isEmpty)
          _panel(Text(_t('No bookings match these filters.', '没有符合筛选条件的预约。'))),
        for (final raw in rows) _booking(raw as Map),
        _panel(
          Row(
            children: <Widget>[
              Text(_t('Page $_page', '第 $_page 页')),
              const Spacer(),
              TextButton(
                onPressed: _page > 1
                    ? () {
                        _page--;
                        _load();
                      }
                    : null,
                child: Text(_t('Previous', '上一页')),
              ),
              TextButton(
                onPressed: _page * 25 < total
                    ? () {
                        _page++;
                        _load();
                      }
                    : null,
                child: Text(_t('Next', '下一页')),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _booking(Map<dynamic, dynamic> row) => _panel(
    LayoutBuilder(
      builder: (context, constraints) {
        final details = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              '${row['equipment']} · ${row['clinic_name']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Text(
              '${_statusLabel(row['status'].toString())} · ${_time(row['start_at'])}',
            ),
            Text(row['purpose']?.toString() ?? ''),
          ],
        );
        final actions = Wrap(
          spacing: 8,
          children: <Widget>[
            for (final next in switch (row['status']) {
              'requested' => <String>['approved', 'declined'],
              'approved' => <String>['completed', 'cancelled'],
              _ => <String>[],
            })
              OutlinedButton(
                onPressed: () => _act(
                  (reason) =>
                      ref.read(repositoryProvider).updateHospitalBooking(
                        row['id'].toString(),
                        <String, dynamic>{'status': next, 'reason': reason},
                      ),
                  _t(
                    'Change request to ${_statusLabel(next)}',
                    '将申请状态改为${_statusLabel(next)}',
                  ),
                ),
                child: Text(_actionLabel(next)),
              ),
          ],
        );
        if (constraints.maxWidth < 650) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[details, actions],
          );
        }
        return Row(
          children: <Widget>[
            Expanded(child: details),
            const SizedBox(width: 16),
            actions,
          ],
        );
      },
    ),
  );

  Widget _resources() {
    final rows = (_data?['resources'] as List?) ?? const [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        if (rows.isEmpty)
          _panel(
            Text(
              _t(
                'No resources are recorded for these departments.',
                '这些科室尚无资源记录。',
              ),
            ),
          ),
        for (final raw in rows) _panel(_resource(raw as Map)),
      ],
    );
  }

  Widget _resource(Map<dynamic, dynamic> row) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      Text(
        row['name'].toString(),
        style: Theme.of(context).textTheme.titleMedium,
      ),
      Text(
        '${_typeLabel(row['type'].toString())} · ${_statusLabel(row['status'].toString())} · ${row['capacity_current'] ?? '—'} / ${row['capacity_total'] ?? '—'}',
      ),
      Wrap(
        spacing: 8,
        children: <Widget>[
          for (final next in <String>['available', 'limited', 'unavailable'])
            OutlinedButton(
              onPressed: row['status'] == next
                  ? null
                  : () => _act(
                      (reason) =>
                          ref.read(repositoryProvider).updateHospitalResource(
                            row['id'].toString(),
                            <String, dynamic>{
                              'status': next,
                              'capacity_current': row['capacity_current'],
                              'reason': reason,
                            },
                          ),
                      _t(
                        'Set availability to ${_statusLabel(next)}',
                        '将可用状态设为${_statusLabel(next)}',
                      ),
                    ),
              child: Text(_statusLabel(next)),
            ),
        ],
      ),
    ],
  );

  Widget _staff() {
    final rows = (_data?['staff'] as List?) ?? const [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        _panel(
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              onPressed: _grantStaff,
              icon: const Icon(Icons.person_add_alt_1),
              label: Text(_t('Grant doctor department access', '授予医生科室权限')),
            ),
          ),
        ),
        if (rows.isEmpty)
          _panel(Text(_t('No doctor assignments are recorded.', '暂无医生权限记录。'))),
        for (final raw in rows) _panel(_staffRow(raw as Map)),
      ],
    );
  }

  Widget _staffRow(Map<dynamic, dynamic> row) => Wrap(
    alignment: WrapAlignment.spaceBetween,
    crossAxisAlignment: WrapCrossAlignment.center,
    spacing: 12,
    runSpacing: 8,
    children: <Widget>[
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            row['name'].toString(),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          Text(
            '${row['email']} · ${row['clinic_name']} · ${_statusLabel(row['status'].toString())}',
          ),
        ],
      ),
      TextButton(
        onPressed: () => _act(
          (reason) => ref
              .read(repositoryProvider)
              .updateHospitalStaff(<String, dynamic>{
                'email': row['email'],
                'clinic_id': row['clinic_id'],
                'active': row['status'] != 'active',
                'reason': reason,
              }),
          row['status'] == 'active'
              ? _t('Revoke access', '撤销权限')
              : _t('Restore access', '恢复权限'),
        ),
        child: Text(
          row['status'] == 'active' ? _t('Revoke', '撤销') : _t('Restore', '恢复'),
        ),
      ),
    ],
  );

  Future<void> _grantStaff() async {
    var email = '';
    String? clinic = _clinicId;
    final clinics = (_data?['clinics'] as List?) ?? const [];
    final entry = await showDialog<Map<String, String>>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, update) => AlertDialog(
          title: Text(_t('Grant doctor access', '授予医生权限')),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              TextField(
                keyboardType: TextInputType.emailAddress,
                onChanged: (value) => update(() => email = value),
                decoration: InputDecoration(
                  labelText: _t('Doctor account email', '医生账户邮箱'),
                ),
              ),
              DropdownButtonFormField<String>(
                initialValue: clinic,
                decoration: InputDecoration(labelText: _t('Department', '科室')),
                items: <DropdownMenuItem<String>>[
                  for (final raw in clinics)
                    DropdownMenuItem(
                      value: (raw as Map)['id'].toString(),
                      child: Text(raw['name'].toString()),
                    ),
                ],
                onChanged: (value) => update(() => clinic = value),
              ),
            ],
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(_t('Cancel', '取消')),
            ),
            FilledButton(
              onPressed: clinic == null || !email.contains('@')
                  ? null
                  : () => Navigator.pop(context, <String, String>{
                      'email': email.trim(),
                      'clinic': clinic!,
                    }),
              child: Text(_t('Continue', '继续')),
            ),
          ],
        ),
      ),
    );
    if (entry == null) return;
    await _act(
      (reason) =>
          ref.read(repositoryProvider).updateHospitalStaff(<String, dynamic>{
            'email': entry['email'],
            'clinic_id': entry['clinic'],
            'active': true,
            'reason': reason,
          }),
      _t('Confirm doctor access', '确认医生权限'),
    );
  }
}
