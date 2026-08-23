class ApiError implements Exception {
  const ApiError({
    required this.code,
    required this.message,
    this.statusCode,
    this.requestId,
    this.details = const <ApiErrorDetail>[],
  });

  final String code;
  final String message;
  final int? statusCode;
  final String? requestId;
  final List<ApiErrorDetail> details;

  @override
  String toString() => message;
}

class ApiErrorDetail {
  const ApiErrorDetail({required this.field, required this.code});

  factory ApiErrorDetail.fromJson(Map<String, dynamic> json) {
    return ApiErrorDetail(
      field: json['field'] as String? ?? 'request',
      code: json['code'] as String? ?? 'invalid_value',
    );
  }

  final String field;
  final String code;
}
