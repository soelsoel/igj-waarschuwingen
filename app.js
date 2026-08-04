const PER_PAGE = 20;
const MONTHS = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];

let warnings = [];

const view = document.getElementById('view');
const flash = document.getElementById('flash');

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function formatDate(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return esc(iso);
    return `${String(d.getDate()).padStart(2, '0')} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function truncateDesc(text, length = 150) {
    if (!text) return '';
    if (text.length <= length) return text;
    return text.slice(0, length).replace(/\s+\S*$/, '') + '...';
}

function showFlash(message, category = 'success') {
    const style = category === 'error'
        ? 'bg-red-100 text-red-800 border-red-200'
        : 'bg-green-100 text-green-800 border-green-200';
    flash.innerHTML = `<div class="mb-4 px-4 py-3 rounded-lg text-sm border ${style}">${esc(message)}</div>`;
}

async function loadData(bustCache = false) {
    const url = bustCache ? `data/warnings.json?t=${Date.now()}` : 'data/warnings.json';
    const response = await fetch(url, { cache: bustCache ? 'reload' : 'default' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    warnings = data.warnings;
    document.getElementById('updated').textContent =
        `Data bijgewerkt: ${formatDate(data.generated_at)}`;
}

function searchWarnings(query) {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    return warnings.filter((w) => {
        const haystack = `${w.company} ${w.apparatus_name} ${w.title_raw} ${w.description}`.toLowerCase();
        return terms.every((term) => haystack.includes(term));
    });
}

function searchBar(query = '') {
    return `
    <form id="search-form" class="mb-6">
        <div class="flex gap-2">
            <input type="text" name="q" value="${esc(query)}"
                   placeholder="Zoek op bedrijf, apparaat of beschrijving..."
                   class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm
                          focus:ring-2 focus:ring-igj-500 focus:border-igj-500 outline-none
                          text-sm transition">
            <button type="submit"
                    class="px-5 py-2.5 bg-igj-500 text-white rounded-lg hover:bg-igj-600
                           text-sm font-medium transition shadow-sm">Zoeken</button>
            ${query ? `<a href="#/" class="px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg
                          hover:bg-gray-300 text-sm font-medium transition shadow-sm">Wissen</a>` : ''}
        </div>
    </form>`;
}

function card(w) {
    const apparatus = w.apparatus_name && w.apparatus_name !== w.company
        ? `<span class="text-sm text-gray-700">${esc(w.apparatus_name)}</span>` : '';
    const description = w.description
        ? `<p class="text-sm text-gray-600 leading-relaxed">${esc(truncateDesc(w.description))}</p>` : '';
    return `
    <a href="#/waarschuwing/${esc(w.id)}" class="block group">
        <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-4
                    hover:shadow-md hover:border-igj-500/30 transition">
            <div class="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4">
                <div class="flex-shrink-0">
                    <span class="inline-block text-xs font-medium text-gray-500 bg-gray-100
                                 rounded px-2 py-1 whitespace-nowrap">${formatDate(w.pub_date)}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-2 mb-1">
                        <span class="font-semibold text-igj-500 group-hover:text-igj-600 transition">
                            ${esc(w.company || 'Onbekend bedrijf')}
                        </span>
                        ${apparatus}
                    </div>
                    ${description}
                </div>
                <div class="hidden sm:block flex-shrink-0 text-gray-300 group-hover:text-igj-500 transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                </div>
            </div>
        </div>
    </a>`;
}

function cardList(items, emptyMessage) {
    if (!items.length) {
        return `<div class="text-center py-12 text-gray-500">${emptyMessage}</div>`;
    }
    return `<div class="space-y-3">${items.map(card).join('')}</div>`;
}

function pagination(page, totalPages) {
    if (totalPages <= 1) return '';
    const link = (p, label) => `<a href="#/archief/${p}" class="px-3 py-2 text-sm bg-white border
        border-gray-300 rounded-lg hover:bg-gray-50 transition">${label}</a>`;
    const parts = [];
    if (page > 1) parts.push(link(page - 1, '&laquo; Vorige'));
    for (let p = 1; p <= totalPages; p++) {
        if (p === page) {
            parts.push(`<span class="px-3 py-2 text-sm bg-igj-500 text-white rounded-lg font-medium">${p}</span>`);
        } else if (p <= 3 || p >= totalPages - 2 || (p >= page - 1 && p <= page + 1)) {
            parts.push(link(p, p));
        } else if (p === 4 || p === totalPages - 3) {
            parts.push('<span class="px-3 py-2 text-sm text-gray-400">...</span>');
        }
    }
    if (page < totalPages) parts.push(link(page + 1, 'Volgende &raquo;'));
    return `<nav class="mt-6 flex justify-center gap-2">${parts.join('')}</nav>`;
}

function renderHome() {
    document.title = 'IGJ Waarschuwingen';
    view.innerHTML = searchBar() + `
        <div class="mb-4"><h2 class="text-lg font-semibold text-gray-800">Laatste waarschuwingen</h2></div>`
        + cardList(warnings.slice(0, PER_PAGE), '<p>Nog geen waarschuwingen beschikbaar.</p>');
}

function renderSearch(query) {
    document.title = `Zoeken: ${query} — IGJ Waarschuwingen`;
    const results = searchWarnings(query);
    view.innerHTML = searchBar(query) + `
        <div class="mb-4">
            <h2 class="text-lg font-semibold text-gray-800">
                Zoekresultaten voor "${esc(query)}"
                <span class="text-sm font-normal text-gray-500">(${results.length} ${results.length === 1 ? 'resultaat' : 'resultaten'})</span>
            </h2>
        </div>`
        + cardList(results, `<p>Geen resultaten gevonden voor "${esc(query)}".</p>
            <a href="#/" class="text-igj-500 hover:underline mt-2 inline-block">Terug naar overzicht</a>`);
}

function renderArchive(page) {
    document.title = 'Archief — IGJ Waarschuwingen';
    const totalPages = Math.max(1, Math.ceil(warnings.length / PER_PAGE));
    page = Math.min(Math.max(1, page), totalPages);
    const start = (page - 1) * PER_PAGE;
    view.innerHTML = searchBar() + `
        <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-800">
                Archief
                <span class="text-sm font-normal text-gray-500">(${warnings.length} waarschuwingen)</span>
            </h2>
        </div>`
        + cardList(warnings.slice(start, start + PER_PAGE), '<p>Nog geen waarschuwingen beschikbaar.</p>')
        + pagination(page, totalPages);
}

function renderDetail(id) {
    const w = warnings.find((item) => item.id === id);
    if (!w) {
        document.title = 'Niet gevonden — IGJ Waarschuwingen';
        view.innerHTML = `<div class="text-center py-12 text-gray-500">
            <p>Deze waarschuwing bestaat niet (meer).</p>
            <a href="#/" class="text-igj-500 hover:underline mt-2 inline-block">Terug naar overzicht</a>
        </div>`;
        return;
    }
    document.title = `${w.company} — IGJ Waarschuwingen`;
    const apparatus = w.apparatus_name && w.apparatus_name !== w.company
        ? `<p class="text-blue-100 mt-1">${esc(w.apparatus_name)}</p>` : '';
    const reference = w.reference_code
        ? `<div>
               <dt class="text-xs uppercase tracking-wide text-gray-500">Referentie</dt>
               <dd class="text-sm text-gray-800 mt-0.5">${esc(w.reference_code)}</dd>
           </div>` : '';
    view.innerHTML = `
    <a href="#/" class="inline-flex items-center gap-1 text-sm text-igj-500 hover:underline mb-4">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Terug naar overzicht
    </a>
    <article class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div class="bg-igj-500 text-white px-6 py-5">
            <h2 class="text-xl font-bold">${esc(w.company || 'Onbekend bedrijf')}</h2>
            ${apparatus}
        </div>
        <div class="px-6 py-5">
            <dl class="grid grid-cols-1 sm:grid-cols-3 gap-4 pb-5 mb-5 border-b border-gray-100">
                <div>
                    <dt class="text-xs uppercase tracking-wide text-gray-500">Datum</dt>
                    <dd class="text-sm text-gray-800 mt-0.5">${formatDate(w.pub_date)}</dd>
                </div>
                ${reference}
                <div>
                    <dt class="text-xs uppercase tracking-wide text-gray-500">Origineel</dt>
                    <dd class="text-sm mt-0.5">
                        <a href="${esc(w.link)}" target="_blank" rel="noopener"
                           class="text-igj-500 hover:underline">Bekijk op igj.nl &rarr;</a>
                    </dd>
                </div>
            </dl>
            <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">${esc(w.description)}</div>
            <p class="mt-6 text-xs text-gray-400">${esc(w.title_raw)}</p>
        </div>
    </article>`;
}

function render() {
    flash.innerHTML = '';
    const hash = location.hash.replace(/^#\/?/, '');
    const [route, ...rest] = hash.split('/');
    const param = decodeURIComponent(rest.join('/'));

    if (route === 'zoek') renderSearch(param);
    else if (route === 'archief') renderArchive(parseInt(param, 10) || 1);
    else if (route === 'waarschuwing') renderDetail(param);
    else renderHome();

    window.scrollTo(0, 0);
    const form = document.getElementById('search-form');
    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const query = form.q.value.trim();
            location.hash = query ? `#/zoek/${encodeURIComponent(query)}` : '#/';
        });
    }
}

document.getElementById('refresh').addEventListener('click', async () => {
    try {
        await loadData(true);
        render();
        showFlash(`Gegevens opnieuw geladen: ${warnings.length} waarschuwingen.`);
    } catch (error) {
        showFlash(`Kon de gegevens niet laden: ${error.message}`, 'error');
    }
});

window.addEventListener('hashchange', render);

loadData()
    .then(render)
    .catch((error) => {
        showFlash(`Kon de gegevens niet laden: ${error.message}`, 'error');
    });

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js');
}
