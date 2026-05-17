const $ = (id) => document.getElementById(id);

const TOKEN_KEY = "jobai_token";

function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }

function showLoginOverlay() {
  const overlay = $("loginOverlay");
  if (overlay) overlay.classList.remove("hidden");
}

function hideLoginOverlay() {
  const overlay = $("loginOverlay");
  if (overlay) overlay.classList.add("hidden");
}

async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    showLoginOverlay();
  }
  return res;
}

async function initAuth() {
  if (!getToken()) {
    showLoginOverlay();
    return;
  }
  // Token varsa gizle
  hideLoginOverlay();
}

function applyAvatar(dataUrl) {
  const img = $("avatarImg");
  const placeholder = $("avatarPlaceholder");
  if (!img || !placeholder) return;
  if (dataUrl) {
    img.src = dataUrl;
    img.classList.remove("hidden");
    placeholder.classList.add("hidden");
  } else {
    img.classList.add("hidden");
    placeholder.classList.remove("hidden");
  }
}

async function loadAvatar() {
  try {
    const res = await authFetch("/profile/avatar");
    if (res.ok) {
      const data = await res.json();
      applyAvatar(data.avatar_data || null);
    }
  } catch {
    // sessizce geç
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  loadAvatar();

  const avatarBtn = $("avatarBtn");
  const avatarInput = $("avatarInput");
  if (avatarBtn && avatarInput) {
    avatarBtn.addEventListener("click", () => avatarInput.click());
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (e) => {
        const dataUrl = e.target.result;
        applyAvatar(dataUrl);
        try {
          await authFetch("/profile/avatar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ avatar_data: dataUrl }),
          });
        } catch {
          // sessizce geç
        }
      };
      reader.readAsDataURL(file);
      avatarInput.value = "";
    });
  }

  // CV modal
  const cvSettingsBtn = $("cvSettingsBtn");
  const cvModal = $("cvModal");
  const cvModalClose = $("cvModalClose");
  const cvUploadBtn = $("cvUploadBtn");
  const cvUploadMsg = $("cvUploadMsg");

  async function loadCvList() {
    const listEl = $("cvList");
    try {
      const res = await authFetch("/profile/cvs");
      const cvs = await res.json();
      if (!cvs.length) { listEl.textContent = "Henüz CV yüklenmedi."; return; }
      listEl.innerHTML = cvs.map(cv =>
        `<div class="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
          <span>${cv.title} <span class="text-xs text-slate-400">(${cv.role_type})</span></span>
          ${cv.is_active ? '<span class="text-xs text-green-600 font-medium">Aktif</span>' : ''}
        </div>`
      ).join("");
    } catch { listEl.textContent = "CV listesi alınamadı."; }
  }

  if (cvSettingsBtn && cvModal) {
    cvSettingsBtn.addEventListener("click", () => {
      cvModal.classList.remove("hidden");
      cvModal.classList.add("flex");
      loadCvList();
    });
    cvModalClose?.addEventListener("click", () => {
      cvModal.classList.add("hidden");
      cvModal.classList.remove("flex");
    });
    cvModal.addEventListener("click", (e) => {
      if (e.target === cvModal) { cvModal.classList.add("hidden"); cvModal.classList.remove("flex"); }
    });
  }

  if (cvUploadBtn) {
    cvUploadBtn.addEventListener("click", async () => {
      const roleType = $("cvRoleType")?.value;
      const title = $("cvTitle")?.value?.trim();
      const file = $("cvFileInput")?.files?.[0];
      if (!file || !title) { showCvMsg("Başlık ve PDF dosyası gerekli.", "red"); return; }

      cvUploadBtn.disabled = true;
      cvUploadBtn.textContent = "Yükleniyor...";
      const form = new FormData();
      form.append("role_type", roleType);
      form.append("title", title);
      form.append("file", file);
      try {
        const res = await authFetch("/profile/cvs", { method: "POST", body: form });
        const data = await res.json();
        if (!res.ok) { showCvMsg(data.detail || "Hata.", "red"); return; }
        showCvMsg(`Yüklendi (${data.chars} karakter)`, "green");
        loadCvList();
      } catch { showCvMsg("Yükleme başarısız.", "red"); }
      finally { cvUploadBtn.disabled = false; cvUploadBtn.textContent = "Yükle"; }
    });
  }

  function showCvMsg(msg, color) {
    const el = cvUploadMsg;
    if (!el) return;
    el.textContent = msg;
    el.className = `text-xs text-center ${color === "green" ? "text-green-600" : "text-red-600"}`;
    el.classList.remove("hidden");
    setTimeout(() => el.classList.add("hidden"), 4000);
  }

  const loginBtn = $("loginBtn");
  const loginPassword = $("loginPassword");
  const loginError = $("loginError");

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {
      const password = loginPassword?.value || "";
      if (!password) return;

      loginBtn.disabled = true;
      loginBtn.textContent = "...";
      if (loginError) loginError.classList.add("hidden");

      try {
        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password }),
        });

        if (!res.ok) {
          if (loginError) loginError.classList.remove("hidden");
          return;
        }

        const data = await res.json();
        setToken(data.token);
        hideLoginOverlay();
      } catch {
        if (loginError) loginError.classList.remove("hidden");
      } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "Giriş Yap";
      }
    });
  }

  if (loginPassword) {
    loginPassword.addEventListener("keydown", (e) => {
      if (e.key === "Enter") loginBtn?.click();
    });
  }
});

let applicationId = null;
let currentCompanyId = null;
let canSendApplication = false;
let refineSupported = false;
let companies = [];
let companiesLoaded = false;
let companiesLoading = false;

const STORAGE_KEY = "jobai_applications";

const cvProfiles = {
  ai_engineer: {
    label: "AI Engineer CV",
    desc: "Genel AI rollerine uygun varsayılan CV.",
    suggestedRole: "AI Engineer",
  },
  backend_ai_engineer: {
    label: "Backend AI Engineer CV",
    desc: "Backend + model servisleme odaklı CV.",
    suggestedRole: "Backend AI Engineer",
  },
};

function getApplicationMode() {
  const checked = document.querySelector('input[name="applicationMode"]:checked');
  return checked ? checked.value : "url";
}

function readUserInstruction() {
  return ($("userInstruction")?.value || "").trim();
}

function updateMailModePlaceholders(mode) {
  const roleInput = $("targetRole");
  if (!roleInput) return;

  roleInput.placeholder =
    mode === "mail"
      ? "Örn: Backend AI Engineer (isteğe bağlı)"
      : "Örn: Backend AI Engineer";
}

function activeCvKey() {
  return $("cvSelector")?.value || "ai_engineer";
}

function suggestCvFromText(role, jobDescription) {
  const text = `${role || ""} ${jobDescription || ""}`.toLowerCase();

  if (
    text.includes("backend") ||
    text.includes("api") ||
    text.includes("fastapi") ||
    text.includes("django") ||
    text.includes("backend engineer")
  ) {
    return "backend_ai_engineer";
  }

  if (
    text.includes("ai") ||
    text.includes("llm") ||
    text.includes("machine learning") ||
    text.includes("researcher") ||
    text.includes("engineer")
  ) {
    return "ai_engineer";
  }

  return activeCvKey();
}

function hide(el) {
  if (!el) return;
  el.classList.add("hidden");
  el.classList.remove("flex");
}

function show(el) {
  if (!el) return;
  el.classList.remove("hidden");
}

function showFlex(el) {
  if (!el) return;
  el.classList.remove("hidden");
  el.classList.add("flex");
}

function setError(msg) {
  $("errorText").textContent = msg;
  showFlex($("errorBanner"));
}

function clearError() {
  hide($("errorBanner"));
}

function setSuccess(visible) {
  if (visible) {
    showFlex($("successBanner"));
  } else {
    hide($("successBanner"));
  }
}

function setSuccessText(message) {
  $("successText").textContent = message;
}

function setLoading(loading) {
  const sk = $("emailSkeleton");
  if (loading) show(sk);
  else hide(sk);
}

function setGenerateLoading(loading) {
  const spin = $("btnGenerateSpinner");
  const label = $("btnGenerateLabel");
  const btn = $("btnGenerate");
  if (spin) spin.classList.toggle("hidden", !loading);
  if (label) label.classList.toggle("opacity-60", loading);
  if (btn) btn.disabled = loading;
}

function setSendButtonSpinner(loading) {
  const spin = $("btnSendSpinner");
  const label = $("btnSendLabel");
  if (spin) spin.classList.toggle("hidden", !loading);
  if (label) label.classList.toggle("opacity-60", loading);
}

function updatePreview(subject, body) {
  const subEl = $("emailSubject");
  const bodyEl = $("emailBody");
  if (subEl) subEl.value = subject ?? "";
  if (bodyEl) bodyEl.value = body ?? "";
}

function resetContactEmail() {
  if ($("contactEmailInput")) {
    $("contactEmailInput").value = "";
  }
}

function setContactEmail(email) {
  const normalized = (email || "").trim();
  if ($("contactEmailInput")) {
    $("contactEmailInput").value = normalized;
  }
}

function setSendState(enabled) {
  canSendApplication = enabled;
  const btn = $("btnSend");
  if (btn) btn.disabled = !enabled;
}

function updateCompanyContactActions() {
  const row = $("companyContactActions");
  if (!row) return;
  row.classList.toggle("hidden", !currentCompanyId);
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showContactEmailEditor() {}

function setChatCompanyInfo() {
  const info = $("chatCompanyInfo");
  if (!info) return;

  if (!currentCompanyId) {
    info.textContent = "Henüz şirket seçilmedi.";
    return;
  }

  const selected = companies.find((c) => c.id === currentCompanyId);
  info.textContent = `Seçili şirket: ${
    selected?.name || selected?.website || currentCompanyId
  }`;
}

function appendChatMessage(role, text) {
  const container = $("companyChatMessages");
  if (!container) return;

  if (
    container.children.length === 1 &&
    container.firstElementChild?.classList.contains("text-slate-500")
  ) {
    container.innerHTML = "";
  }

  const item = document.createElement("div");
  item.className = role === "user"
    ? "ml-auto max-w-[90%] rounded-lg px-md py-sm bg-primary text-on-primary text-body-sm whitespace-pre-wrap"
    : "mr-auto max-w-[90%] rounded-lg px-md py-sm bg-white border border-outline-variant text-body-sm text-on-surface whitespace-pre-wrap";
  item.textContent = text;
  container.appendChild(item);
  container.scrollTop = container.scrollHeight;
}

function clearCompanyChat() {
  const container = $("companyChatMessages");
  if (!container) return;
  container.innerHTML = `
    <div class="text-body-sm text-slate-500">
      Şirket seçip soru yazdığınızda sohbet burada görünür.
    </div>
  `;
}

async function askCompanyQuestion() {
  clearError();

  if (!currentCompanyId) {
    setError("Lütfen önce bir şirket seçin veya URL ile e-posta oluşturun.");
    return;
  }

  const question = ($("companyQuestion")?.value || "").trim();
  if (!question) {
    setError("Lütfen şirkete sorulacak bir soru yazın.");
    return;
  }

  const btn = $("btnAskCompany");
  const questionInput = $("companyQuestion");

  if (btn) btn.disabled = true;
  appendChatMessage("user", question);
  appendChatMessage("assistant", "Yanıt hazırlanıyor...");
  if (questionInput) questionInput.value = "";

  try {
    const res = await authFetch(`/companies/${currentCompanyId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();
    const container = $("companyChatMessages");
    if (container?.lastElementChild) {
      container.lastElementChild.textContent =
        data.answer || "Bu şirket hakkında yeterli bilgi bulunamadı.";
    }
  } catch (e) {
    const container = $("companyChatMessages");
    if (container?.lastElementChild) {
      container.lastElementChild.textContent = "Yanıt alınamadı.";
    }
    setError(e.message || "Şirket sorusu cevaplanamadı.");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function saveContactEmail() {
  clearError();

  if (!currentCompanyId) {
    setError("Önce şirket seçin veya e-posta oluşturun.");
    return;
  }

  const input = $("contactEmailInput");
  const value = (input?.value || "").trim();

  if (!isValidEmail(value)) {
    setError("Geçerli bir e-posta girin.");
    return;
  }

  const btn = $("btnSaveContactEmail");
  if (btn) btn.disabled = true;

  try {
    const res = await authFetch(`/companies/${currentCompanyId}/contact-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contact_email: value }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();
    setContactEmail(data.contact_email || value);
    refreshSendAvailability();
    setSuccessText("İletişim e-postası güncellendi.");
    setSuccess(true);
  } catch (e) {
    setError(e.message || "İletişim e-postası güncellenemedi.");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function setupContactEmailEditor() {
  if ($("btnSaveContactEmail")) {
    $("btnSaveContactEmail").addEventListener("click", async () => {
      await saveContactEmail();
    });
  }
}

function setupCompanyChat() {
  if ($("btnAskCompany")) {
    $("btnAskCompany").addEventListener("click", async () => {
      await askCompanyQuestion();
    });
  }

  if ($("btnClearCompanyChat")) {
    $("btnClearCompanyChat").addEventListener("click", async () => {
      clearError();

      if (!currentCompanyId) {
        clearCompanyChat();
        return;
      }

      const clearBtn = $("btnClearCompanyChat");
      if (clearBtn) clearBtn.disabled = true;

      try {
        const res = await authFetch(`/companies/${currentCompanyId}/chat`, {
          method: "DELETE",
        });

        if (!res.ok) {
          throw new Error(await parseErrorDetail(res));
        }

        clearCompanyChat();
        setSuccessText("Şirket sohbet geçmişi temizlendi.");
        setSuccess(true);
      } catch (e) {
        setError(e.message || "Sohbet geçmişi temizlenemedi.");
      } finally {
        if (clearBtn) clearBtn.disabled = false;
      }
    });
  }

  if ($("companyQuestion")) {
    $("companyQuestion").addEventListener("keydown", async (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        await askCompanyQuestion();
      }
    });
  }
}

async function parseErrorDetail(res) {
  try {
    const data = await res.json();

    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;

      if (Array.isArray(data.detail)) {
        return data.detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
      }
    }
  } catch {}

  return res.statusText || `HTTP ${res.status}`;
}

async function fetchCompanies() {
  const res = await authFetch("/companies/");

  if (!res.ok) {
    throw new Error("Şirketler alınamadı.");
  }

  const data = await res.json();
  const raw = Array.isArray(data) ? data : [];
  const seen = new Set();

  return raw.filter((company) => {
    const id = String(company.id || "");
    if (!id || seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}

function filterCompaniesBySearch(term) {
  const q = (term || "").toLocaleLowerCase("tr-TR").trim();
  if (!q) return companies;

  return companies.filter((company) => {
    const name = (company.name || "").toLocaleLowerCase("tr-TR");
    const website = (company.website || "").toLocaleLowerCase("tr-TR");
    const email = (company.contact_email || "").toLocaleLowerCase("tr-TR");
    return name.includes(q) || website.includes(q) || email.includes(q);
  });
}

function renderCompanyList(list) {
  const companyList = $("companyList");
  if (!companyList) return;

  companyList.innerHTML = "";

  if (!list.length) {
    const searchTerm = ($("companySearch")?.value || "").trim();
    const message = searchTerm
      ? "Aramanızla eşleşen şirket bulunamadı."
      : companies.length
        ? "Gösterilecek şirket yok."
        : "Henüz kayıtlı şirket yok.";

    companyList.innerHTML = `
      <div class="p-md text-body-sm text-slate-500">
        ${message}
      </div>
    `;
    return;
  }

  const selectedId = String($("selectedCompanyId")?.value || "");

  list.forEach((company) => {
    const item = document.createElement("button");
    item.type = "button";
    const isSelected = String(company.id) === selectedId;
    item.className = [
      "w-full text-left p-md transition-all border-b border-outline-variant last:border-b-0",
      isSelected
        ? "bg-surface-container ring-2 ring-inset ring-primary"
        : "hover:bg-surface-container-low",
    ].join(" ");

    item.innerHTML = `
      <p class="font-semibold text-on-surface">
        ${company.name || "İsimsiz şirket"}
      </p>
      <p class="text-body-sm text-slate-500 truncate">
        ${company.website || "Web sitesi yok"}
      </p>
      <p class="text-body-sm text-slate-500 truncate">
        ${company.contact_email || "E-posta bulunamadı"}
      </p>
    `;

    item.addEventListener("click", () => {
      $("selectedCompanyId").value = company.id;
      currentCompanyId = company.id;
      $("selectedCompanyText").textContent = `Seçili şirket: ${
        company.name || company.website || company.id
      }`;
      setContactEmail(company.contact_email);
      setChatCompanyInfo();
      clearCompanyChat();
      updateCompanyContactActions();
      renderCompanyList(filterCompaniesBySearch($("companySearch")?.value || ""));
    });

    companyList.appendChild(item);
  });
}

function showCompanyListLoading() {
  const companyList = $("companyList");
  if (!companyList) return;

  companyList.innerHTML = `
    <div class="p-md text-body-sm text-slate-500">
      Şirketler yükleniyor...
    </div>
  `;
}

async function loadCompanies({ force = false } = {}) {
  const companyList = $("companyList");
  if (!companyList) return;

  if (companiesLoading) return;

  if (companiesLoaded && !force) {
    renderCompanyList(filterCompaniesBySearch($("companySearch")?.value || ""));
    return;
  }

  companiesLoading = true;
  showCompanyListLoading();

  try {
    companies = await fetchCompanies();
    companiesLoaded = true;
    renderCompanyList(filterCompaniesBySearch($("companySearch")?.value || ""));
  } catch {
    companiesLoaded = false;
    companyList.innerHTML = `
      <div class="p-md text-body-sm text-red-600">
        Şirketler yüklenirken hata oluştu. Backend çalışıyor mu?
      </div>
    `;
  } finally {
    companiesLoading = false;
  }
}

function setupApplicationMode() {
  const modeInputs = document.querySelectorAll('input[name="applicationMode"]');

  const applyModeVisibility = async (mode) => {
    const urlWrap = $("urlInputWrapper");
    const companyWrap = $("companySelectWrapper");
    const mailWrap = $("mailInputWrapper");
    const langWrap = $("languageWrapper");

    if (mode === "url") {
      show(urlWrap);
      hide(companyWrap);
      hide(mailWrap);
      show(langWrap);
      if ($("selectedCompanyId")) $("selectedCompanyId").value = "";
      currentCompanyId = null;
      if ($("selectedCompanyText")) {
        $("selectedCompanyText").textContent = "Henüz şirket seçilmedi.";
      }
      resetContactEmail();
      setChatCompanyInfo();
      clearCompanyChat();
      updateCompanyContactActions();
    } else if (mode === "company") {
      hide(urlWrap);
      show(companyWrap);
      hide(mailWrap);
      show(langWrap);
      if ($("companySearch")) $("companySearch").value = "";
      await loadCompanies();
      setChatCompanyInfo();
    } else {
      hide(urlWrap);
      hide(companyWrap);
      show(mailWrap);
      show(langWrap);
      if ($("selectedCompanyId")) $("selectedCompanyId").value = "";
      currentCompanyId = null;
      if ($("selectedCompanyText")) {
        $("selectedCompanyText").textContent = "Henüz şirket seçilmedi.";
      }
      setChatCompanyInfo();
      clearCompanyChat();
      updateCompanyContactActions();
    }

    updateMailModePlaceholders(mode);
  };

  modeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      applyModeVisibility(getApplicationMode());
    });
  });

  if ($("companySearch")) {
    $("companySearch").addEventListener("input", () => {
      if (!companiesLoaded && !companiesLoading) {
        loadCompanies();
        return;
      }
      renderCompanyList(filterCompaniesBySearch($("companySearch").value));
    });
  }

  applyModeVisibility(getApplicationMode());
}

function readApplications() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveApplications(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function upsertApplicationRecord(patch) {
  if (!patch?.id) return;

  const items = readApplications();
  const idx = items.findIndex((item) => item.id === patch.id);
  const now = new Date().toISOString();

  if (idx === -1) {
    items.unshift({
      id: patch.id,
      companyUrl: patch.companyUrl || "",
      companyName: patch.companyName || "",
      role: patch.role || "",
      language: patch.language || "tr",
      cvKey: patch.cvKey || "ai_engineer",
      cvLabel: (cvProfiles[patch.cvKey] || cvProfiles.ai_engineer).label,
      contactEmail: patch.contactEmail || "",
      subject: patch.subject || "",
      body: patch.body || "",
      status: patch.status || "draft",
      instruction: patch.instruction || "",
      createdAt: patch.createdAt || now,
      updatedAt: now,
    });
  } else {
    items[idx] = {
      ...items[idx],
      ...patch,
      cvLabel: (cvProfiles[patch.cvKey || items[idx].cvKey] || cvProfiles.ai_engineer).label,
      updatedAt: now,
    };
  }

  saveApplications(items);
  renderApplicationsList();
}

function formatDate(iso) {
  if (!iso) return "-";

  const d = new Date(iso);

  if (Number.isNaN(d.getTime())) return "-";

  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(d);
}

function renderStats(items) {
  if (!$("statTotal") || !$("statDraft") || !$("statSent")) return;

  $("statTotal").textContent = String(items.length);
  $("statDraft").textContent = String(items.filter((x) => x.status !== "sent").length);
  $("statSent").textContent = String(items.filter((x) => x.status === "sent").length);
}

function mapCompanyToRecord(c) {
  const companyName = c.name || "Şirket";

  return {
    id: c.id,
    role: "Pozisyon belirtilmedi",
    companyUrl: c.website || c.source_url || "-",
    companyName,
    subject: `${companyName} için kayıtlı şirket`,
    body: c.ai_summary || c.description || "",
    cvLabel: "-",
    contactEmail: c.contact_email || "Bilinmiyor",
    status: "draft",
    updatedAt: c.updated_at || c.created_at || new Date().toISOString(),
  };
}

function cardHtml(item) {
  const badge =
    item.status === "sent"
      ? '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 border border-green-200">Gönderildi</span>'
      : '<span class="px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-700 border border-amber-200">Taslak</span>';

  const detailId = `detail-${item.id}`;

  const detailBody = item.body
    ? item.body
    : "Bu kayıtta e-posta gövdesi bulunmuyor.";

  return `
    <article class="bg-white border border-outline-variant rounded-lg p-md">
      <div class="flex items-start justify-between gap-sm">
        <div class="min-w-0">
          <div class="flex items-center gap-xs mb-xs">
            ${badge}
            <span class="text-label-sm text-slate-500">ID: ${item.id}</span>
          </div>
          <p class="text-body-md font-semibold text-on-surface truncate">${item.subject || "-"}</p>
          <p class="text-body-sm text-on-surface-variant truncate">Şirket: ${item.companyName || item.companyUrl || "-"}</p>
          <p class="text-body-sm text-on-surface-variant truncate">Pozisyon: ${item.role || "-"}</p>
        </div>
        <div class="text-right text-body-sm text-on-surface-variant">
          <p>CV: ${item.cvLabel || "-"}</p>
          <p>İletişim: ${item.contactEmail || "Bilinmiyor"}</p>
          <p>${formatDate(item.updatedAt)}</p>
          <button
            type="button"
            data-detail-target="${detailId}"
            class="mt-xs px-sm py-xs text-label-sm rounded-md border border-outline-variant hover:bg-surface-container transition-all"
          >
            İçeriğe Gir
          </button>
        </div>
      </div>

      <div id="${detailId}" class="hidden mt-sm pt-sm border-t border-outline-variant">
        <p class="text-label-sm text-slate-500 mb-xs">E-posta İçeriği</p>
        <div class="text-body-sm text-on-surface whitespace-pre-wrap leading-relaxed bg-surface-container-low p-sm rounded-md border border-outline-variant">
${detailBody}
        </div>
      </div>
    </article>
  `;
}

async function renderApplicationsList() {
  const listEl = $("applicationsList");
  const emptyEl = $("applicationsEmpty");

  if (!listEl || !emptyEl) return;

  const local = readApplications();
  let combined = [...local];

  try {
    const companiesData = await fetchCompanies();
    const map = new Map();

    [...local, ...companiesData.map(mapCompanyToRecord)].forEach((item) => {
      if (!map.has(item.id)) map.set(item.id, item);
    });

    combined = Array.from(map.values());
  } catch {}

  combined.sort((a, b) => {
    return new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime();
  });

  renderStats(combined);

  if (!combined.length) {
    listEl.innerHTML = "";
    emptyEl.classList.remove("hidden");
    return;
  }

  emptyEl.classList.add("hidden");
  listEl.innerHTML = combined.map(cardHtml).join("");

  listEl.querySelectorAll("[data-detail-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-detail-target");
      const panel = document.getElementById(targetId);

      if (!panel) return;

      panel.classList.toggle("hidden");
      btn.textContent = panel.classList.contains("hidden")
        ? "İçeriğe Gir"
        : "İçeriği Gizle";
    });
  });
}

function refreshSendAvailability() {
  if (!applicationId || !refineSupported) {
    setSendState(false);
    return;
  }
  const to = ($("contactEmailInput")?.value || "").trim();
  setSendState(Boolean(to) && isValidEmail(to));
}

function syncCvCard(cvKey) {
  const profile = cvProfiles[cvKey] || cvProfiles.ai_engineer;

  $("cvSelector").value = cvKey;
  $("selectedCvName").textContent = profile.label;
  $("selectedCvDesc").textContent = profile.desc;
}

$("btnGenerate").addEventListener("click", async () => {
  clearError();
  setSuccess(false);
  resetContactEmail();
  setSendState(false);
  refineSupported = false;
  currentCompanyId = null;
  applicationId = null;
  updateCompanyContactActions();

  const mode = getApplicationMode();
  const url = $("companyUrl").value.trim();
  const companyId = ($("selectedCompanyId")?.value || "").trim();
  const role = $("targetRole").value.trim();
  const language = $("language").value;
  const companyName = ($("companyName")?.value || "").trim();
  const recipientEmail = ($("recipientEmail")?.value || "").trim();
  const jobDescription = ($("jobDescription")?.value || "").trim();
  const userInstruction = readUserInstruction();

  let payload = {};
  let companyDisplay = "";
  let endpoint = "/applications/prepare";

  if (mode !== "mail" && !role) {
    setError("Hedef pozisyon zorunludur.");
    return;
  }

  if (mode === "url") {
    if (!url) {
      setError("Şirket / Kariyer URL zorunludur.");
      return;
    }
    const suggestedCvKey = suggestCvFromText(role, jobDescription);
    syncCvCard(suggestedCvKey);
    payload = {
      role,
      language,
      url,
      user_instruction: userInstruction || null,
      cv_role_type: suggestedCvKey,
    };
    companyDisplay = url;
  } else if (mode === "company") {
    if (!companyId) {
      setError("Lütfen kayıtlı bir şirket seçin.");
      return;
    }

    payload = {
      role,
      language,
      company_id: companyId,
      user_instruction: userInstruction || null,
    };

    const selectedCompany = companies.find((c) => c.id === companyId);
    companyDisplay =
      selectedCompany?.name || selectedCompany?.website || companyId;
  } else {
    if (!companyName && !recipientEmail) {
      setError("Şirket adı veya alıcı e-postasından en az biri dolu olmalı.");
      return;
    }

    if (!companyName && recipientEmail && !userInstruction) {
      setError(
        "Yalnızca alıcı e-postası verildiğinde mailin nasıl yazılacağını belirtin."
      );
      return;
    }

    if (recipientEmail && !isValidEmail(recipientEmail)) {
      setError("Geçerli bir alıcı e-postası girin.");
      return;
    }

    endpoint = "/companies/generate-application-email";

    const suggestedCvKey = suggestCvFromText(role, jobDescription);
    syncCvCard(suggestedCvKey);

    payload = {
      company_name: companyName || null,
      position: role || null,
      recipient_email: recipientEmail || null,
      job_description: jobDescription || null,
      user_instruction: userInstruction || null,
      cv_role_type: suggestedCvKey,
      language: language || "tr",
    };

    companyDisplay = companyName || recipientEmail || "Belirtilmedi";
  }

  setGenerateLoading(true);
  setLoading(true);

  try {
    const res = await authFetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();

    if (mode === "mail") {
      applicationId = data.application_id || data.id || null;
      currentCompanyId = data.company_id || null;
      refineSupported = Boolean(applicationId);

      setChatCompanyInfo();
      clearCompanyChat();

      updatePreview(data.subject, data.body);

      const to =
        (data.recipient_email || "").trim() || recipientEmail || "";

      setContactEmail(to);

      upsertApplicationRecord({
        id: applicationId,
        companyUrl: "",
        companyName: companyDisplay,
        role: role || "",
        language: language || "tr",
        cvKey: activeCvKey(),
        contactEmail: to,
        subject: data.subject || "",
        body: data.body || "",
        status: "draft",
        instruction: userInstruction,
      });

      setSuccessText("E-posta başarıyla oluşturuldu.");
      refreshSendAvailability();
      $("btnRefine").disabled = !refineSupported;
      setSuccess(true);
      updateCompanyContactActions();
      return;
    }

    applicationId = data.application_id;
    currentCompanyId =
      data.company_id || (mode === "company" ? companyId : null);
    refineSupported = Boolean(applicationId);

    setChatCompanyInfo();
    clearCompanyChat();

    updatePreview(data.subject, data.body);
    setContactEmail(data.contact_email || "");

    upsertApplicationRecord({
      id: data.application_id,
      companyUrl: mode === "url" ? url : "",
      companyName: companyDisplay,
      role,
      language,
      cvKey: activeCvKey(),
      contactEmail: data.contact_email || "",
      subject: data.subject || "",
      body: data.body || "",
      status: "draft",
      instruction: userInstruction,
    });

    updateCompanyContactActions();

    if (data.contact_email && isValidEmail(String(data.contact_email).trim())) {
      setSuccessText("E-posta başarıyla oluşturuldu.");
      refreshSendAvailability();
    } else {
      setSuccessText(
        "E-posta oluştu. Gönderim için önizlemede geçerli bir alıcı e-postası girin."
      );
      setSendState(false);
    }

    $("btnRefine").disabled = !refineSupported;
    setSuccess(true);
  } catch (e) {
    applicationId = null;
    currentCompanyId = null;
    refineSupported = false;
    updatePreview("", "");
    resetContactEmail();
    setSendState(false);
    $("btnRefine").disabled = true;
    setError(e.message || "İstek başarısız. Backend çalışıyor mu?");
  } finally {
    setGenerateLoading(false);
    setLoading(false);
  }
});

$("btnChangeCv").addEventListener("click", () => {
  const current = $("cvSelector").value;
  const next =
    current === "ai_engineer" ? "backend_ai_engineer" : "ai_engineer";

  syncCvCard(next);
});

$("cvSelector").addEventListener("change", (e) => {
  syncCvCard(e.target.value);
});

$("btnRefine").addEventListener("click", async () => {
  clearError();

  if (!applicationId) {
    setError("Önce e-posta oluşturun.");
    return;
  }

  const instruction = $("refineInstruction").value.trim();

  if (!instruction) {
    setError("Düzenleme talimatı yazın.");
    return;
  }

  const btn = $("btnRefine");
  btn.disabled = true;
  setLoading(true);

  try {
    const res = await authFetch(`/applications/${applicationId}/refine-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();

    updatePreview(data.subject, data.body);

    upsertApplicationRecord({
      id: applicationId,
      subject: data.subject || "",
      body: data.body || "",
      status: data.status || "draft",
      instruction,
    });

    setSuccessText("E-posta düzenlendi.");
    setSuccess(true);
  } catch (e) {
    setError(e.message || "Düzenleme başarısız.");
  } finally {
    btn.disabled = false;
    setLoading(false);
  }
});

$("btnSend").addEventListener("click", async () => {
  clearError();

  if (!applicationId) {
    setError("Önce e-posta oluşturun.");
    return;
  }

  if (!refineSupported) {
    setError("Gönderim için geçerli bir başvuru kaydı gerekir.");
    return;
  }

  const to = ($("contactEmailInput")?.value || "").trim();
  if (!isValidEmail(to)) {
    setError("Önizlemede geçerli bir alıcı e-postası girin.");
    return;
  }

  const btn = $("btnSend");
  btn.disabled = true;
  setSendButtonSpinner(true);

  try {
    const formData = new FormData();
    const subjectVal = ($("emailSubject")?.value || "").trim();
    const bodyVal = ($("emailBody")?.value || "").trim();
    if (subjectVal) formData.append("subject", subjectVal);
    if (bodyVal) formData.append("body", bodyVal);
    if (to) formData.append("to_email", to);

    const extraFileInput = $("extraAttachment");
    if (extraFileInput?.files?.[0]) {
      formData.append("extra_file", extraFileInput.files[0]);
    }

    const res = await authFetch(`/applications/${applicationId}/send`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();

    upsertApplicationRecord({
      id: applicationId,
      status: data.status || "sent",
    });

    applicationId = null;
    currentCompanyId = null;
    refineSupported = false;
    updateCompanyContactActions();

    setSuccessText(data.message || "Başvuru başarıyla gönderildi.");
    setSuccess(true);
    clearError();
    alert(data.message || "Gönderildi.");
    setSendState(false);
    if ($("btnSend")) $("btnSend").disabled = true;
    if ($("btnRefine")) $("btnRefine").disabled = true;
  } catch (e) {
    setError(e.message || "Gönderim başarısız.");
  } finally {
    setSendButtonSpinner(false);
    refreshSendAvailability();
  }
});

setupApplicationMode();
setupContactEmailEditor();
setupCompanyChat();
syncCvCard("ai_engineer");
setChatCompanyInfo();
clearCompanyChat();
updateCompanyContactActions();
updateMailModePlaceholders(getApplicationMode());
loadCompanies().catch(() => {});

if ($("contactEmailInput")) {
  $("contactEmailInput").addEventListener("input", () => {
    refreshSendAvailability();
  });
}

if ($("btnRefreshApplications")) {
  $("btnRefreshApplications").addEventListener("click", () => {
    renderApplicationsList();
  });
}

renderApplicationsList();