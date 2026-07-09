// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use

import 'dart:async';
import 'dart:html' as html;

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
  final input = html.FileUploadInputElement()
    ..accept = 'image/jpeg,image/png'
    ..multiple = false;
  input.click();
  await input.onChange.first;
  final files = input.files;
  if (files == null || files.isEmpty) {
    return null;
  }
  final file = files.first;
  if (file.size > 2 * 1024 * 1024) {
    throw const AvatarUploadException('Use a JPG or PNG up to 2 MB.');
  }
  if (file.type != 'image/jpeg' && file.type != 'image/png') {
    throw const AvatarUploadException('Use a JPG or PNG image.');
  }
  final reader = html.FileReader();
  reader.readAsDataUrl(file);
  await reader.onLoad.first;
  return AvatarUploadResult(
    dataUrl: reader.result as String,
    fileName: file.name,
  );
}
