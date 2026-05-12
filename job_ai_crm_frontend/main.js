const $ = (id) => document.getElementById(id);

let applicationId = null;
let currentCompanyId = null;
let canSendApplication = false;
let companies = [];

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

function updateMailModePlaceholders(mode) {
  const roleInput = $("targetRole");
  if (roleInput) {
    roleInput.placeholder =
      mode === "mail"
        ? "Örn: Backend AI Engineer (opsiyonel)"
        : "Örn: Backend AI Engineer";
  }
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
  const body = $("emailBody");

  if (loading) {
    show(sk);
    body.classList.add("hidden");
  } else {
    hide(sk);
    body.classList.remove("hidden");
  }
}

function updatePreview(subject, body) {
  $("emailSubject").textContent = subject || "—";
  $("emailBody").textContent = body || "";
}

function resetContactEmail() {
  $("contactEmail").textContent = "Bilinmiyor";
  if ($("contactEmailInput")) {
    $("contactEmailInput").value = "";
  }
}

function setContactEmail(email) {
  const normalized = (email || "").trim();
  $("contactEmail").textContent = normalized || "Bilinmiyor";
  if ($("contactEmailInput")) {
    $("contactEmailInput").value = normalized;
  }
}

function setSendState(enabled) {
  canSendApplication = enabled;
  $("btnSend").disabled = !enabled;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showContactEmailEditor(visible) {
  const editor = $("contactEmailEditor");
  if (!editor) return;
  editor.classList.toggle("hidden", !visible);
}

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
    const res = await fetch(`/companies/${currentCompanyId}/chat`, {
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
    const res = await fetch(`/companies/${currentCompanyId}/contact-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contact_email: value }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();
    setContactEmail(data.contact_email || value);
    setSendState(true);
    setSuccessText("İletişim e-postası güncellendi.");
    setSuccess(true);
    showContactEmailEditor(false);
  } catch (e) {
    setError(e.message || "İletişim e-postası güncellenemedi.");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function setupContactEmailEditor() {
  if ($("btnEditContactEmail")) {
    $("btnEditContactEmail").addEventListener("click", () => {
      showContactEmailEditor(true);
      const input = $("contactEmailInput");
      if (input) input.focus();
    });
  }

  if ($("btnCancelContactEmail")) {
    $("btnCancelContactEmail").addEventListener("click", () => {
      showContactEmailEditor(false);
      const current = $("contactEmail")?.textContent || "";
      $("contactEmailInput").value = current === "Bilinmiyor" ? "" : current;
    });
  }

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
        const res = await fetch(`/companies/${currentCompanyId}/chat`, {
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
  const res = await fetch("/companies/");

  if (!res.ok) {
    throw new Error("Şirketler alınamadı.");
  }

  const data = await res.json();
  const raw = Array.isArray(data) ? data : [];
  const seen = new Set();

  return raw.filter((company) => {
    const emailKey = (company.contact_email || "").trim().toLowerCase();
    const fallbackKey = (company.website || company.id || "").trim().toLowerCase();
    const key = emailKey || fallbackKey;

    if (!key) return true;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function renderCompanyList(list) {
  const companyList = $("companyList");

  if (!companyList) return;

  companyList.innerHTML = "";

  if (!list.length) {
    companyList.innerHTML = `
      <div class="p-md text-body-sm text-slate-500">
        Şirket bulunamadı.
      </div>
    `;
    return;
  }

  list.forEach((company) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className =
      "w-full text-left p-md hover:bg-surface-container-low transition-all";

    item.innerHTML = `
      <p class="font-semibold text-on-surface">
        ${company.name || "İsimsiz Şirket"}
      </p>
      <p class="text-body-sm text-slate-500">
        ${company.website || ""}
      </p>
      <p class="text-body-sm text-slate-500">
        ${company.contact_email || "Mail bulunamadı"}
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
    });

    companyList.appendChild(item);
  });
}

async function loadCompanies() {
  const companyList = $("companyList");

  try {
    companyList.innerHTML = `
      <div class="p-md text-body-sm text-slate-500">
        Şirketler yükleniyor...
      </div>
    `;

    companies = await fetchCompanies();
    renderCompanyList(companies);
  } catch (e) {
    companyList.innerHTML = `
      <div class="p-md text-body-sm text-red-600">
        Şirketler yüklenirken hata oluştu.
      </div>
    `;
  }
}

function setupApplicationMode() {
  const modeInputs = document.querySelectorAll('input[name="applicationMode"]');

  modeInputs.forEach((input) => {
    input.addEventListener("change", async () => {
      const mode = getApplicationMode();

      if (mode === "url") {
        show($("urlInputWrapper"));
        hide($("companySelectWrapper"));
        hide($("mailInputWrapper"));
        show($("languageWrapper"));
        $("selectedCompanyId").value = "";
        currentCompanyId = null;
        $("selectedCompanyText").textContent = "Henüz şirket seçilmedi.";
        resetContactEmail();
        setChatCompanyInfo();
        clearCompanyChat();
      } else if (mode === "company") {
        hide($("urlInputWrapper"));
        show($("companySelectWrapper"));
        hide($("mailInputWrapper"));
        show($("languageWrapper"));
        await loadCompanies();
        setChatCompanyInfo();
      } else {
        hide($("urlInputWrapper"));
        hide($("companySelectWrapper"));
        show($("mailInputWrapper"));
        hide($("languageWrapper"));
        $("selectedCompanyId").value = "";
        currentCompanyId = null;
        $("selectedCompanyText").textContent = "Henüz şirket seçilmedi.";
        setChatCompanyInfo();
        clearCompanyChat();
      }

      updateMailModePlaceholders(mode);
    });
  });

  if ($("companySearch")) {
    $("companySearch").addEventListener("input", () => {
      const term = $("companySearch").value.toLowerCase().trim();

      const filtered = companies.filter((company) => {
        return (
          company.name?.toLowerCase().includes(term) ||
          company.website?.toLowerCase().includes(term) ||
          company.contact_email?.toLowerCase().includes(term)
        );
      });

      renderCompanyList(filtered);
    });
  }
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

function getCvKeyFromRole(role) {
  const lower = role.toLowerCase();

  if (lower.includes("backend")) return "backend_ai_engineer";

  if (
    lower.includes("ai") ||
    lower.includes("ml") ||
    lower.includes("machine learning") ||
    lower.includes("yapay zeka")
  ) {
    return "ai_engineer";
  }

  return "ai_engineer";
}

function syncCvCard(cvKey) {
  const profile = cvProfiles[cvKey] || cvProfiles.ai_engineer;

  $("cvSelector").value = cvKey;
  $("selectedCvName").textContent = profile.label;
  $("selectedCvDesc").textContent = profile.desc;
}

function applyCvToRole(cvKey) {
  const profile = cvProfiles[cvKey] || cvProfiles.ai_engineer;
  const roleInput = $("targetRole");

  if (!roleInput.value.trim()) {
    roleInput.value = profile.suggestedRole;
  }
}

function createDraftRecordId() {
  return `draft-${Date.now()}`;
}

$("btnGenerate").addEventListener("click", async () => {
  clearError();
  setSuccess(false);
  resetContactEmail();
  setSendState(false);

  const mode = getApplicationMode();
  const url = $("companyUrl").value.trim();
  const companyId = $("selectedCompanyId")?.value.trim();
  const role = $("targetRole").value.trim();
  const language = $("language").value;
  const companyName = ($("companyName")?.value || "").trim();
  const recipientEmail = ($("recipientEmail")?.value || "").trim();
  const jobDescription = ($("jobDescription")?.value || "").trim();
  const userInstruction = ($("userInstruction")?.value || "").trim();

  let payload = {};
  let companyDisplay = "";
  let endpoint = "/applications/prepare";

  if (mode !== "mail" && !role) {
    setError("Hedef pozisyon zorunludur.");
    return;
  }

  if (mode === "url") {
    if (!url) {
      setError("Şirket URL zorunludur.");
      return;
    }

    payload = { role, language, url };
    companyDisplay = url;
  } else if (mode === "company") {
    if (!companyId) {
      setError("Lütfen kayıtlı bir şirket seçin.");
      return;
    }

    payload = { role, language, company_id: companyId };

    const selectedCompany = companies.find((c) => c.id === companyId);
    companyDisplay = selectedCompany?.name || selectedCompany?.website || companyId;
  } else {
    if (!companyName && !recipientEmail) {
      setError("Şirket adı veya alıcı mail adresinden en az biri dolu olmalı.");
      return;
    }

    if (!companyName && recipientEmail && !userInstruction) {
      setError(
        "Şirket bilgisi olmadan mail üretmek için mailin nasıl yazılacağını açıklamalısın."
      );
      return;
    }

    if (recipientEmail && !isValidEmail(recipientEmail)) {
      setError("Geçerli bir alıcı mail adresi girin.");
      return;
    }

    endpoint = "/companies/generate-application-email";

    payload = {
      company_name: companyName || null,
      position: role || null,
      recipient_email: recipientEmail || null,
      job_description: jobDescription || null,
      user_instruction: userInstruction || null,
    };

    companyDisplay = companyName || recipientEmail || "Belirtilmedi";
  }

  const btn = $("btnGenerate");
  btn.disabled = true;
  setLoading(true);

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();

    if (mode === "mail") {
      applicationId = data.id || data.application_id || createDraftRecordId();
      currentCompanyId = null;

      setChatCompanyInfo();
      clearCompanyChat();

      updatePreview(data.subject, data.body);
      setContactEmail(data.recipient_email || recipientEmail || null);

      upsertApplicationRecord({
        id: applicationId,
        companyUrl: "",
        companyName: companyDisplay,
        role: role || "",
        language: "tr",
        cvKey: getCvKeyFromRole(role || "ai engineer"),
        contactEmail: data.recipient_email || recipientEmail || "",
        subject: data.subject || "",
        body: data.body || "",
        status: "draft",
      });

      setSuccessText("E-posta başarıyla oluşturuldu.");
      setSendState(Boolean(data.recipient_email || recipientEmail));
      showContactEmailEditor(!(data.recipient_email || recipientEmail));
      $("btnRefine").disabled = false;
      setSuccess(true);

      return;
    }

    applicationId = data.application_id;
    currentCompanyId = data.company_id || (mode === "company" ? companyId : null);

    setChatCompanyInfo();
    clearCompanyChat();

    updatePreview(data.subject, data.body);
    setContactEmail(data.contact_email);

    upsertApplicationRecord({
      id: data.application_id,
      companyUrl: mode === "url" ? url : "",
      companyName: companyDisplay,
      role,
      language,
      cvKey: getCvKeyFromRole(role),
      contactEmail: data.contact_email || "",
      subject: data.subject || "",
      body: data.body || "",
      status: "draft",
    });

    if (data.contact_email) {
      setSuccessText("E-posta başarıyla oluşturuldu.");
      setSendState(true);
      showContactEmailEditor(false);
    } else {
      setSuccessText(
        "E-posta oluştu ama şirketin iletişim e-postası bulunamadı. Elle ekleyebilirsin."
      );
      setSendState(false);
      showContactEmailEditor(true);
    }

    $("btnRefine").disabled = false;
    setSuccess(true);
  } catch (e) {
    applicationId = null;
    updatePreview("—", "Formu doldurup tekrar deneyin.");
    resetContactEmail();
    setSendState(false);
    $("btnRefine").disabled = true;
    setError(e.message || "İstek başarısız. Backend çalışıyor mu?");
  } finally {
    btn.disabled = false;
    setLoading(false);
  }
});

$("targetRole").addEventListener("input", (e) => {
  const cvKey = getCvKeyFromRole(e.target.value || "");
  syncCvCard(cvKey);
});

$("btnChangeCv").addEventListener("click", () => {
  const current = $("cvSelector").value;
  const next =
    current === "ai_engineer" ? "backend_ai_engineer" : "ai_engineer";

  syncCvCard(next);
  applyCvToRole(next);
});

$("cvSelector").addEventListener("change", (e) => {
  const cvKey = e.target.value;

  syncCvCard(cvKey);
  applyCvToRole(cvKey);
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
    const res = await fetch(`/applications/${applicationId}/refine-email`, {
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

  if (!canSendApplication) {
    setError("Gönderim için hedef iletişim e-postası bulunmuyor.");
    return;
  }

  const btn = $("btnSend");
  btn.disabled = true;

  try {
    const res = await fetch(`/applications/${applicationId}/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();

    upsertApplicationRecord({
      id: applicationId,
      status: data.status || "sent",
    });

    setSuccessText(data.message || "Başvuru başarıyla gönderildi.");
    setSuccess(true);
    clearError();
    alert(data.message || "Gönderildi.");
  } catch (e) {
    setError(e.message || "Gönderim başarısız.");
  } finally {
    btn.disabled = false;
  }
});

setupApplicationMode();
setupContactEmailEditor();
setupCompanyChat();
syncCvCard("ai_engineer");
setChatCompanyInfo();
clearCompanyChat();
updateMailModePlaceholders(getApplicationMode());

if ($("btnRefreshApplications")) {
  $("btnRefreshApplications").addEventListener("click", () => {
    renderApplicationsList();
  });
}

renderApplicationsList();