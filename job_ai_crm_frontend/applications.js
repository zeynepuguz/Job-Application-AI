const STORAGE_KEY = "jobai_applications";

const $ = (id) => document.getElementById(id);

function readApplications() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function fetchSentApplications() {
  const res = await fetch("/applications/sent");
  if (!res.ok) {
    throw new Error(`Applications endpoint hatası: ${res.status}`);
  }
  const data = await res.json();
  return Array.isArray(data?.applications) ? data.applications : [];
}

function formatDate(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function statusBadge(status) {
  if (status === "sent") {
    return '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 border border-green-200">Gönderildi</span>';
  }
  return '<span class="px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-700 border border-amber-200">Taslak</span>';
}

function renderStats(items) {
  const total = items.length;
  const draft = items.filter((x) => x.status !== "sent").length;
  const sent = items.filter((x) => x.status === "sent").length;
  $("statTotal").textContent = String(total);
  $("statDraft").textContent = String(draft);
  $("statSent").textContent = String(sent);
}

function renderList(items) {
  const list = $("applicationsList");
  const empty = $("emptyState");
  if (!items.length) {
    list.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  list.innerHTML = items
    .map((item) => {
      const role = item.role || "-";
      const company = item.companyUrl || "-";
      const subject = item.subject || "-";
      const cvLabel = item.cvLabel || "AI Engineer CV";
      const contact = item.contactEmail || "Bilinmiyor";
      const updated = formatDate(item.updatedAt);
      const hasBody = Boolean(item.body && item.body.trim());
      const detailId = `detay-${item.id}`;

      return `
        <article class="border border-slate-200 rounded-xl p-4 hover:shadow-sm transition-shadow bg-white">
          <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
            <div class="space-y-2 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                ${statusBadge(item.status)}
                <span class="text-xs text-slate-500">ID: ${item.id}</span>
              </div>
              <h3 class="font-semibold text-slate-900 truncate">${subject}</h3>
              <p class="text-sm text-slate-600 truncate"><span class="font-medium">Şirket:</span> ${company}</p>
              <p class="text-sm text-slate-600 truncate"><span class="font-medium">Pozisyon:</span> ${role}</p>
              <p class="text-sm text-slate-600 truncate"><span class="font-medium">Konu:</span> ${subject}</p>
            </div>
            <div class="text-sm text-slate-600 space-y-1 md:text-right">
              <p><span class="font-medium">CV:</span> ${cvLabel}</p>
              <p><span class="font-medium">İletişim:</span> ${contact}</p>
              <p><span class="font-medium">Güncelleme:</span> ${updated}</p>
              ${
                hasBody
                  ? `<button type="button" data-toggle-detail="${detailId}" class="px-3 py-1 text-xs rounded-md border border-slate-300 hover:bg-slate-100">İçeriği Gör</button>`
                  : `<span class="inline-block px-3 py-1 text-xs rounded-md border border-slate-200 text-slate-400">İçerik Yok</span>`
              }
            </div>
          </div>
          ${
            hasBody
              ? `<div id="${detailId}" class="hidden mt-3 pt-3 border-t border-slate-200">
                  <p class="text-xs text-slate-500 mb-2">Başvuru E-posta İçeriği</p>
                  <div class="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed bg-slate-50 border border-slate-200 rounded-lg p-3">${item.body}</div>
                </div>`
              : ""
          }
        </article>
      `;
    })
    .join("");

  list.querySelectorAll("[data-toggle-detail]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-toggle-detail");
      const panel = id ? document.getElementById(id) : null;
      if (!panel) return;
      const isHidden = panel.classList.toggle("hidden");
      btn.textContent = isHidden ? "İçeriği Gör" : "İçeriği Gizle";
    });
  });
}

function normalizeLocal(items) {
  return items.map((item) => ({
    id: item.id,
    role: item.role || "-",
    companyUrl: item.companyUrl || "-",
    subject: item.subject || "-",
    cvLabel: item.cvLabel || "AI Engineer CV",
    contactEmail: item.contactEmail || "Bilinmiyor",
    status: item.status || "draft",
    updatedAt: item.updatedAt || item.createdAt || new Date().toISOString(),
    body: item.body || "",
  }));
}

function normalizeCompanies(items) {
  return items.map((a) => ({
    id: a.application_id,
    role: a.role || "Pozisyon belirtilmedi",
    companyUrl: a.company_name || "-",
    subject: a.subject || "Başvuru",
    cvLabel: "-",
    contactEmail: a.company_email || "Bilinmiyor",
    status: a.status || "sent",
    updatedAt: a.sent_at || new Date().toISOString(),
    body: a.body || "",
  }));
}

function applyFilters(sourceItems) {
  const query = $("searchInput").value.trim().toLowerCase();
  const status = $("statusFilter").value;
  const all = [...sourceItems].sort((a, b) => {
    const da = new Date(a.updatedAt || 0).getTime();
    const db = new Date(b.updatedAt || 0).getTime();
    return db - da;
  });

  const filtered = all.filter((item) => {
    const matchesStatus = status === "all" ? true : item.status === status;
    const blob = `${item.companyUrl || ""} ${item.role || ""} ${item.subject || ""}`.toLowerCase();
    const matchesQuery = query ? blob.includes(query) : true;
    return matchesStatus && matchesQuery;
  });

  renderStats(all);
  renderList(filtered);
}

let sourceItems = [];

$("searchInput").addEventListener("input", () => applyFilters(sourceItems));
$("statusFilter").addEventListener("change", () => applyFilters(sourceItems));

async function init() {
  const local = normalizeLocal(readApplications());
  try {
    const companies = normalizeCompanies(await fetchSentApplications());
    sourceItems = companies;
  } catch {
    sourceItems = local;
  }
  applyFilters(sourceItems);
}

init();
