// Suivi Matériel VPMI — logique front (Alpine.js)

const CAT_COLORS = ['#3366ff','#22c55e','#f59e0b','#a855f7','#06b6d4','#ec4899','#64748b','#14b8a6','#f43f5e','#84cc16','#fb923c','#94a3b8'];
const AVATAR_COLORS = ['bg-blue-100 text-blue-700','bg-emerald-100 text-emerald-700','bg-amber-100 text-amber-700','bg-purple-100 text-purple-700','bg-pink-100 text-pink-700','bg-cyan-100 text-cyan-700'];
const BAD_ETATS = ["En réparation", "Endommagé", "Perdu", "Hors service"];

function suiviApp() {
  return {
    ready: false,
    cfg: { fields: [], configured: false, missing: [], list_name: "", password_required: false },
    authed: false,
    passwordInput: "",
    loginError: "",
    password: "",

    items: [],
    loading: false,
    saving: false,
    error: "",

    view: "dashboard",
    activeNav: "dashboard",
    sidebarOpen: false,

    // filtres globaux
    search: "",
    filterCat: "",
    filterStatut: "",   // utilisé seulement dans la vue Parc (présélections du menu)
    filterSite: "",
    filterEtat: "",
    filterUser: "",
    problemOnly: false,

    modalOpen: false,
    editing: null,
    form: {},
    deleteTarget: null,
    assignTarget: null,
    assignForm: { Utilisateur: "", Site: "", Etat: "En cours d'utilisation" },
    bulkOpen: false,
    bulkSaving: false,
    bulkRows: [],
    // pagination (vue Parc)
    page: 1,
    perPage: 12,
    // pagination des cartes du tableau de bord (5 lignes)
    dashPer: 5,
    attrPage: 1,
    stockPage: 1,
    // import de fichier
    importOpen: false,
    importFile: null,
    importSite: "",
    importBusy: false,
    importResult: null,
    toasts: [],

    nav: [
      { id: "dashboard",   label: "Tableau de bord",   icon: "layout-dashboard" },
      { id: "inventaire",  label: "Inventaire",        icon: "clipboard-list" },
      { id: "stock",       label: "Stock",             icon: "package" },
      { id: "users",       label: "Utilisateurs",      icon: "users" },
      { id: "maintenance", label: "Maintenance",       icon: "wrench" },
      { id: "rapports",    label: "Rapports",          icon: "bar-chart-3" },
    ],

    // ---------- init ----------
    async init() {
      try { const r = await fetch("/api/config"); this.cfg = await r.json(); }
      catch (e) { this.cfg.configured = false; }
      this.password = sessionStorage.getItem("apppw") || "";
      if (!this.cfg.password_required) this.authed = true;
      else if (this.password) this.authed = true;
      this.ready = true;
      this.refreshIcons();
      if (this.cfg.configured && this.authed) this.load();
      ["modalOpen", "deleteTarget", "assignTarget", "bulkOpen", "bulkRows", "importOpen", "items", "loading", "view", "filterCat", "filterSite", "filterEtat", "filterUser", "search"].forEach((p) => this.$watch(p, () => this.refreshIcons()));
      // revenir à la page 1 quand les filtres/la recherche changent
      ["filterCat", "filterStatut", "filterSite", "filterEtat", "filterUser", "search", "view"].forEach((p) => this.$watch(p, () => { this.page = 1; this.attrPage = 1; this.stockPage = 1; }));
    },

    refreshIcons() { this.$nextTick(() => window.lucide && lucide.createIcons()); },
    headers() {
      const h = { "Content-Type": "application/json" };
      if (this.cfg.password_required && this.password) h["X-App-Password"] = this.password;
      return h;
    },

    // ---------- navigation ----------
    go(id) {
      this.activeNav = id;
      this.sidebarOpen = false;
      // chaque navigation repart propre : on remet tous les filtres à zéro
      this.filterCat = ""; this.filterSite = ""; this.filterEtat = ""; this.filterUser = ""; this.search = "";
      this.filterStatut = ""; this.problemOnly = false;
      this.page = 1; this.attrPage = 1; this.stockPage = 1;
      if (id === "dashboard" || id === "users" || id === "rapports") { this.view = id; }
      else { // vues "tableau" avec présélection
        this.view = "parc";
        if (id === "attribue") this.filterStatut = "Attribué";
        else if (id === "stock") this.filterStatut = "En stock";
        else if (id === "maintenance") this.problemOnly = true;
      }
      this.refreshIcons();
    },
    navTitle() {
      return { dashboard: "Tableau de bord", parc: "Inventaire", users: "Utilisateurs", rapports: "Rapports" }[this.view] || "Suivi du matériel";
    },
    resetFilters() { this.filterCat = ""; this.filterSite = ""; this.filterEtat = ""; this.filterUser = ""; this.search = ""; },

    // ---------- auth ----------
    async login() {
      this.loginError = "";
      try {
        const r = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: this.passwordInput }) });
        if (!r.ok) throw new Error("Mot de passe incorrect");
        this.password = this.passwordInput; sessionStorage.setItem("apppw", this.password);
        this.authed = true; this.refreshIcons(); this.load();
      } catch (e) { this.loginError = e.message; }
    },

    // ---------- chargement ----------
    async load() {
      this.loading = true; this.error = "";
      try {
        const r = await fetch("/api/materiels", { headers: this.headers() });
        if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || ("Erreur " + r.status)); }
        this.items = await r.json();
      } catch (e) { this.error = e.message; }
      finally { this.loading = false; this.refreshIcons(); }
    },

    // ---------- filtrage ----------
    choicesFor(internal) { const f = this.cfg.fields.find((x) => x.internal === internal); return f && f.choices ? f.choices : []; },
    userList() { return [...new Set(this.items.map((i) => i.Utilisateur).filter(Boolean))].sort(); },

    // base : applique tous les filtres SAUF le statut (recherche incluse)
    base() {
      const q = this.search.trim().toLowerCase();
      return this.items.filter((it) => {
        if (this.filterCat && it.Categorie !== this.filterCat) return false;
        if (this.filterSite && it.Site !== this.filterSite) return false;
        if (this.filterEtat && it.Etat !== this.filterEtat) return false;
        if (this.filterUser && it.Utilisateur !== this.filterUser) return false;
        if (this.problemOnly && !BAD_ETATS.includes(it.Etat)) return false;
        if (!q) return true;
        return ["Categorie", "Marque", "Modele", "NumeroSerie", "Utilisateur", "Accessoires", "Remarque", "Site"]
          .some((k) => (it[k] || "").toString().toLowerCase().includes(q));
      });
    },
    attribues() { return this.base().filter((i) => i.Statut === "Attribué"); },
    stockItems() { return this.base().filter((i) => i.Statut === "En stock"); },
    // pages des cartes du tableau de bord (5 lignes)
    attrPages() { return Math.max(1, Math.ceil(this.attribues().length / this.dashPer)); },
    attrPaged() { const p = Math.min(this.attrPage, this.attrPages()); return this.attribues().slice((p - 1) * this.dashPer, p * this.dashPer); },
    stockPages() { return Math.max(1, Math.ceil(this.stockItems().length / this.dashPer)); },
    stockPaged() { const p = Math.min(this.stockPage, this.stockPages()); return this.stockItems().slice((p - 1) * this.dashPer, p * this.dashPer); },
    // vue Parc : base + filtre statut (présélection menu)
    filtered() { return this.base().filter((i) => !this.filterStatut || i.Statut === this.filterStatut); },

    // ---------- KPIs ----------
    kpis() {
      const b = this.base();
      const cnt = (fn) => b.filter(fn).length;
      const pays = [...new Set(b.map((i) => i.Site).filter(Boolean))];
      return [
        { label: "Total matériel", value: b.length, sub: "équipements", icon: "boxes", bg: "bg-brand-50", fg: "text-brand-600" },
        { label: "Matériel attribué", value: cnt((i) => i.Statut === "Attribué"), sub: "équipements", icon: "laptop", bg: "bg-blue-50", fg: "text-blue-600" },
        { label: "Matériel en stock", value: cnt((i) => i.Statut === "En stock"), sub: "équipements", icon: "package", bg: "bg-emerald-50", fg: "text-emerald-600" },
        { label: "En cours d'utilisation", value: cnt((i) => i.Etat === "En cours d'utilisation"), sub: "équipements", icon: "activity", bg: "bg-green-50", fg: "text-green-600" },
        { label: "Matériels à problème", value: cnt((i) => BAD_ETATS.includes(i.Etat)), sub: "à surveiller", icon: "alert-triangle", bg: "bg-amber-50", fg: "text-amber-600" },
        { label: "Pays couverts", value: pays.length, sub: pays.join(" · ") || "—", icon: "globe", bg: "bg-purple-50", fg: "text-purple-600" },
      ];
    },

    // ---------- graphiques ----------
    categoryDist() {
      const b = this.base(); const counts = {};
      b.forEach((i) => { const c = i.Categorie || "Autre"; counts[c] = (counts[c] || 0) + 1; });
      const total = b.length || 1;
      return Object.entries(counts).sort((a, b) => b[1] - a[1])
        .map(([label, count], idx) => ({ label, count, pct: Math.round((count / total) * 100), color: CAT_COLORS[idx % CAT_COLORS.length] }));
    },
    donutTotal() { return this.base().length; },
    // Donut CSS (conic-gradient) avec angles EXACTS basés sur les comptes (aucun trou d'arrondi).
    donutStyle() {
      const dist = this.categoryDist();
      const total = dist.reduce((s, c) => s + c.count, 0);
      if (!total) return "background:#e2e8f0";
      let acc = 0; const stops = [];
      dist.forEach((c) => {
        const s = (acc / total) * 360;
        acc += c.count;
        const e = (acc / total) * 360;
        stops.push(`${c.color} ${s}deg ${e}deg`);
      });
      return `background: conic-gradient(${stops.join(",")})`;
    },
    siteDist() {
      const b = this.base(); const counts = {};
      b.forEach((i) => { const s = i.Site || "—"; counts[s] = (counts[s] || 0) + 1; });
      const total = b.length || 1;
      return Object.entries(counts).sort((a, b) => b[1] - a[1])
        .map(([label, count]) => ({ label, count, pct: Math.round((count / total) * 100) }));
    },

    // ---------- alertes & attributions ----------
    alerts() { return this.base().filter((i) => BAD_ETATS.includes(i.Etat)); },
    recentAttributions() {
      return this.items.filter((i) => i.Statut === "Attribué")
        .sort((a, b) => (b._created || "").localeCompare(a._created || "")).slice(0, 6);
    },
    initials(name) {
      if (!name) return "?";
      const parts = name.replace(/\(.*?\)/g, "").trim().split(/\s+/).filter(Boolean);
      return ((parts[0] || "")[0] || "" + (parts[1] ? parts[1][0] : "")).toUpperCase() + (parts[1] ? parts[1][0].toUpperCase() : "");
    },
    avatarColor(name) { let h = 0; for (const c of (name || "")) h = (h + c.charCodeAt(0)) % AVATAR_COLORS.length; return AVATAR_COLORS[h]; },
    fmtDate(iso) {
      if (!iso) return "";
      const d = new Date(iso);
      if (isNaN(d)) return "";
      const p = (n) => String(n).padStart(2, "0");
      return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
    },

    // ---------- vue Utilisateurs ----------
    userGroups() {
      const g = {};
      this.base().forEach((i) => { const u = i.Utilisateur || "— Non attribué"; (g[u] = g[u] || []).push(i); });
      return Object.entries(g).sort((a, b) => b[1].length - a[1].length)
        .map(([user, list]) => ({ user, count: list.length, sites: [...new Set(list.map((x) => x.Site).filter(Boolean))].join(", "), cats: [...new Set(list.map((x) => x.Categorie).filter(Boolean))].join(", ") }));
    },

    // ---------- icônes & badges ----------
    catIcon(c) {
      return { "Ordinateur": "laptop", "Tablette": "tablet", "Téléphone": "smartphone", "Écran": "monitor", "Imprimante": "printer", "Clé WiFi": "wifi", "Carte mémoire": "memory-stick", "Serveur": "server", "Réseau": "router", "Onduleur": "battery-charging", "Accessoire": "cable" }[c] || "package";
    },
    statutClass(s) { return { "Attribué": "bg-blue-50 text-blue-700", "En stock": "bg-emerald-50 text-emerald-700", "Réformé": "bg-slate-100 text-slate-500" }[s] || "bg-slate-100 text-slate-600"; },
    statutDot(s) { return { "Attribué": "bg-blue-500", "En stock": "bg-emerald-500", "Réformé": "bg-slate-400" }[s] || "bg-slate-400"; },
    etatClass(e) {
      return { "En cours d'utilisation": "bg-emerald-50 text-emerald-700", "Fonctionne": "bg-emerald-50 text-emerald-700", "En réparation": "bg-amber-50 text-amber-700", "Endommagé": "bg-red-50 text-red-700", "Perdu": "bg-red-50 text-red-700", "Hors service": "bg-slate-100 text-slate-500" }[e] || "bg-slate-100 text-slate-600";
    },
    etatDot(e) {
      return { "En cours d'utilisation": "bg-emerald-500", "Fonctionne": "bg-emerald-500", "En réparation": "bg-amber-500", "Endommagé": "bg-red-500", "Perdu": "bg-red-500", "Hors service": "bg-slate-400" }[e] || "bg-slate-400";
    },

    // ---------- CRUD ----------
    openCreate() { this.editing = null; this.form = {}; this.cfg.fields.forEach((f) => (this.form[f.internal] = "")); this.modalOpen = true; },
    openEdit(it) {
      this.editing = it; this.form = {};
      this.cfg.fields.forEach((f) => { let v = it[f.internal] ?? ""; if (f.type === "dateTime" && v) v = (v + "").slice(0, 10); this.form[f.internal] = v; });
      this.modalOpen = true;
    },
    payload() {
      const p = {};
      this.cfg.fields.forEach((f) => {
        let v = this.form[f.internal];
        if (v === "" || v === null || v === undefined) return;
        if (f.type === "number" || f.type === "currency") v = parseFloat(v);
        if (f.type === "dateTime") v = new Date(v + "T00:00:00").toISOString();
        p[f.internal] = v;
      });
      return p;
    },
    async save() {
      this.saving = true;
      try {
        const body = JSON.stringify(this.payload());
        let r;
        if (this.editing) r = await fetch("/api/materiels/" + this.editing.id, { method: "PUT", headers: this.headers(), body });
        else r = await fetch("/api/materiels", { method: "POST", headers: this.headers(), body });
        if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || ("Erreur " + r.status)); }
        this.modalOpen = false;
        this.toast(this.editing ? "Matériel mis à jour" : "Matériel ajouté");
        await this.load();
      } catch (e) { this.toast(e.message, "error"); }
      finally { this.saving = false; }
    },
    // ---------- attribution rapide ----------
    openAssign(it) {
      this.assignTarget = it;
      this.assignForm = { Utilisateur: it.Utilisateur || "", Site: it.Site || "", Etat: "En cours d'utilisation" };
      this.refreshIcons();
    },
    async confirmAssign() {
      if (!this.assignForm.Utilisateur.trim()) { this.toast("Indiquez à qui attribuer le matériel", "error"); return; }
      this.saving = true;
      try {
        const body = JSON.stringify({
          Statut: "Attribué",
          Utilisateur: this.assignForm.Utilisateur.trim(),
          Site: this.assignForm.Site,
          Etat: this.assignForm.Etat,
        });
        const r = await fetch("/api/materiels/" + this.assignTarget.id, { method: "PUT", headers: this.headers(), body });
        if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || ("Erreur " + r.status)); }
        this.toast("Attribué à " + this.assignForm.Utilisateur.trim());
        this.assignTarget = null;
        await this.load();
      } catch (e) { this.toast(e.message, "error"); }
      finally { this.saving = false; }
    },

    // ---------- ajout multiple ----------
    emptyBulkRow(prev) {
      return {
        Categorie: prev ? prev.Categorie : "",
        Marque: "", Modele: "", NumeroSerie: "",
        Quantite: 1,
        Etat: prev ? prev.Etat : "En cours d'utilisation",
        Statut: prev ? prev.Statut : "En stock",
        Utilisateur: "",
        Site: prev ? prev.Site : "",
      };
    },
    openBulk() { this.bulkRows = [this.emptyBulkRow()]; this.bulkOpen = true; this.refreshIcons(); },
    addBulkRow() { this.bulkRows.push(this.emptyBulkRow(this.bulkRows[this.bulkRows.length - 1])); this.refreshIcons(); },
    removeBulkRow(i) { this.bulkRows.splice(i, 1); if (!this.bulkRows.length) this.bulkRows = [this.emptyBulkRow()]; this.refreshIcons(); },
    bulkValidCount() { return this.bulkRows.filter((r) => (r.Categorie || "").toString().trim() && (r.Marque || "").toString().trim()).length; },
    async saveBulk() {
      const rows = this.bulkRows
        .filter((r) => (r.Categorie || "").toString().trim() && (r.Marque || "").toString().trim())
        .map((r) => {
          const o = {};
          ["Categorie", "Marque", "Modele", "NumeroSerie", "Etat", "Statut", "Utilisateur", "Site"].forEach((k) => {
            if ((r[k] || "").toString().trim()) o[k] = r[k];
          });
          if (r.Quantite !== "" && r.Quantite != null) o.Quantite = parseFloat(r.Quantite);
          return o;
        });
      if (!rows.length) { this.toast("Renseignez au moins Catégorie et Marque sur une ligne", "error"); return; }
      this.bulkSaving = true;
      try {
        const r = await fetch("/api/materiels/bulk", { method: "POST", headers: this.headers(), body: JSON.stringify(rows) });
        if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || ("Erreur " + r.status)); }
        const res = await r.json();
        if (res.errors && res.errors.length) this.toast(`${res.created} ajouté(s), ${res.errors.length} erreur(s)`, res.created ? "ok" : "error");
        else this.toast(`${res.created} matériel(s) ajouté(s)`);
        this.bulkOpen = false;
        await this.load();
      } catch (e) { this.toast(e.message, "error"); }
      finally { this.bulkSaving = false; }
    },

    // ---------- pagination (vue Parc) ----------
    pageCount() { return Math.max(1, Math.ceil(this.filtered().length / this.perPage)); },
    paged() {
      const p = Math.min(this.page, this.pageCount());
      return this.filtered().slice((p - 1) * this.perPage, p * this.perPage);
    },
    goPage(n) { this.page = Math.min(Math.max(1, n), this.pageCount()); this.refreshIcons(); },

    // ---------- import de fichier (Excel/CSV) ----------
    openImport() { this.importFile = null; this.importSite = ""; this.importResult = null; this.importOpen = true; this.refreshIcons(); },
    onImportFile(e) { this.importFile = e.target.files[0] || null; this.importResult = null; },
    async sendImport(dryRun) {
      if (!this.importFile) { this.toast("Choisissez un fichier", "error"); return; }
      this.importBusy = true;
      try {
        const fd = new FormData();
        fd.append("file", this.importFile);
        fd.append("site", this.importSite);
        fd.append("dry_run", dryRun ? "true" : "false");
        const h = {};
        if (this.cfg.password_required && this.password) h["X-App-Password"] = this.password;
        const r = await fetch("/api/import", { method: "POST", headers: h, body: fd });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || ("Erreur " + r.status));
        if (dryRun) { this.importResult = d; this.refreshIcons(); }
        else {
          this.toast(`${d.created} matériel(s) importé(s)` + (d.errors && d.errors.length ? `, ${d.errors.length} erreur(s)` : ""));
          this.importOpen = false;
          await this.load();
        }
      } catch (e) { this.toast(e.message, "error"); }
      finally { this.importBusy = false; }
    },

    askDelete(it) { this.deleteTarget = it; },
    async confirmDelete() {
      this.saving = true;
      try {
        const r = await fetch("/api/materiels/" + this.deleteTarget.id, { method: "DELETE", headers: this.headers() });
        if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || ("Erreur " + r.status)); }
        this.toast("Matériel supprimé"); this.deleteTarget = null; await this.load();
      } catch (e) { this.toast(e.message, "error"); }
      finally { this.saving = false; }
    },

    // ---------- export ----------
    exportCsv() {
      const rows = this.filtered();
      if (rows.length === 0) { this.toast("Rien à exporter", "error"); return; }
      const cols = this.cfg.fields.map((f) => f.internal);
      const head = this.cfg.fields.map((f) => '"' + f.label + '"').join(";");
      const lines = rows.map((r) => cols.map((c) => '"' + ((r[c] ?? "") + "").replace(/"/g, '""') + '"').join(";"));
      const csv = "﻿" + [head, ...lines].join("\r\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "suivi_materiel_vpmi.csv"; a.click();
    },

    // ---------- toasts ----------
    toast(msg, type = "ok") {
      const id = Math.random().toString(36).slice(2);
      this.toasts.push({ id, msg, type }); this.refreshIcons();
      setTimeout(() => { this.toasts = this.toasts.filter((t) => t.id !== id); }, 3500);
    },
  };
}
