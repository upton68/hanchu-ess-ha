// Hanchuess Weather Optimize card (issue #74).
//
//   type: custom:hanchuess-weather-card
//   sn: YOUR_INVERTER_SN
//
// Mirrors the Hanchu app's Weather Optimize screen, built on the integration's
// Weather Optimize entities. Changes are staged and sent by the Save button.

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

// The app's order.
const WEATHER_BANDS = [
  "sunny",
  "few_clouds",
  "partly_cloudy",
  "mostly_cloudy",
  "heavy_clouds",
  "light_rain",
  "moderate_rain",
  "heavy_rain",
  "heavy_snow",
  "haze_dust",
  "other_weather",
];

class HanchuessWeatherCardEditor extends HanchuessStrategyCardEditor {}

class HanchuessWeatherCard extends HanchuessStrategyCardBase {
  static getConfigElement() {
    return document.createElement("hanchuess-weather-card-editor");
  }

  static getStubConfig(hass) {
    const first = findInverters(hass)[0];
    return { sn: first ? first.sn : "" };
  }

  get requiredKeys() {
    return [
      "weather_optimize",
      "weather_charge_start",
      "weather_charge_end",
      ...WEATHER_BANDS.map((band) => `weather_soc_${band}`),
      "strategy_priority",
      "save_weather_optimize",
      "pending_changes",
    ];
  }

  get saveKey() {
    return "save_weather_optimize";
  }

  get pendingAttr() {
    return "weather_optimize";
  }

  get titleKey() {
    return "weather_title";
  }

  _renderBody() {
    const t = (k, v) => _t(this._hass, k, v);
    const enabled = (this._st("weather_optimize") || {}).state === "on";
    const start = this._timeValue("weather_charge_start");
    const end = this._timeValue("weather_charge_end");
    const nextDay = start && end && end < start;

    return `
      <div class="section">
        <div class="row">
          <div class="label">${esc(t("weather_optimize"))}</div>
          ${this._switch("weather_optimize")}
        </div>
      </div>

      <div class="section">
        <div class="section-title">${esc(t("charge_time"))}</div>
        <div class="times">
          <span class="field"><label>${esc(t("charge_start"))}</label>${this._time("weather_charge_start")}</span>
          <span class="field"><label>${esc(t("charge_end"))}</label>${this._time("weather_charge_end")}${
            nextDay ? `<span class="next-day" title="${esc(t("next_day_title"))}">${esc(t("next_day"))}</span>` : ""
          }</span>
        </div>
      </div>

      <div class="section ${enabled ? "" : "off"}">
        <div class="section-title">${esc(t("soc_title"))}</div>
        ${enabled ? "" : `<div class="sub" style="margin-bottom:8px">${esc(t("soc_off_hint"))}</div>`}
        <div class="soc-grid">
          ${WEATHER_BANDS.map(
            (band) => `
            <span class="field">
              <span class="name">${esc(t(`band_${band}`))}</span>
              ${this._number(`weather_soc_${band}`, { min: 0, max: 100, step: 1, unit: "%", disabled: !enabled })}
            </span>`
          ).join("")}
        </div>
      </div>

      ${this._renderPriority()}`;
  }
}

registerStrategyCard({
  type: "hanchuess-weather-card",
  cardClass: HanchuessWeatherCard,
  editorClass: HanchuessWeatherCardEditor,
  nameKey: "weather_title",
  descKey: "weather_desc",
});
