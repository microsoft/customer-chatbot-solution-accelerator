import axios from 'axios';

export interface ApiErrorResponse {
  ok: false;
  status: number;
  message: string;
  details?: unknown;
}

export const createErrorResponse = (
  status: number,
  message: string,
  details?: unknown,
): ApiErrorResponse => ({
  ok: false,
  status,
  message,
  details,
});

export const normalizeApiError = (error: unknown, fallbackMessage: string): ApiErrorResponse => {
  if (axios.isAxiosError(error)) {
    return createErrorResponse(
      error.response?.status ?? 500,
      error.response?.data?.detail ?? error.message ?? fallbackMessage,
      error.response?.data,
    );
  }

  if (error instanceof Error) {
    return createErrorResponse(500, error.message || fallbackMessage);
  }

  return createErrorResponse(500, fallbackMessage, error);
};

export const retryRequest = async <T>(
  request: () => Promise<T>,
  retries = 2,
  baseDelayMs = 300,
): Promise<T> => {
  let attempt = 0;
  for (;;) {
    try {
      return await request();
    } catch (error) {
      if (attempt >= retries) {
        throw error;
      }
      const delay = baseDelayMs * Math.pow(2, attempt);
      await new Promise((resolve) => setTimeout(resolve, delay));
      attempt += 1;
    }
  }
};

export class RequestCache {
  private readonly inFlight = new Map<string, Promise<unknown>>();

  getOrCreate<T>(key: string, factory: () => Promise<T>): Promise<T> {
    const existing = this.inFlight.get(key) as Promise<T> | undefined;
    if (existing) {
      return existing;
    }

    const request = factory().finally(() => {
      this.inFlight.delete(key);
    });

    this.inFlight.set(key, request);
    return request;
  }
}
