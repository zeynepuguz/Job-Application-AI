const $ = (id) => document.getElementById(id);

async function fetchCompanies() {
  const res = await fetch("/companies/");
  if (!res.ok) throw new Error(`Şirketler alınamadı: ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

async function fetchSentApplications() {
  const res = await fetch("/applications/sent");
  if (!res.ok) throw new Error(`Başvurular alınamadı: ${res.status}`);
  const data = await res.json();
  return Array.isArray(data?.applications) ? data.applications : [];
}

function normalizeText(value) {
  return (value || "").toString().toLocaleLowerCase("tr-TR").trim();
}

function isApplied(company, sentSet) {
  const companyName = normalizeText(company.name);
  const companyWebsite = normalizeText(company.website);
  return sentSet.has(companyName) || sentSet.has(companyWebsite);
}

function cardHtml(company, applied) {
  const status = applied
    ? '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 border border-green-200">Başvuruldu</span>'
    : '<span class="px-2 py-1 text-xs rounded-full bg-slate-100 text-slate-700 border border-slate-200">Başvurulmadı</span>';

  return `
    <article class="border border-slate-200 rounded-xl p-4 hover:shadow-sm transition-shadow bg-white">
      <div class="flex items-center justify-between gap-3">
        <div class="min-w-0">
          <h3 class="font-semibold text-slate-900 truncate">${company.name || "İsimsiz Şirket"}</h3>
          <p class="text-sm text-slate-600 truncate"><span class="font-medium">Website:</span> ${company.website || "-"}</p>
          <p class="text-sm text-slate-600 truncate"><span class="font-medium">İletişim:</span> ${company.contact_email || "Bilinmiyor"}</p>
        </div>
        <div>${status}</div>
      </div>
    </article>
  `;
}

function renderCompanies(companies, sentSet, query) {
  const listEl = $("companiesList");
  const emptyEl = $("companiesEmpty");

  const q = normalizeText(query);
  const filtered = companies.filter((company) => {
    if (!q) return true;
    const name = normalizeText(company.name);
    const website = normalizeText(company.website);
    return name.includes(q) || website.includes(q);
  });

  if (!filtered.length) {
    listEl.innerHTML = "";
    emptyEl.classList.remove("hidden");
    return;
  }

  emptyEl.classList.add("hidden");
  listEl.innerHTML = filtered
    .map((company) => cardHtml(company, isApplied(company, sentSet)))
    .join("");
}

let allCompanies = [];
let sentCompanySet = new Set();

async function init() {
  try {
    const [companies, sentApplications] = await Promise.all([
      fetchCompanies(),
      fetchSentApplications().catch(() => []),
    ]);

    allCompanies = companies;
    sentCompanySet = new Set();
    sentApplications.forEach((app) => {
      sentCompanySet.add(normalizeText(app.company_name));
      sentCompanySet.add(normalizeText(app.company_email));
    });
    renderCompanies(allCompanies, sentCompanySet, $("companySearchInput").value);
  } catch (err) {
    $("companiesList").innerHTML = `<div class="rounded-lg border border-red-200 bg-red-50 text-red-700 p-4 text-sm">${err.message}</div>`;
    $("companiesEmpty").classList.add("hidden");
  }
}

$("btnCompanySearch").addEventListener("click", () => {
  renderCompanies(allCompanies, sentCompanySet, $("companySearchInput").value);
});

$("companySearchInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    renderCompanies(allCompanies, sentCompanySet, $("companySearchInput").value);
  }
});

init();
