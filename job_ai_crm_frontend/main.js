const $ = (id) => document.getElementById(id);

let applicationId = null;
let canSendApplication = false;
const STORAGE_KEY = "jobai_applications";
const cvProfiles = {
  ai_engineer: {
    label: "AI Engineer CV",
    desc: "Genel AI rollerine uygun varsayilan CV.",
    suggestedRole: "AI Engineer",
  },
  backend_ai_engineer: {
    label: "Backend AI Engineer CV",
    desc: "Backend + model servisleme odakli CV.",
    suggestedRole: "Backend AI Engineer",
  },
};

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

async function fetchCompanies() {
  const res = await fetch("/companies/");
  if (!res.ok) throw new Error("companies endpoint");
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return new Intl.DateTimeFormat("tr-TR", { dateStyle: "short", timeStyle: "short" }).format(d);
}

function renderStats(items) {
  $("statTotal").textContent = String(items.length);
  $("statDraft").textContent = String(items.filter((x) => x.status !== "sent").length);
  $("statSent").textContent = String(items.filter((x) => x.status === "sent").length);
}

function mapCompanyToRecord(c) {
  const companyName = c.name || "Sirket";
  const subject = `${companyName} icin basvuru`;
  return {
    id: c.id,
    role: c.name || "Pozisyon belirtilmedi",
    companyUrl: c.website || c.source_url || "-",
    subject,
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
      ? '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 border border-green-200">Gonderildi</span>'
      : '<span class="px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-700 border border-amber-200">Taslak</span>';

  const detailId = `detail-${item.id}`;
  const detailBody = item.body
    ? item.body
    : "Bu kayit backendde company endpointinden geldigi icin e-posta govdesi bulunmuyor.";

  return `
    <article class="bg-white border border-outline-variant rounded-lg p-md">
      <div class="flex items-start justify-between gap-sm">
        <div class="min-w-0">
          <div class="flex items-center gap-xs mb-xs">${badge}<span class="text-label-sm text-slate-500">ID: ${item.id}</span></div>
          <p class="text-body-md font-semibold text-on-surface truncate">${item.subject || "-"}</p>
          <p class="text-body-sm text-on-surface-variant truncate">Sirket: ${item.companyUrl || "-"}</p>
          <p class="text-body-sm text-on-surface-variant truncate">Pozisyon: ${item.role || "-"}</p>
        </div>
        <div class="text-right text-body-sm text-on-surface-variant">
          <p>CV: ${item.cvLabel || "-"}</p>
          <p>Iletisim: ${item.contactEmail || "Bilinmiyor"}</p>
          <p>${formatDate(item.updatedAt)}</p>
          <button
            type="button"
            data-detail-target="${detailId}"
            class="mt-xs px-sm py-xs text-label-sm rounded-md border border-outline-variant hover:bg-surface-container transition-all"
          >
            Icerige Gir
          </button>
        </div>
      </div>
      <div id="${detailId}" class="hidden mt-sm pt-sm border-t border-outline-variant">
        <p class="text-label-sm text-slate-500 mb-xs">E-posta Icerigi</p>
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
  if (!listEl || !emptyEl || !$("statTotal") || !$("statDraft") || !$("statSent")) {
    return;
  }
  const local = readApplications();
  let combined = [...local];

  try {
    const companies = await fetchCompanies();
    const map = new Map();
    [...local, ...companies.map(mapCompanyToRecord)].forEach((item) => {
      if (!map.has(item.id)) map.set(item.id, item);
    });
    combined = Array.from(map.values());
  } catch {
    // local verilerle devam
  }

  combined.sort((a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime());
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
      btn.textContent = panel.classList.contains("hidden") ? "Icerige Gir" : "Icerigi Gizle";
    });
  });
}

function hide(el) {
  el.classList.add("hidden");
  el.classList.remove("flex");
}

function showFlex(el) {
  el.classList.remove("hidden");
  el.classList.add("flex");
}

function setError(msg) {
  const banner = $("errorBanner");
  $("errorText").textContent = msg;
  showFlex(banner);
}

function clearError() {
  hide($("errorBanner"));
}

function setSuccess(visible) {
  const banner = $("successBanner");
  if (visible) {
    banner.classList.remove("hidden");
    banner.classList.add("flex");
  } else {
    hide(banner);
  }
}

function setSuccessText(message) {
  $("successText").textContent = message;
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
  } catch {
    /* ignore */
  }
  return res.statusText || `HTTP ${res.status}`;
}

function setLoading(loading) {
  const sk = $("emailSkeleton");
  const body = $("emailBody");
  if (loading) {
    sk.classList.remove("hidden");
    body.classList.add("hidden");
  } else {
    sk.classList.add("hidden");
    body.classList.remove("hidden");
  }
}

function updatePreview(subject, body) {
  $("emailSubject").textContent = subject || "—";
  $("emailBody").textContent = body || "";
}

function resetContactEmail() {
  $("contactEmail").textContent = "Bilinmiyor";
}

function setContactEmail(email) {
  $("contactEmail").textContent = email || "Bilinmiyor";
}

function setSendState(enabled) {
  canSendApplication = enabled;
  $("btnSend").disabled = !enabled;
}

function getCvKeyFromRole(role) {
  const lower = role.toLowerCase();
  if (lower.includes("backend")) return "backend_ai_engineer";
  if (lower.includes("ai") || lower.includes("ml") || lower.includes("machine learning")) return "ai_engineer";
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

$("btnGenerate").addEventListener("click", async () => {
  clearError();
  setSuccess(false);
  resetContactEmail();
  setSendState(false);

  const url = $("companyUrl").value.trim();
  const role = $("targetRole").value.trim();
  const language = $("language").value;

  if (!url || !role) {
    setError("Sirket URL ve hedef pozisyon zorunludur.");
    return;
  }

  const btn = $("btnGenerate");
  btn.disabled = true;
  setLoading(true);

  try {
    const res = await fetch("/applications/prepare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, role, language }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorDetail(res));
    }

    const data = await res.json();
    applicationId = data.application_id;
    updatePreview(data.subject, data.body);
    setContactEmail(data.contact_email);
    upsertApplicationRecord({
      id: data.application_id,
      companyUrl: url,
      role,
      language,
      cvKey: getCvKeyFromRole(role),
      contactEmail: data.contact_email || "",
      subject: data.subject || "",
      body: data.body || "",
      status: "draft",
    });
    if (data.contact_email) {
      setSuccessText("E-posta basariyla olusturuldu");
      setSendState(true);
    } else {
      setSuccessText("E-posta olustu ama sirketin iletisim e-postasi bulunamadi");
      setSendState(false);
    }
    setSuccess(true);
  } catch (e) {
    applicationId = null;
    updatePreview("—", "Formu doldurup tekrar deneyin.");
    resetContactEmail();
    setSendState(false);
    setError(e.message || "Istek basarisiz. Backend calisiyor mu? (uvicorn 8000)");
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
  const next = current === "ai_engineer" ? "backend_ai_engineer" : "ai_engineer";
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
    setError("Once e-posta olusturun.");
    return;
  }

  const instruction = $("refineInstruction").value.trim();
  if (!instruction) {
    setError("Duzenleme talimati yazin.");
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
    setSuccessText("E-posta duzenlendi");
    setSuccess(true);
  } catch (e) {
    setError(e.message || "Duzenleme basarisiz.");
  } finally {
    btn.disabled = false;
    setLoading(false);
  }
});

$("btnSend").addEventListener("click", async () => {
  clearError();

  if (!applicationId) {
    setError("Once e-posta olusturun.");
    return;
  }

  if (!canSendApplication) {
    setError("Gonderim icin hedef iletisim e-postasi bulunmuyor.");
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
    setSuccessText(data.message || "Basvuru basariyla gonderildi.");
    setSuccess(true);
    clearError();
    alert(data.message || "Gonderildi.");
  } catch (e) {
    setError(e.message || "Gonderim basarisiz.");
  } finally {
    btn.disabled = false;
  }
});

syncCvCard("ai_engineer");
if ($("btnRefreshApplications")) {
  $("btnRefreshApplications").addEventListener("click", () => {
    renderApplicationsList();
  });
}
