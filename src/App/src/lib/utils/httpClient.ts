import { normalizeApiError } from '@/lib/utils/apiUtils';
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

let cachedEasyAuthHeaders: Record<string, string> | null = null;

const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).__RUNTIME_CONFIG__?.VITE_API_BASE_URL) {
    return (window as any).__RUNTIME_CONFIG__.VITE_API_BASE_URL;
  }

  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

const serializeParams = (params?: Record<string, unknown>): string => {
  if (!params) {
    return '';
  }

  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => searchParams.append(key, String(item)));
      return;
    }

    searchParams.append(key, String(value));
  });

  return searchParams.toString();
};

class HttpClient {
  private static singleton: HttpClient;

  private readonly client: AxiosInstance;

  private constructor() {
    this.client = axios.create({
      baseURL: getApiBaseUrl(),
      timeout: 60_000,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
      paramsSerializer: {
        serialize: serializeParams,
      },
    });

    this.client.interceptors.request.use((config) => {
      if (config.headers && cachedEasyAuthHeaders) {
        Object.entries(cachedEasyAuthHeaders).forEach(([key, value]) => {
          config.headers[key] = value;
        });
      }

      if (config.headers && typeof window !== 'undefined') {
        const userId = localStorage.getItem('userId');
        if (userId && !config.headers['x-ms-client-principal-id']) {
          config.headers['x-ms-client-principal-id'] = userId;
        }
      }

      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(normalizeApiError(error, 'Request failed')),
    );
  }

  static getInstance(): HttpClient {
    if (!HttpClient.singleton) {
      HttpClient.singleton = new HttpClient();
    }

    return HttpClient.singleton;
  }

  get instance(): AxiosInstance {
    return this.client;
  }

  async request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client.request<T>(config);
    return response.data;
  }

  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }
}

export const setEasyAuthHeaders = (headers: Record<string, string> | null) => {
  cachedEasyAuthHeaders = headers;
};

export const httpClient = HttpClient.getInstance();
export const api: AxiosInstance = httpClient.instance;

export type HttpResponse<T> = AxiosResponse<T>;
