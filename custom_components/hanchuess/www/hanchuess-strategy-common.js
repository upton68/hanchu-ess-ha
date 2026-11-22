// Shared code for the Weather Optimize and Octopus cards (issue #74).
//
// Imported by hanchuess-weather-card.js and hanchuess-octopus-card.js; it is
// not a Lovelace resource itself. The cards never call the strategy
// endpoints: they read entity states from `hass` and change them through the
// normal entity services, so the integration's staging and Save logic stays
// the only way settings reach the cloud.

// ===== i18n =====
export const HANCHUESS_STRATEGY_I18N = {
  en: {
    // common
    inverter: "Inverter",
    select_inverter: "Select inverter",
    no_sn: "Pick the inverter in the card editor.",
    sn_not_found: "Inverter {sn} was not found. Check the card's sn, or that the Hanchuess integration is set up for it.",
    lookup_failed: "Could not look up the strategy entities: ",
    loading: "Loading...",
    disabled_entities: "These entities are disabled. Enable them on the Hanchuess {sn} device (Settings → Devices & services → Hanchuess) and they will show here:",
    unavailable: "These settings are unavailable. If this strategy has never been saved, open it in the Hanchu app and save it once.",
    unsaved_one: "1 unsaved change",
    unsaved_other: "{n} unsaved changes",
    save: "Save",
    saving: "Saving...",
    saved: "Saved",
    save_failed: "Save failed: ",
    change_failed: "Change failed: ",
    out_of_range: "Enter a value from {min} to {max}",
    unknown_error: "Unknown error",
    strategy_priority: "Strategy Priority",
    priority_hint: "When strategies overlap, give priority to which",
    opt_octopus: "Octopus",
    "opt_weather optimize": "Weather Optimize",
    // weather
    weather_title: "Weather Optimize",
    weather_desc: "Weather Optimize strategy, as in the Hanchu app",
    weather_optimize: "Weather Optimize",
    charge_time: "Charge time",
    charge_start: "Start",
    charge_end: "End",
    next_day: "+1",
    next_day_title: "Ends on the next day",
    soc_title: "Day 2 weather and SOC limits for battery charging (%)",
    soc_off_hint: "Turn on Weather Optimize to change these.",
    band_sunny: "Sunny",
    band_few_clouds: "Few Clouds",
    band_partly_cloudy: "Partly Clouds",
    band_mostly_cloudy: "Mostly Clouds",
    band_heavy_clouds: "Heavy Cloud",
    band_light_rain: "Light Rain",
    band_moderate_rain: "Moderate Rain",
    band_heavy_rain: "Heavy Rain",
    band_heavy_snow: "Heavy Snow",
    band_haze_dust: "Haze/Dust",
    band_other_weather: "Other Weather",
    // octopus
    octopus_title: "Electricity Price Strategy",
    octopus_desc: "Octopus Electricity Price Strategy, as in the Hanchu app",
    octopus_switch: "Octopus Settings Switch",
    schema_type: "Schema Type",
    "opt_point settings": "Point settings",
    "opt_price settings": "Price settings",
    low_tariffs: "Quantity of low tariffs [{window}]",
    slots_hint: "Finds the {hours} hours with the lowest price in {window}",
    window_off: "Window off",
    charging_price: "Charging Price",
    discharge_price: "Discharge Price",
    country: "Country",
    postcode: "Postcode",
    postcode_hint: "Octopus charging can take effect only after the postcode information is filled in",
    schema_unknown: "Choose a schema type to see its settings.",
    effective_note: "Settings saved before 22:00 apply from the next day (00:00-23:59). Settings saved after 22:00 apply from the day after tomorrow.",
  },
  "zh-Hans": {
    inverter: "逆变器",
    select_inverter: "请选择逆变器",
    no_sn: "请在卡片编辑器中选择逆变器。",
    sn_not_found: "未找到逆变器 {sn}。请检查卡片的 sn，或确认已为其配置 Hanchuess 集成。",
    lookup_failed: "无法查找策略实体：",
    loading: "加载中...",
    disabled_entities: "以下实体已禁用。请在 Hanchuess {sn} 设备上启用它们（设置 → 设备与服务 → Hanchuess），之后会在此显示：",
    unavailable: "这些设置不可用。如果从未保存过该策略，请先在 Hanchu App 中打开并保存一次。",
    unsaved_one: "1 项未保存的更改",
    unsaved_other: "{n} 项未保存的更改",
    save: "保存",
    saving: "保存中...",
    saved: "已保存",
    save_failed: "保存失败：",
    change_failed: "修改失败：",
    out_of_range: "请输入 {min} 到 {max} 之间的数值",
    unknown_error: "未知错误",
    strategy_priority: "策略优先级",
    priority_hint: "当策略重叠时，优先执行哪一个",
    opt_octopus: "Octopus",
    "opt_weather optimize": "天气优化",
    weather_title: "天气优化",
    weather_desc: "天气优化策略，与 Hanchu App 一致",
    weather_optimize: "天气优化",
    charge_time: "充电时间",
    charge_start: "开始",
    charge_end: "结束",
    next_day: "+1",
    next_day_title: "次日结束",
    soc_title: "次日天气与电池充电 SOC 上限 (%)",
    soc_off_hint: "开启天气优化后才能修改。",
    band_sunny: "晴",
    band_few_clouds: "少云",
    band_partly_cloudy: "部分多云",
    band_mostly_cloudy: "多云",
    band_heavy_clouds: "阴",
    band_light_rain: "小雨",
    band_moderate_rain: "中雨",
    band_heavy_rain: "大雨",
    band_heavy_snow: "大雪",
    band_haze_dust: "雾霾/沙尘",
    band_other_weather: "其他天气",
    octopus_title: "电价策略",
    octopus_desc: "Octopus 电价策略，与 Hanchu App 一致",
    octopus_switch: "Octopus 设置开关",
    schema_type: "方案类型",
    "opt_point settings": "时段设置",
    "opt_price settings": "电价设置",
    low_tariffs: "低电价时段数量 [{window}]",
    slots_hint: "在 {window} 内寻找电价最低的 {hours} 小时",
    window_off: "时段已关闭",
    charging_price: "充电电价",
    discharge_price: "放电电价",
    country: "国家",
    postcode: "邮编",
    postcode_hint: "填写邮编信息后，Octopus 充电才能生效",
    schema_unknown: "请选择方案类型以查看其设置。",
    effective_note: "22:00 前保存的设置从次日（00:00-23:59）起生效；22:00 后保存的设置从后天起生效。",
  },
};

function _hassLang(hass) {
  const lang = (hass && hass.language) || "en";
  return lang.startsWith("zh") ? "zh-Hans" : "en";
}

export function _t(hass, key, vars) {
  const lang = _hassLang(hass);
  let text =
    (HANCHUESS_STRATEGY_I18N[lang] && HANCHUESS_STRATEGY_I18N[lang][key]) ||
    HANCHUESS_STRATEGY_I18N.en[key] ||
    key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.split(`{${name}}`).join(String(value));
    }
  }
  return text;
}

export function esc(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Entity names as the integration creates them, for the "disabled" list, so
// they can be found on the device page.
export const ENTITY_NAMES = {
  weather_optimize: "Weather Optimize",
  weather_charge_start: "Weather Charge Start",
  weather_charge_end: "Weather Charge End",
  weather_soc_sunny: "Weather SOC Sunny",
  weather_soc_few_clouds: "Weather SOC Few Clouds",
  weather_soc_partly_cloudy: "Weather SOC Partly Cloudy",
  weather_soc_mostly_cloudy: "Weather SOC Mostly Cloudy",
  weather_soc_heavy_clouds: "Weather SOC Heavy Clouds",
  weather_soc_light_rain: "Weather SOC Light Rain",
  weather_soc_moderate_rain: "Weather SOC Moderate Rain",
  weather_soc_heavy_rain: "Weather SOC Heavy Rain",
  weather_soc_heavy_snow: "Weather SOC Heavy Snow",
  weather_soc_haze_dust: "Weather SOC Haze/Dust",
  weather_soc_other_weather: "Weather SOC Other Weather",
  octopus_strategy: "Octopus Strategy",
  octopus_schema_type: "Octopus Schema Type",
  octopus_charge: "Octopus Switch 00:00-08:00 / Charge Price",
  octopus_discharge: "Octopus Switch 12:00-19:00 / Discharge Price",
  octopus_charge_slots_0000_0800: "Octopus Charge Slots 00:00-08:00",
  octopus_charge_slots_1200_1900: "Octopus Charge Slots 12:00-19:00",
  octopus_charge_price: "Octopus Charge Price",
  octopus_discharge_price: "Octopus Discharge Price",
  octopus_postcode: "Octopus Postcode",
  strategy_priority: "Strategy Priority",
  save_weather_optimize: "Save Weather Optimize",
  save_octopus_strategy: "Save Octopus Strategy",
  pending_changes: "Pending Changes",
};

// ===== inverter discovery (editor, stub config) =====
// As the energy card: the Device Status sensor carries the inverter's sn.
export function findInverters(hass) {
  const seen = new Map();
  if (!hass || !hass.states) return [];
  for (const [entityId, state] of Object.entries(hass.states)) {
    if (!entityId.startsWith("sensor.") || !entityId.includes("device_status")) continue;
    let sn = state.attributes && state.attributes.sn ? String(state.attributes.sn) : "";
    if (!sn) {
      const m = entityId.match(/hanchuess_(.+?)_device_status/);
      if (m) sn = m[1].toUpperCase();
    }
    if (!sn || seen.has(sn)) continue;
    const name = String((state.attributes && state.attributes.friendly_name) || sn)
      .replace(/ [Dd]evice [Ss]tatus| 设备状态/g, "");
    seen.set(sn, { sn, name });
  }
  return [...seen.values()];
}

// ===== editor =====
export class HanchuessStrategyCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = Object.assign({ sn: "" }, config || {});
    this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    const inverters = findInverters(this._hass);
    const current = this._config.sn || "";
    if (current && !inverters.some((inv) => inv.sn === current)) {
      inverters.unshift({ sn: current, name: current });
    }
    this.innerHTML = `
      <div style="padding: 16px;">
        <label style="font-weight:500;display:block;margin-bottom:8px;">${esc(_t(this._hass, "inverter"))}</label>
        <select id="sn_select" style="width:100%;padding:8px;border:1px solid var(--divider-color,#ccc);border-radius:4px;background:var(--card-background-color);color:var(--primary-text-color);">
          <option value="">${esc(_t(this._hass, "select_inverter"))}</option>
          ${inverters
            .map(
              (inv) =>
                `<option value="${esc(inv.sn)}" ${inv.sn === current ? "selected" : ""}>${esc(inv.name)}${inv.name.includes(inv.sn) ? "" : ` (${esc(inv.sn)})`}</option>`
            )
            .join("")}
        </select>
      </div>`;
    this.querySelector("#sn_select").addEventListener("change", (ev) => {
      this._config = { ...this._config, sn: ev.target.value };
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: this._config },
          bubbles: true,
          composed: true,
        })
      );
    });
  }
}

// ===== styles =====
const STYLES = `
  :host { display: block; }
  ha-card { padding: 16px; color: var(--primary-text-color); }
  .header { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .title { font-size: 18px; font-weight: 500; }
  .sn { font-size: 13px; color: var(--secondary-text-color); margin: 2px 0 12px; }
  .badge {
    font-size: 12px; padding: 2px 10px; border-radius: 12px;
    background: var(--warning-color, #ff9800); color: var(--text-primary-color, #fff);
    white-space: nowrap;
  }
  .banner {
    border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; font-size: 14px; line-height: 1.4;
    border-left: 4px solid var(--info-color, #039be5);
    background: rgba(3, 155, 229, 0.1);
  }
  .banner.warning { border-left-color: var(--warning-color, #ff9800); background: rgba(255, 152, 0, 0.12); }
  .banner.error { border-left-color: var(--error-color, #db4437); background: rgba(219, 68, 55, 0.1); }
  .banner ul { margin: 6px 0 0; padding-left: 20px; }
  .section { border-top: 1px solid var(--divider-color); padding: 12px 0; }
  .section-title { font-size: 14px; font-weight: 500; margin-bottom: 8px; }
  .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 40px; }
  .row + .row { margin-top: 6px; }
  .row .label { flex: 1; font-size: 14px; min-width: 0; }
  .sub { font-size: 12px; color: var(--secondary-text-color); margin-top: 2px; line-height: 1.4; }
  .muted { color: var(--secondary-text-color); }
  .off { opacity: 0.5; }
  input, select {
    font: inherit; font-size: 14px; padding: 6px 8px; box-sizing: border-box;
    border: 1px solid var(--divider-color); border-radius: 4px;
    background: var(--card-background-color, var(--ha-card-background));
    color: var(--primary-text-color);
  }
  input:disabled, select:disabled { color: var(--disabled-text-color, #9e9e9e); cursor: not-allowed; }
  input[type="number"] { width: 90px; text-align: right; }
  input[type="time"] { width: 120px; }
  input[type="text"] { width: 140px; }
  select { min-width: 150px; max-width: 100%; }
  .unit { font-size: 13px; color: var(--secondary-text-color); margin-left: 4px; }
  .field { display: inline-flex; align-items: center; white-space: nowrap; }
  .times { display: flex; gap: 16px; flex-wrap: wrap; }
  .times .field label { font-size: 13px; color: var(--secondary-text-color); margin-right: 6px; }
  .next-day {
    font-size: 11px; font-weight: 600; margin-left: 4px; padding: 1px 5px; border-radius: 8px;
    background: var(--primary-color); color: var(--text-primary-color, #fff);
  }
  .soc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); gap: 8px 16px; }
  .soc-grid .field { justify-content: space-between; gap: 8px; }
  .soc-grid .field span.name { font-size: 13px; white-space: normal; }
  .soc-grid input[type="number"] { width: 64px; }
  .window { border: 1px solid var(--divider-color); border-radius: 6px; padding: 10px 12px; }
  .window + .window { margin-top: 8px; }
  .toggle { position: relative; display: inline-block; width: 40px; height: 22px; flex-shrink: 0; }
  .toggle input { opacity: 0; width: 0; height: 0; margin: 0; }
  .toggle .slider {
    position: absolute; inset: 0; cursor: pointer; border-radius: 22px;
    background: var(--switch-unchecked-track-color, #bdbdbd); transition: background 0.2s;
  }
  .toggle .slider:before {
    content: ""; position: absolute; height: 16px; width: 16px; left: 3px; top: 3px;
    border-radius: 50%; background: var(--switch-unchecked-button-color, #fff); transition: transform 0.2s;
  }
  .toggle input:checked + .slider { background: var(--switch-checked-track-color, var(--primary-color)); }
  .toggle input:checked + .slider:before { transform: translateX(18px); background: var(--switch-checked-button-color, #fff); }
  .toggle input:disabled + .slider { cursor: not-allowed; opacity: 0.5; }
  .toggle input:focus-visible + .slider { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .footer { border-top: 1px solid var(--divider-color); padding-top: 12px; }
  .save-row { display: flex; align-items: center; justify-content: flex-end; gap: 12px; flex-wrap: wrap; }
  .status { font-size: 13px; flex: 1; min-width: 0; }
  .status.error { color: var(--error-color, #db4437); }
  .status.success { color: var(--success-color, #43a047); }
  .btn-save {
    font: inherit; font-size: 14px; font-weight: 500; padding: 8px 24px; border-radius: 4px; cursor: pointer;
    border: 1px solid var(--primary-color); background: transparent; color: var(--primary-color);
  }
  .btn-save.has-changes { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
  .note { font-size: 12px; color: var(--secondary-text-color); margin-top: 10px; line-height: 1.4; }
  @media (max-width: 420px) {
    ha-card { padding: 12px; }
    input[type="text"] { width: 110px; }
    select { min-width: 120px; }
  }
`;

// Inputs whose value is typed: don't re-render under the user while they have focus.
const TYPED_INPUTS = new Set(["number", "text", "time"]);

// ===== base card =====
// Subclasses set:
//   get requiredKeys()  keys (from hanchuess/strategy_entities) the card uses
//   get saveKey(), pendingAttr(), titleKey()
//   _renderBody()       HTML for the settings, using the control helpers
//   _renderNote()       optional HTML under the Save button
export class HanchuessStrategyCardBase extends HTMLElement {
  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this._config = Object.assign({ sn: "" }, config);
    this._map = null;
    this._mapError = null;
    this._mapFor = null;
    this._mapAt = 0;
    this._sig = null;
    this._ensureRoot();
    if (this._hass) {
      this._loadMap();
      this._maybeRender();
    }
  }

  set hass(hass) {
    this._hass = hass;
    this._loadMap();
    this._maybeRender();
  }

  getCardSize() {
    return 8;
  }

  // ---------- entity map ----------

  _ensureRoot() {
    if (this.shadowRoot) return;
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    this.shadowRoot.addEventListener("click", (ev) => {
      const target = ev.target.closest && ev.target.closest("[data-action='save']");
      if (target) this._save();
    });
    this.shadowRoot.addEventListener("focusout", () => {
      // Let focus settle on the next element first.
      setTimeout(() => {
        if (this._deferred) this._maybeRender();
      }, 0);
    });
  }

  _missingKeys() {
    if (!this._map) return [];
    return this.requiredKeys.filter((key) => !this._map[key] || this._map[key].disabled);
  }

  async _loadMap() {
    const sn = this._config && this._config.sn;
    if (!sn || !this._hass || this._loading) return;
    if (this._mapFor === sn && (this._map || this._mapError)) {
      // Entities enabled since the last look-up appear after the integration
      // reloads, so look again now and then while some are missing.
      const stale = this._map && this._missingKeys().length && Date.now() - this._mapAt > 30000;
      if (!stale) return;
    }
    this._loading = true;
    try {
      const result = await this._hass.callWS({ type: "hanchuess/strategy_entities", sn });
      this._map = (result && result.entities) || {};
      this._mapError = null;
    } catch (err) {
      this._map = null;
      this._mapError = err && err.code === "not_found" ? "not_found" : this._errText(err);
    } finally {
      this._mapFor = sn;
      this._mapAt = Date.now();
      this._loading = false;
      this._sig = null;
      this._maybeRender();
    }
  }

  _eid(key) {
    const item = this._map && this._map[key];
    return item && !item.disabled ? item.entity_id : null;
  }

  _st(key) {
    const eid = this._eid(key);
    return eid && this._hass ? this._hass.states[eid] : undefined;
  }

  _usable(key) {
    const st = this._st(key);
    return !!st && st.state !== "unavailable";
  }

  _pending() {
    const st = this._st("pending_changes");
    const n = st && st.attributes ? Number(st.attributes[this.pendingAttr]) : 0;
    return Number.isFinite(n) ? n : 0;
  }

  // ---------- rendering ----------

  _signature() {
    const parts = [
      this._hass && this._hass.language,
      this._config && this._config.sn,
      JSON.stringify(this._map),
      this._mapError,
      this._saving ? 1 : 0,
      this._status ? `${this._status.type}:${this._status.text}` : "",
      this._pending(),
    ];
    for (const key of this.requiredKeys) {
      const st = this._st(key);
      parts.push(st ? `${st.state}|${(st.attributes && st.attributes.applies_to) || ""}|${JSON.stringify((st.attributes && st.attributes.options) || "")}` : "-");
    }
    return parts.join("\u0001");
  }

  _maybeRender(force) {
    if (!this._hass || !this._config) return;
    this._ensureRoot();
    const active = this.shadowRoot.activeElement;
    if (active && active.tagName === "INPUT" && TYPED_INPUTS.has(active.type)) {
      this._deferred = true;
      return;
    }
    this._deferred = false;
    const sig = this._signature();
    if (!force && sig === this._sig) return;
    this._sig = sig;
    this.shadowRoot.innerHTML = `<style>${STYLES}</style><ha-card>${this._renderCard()}</ha-card>`;
  }

  _renderCard() {
    const t = (k, v) => _t(this._hass, k, v);
    const sn = this._config.sn;
    const pending = this._pending();
    const header = `
      <div class="header">
        <div class="title">${esc(t(this.titleKey))}</div>
        ${pending > 0 ? `<span class="badge">${esc(pending === 1 ? t("unsaved_one") : t("unsaved_other", { n: pending }))}</span>` : ""}
      </div>
      ${sn ? `<div class="sn">${esc(sn)}</div>` : ""}`;

    if (!sn) return header + `<div class="banner">${esc(t("no_sn"))}</div>`;
    if (this._mapError === "not_found") {
      return header + `<div class="banner error">${esc(t("sn_not_found", { sn }))}</div>`;
    }
    if (this._mapError) {
      return header + `<div class="banner error">${esc(t("lookup_failed") + this._mapError)}</div>`;
    }
    if (!this._map) return header + `<div class="banner">${esc(t("loading"))}</div>`;

    let html = header;
    const missing = this._missingKeys();
    if (missing.length) {
      html += `<div class="banner warning">${esc(t("disabled_entities", { sn }))}<ul>${missing
        .map((key) => `<li>${esc(ENTITY_NAMES[key] || key)}</li>`)
        .join("")}</ul></div>`;
    }
    // A strategy never saved in the app reads back empty, and all its
    // entities are unavailable.
    const states = this.requiredKeys
      .filter((key) => key !== "pending_changes")
      .map((key) => this._st(key))
      .filter(Boolean);
    if (!states.length) return html;
    if (states.every((st) => st.state === "unavailable")) {
      return html + `<div class="banner warning">${esc(t("unavailable"))}</div>`;
    }

    html += this._renderBody();
    html += this._renderFooter();
    return html;
  }

  _renderFooter() {
    const t = (k, v) => _t(this._hass, k, v);
    const pending = this._pending();
    const canSave = this._usable(this.saveKey) && !this._saving;
    const status = this._status
      ? `<span class="status ${esc(this._status.type)}">${esc(this._status.text)}</span>`
      : `<span class="status"></span>`;
    return `
      <div class="footer">
        <div class="save-row">
          ${status}
          <button class="btn-save ${pending > 0 ? "has-changes" : ""}" data-action="save" ${canSave ? "" : "disabled"}>
            ${esc(this._saving ? t("saving") : t("save"))}
          </button>
        </div>
        ${this._renderNote ? this._renderNote() : ""}
      </div>`;
  }

  // ---------- control helpers ----------

  _locked(key, extraDisabled) {
    return !this._usable(key) || this._saving || !!extraDisabled;
  }

  _switch(key, { disabled } = {}) {
    const st = this._st(key);
    const on = st && st.state === "on";
    return `<label class="toggle"><input type="checkbox" data-key="${esc(key)}" data-ctl="switch" ${on ? "checked" : ""} ${this._locked(key, disabled) ? "disabled" : ""}><span class="slider"></span></label>`;
  }

  _numberValue(key, step) {
    const st = this._st(key);
    if (!st) return "";
    const n = parseFloat(st.state);
    if (!Number.isFinite(n)) return "";
    return step >= 1 ? String(Math.round(n)) : String(Math.round(n * 100) / 100);
  }

  _number(key, { min = 0, max = 100, step = 1, unit = "", disabled } = {}) {
    const st = this._st(key);
    const attrs = (st && st.attributes) || {};
    const lo = attrs.min != null ? attrs.min : min;
    const hi = attrs.max != null ? attrs.max : max;
    const stp = attrs.step != null ? attrs.step : step;
    return `<span class="field"><input type="number" inputmode="decimal" data-key="${esc(key)}" data-ctl="number" min="${esc(lo)}" max="${esc(hi)}" step="${esc(stp)}" value="${esc(this._numberValue(key, stp))}" ${this._locked(key, disabled) ? "disabled" : ""}>${unit ? `<span class="unit">${esc(unit)}</span>` : ""}</span>`;
  }

  _timeValue(key) {
    const st = this._st(key);
    if (!st || !/^\d{1,2}:\d{2}/.test(st.state)) return "";
    const [h, m] = st.state.split(":");
    return `${h.padStart(2, "0")}:${m}`;
  }

  _time(key, { disabled } = {}) {
    return `<input type="time" data-key="${esc(key)}" data-ctl="time" value="${esc(this._timeValue(key))}" ${this._locked(key, disabled) ? "disabled" : ""}>`;
  }

  _select(key, { disabled } = {}) {
    const st = this._st(key);
    const options = (st && st.attributes && st.attributes.options) || [];
    const current = st ? st.state : "";
    const known = options.includes(current);
    return `<select data-key="${esc(key)}" data-ctl="select" ${this._locked(key, disabled) ? "disabled" : ""}>
      ${known ? "" : `<option value="" selected></option>`}
      ${options
        .map((opt) => `<option value="${esc(opt)}" ${opt === current ? "selected" : ""}>${esc(this._optionLabel(opt))}</option>`)
        .join("")}
    </select>`;
  }

  _optionLabel(option) {
    const key = `opt_${String(option).toLowerCase()}`;
    const label = _t(this._hass, key);
    return label === key ? option : label;
  }

  _text(key, { disabled } = {}) {
    const st = this._st(key);
    const attrs = (st && st.attributes) || {};
    const value = st && st.state !== "unknown" && st.state !== "unavailable" ? st.state : "";
    return `<input type="text" data-key="${esc(key)}" data-ctl="text" value="${esc(value)}" ${attrs.max ? `maxlength="${esc(attrs.max)}"` : ""} ${this._locked(key, disabled) ? "disabled" : ""}>`;
  }

  _renderPriority() {
    const t = (k) => _t(this._hass, k);
    return `
      <div class="section">
        <div class="row">
          <div class="label">${esc(t("strategy_priority"))}<div class="sub">${esc(t("priority_hint"))}</div></div>
          ${this._select("strategy_priority")}
        </div>
      </div>`;
  }

  // ---------- actions ----------

  _errText(err) {
    if (!err) return _t(this._hass, "unknown_error");
    return err.message || err.error || (typeof err === "string" ? err : _t(this._hass, "unknown_error"));
  }

  _setStatus(type, text, clearAfterMs) {
    clearTimeout(this._statusTimer);
    this._status = text ? { type, text } : null;
    if (clearAfterMs) {
      this._statusTimer = setTimeout(() => {
        this._status = null;
        this._maybeRender();
      }, clearAfterMs);
    }
    this._maybeRender();
  }

  async _onChange(ev) {
    const el = ev.target;
    const key = el && el.dataset ? el.dataset.key : null;
    const entityId = key ? this._eid(key) : null;
    if (!entityId) return;
    const ctl = el.dataset.ctl;
    if (ctl === "switch" || ctl === "select") el.blur();
    try {
      if (ctl === "switch") {
        await this._hass.callService("switch", el.checked ? "turn_on" : "turn_off", { entity_id: entityId });
      } else if (ctl === "number") {
        const value = parseFloat(el.value);
        const min = parseFloat(el.min);
        const max = parseFloat(el.max);
        if (!Number.isFinite(value) || value < min || value > max) {
          throw new Error(_t(this._hass, "out_of_range", { min, max }));
        }
        await this._hass.callService("number", "set_value", { entity_id: entityId, value });
      } else if (ctl === "time") {
        if (!el.value) return;
        const time = el.value.length === 5 ? `${el.value}:00` : el.value;
        await this._hass.callService("time", "set_value", { entity_id: entityId, time });
      } else if (ctl === "select") {
        if (!el.value) return;
        await this._hass.callService("select", "select_option", { entity_id: entityId, option: el.value });
      } else if (ctl === "text") {
        await this._hass.callService("text", "set_value", { entity_id: entityId, value: el.value.trim() });
      }
      if (this._status && this._status.type === "error") this._setStatus(null, null);
    } catch (err) {
      // Show the entity's real value again.
      this._sig = null;
      el.blur();
      this._setStatus("error", _t(this._hass, "change_failed") + this._errText(err));
    }
  }

  async _save() {
    const entityId = this._eid(this.saveKey);
    if (!entityId || this._saving) return;
    this._saving = true;
    this._setStatus(null, null);
    try {
      // Fails with the integration's error when the save fails; the changes
      // then stay staged.
      await this._hass.callService("button", "press", { entity_id: entityId });
      this._saving = false;
      this._setStatus("success", _t(this._hass, "saved"), 3000);
    } catch (err) {
      this._saving = false;
      this._setStatus("error", _t(this._hass, "save_failed") + this._errText(err));
    }
  }
}

export function registerStrategyCard({ type, cardClass, editorClass, nameKey, descKey }) {
  if (!customElements.get(`${type}-editor`)) customElements.define(`${type}-editor`, editorClass);
  if (!customElements.get(type)) customElements.define(type, cardClass);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === type)) {
    window.customCards.push({
      type,
      name: HANCHUESS_STRATEGY_I18N.en[nameKey],
      description: HANCHUESS_STRATEGY_I18N.en[descKey],
      preview: false,
    });
  }
}
