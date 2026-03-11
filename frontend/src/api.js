const API_URL = '';

export async function apiFetch(path, options = {}) {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    credentials: 'omit',
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...options.headers,
    },
  });
  return res;
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  const ct = res.headers.get('content-type');
  if (!res.ok) {
    const err = ct?.includes('application/json')
      ? (await res.json()).detail
      : (await res.text()).substring(0, 200);
    throw new Error(err || `Server error ${res.status}`);
  }
  return res.json();
}

export function getApiUrl() {
  return API_URL;
}

export async function downloadFile(url, filename) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Server error ${res.status}`);
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}
