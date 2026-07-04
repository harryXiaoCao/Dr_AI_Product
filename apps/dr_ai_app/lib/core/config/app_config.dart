abstract final class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'DR_AI_API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
}
