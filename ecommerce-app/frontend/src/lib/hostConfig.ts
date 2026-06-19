export type HostScenario = 'ecommerce' | 'healthcare' | 'banking';

export type HostRuntimeConfig = {
  VITE_SCENARIO?: string;
  VITE_HOST_APP_TITLE?: string;
  VITE_CHAT_WIDGET_THEME?: string;
};

function runtimeStr(key: keyof HostRuntimeConfig): string {
  if (typeof window === 'undefined') {
    return '';
  }
  const v = window.__RUNTIME_CONFIG__?.[key as keyof NonNullable<Window['__RUNTIME_CONFIG__']>];
  return v != null ? String(v).trim() : '';
}

export function resolveHostScenario(): HostScenario {
  const raw =
    runtimeStr('VITE_SCENARIO') ||
    String(import.meta.env.VITE_SCENARIO ?? 'ecommerce').trim().toLowerCase();
  if (raw === 'healthcare' || raw === 'banking') {
    return raw;
  }
  return 'ecommerce';
}

export function hostAppTitle(): string {
  const scenario = resolveHostScenario();
  const defaults: Record<HostScenario, string> = {
    ecommerce: 'Contoso',
    healthcare: 'Contoso Health',
    banking: 'Contoso Banking',
  };
  const fromEnv =
    runtimeStr('VITE_HOST_APP_TITLE') ||
    String(import.meta.env.VITE_HOST_APP_TITLE ?? '').trim();
  const genericTitles = new Set([
    'Contoso',
    'Contoso Bank',
    'Contoso Banking',
    'E-commerce Store',
    'Ecommerce Store',
  ]);
  if (scenario !== 'ecommerce' && (!fromEnv || genericTitles.has(fromEnv))) {
    return defaults[scenario];
  }
  return fromEnv || defaults[scenario];
}

export function hostComplianceBanner(): string {
  if (resolveHostScenario() === 'healthcare') {
    return 'Not for medical emergencies. This assistant does not provide medical diagnosis or treatment advice.';
  }
  if (resolveHostScenario() === 'banking') {
    return 'Not financial advice. Do not share full account numbers, PINs, or passwords in chat.';
  }
  return '';
}
