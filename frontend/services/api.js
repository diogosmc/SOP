const DEFAULT_BASE = "";
const REQUEST_TIMEOUT_MS = 12000;
const GET_CACHE_TTL_MS = 30000;
const MAX_GET_RETRIES = 1;

/** @type {boolean} */
let authRedirectInProgress = false;

/** @type {Map<string, { expires: number, result: unknown }>} */
const getCache = new Map();

/** @type {Map<string, Promise<unknown>>} */
const inflightRequests = new Map();

function isRetryableStatus(status) {
  return status === 0 || status === 502 || status === 503 || status === 504;
}

function buildErrorMessage(payload, status) {
  if (status === 401) return "Sessão expirada. Faça login novamente.";
  if (status >= 500) return "Erro interno do servidor. Tente novamente.";
  if (status === 0) return "Servidor indisponível ou sem conexão.";
  return (
    payload?.error?.message ||
    payload?.detail ||
    `Erro HTTP ${status}`
  );
}

/**
 * @template T
 * @param {string} path
 * @param {RequestInit & { skipCache?: boolean, retries?: number }} [options]
 * @returns {Promise<{ ok: boolean, data: T|null, error: string|null, status: number }>}
 */
export async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const isGet = method === "GET";
  const cacheable = isGet && !options.skipCache && !options.body;
  const cacheKey = `${method}:${path}`;

  if (cacheable) {
    const cached = getCache.get(cacheKey);
    if (cached && cached.expires > Date.now()) {
      return /** @type {any} */ (cached.result);
    }
    if (inflightRequests.has(cacheKey)) {
      return /** @type {any} */ (await inflightRequests.get(cacheKey));
    }
  }

  const execute = async (attempt = 0) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(`${DEFAULT_BASE}${path}`, {
        credentials: "include",
        headers: {
          Accept: "application/json",
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          ...options.headers,
        },
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeout);

      let payload = null;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        payload = await response.json();
      }

      if (response.status === 401 && !path.includes("/auth/") && !authRedirectInProgress) {
        authRedirectInProgress = true;
        if (window.location.hash !== "#/login") {
          window.location.hash = "#/login";
        }
        authRedirectInProgress = false;
      }

      if (!response.ok) {
        const result = {
          ok: false,
          data: null,
          error: String(buildErrorMessage(payload, response.status)),
          status: response.status,
        };
        const maxRetries = options.retries ?? MAX_GET_RETRIES;
        if (isGet && isRetryableStatus(response.status) && attempt < maxRetries) {
          return execute(attempt + 1);
        }
        return result;
      }

      const data = payload?.data !== undefined ? payload.data : payload;
      return { ok: true, data, error: null, status: response.status };
    } catch (error) {
      clearTimeout(timeout);
      const message =
        error instanceof DOMException && error.name === "AbortError"
          ? "Tempo esgotado ao conectar com a API"
          : error instanceof Error
            ? error.message
            : "Falha de rede";
      const result = { ok: false, data: null, error: message, status: 0 };
      const maxRetries = options.retries ?? MAX_GET_RETRIES;
      if (isGet && attempt < maxRetries) {
        return execute(attempt + 1);
      }
      return result;
    }
  };

  const promise = execute();
  if (cacheable) {
    inflightRequests.set(cacheKey, promise);
  }

  const result = await promise;

  if (cacheable) {
    inflightRequests.delete(cacheKey);
    if (result.ok) {
      getCache.set(cacheKey, { expires: Date.now() + GET_CACHE_TTL_MS, result });
    }
  }

  return result;
}

/** Clear in-memory GET cache (e.g. after mutations). */
export function clearApiCache(prefix = "") {
  if (!prefix) {
    getCache.clear();
    return;
  }
  for (const key of getCache.keys()) {
    if (key.includes(prefix)) getCache.delete(key);
  }
}

export function getHealth() {
  return request("/health");
}

export function getDetailedHealth() {
  return request("/api/v1/health");
}

export function getAiHealth() {
  return request("/api/v1/ai/health");
}

export function getMemoryCount() {
  return request("/api/v1/memory/memories?page=1&page_size=1");
}

export function getPendingReminders() {
  return request("/api/v1/reminders?page=1&page_size=1&status=pending");
}

/** @param {Record<string, unknown>} [params] */
export function listTasks(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return request(`/api/v1/tasks${qs ? `?${qs}` : ""}`);
}

export function getTask(taskId) {
  return request(`/api/v1/tasks/${taskId}`);
}

/** @param {object} payload */
export function createTask(payload) {
  return request("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** @param {string} taskId @param {object} payload */
export function updateTask(taskId, payload) {
  return request(`/api/v1/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTask(taskId) {
  return request(`/api/v1/tasks/${taskId}`, { method: "DELETE" });
}

/** @param {Record<string, unknown>} [params] */
export function listHabits(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.type) query.set("type", String(params.type));
  if (params.active === true || params.active === false) {
    query.set("active", String(params.active));
  }
  const qs = query.toString();
  return request(`/api/v1/habits${qs ? `?${qs}` : ""}`);
}

export function getHabit(habitId) {
  return request(`/api/v1/habits/${habitId}`);
}

/** @param {object} payload */
export function createHabit(payload) {
  return request("/api/v1/habits", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** @param {string} habitId @param {object} payload */
export function updateHabit(habitId, payload) {
  return request(`/api/v1/habits/${habitId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteHabit(habitId) {
  return request(`/api/v1/habits/${habitId}`, { method: "DELETE" });
}

/** @param {Record<string, unknown>} [params] */
export function listNotes(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.tag) query.set("tag", String(params.tag));
  if (params.favorite === true || params.favorite === false) {
    query.set("favorite", String(params.favorite));
  }
  if (params.archived === true || params.archived === false) {
    query.set("archived", String(params.archived));
  }
  const qs = query.toString();
  return request(`/api/v1/notes${qs ? `?${qs}` : ""}`);
}

/** @param {string} q @param {Record<string, unknown>} [params] */
export function searchNotes(q, params = {}) {
  const query = new URLSearchParams({ q });
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  return request(`/api/v1/notes/search?${query.toString()}`);
}

export function getNote(noteId) {
  return request(`/api/v1/notes/${noteId}`);
}

/** @param {object} payload */
export function createNote(payload) {
  return request("/api/v1/notes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** @param {string} noteId @param {object} payload */
export function updateNote(noteId, payload) {
  return request(`/api/v1/notes/${noteId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteNote(noteId) {
  return request(`/api/v1/notes/${noteId}`, { method: "DELETE" });
}

export function indexNote(noteId) {
  return request(`/api/v1/notes/${noteId}/index`, { method: "POST" });
}

/** @param {string} query @param {number} [limit] */
export function searchSemanticNotes(query, limit = 5) {
  return request("/api/v1/notes/search-semantic", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
}

function financeQueryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

/** @param {Record<string, unknown>} [params] */
export function listFinanceTransactions(params = {}) {
  return request(`/api/v1/finance/transactions${financeQueryString(params)}`);
}

/** @param {Record<string, unknown>} [params] */
export function getFinanceSummary(params = {}) {
  return request(`/api/v1/finance/summary${financeQueryString(params)}`);
}

/** @param {Record<string, unknown>} [params] */
export function getFinanceByCategory(params = {}) {
  return request(`/api/v1/finance/by-category${financeQueryString(params)}`);
}

/** @param {Record<string, unknown>} [params] */
export function getFinanceByDay(params = {}) {
  return request(`/api/v1/finance/by-day${financeQueryString(params)}`);
}

/** @param {object} payload */
export function createFinanceTransaction(payload) {
  return request("/api/v1/finance/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** @param {string} id @param {object} payload */
export function updateFinanceTransaction(id, payload) {
  return request(`/api/v1/finance/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteFinanceTransaction(id) {
  return request(`/api/v1/finance/transactions/${id}`, { method: "DELETE" });
}

function studyQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

export function getStudySummary() {
  return request("/api/v1/study/summary");
}

export function listStudySubjects(params = {}) {
  return request(`/api/v1/study/subjects${studyQuery(params)}`);
}

export function createStudySubject(payload) {
  return request("/api/v1/study/subjects", { method: "POST", body: JSON.stringify(payload) });
}

export function updateStudySubject(id, payload) {
  return request(`/api/v1/study/subjects/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteStudySubject(id) {
  return request(`/api/v1/study/subjects/${id}`, { method: "DELETE" });
}

export function listStudyTopics(params = {}) {
  return request(`/api/v1/study/topics${studyQuery(params)}`);
}

export function createStudyTopic(payload) {
  return request("/api/v1/study/topics", { method: "POST", body: JSON.stringify(payload) });
}

export function updateStudyTopic(id, payload) {
  return request(`/api/v1/study/topics/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteStudyTopic(id) {
  return request(`/api/v1/study/topics/${id}`, { method: "DELETE" });
}

export function generateTopicAIPlan(topicId) {
  return request(`/api/v1/study/topics/${topicId}/ai-plan`, { method: "POST" });
}

export function listFlashcards(params = {}) {
  return request(`/api/v1/study/flashcards${studyQuery(params)}`);
}

export function createFlashcard(payload) {
  return request("/api/v1/study/flashcards", { method: "POST", body: JSON.stringify(payload) });
}

export function reviewFlashcard(id, rating) {
  return request(`/api/v1/study/flashcards/${id}/review`, {
    method: "PATCH",
    body: JSON.stringify({ rating }),
  });
}

export function deleteFlashcard(id) {
  return request(`/api/v1/study/flashcards/${id}`, { method: "DELETE" });
}

export function createStudySession(payload) {
  return request("/api/v1/study/sessions", { method: "POST", body: JSON.stringify(payload) });
}

export function getWorkoutProfile() {
  return request("/api/v1/workout/profile");
}

export function upsertWorkoutProfile(payload) {
  return request("/api/v1/workout/profile", { method: "PUT", body: JSON.stringify(payload) });
}

/** @param {Record<string, unknown>} [params] */
export function listWorkoutExercises(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return request(`/api/v1/workout/exercises${qs ? `?${qs}` : ""}`);
}

export function createWorkoutExercise(payload) {
  return request("/api/v1/workout/exercises", { method: "POST", body: JSON.stringify(payload) });
}

export function updateWorkoutExercise(id, payload) {
  return request(`/api/v1/workout/exercises/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteWorkoutExercise(id) {
  return request(`/api/v1/workout/exercises/${id}`, { method: "DELETE" });
}

/** @param {Record<string, unknown>} [params] */
export function listWorkoutPlans(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return request(`/api/v1/workout/plans${qs ? `?${qs}` : ""}`);
}

export function getWorkoutPlan(id) {
  return request(`/api/v1/workout/plans/${id}`);
}

export function createWorkoutPlan(payload) {
  return request("/api/v1/workout/plans", { method: "POST", body: JSON.stringify(payload) });
}

export function updateWorkoutPlan(id, payload) {
  return request(`/api/v1/workout/plans/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteWorkoutPlan(id) {
  return request(`/api/v1/workout/plans/${id}`, { method: "DELETE" });
}

export function addWorkoutPlanExercise(planId, payload) {
  return request(`/api/v1/workout/plans/${planId}/exercises`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteWorkoutPlanExercise(planId, planExerciseId) {
  return request(`/api/v1/workout/plans/${planId}/exercises/${planExerciseId}`, { method: "DELETE" });
}

/** @param {Record<string, unknown>} [params] */
export function listWorkoutLogs(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return request(`/api/v1/workout/logs${qs ? `?${qs}` : ""}`);
}

export function getWorkoutLog(id) {
  return request(`/api/v1/workout/logs/${id}`);
}

export function createWorkoutLog(payload) {
  return request("/api/v1/workout/logs", { method: "POST", body: JSON.stringify(payload) });
}

export function updateWorkoutLog(id, payload) {
  return request(`/api/v1/workout/logs/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteWorkoutLog(id) {
  return request(`/api/v1/workout/logs/${id}`, { method: "DELETE" });
}

export function addWorkoutSetLog(logId, payload) {
  return request(`/api/v1/workout/logs/${logId}/sets`, { method: "POST", body: JSON.stringify(payload) });
}

export function getWorkoutSummary() {
  return request("/api/v1/workout/summary");
}

/** @param {Record<string, unknown>} [params] */
export function getWorkoutProgression(params = {}) {
  const query = new URLSearchParams();
  if (params.exercise_id) query.set("exercise_id", String(params.exercise_id));
  const qs = query.toString();
  return request(`/api/v1/workout/progression${qs ? `?${qs}` : ""}`);
}

/** @param {Record<string, unknown>} [params] */
export function getReportDaily(params = {}) {
  const query = new URLSearchParams();
  if (params.date) query.set("date", String(params.date));
  const qs = query.toString();
  return request(`/api/v1/reports/daily${qs ? `?${qs}` : ""}`);
}

/** @param {Record<string, unknown>} [params] */
export function getReportWeekly(params = {}) {
  const query = new URLSearchParams();
  if (params.date) query.set("date", String(params.date));
  const qs = query.toString();
  return request(`/api/v1/reports/weekly${qs ? `?${qs}` : ""}`);
}

/** @param {Record<string, unknown>} [params] */
export function getReportAnalytics(params = {}) {
  const query = new URLSearchParams();
  if (params.start_date) query.set("start_date", String(params.start_date));
  if (params.end_date) query.set("end_date", String(params.end_date));
  const qs = query.toString();
  return request(`/api/v1/reports/analytics${qs ? `?${qs}` : ""}`);
}

/** @param {Record<string, unknown>} [params] */
export function getReportInsights(params = {}) {
  const query = new URLSearchParams();
  if (params.use_ai) query.set("use_ai", "true");
  const qs = query.toString();
  return request(`/api/v1/reports/insights${qs ? `?${qs}` : ""}`);
}

export function rebuildReportDaily() {
  return request("/api/v1/reports/rebuild-daily", { method: "POST" });
}

export function getAuthBootstrapAvailable() {
  return request("/api/v1/auth/bootstrap-available");
}

export function login(payload) {
  return request("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function logout() {
  return request("/api/v1/auth/logout", { method: "POST" });
}

export function refreshAuth() {
  return request("/api/v1/auth/refresh", { method: "POST" });
}

export function getAuthMe() {
  return request("/api/v1/auth/me");
}

export function bootstrapAdmin(payload) {
  return request("/api/v1/auth/bootstrap-admin", { method: "POST", body: JSON.stringify(payload) });
}
