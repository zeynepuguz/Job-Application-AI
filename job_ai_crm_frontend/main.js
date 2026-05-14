const $ = (id) => document.getElementById(id);

let applicationId = null;
let currentCompanyId = null;
let canSendApplication = false;
let refineSupported = false;
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
  return checked ? checked.value : "career_url";
}

function readMailStyle() {
  return ($("mailStyleInstruction")?.value || "").trim();
}

function readUserExtra() {
  return ($("userInstruction")?.value || "").trim();
}

function mergedInstructionForApi() {
  const style = readMailStyle();
  const extra = readUserExtra();
  if (style && extra) return `${style}\n\n${extra}`;
  return style || extra || null;
}

function activeCvKey() {
  return $("cvSelector")?.value || "ai_engineer";
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

function setupApplicationMode() {
  const modeInputs = document.querySelectorAll('input[name="applicationMode"]');

  const applyModeVisibility = (mode) => {
    const urlWrap = $("urlInputWrapper");
    const mailWrap = $("mailInputWrapper");
    const liWrap = $("linkedinJobWrapper");
    const langWrap = $("languageWrapper");

    if (mode === "career_url") {
      show(urlWrap);
      hide(mailWrap);
      hide(liWrap);
      show(langWrap);
    } else if (mode === "recruiter_mail") {
      hide(urlWrap);
      show(mailWrap);
      hide(liWrap);
      hide(langWrap);
    } else {
      hide(urlWrap);
      hide(mailWrap);
      show(liWrap);
      hide(langWrap);
    }
  };

  modeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      const mode = getApplicationMode();
      applyModeVisibility(mode);
    });
  });

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
  const role = $("targetRole").value.trim();
  const language = $("language").value;
  const companyName = ($("companyName")?.value || "").trim();
  const recipientEmail = ($("recipientEmail")?.value || "").trim();
  const linkedinRecipient = ($("linkedinRecipientEmail")?.value || "").trim();
  const jobDescription = ($("jobDescription")?.value || "").trim();
  const mergedInstr = mergedInstructionForApi();

  let payload = {};
  let companyDisplay = "";
  let endpoint = "/applications/prepare";

  if (mode === "career_url") {
    if (!url) {
      setError("Kariyer sayfası URL zorunludur.");
      return;
    }
    if (!role) {
      setError("Hedef pozisyon zorunludur.");
      return;
    }

    payload = {
      role,
      language,
      url,
      user_instruction: mergedInstr || null,
    };
    companyDisplay = url;
  } else if (mode === "recruiter_mail") {
    endpoint = "/companies/generate-application-email";

    if (!companyName && !recipientEmail) {
      setError("Şirket adı veya alıcı e-postasından en az biri dolu olmalı.");
      return;
    }

    if (!companyName && recipientEmail && !mergedInstr) {
      setError(
        "Yalnızca alıcı e-postası verildiğinde nasıl yazılacağını kısaca belirtin."
      );
      return;
    }

    if (recipientEmail && !isValidEmail(recipientEmail)) {
      setError("Geçerli bir alıcı e-postası girin.");
      return;
    }

    payload = {
      company_name: companyName || null,
      position: role || null,
      recipient_email: recipientEmail || null,
      job_description: null,
      user_instruction: mergedInstr || null,
      cv_role_type: activeCvKey(),
    };

    companyDisplay = companyName || recipientEmail || "Belirtilmedi";
  } else {
    endpoint = "/companies/generate-application-email";

    if (!jobDescription) {
      setError("LinkedIn / ilan metni zorunludur.");
      return;
    }

    if (linkedinRecipient && !isValidEmail(linkedinRecipient)) {
      setError("İsteğe bağlı alıcı e-postası geçerli olmalıdır.");
      return;
    }

    payload = {
      company_name: null,
      position: role || null,
      recipient_email: linkedinRecipient || null,
      job_description: jobDescription || null,
      user_instruction: mergedInstr || null,
      cv_role_type: activeCvKey(),
    };

    companyDisplay = linkedinRecipient || "İlan başvurusu";
  }

  setGenerateLoading(true);
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

    if (mode !== "career_url") {
      applicationId = data.application_id;
      currentCompanyId = data.company_id || null;
      refineSupported = Boolean(applicationId);

      setChatCompanyInfo();
      clearCompanyChat();

      updatePreview(data.subject, data.body);

      const to =
        (data.recipient_email || "").trim() ||
        (mode === "linkedin_job" ? linkedinRecipient : recipientEmail) ||
        "";

      setContactEmail(to);

      upsertApplicationRecord({
        id: applicationId,
        companyUrl: "",
        companyName: companyDisplay,
        role: role || "",
        language: "tr",
        cvKey: activeCvKey(),
        contactEmail: to,
        subject: data.subject || "",
        body: data.body || "",
        status: "draft",
      });

      setSuccessText("E-posta başarıyla oluşturuldu.");
      refreshSendAvailability();
      $("btnRefine").disabled = !refineSupported;
      setSuccess(true);
      updateCompanyContactActions();
      return;
    }

    applicationId = data.application_id;
    currentCompanyId = data.company_id || null;
    refineSupported = Boolean(applicationId);

    setChatCompanyInfo();
    clearCompanyChat();

    updatePreview(data.subject, data.body);
    setContactEmail(data.contact_email || "");

    upsertApplicationRecord({
      id: data.application_id,
      companyUrl: url,
      companyName: companyDisplay,
      role,
      language,
      cvKey: activeCvKey(),
      contactEmail: data.contact_email || "",
      subject: data.subject || "",
      body: data.body || "",
      status: "draft",
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
    const res = await fetch(`/applications/${applicationId}/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject: ($("emailSubject")?.value || "").trim() || null,
        body: ($("emailBody")?.value || "").trim() || null,
        to_email: to || null,
      }),
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