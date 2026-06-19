function removeKeyFromJSON(input: Record<string, unknown>, keyToRemove: string) {
  const cloned = { ...input };
  delete cloned[keyToRemove];
  return cloned;
}

function sanitizeJSONString(input: string): string {
  return input.replace(/[\u0000-\u001F]+/g, '').trim();
}

function parseNestedAnswer(input: unknown): string {
  if (typeof input === 'string') {
    return input;
  }

  if (input && typeof input === 'object' && 'answer' in input) {
    return parseNestedAnswer((input as Record<string, unknown>).answer);
  }

  return '';
}

export const parseJSONSafe = <T>(value: string, fallback: T): T => {
  try {
    const parsed = JSON.parse(sanitizeJSONString(value)) as T;
    return parsed;
  } catch {
    return fallback;
  }
};

export const extractAnswerText = (payload: unknown): string => {
  const parsedText = parseNestedAnswer(payload);
  if (!parsedText) {
    return '';
  }

  if (parsedText.startsWith('{')) {
    const parsed = parseJSONSafe<Record<string, unknown>>(parsedText, {});
    const withoutMetadata = removeKeyFromJSON(parsed, 'metadata');
    return JSON.stringify(withoutMetadata);
  }

  return parsedText;
};
