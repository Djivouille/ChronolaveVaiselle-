const DOMAIN = "chronolavevaiselle";
const CARD_TAG = "chronolavevaiselle-card";
const EDITOR_TAG = "chronolavevaiselle-card-editor";

const DEFAULT_CONFIG = {
  show_status: true,
  show_last_empty: true,
  show_counters: true,
  show_empty_buttons: true,
};

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (char) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])
  );

const formatMinutes = (minutes) => {
  const total = Math.max(0, Math.round(Number(minutes) || 0));
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  if (hours > 0) {
    return `${hours} h ${String(mins).padStart(2, "0")} min`;
  }
  return `${mins} min`;
};

const formatTime = (iso, hass) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  const language = hass?.locale?.language || navigator.language || "fr";
  return date.toLocaleTimeString(language, { hour: "2-digit", minute: "2-digit" });
};

const formatDateTime = (iso, hass) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  const language = hass?.locale?.language || navigator.language || "fr";
  return date.toLocaleString(language, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

class ChronolaveVaiselleCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement(EDITOR_TAG);
  }

  static getStubConfig(hass) {
    let entity = "";
    if (hass && hass.entities) {
      for (const [entityId, entry] of Object.entries(hass.entities)) {
        if (
          entry.platform === DOMAIN &&
          entityId.startsWith("sensor.") &&
          entry.translation_key === "remaining_time"
        ) {
          entity = entityId;
          break;
        }
      }
    }
    return { entity, ...DEFAULT_CONFIG };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Veuillez sélectionner le capteur « Temps restant » de l'intégration.");
    }
    this._config = { ...DEFAULT_CONFIG, ...config };
  }

  getCardSize() {
    return 3;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  get hass() {
    return this._hass;
  }

  _resolveEntities() {
    const hass = this._hass;
    const config = this._config;
    const main = hass.states[config.entity] || null;
    const registry = hass.entities || {};
    const mainEntry = registry[config.entity];
    const result = {
      main,
      pending: null,
      lastActor: null,
      lastEmpty: null,
      counters: [],
    };
    if (!mainEntry || !mainEntry.device_id) {
      return result;
    }
    for (const [entityId, entry] of Object.entries(registry)) {
      if (
        entry.device_id !== mainEntry.device_id ||
        entry.platform !== DOMAIN ||
        entityId === config.entity
      ) {
        continue;
      }
      const state = hass.states[entityId];
      if (!state) {
        continue;
      }
      if (entry.translation_key === "dishes_pending") {
        result.pending = state;
      } else if (entry.translation_key === "last_actor") {
        result.lastActor = state;
      } else if (entry.translation_key === "last_empty") {
        result.lastEmpty = state;
      } else if (entityId.startsWith("sensor.")) {
        result.counters.push({
          entity: entityId,
          person: entry.original_name || state.attributes.friendly_name || entityId,
          state,
        });
      }
    }
    result.counters.sort((a, b) => a.person.localeCompare(b.person));
    return result;
  }

  _statusHtml(entities) {
    const { main, pending } = entities;
    if (pending && pending.state === "on") {
      return `<div class="status pending"><ha-icon icon="mdi:dishwasher-alert"></ha-icon><span>Vaisselle à ranger !</span></div>`;
    }
    if (main && main.attributes && main.attributes.running) {
      const remaining = formatMinutes(main.state);
      const end = main.attributes.cycle_end
        ? ` — fin à ${formatTime(main.attributes.cycle_end, this._hass)}`
        : "";
      return `<div class="status running"><ha-icon icon="mdi:dishwasher"></ha-icon><span>Lavage en cours : encore <strong>${remaining}</strong>${escapeHtml(end)}</span></div>`;
    }
    return `<div class="status idle"><ha-icon icon="mdi:dishwasher"></ha-icon><span>Lave-vaisselle prêt</span></div>`;
  }

  _emptyPerson(person) {
    this._hass.callService(DOMAIN, "empty", { person });
  }

  _render() {
    if (!this._hass || !this._config) {
      return;
    }
    const entities = this._resolveEntities();
    const title = this._config.name || entities.main?.attributes.friendly_name || "Lave-vaisselle";
    const parts = [];
    parts.push(`<ha-card header="${escapeHtml(title)}">`);
    if (!entities.main) {
      parts.push(`<div class="status idle"><span>Capteur introuvable : ${escapeHtml(this._config.entity)}</span></div>`);
    } else {
      if (this._config.show_status) {
        parts.push(this._statusHtml(entities));
      }
      if (this._config.show_last_empty && (entities.lastActor || entities.lastEmpty)) {
        const actor = entities.lastActor && entities.lastActor.state !== "unknown" && entities.lastActor.state !== "unavailable"
          ? escapeHtml(entities.lastActor.state)
          : "—";
        const when = entities.lastEmpty && entities.lastEmpty.state !== "unknown" && entities.lastEmpty.state !== "unavailable"
          ? escapeHtml(formatDateTime(entities.lastEmpty.state, this._hass))
          : "—";
        parts.push(`<div class="last-empty">Dernier vidage par <strong>${actor}</strong> le ${when}</div>`);
      }
      if (this._config.show_counters && entities.counters.length > 0) {
        parts.push(`<div class="counters">`);
        for (const counter of entities.counters) {
          const count = counter.state.state;
          const button = this._config.show_empty_buttons
            ? `<button class="empty-btn" data-person="${escapeHtml(counter.person)}">J'ai vidé</button>`
            : "";
          parts.push(
            `<div class="counter"><span class="person">${escapeHtml(counter.person)}</span><span class="count">${escapeHtml(count)}</span>${button}</div>`
          );
        }
        parts.push(`</div>`);
      }
    }
    parts.push(`</ha-card>`);
    this.innerHTML = parts.join("");
    for (const button of this.querySelectorAll(".empty-btn")) {
      button.addEventListener("click", () => this._emptyPerson(button.dataset.person));
    }
  }

  static get styles() {
    return `
      ha-card { padding: 16px; height: 100%; box-sizing: border-box; }
      .status { display: flex; align-items: center; gap: 8px; font-size: 16px; margin-bottom: 8px; }
      .status ha-icon { --mdc-icon-size: 28px; }
      .status.pending { color: var(--warning-color, #f4b400); font-weight: 600; }
      .status.running { color: var(--primary-color); }
      .status.idle { color: var(--secondary-text-color); }
      .last-empty { color: var(--secondary-text-color); font-size: 13px; margin-bottom: 8px; }
      .counters { display: flex; flex-direction: column; gap: 6px; }
      .counter { display: flex; align-items: center; gap: 8px; }
      .counter .person { flex: 1; }
      .counter .count { font-weight: 700; min-width: 2ch; text-align: right; }
      .empty-btn {
        border: none; border-radius: 12px; padding: 4px 12px; cursor: pointer;
        background: var(--primary-color); color: var(--text-primary-color, #fff); font-size: 12px;
      }
      .empty-btn:hover { filter: brightness(1.1); }
    `;
  }
}

const styleElement = document.createElement("style");
styleElement.textContent = ChronolaveVaiselleCard.styles;
document.head.appendChild(styleElement);

class ChronolaveVaiselleCardEditor extends HTMLElement {
  constructor() {
    super();
    this._shadow = this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    this._renderEditor();
  }

  get hass() {
    return this._hass;
  }

  setConfig(config) {
    this._config = config;
    this._renderEditor();
  }

  _schema() {
    return [
      { name: "name", label: "Titre de la carte", selector: { text: {} } },
      {
        name: "entity",
        label: "Capteur « Temps restant »",
        required: true,
        selector: { entity: { domain: "sensor", integration: DOMAIN } },
      },
      { name: "show_status", label: "Afficher le statut", type: "boolean", default: true },
      { name: "show_last_empty", label: "Afficher le dernier vidage", type: "boolean", default: true },
      { name: "show_counters", label: "Afficher les compteurs par personne", type: "boolean", default: true },
      { name: "show_empty_buttons", label: "Afficher les boutons « J'ai vidé »", type: "boolean", default: true },
    ];
  }

  _renderEditor() {
    if (!this._hass || !this._config) {
      return;
    }
    this._shadow.innerHTML = "";
    const form = document.createElement("ha-form");
    form.hass = this._hass;
    form.schema = this._schema();
    form.data = { ...DEFAULT_CONFIG, ...this._config };
    form.addEventListener("value-changed", (event) => {
      event.stopPropagation();
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: { ...this._config, ...event.detail.value } },
          bubbles: true,
          composed: true,
        })
      );
    });
    this._shadow.appendChild(form);
  }
}

customElements.define(CARD_TAG, ChronolaveVaiselleCard);
customElements.define(EDITOR_TAG, ChronolaveVaiselleCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: `custom:${CARD_TAG}`,
  name: "ChronolaveVaiselle",
  preview: true,
  description:
    "Carte du lave-vaisselle : temps restant, vaisselle à ranger, dernier vidage et compteurs par personne avec boutons de vidage.",
});
