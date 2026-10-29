const STORAGE_KEY = "snipatlas-admin-sections";

function readOpenSections() {
  try {
    return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]"));
  } catch {
    return new Set();
  }
}

function saveOpenSections(sections) {
  const open = sections.filter((section) => section.open).map((section) => section.dataset.section);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(open));
  } catch {}
}

function restoreSections() {
  const sections = [...document.querySelectorAll(".snipatlas-section")];
  const open = readOpenSections();
  for (const section of sections) {
    section.open = open.has(section.dataset.section);
    section.addEventListener("toggle", () => saveOpenSections(sections));
  }
}

restoreSections();
