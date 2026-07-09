class AvatarUploadException implements Exception {
  const AvatarUploadException(this.message);

  final String message;

  @override
  String toString() => message;
}

class AvatarUploadResult {
  const AvatarUploadResult({required this.dataUrl, required this.fileName});

  final String dataUrl;
  final String fileName;
}

Future<AvatarUploadResult?> pickAvatarImage() async {
  return null;
}
