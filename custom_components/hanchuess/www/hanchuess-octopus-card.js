// Hanchuess Octopus (Electricity Price Strategy) card (issue #74).
//
//   type: custom:hanchuess-octopus-card
//   sn: YOUR_INVERTER_SN
//
// Mirrors the Hanchu app's Electricity Price Strategy screen, built on the
// integration's Octopus entities. Changes are staged and sent by the Save
// button.

// Same version query as this file, so an update fetches the new shared code.
const {
  HanchuessStrategyCardBase,
  HanchuessStrategyCardEditor,
  findInverters,
  registerStrategyCard,
  esc,
  _t,
} = await import(
  new URL(`./hanchuess-strategy-common.js${new URL(import.meta.url).search}`, import.meta.url).href
);

const POINT = "Point settings";
const PRICE = "Price settings";
const PRICE_UNIT = "p/kWh";

// The two Point-settings windows and the switch each one is turned on by.
const WINDOWS = [
  { window: "00:00-08:00", label: "00:00 - 08:00", hint: "00:00–08:00", switchKey: "octopus_charge", slotsKey: "octopus_charge_slots_0000_0800" },
  { window: "12:00-19:00", label: "12:00 - 19:00", hint: "12:00–19:00", switchKey: "octopus_discharge", slotsKey: "octopus_charge_slots_1200_1900" },
];

// In Price settings the same two switches turn the price strategies on.
const PRICES = [
  { labelKey: "charging_price", switchKey: "octopus_charge", priceKey: "octopus_charge_price" },
  { labelKey: "discharge_price", switchKey: "octopus_discharge", priceKey: "octopus_discharge_price" },
];

class HanchuessOctopusCardEditor extends HanchuessStrategyCardEditor {}

class HanchuessOctopusCard extends HanchuessStrategyCardBase {
  static getConfigElement() {
    return document.createElement("hanchuess-octopus-card-editor");
  }

  static getStubConfig(hass) {
    const first = findInverters(hass)[0];
    return { sn: first ? first.sn : "" };
  }

  get requiredKeys() {
    return [
      "octopus_strategy",
      "octopus_schema_type",
      "octopus_charge",
      "octopus_discharge",
      "octopus_charge_slots_0000_0800",
      "octopus_charge_slots_1200_1900",
      "octopus_charge_price",
      "octopus_discharge_price",
      "octopus_postcode",
      "strategy_priority",
      "save_octopus_strategy",
      "pending_changes",
    ];
  }

  get saveKey() {
    return "save_octopus_strategy";
  }

  get pendingAttr() {
    return "octopus_strategy";
  }

  get titleKey() {
    return "octopus_title";
  }

  // The schema type as shown (staged or saved); the switches' applies_to
  // attribute follows the same value.
  _schemaType() {
    const st = this._st("octopus_schema_type");
    return st ? st.state : null;
  }

  _renderPoint() {
    const t = (k, v) => _t(this._hass, k, v);
    return WINDOWS.map(({ label, hint, switchKey, slotsKey }) => {
      const on = (this._st(switchKey) || {}).state === "on";
      const slots = parseFloat(this._numberValue(slotsKey, 1));
      const hours = Number.isFinite(slots) ? (slots / 2).toFixed(1) : "–";
      return `
        <div class="window">
          <div class="row">
            <div class="label">${esc(t("low_tariffs", { window: label }))}</div>
            ${this._switch(switchKey)}
          </div>
          <div class="row ${on ? "" : "off"}">
            <div class="label sub">${esc(on ? t("slots_hint", { hours, window: hint }) : t("window_off"))}</div>
            ${this._number(slotsKey, { min: 0, max: 10, step: 1 })}
          </div>
        </div>`;
    }).join("");
  }

  _renderPrice() {
    const t = (k) => _t(this._hass, k);
    return PRICES.map(({ labelKey, switchKey, priceKey }) => {
      const on = (this._st(switchKey) || {}).state === "on";
      return `
        <div class="window">
          <div class="row">
            <div class="label">${esc(t(labelKey))}</div>
            ${this._switch(switchKey)}
          </div>
          <div class="row ${on ? "" : "off"}">
            <div class="label"></div>
            ${this._number(priceKey, { min: 0, max: 50, step: 0.01, unit: PRICE_UNIT })}
          </div>
        </div>`;
    }).join("");
  }

  _renderBody() {
    const t = (k, v) => _t(this._hass, k, v);
    const type = this._schemaType();
    let modeRows;
    if (type === POINT) modeRows = this._renderPoint();
    else if (type === PRICE) modeRows = this._renderPrice();
    else modeRows = `<div class="sub">${esc(t("schema_unknown"))}</div>`;

    return `
      <div class="section">
        <div class="row">
          <div class="label">${esc(t("octopus_switch"))}</div>
          ${this._switch("octopus_strategy")}
        </div>
      </div>

      <div class="section">
        <div class="row">
          <div class="label">${esc(t("schema_type"))}</div>
          ${this._select("octopus_schema_type")}
        </div>
      </div>

      <div class="section">${modeRows}</div>

      <div class="section">
        <div class="row">
          <div class="label">${esc(t("country"))}</div>
          <span class="muted">GB</span>
        </div>
        <div class="row">
          <div class="label">${esc(t("postcode"))}<div class="sub">${esc(t("postcode_hint"))}</div></div>
          ${this._text("octopus_postcode")}
        </div>
      </div>

      ${this._renderPriority()}`;
  }

  _renderNote() {
    return `<div class="note">${esc(_t(this._hass, "effective_note"))}</div>`;
  }
}

registerStrategyCard({
  type: "hanchuess-octopus-card",
  cardClass: HanchuessOctopusCard,
  editorClass: HanchuessOctopusCardEditor,
  nameKey: "octopus_title",
  descKey: "octopus_desc",
});
