import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:image_picker/image_picker.dart';

const int _maxAvatarBytes = 2 * 1024 * 1024;
const Set<String> _allowedAvatarMimeTypes = <String>{'image/jpeg', 'image/png'};

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
  final file = await ImagePicker().pickImage(
    source: ImageSource.gallery,
    maxWidth: 1024,
    maxHeight: 1024,
    imageQuality: 88,
  );
  if (file == null) {
    return null;
  }

  final bytes = await file.readAsBytes();
  if (bytes.lengthInBytes > _maxAvatarBytes) {
    throw const AvatarUploadException('Use a JPG or PNG up to 2 MB.');
  }

  final mimeType = _detectAvatarMimeType(
    bytes,
    reportedMimeType: file.mimeType,
    fileName: file.name,
  );
  if (mimeType == null || !_allowedAvatarMimeTypes.contains(mimeType)) {
    throw const AvatarUploadException('Use a JPG or PNG image.');
  }

  return AvatarUploadResult(
    dataUrl: 'data:$mimeType;base64,${base64Encode(bytes)}',
    fileName: file.name,
  );
}

ImageProvider<Object>? avatarImageProvider(String? value) {
  final source = value?.trim();
  if (source == null || source.isEmpty) {
    return null;
  }
  if (source.startsWith('data:image/')) {
    final commaIndex = source.indexOf(',');
    if (commaIndex == -1) {
      return null;
    }
    try {
      return MemoryImage(base64Decode(source.substring(commaIndex + 1)));
    } on FormatException {
      return null;
    }
  }
  return NetworkImage(source);
}

String? _detectAvatarMimeType(
  Uint8List bytes, {
  required String? reportedMimeType,
  required String fileName,
}) {
  if (reportedMimeType != null &&
      _allowedAvatarMimeTypes.contains(reportedMimeType)) {
    return reportedMimeType;
  }
  if (_isJpeg(bytes)) {
    return 'image/jpeg';
  }
  if (_isPng(bytes)) {
    return 'image/png';
  }
  final lowerName = fileName.toLowerCase();
  if (lowerName.endsWith('.jpg') || lowerName.endsWith('.jpeg')) {
    return 'image/jpeg';
  }
  if (lowerName.endsWith('.png')) {
    return 'image/png';
  }
  return reportedMimeType;
}

bool _isJpeg(Uint8List bytes) {
  return bytes.length >= 3 &&
      bytes[0] == 0xFF &&
      bytes[1] == 0xD8 &&
      bytes[2] == 0xFF;
}

bool _isPng(Uint8List bytes) {
  return bytes.length >= 8 &&
      bytes[0] == 0x89 &&
      bytes[1] == 0x50 &&
      bytes[2] == 0x4E &&
      bytes[3] == 0x47 &&
      bytes[4] == 0x0D &&
      bytes[5] == 0x0A &&
      bytes[6] == 0x1A &&
      bytes[7] == 0x0A;
}
