// ===== icons =====
const HANCHUESS_ICONS = {
  charging: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAACE4AAAhOAFFljFgAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAOdEVYdFNvZnR3YXJlAEZpZ21hnrGWYwAAAqlJREFUeAHtmk9y0zAUxj/FKcMyRwg3iE+Au2QYUjgB4QicgHAC4ATACdKU6RrfwL5BzQnwkhkahOTOtE5tSe/Jkrrpb+FF/GT7WZ/eHznAIw+LAJdqtwCy1/QBWY38ZY1I8B2o91dq2JIzBFKcIn9VIgIzlnV1uWI/fGR4DuCaIZ1bmlhvX8NzQIjnYDMrERG6A9VuqY4FuEj5HRFhzEBWgE9U+WjoDghxBjZx5dPdgW4qC3CJLB8NzYHqR6GOC/CILh8NcQb+eYTP+PLp7kKyEuDrP4F8NO5SQodPkV2BR4PV+hkSQJgBn/CZRj7dnZwWAm/BJZF8NHYJ6dJZZL/BI5l8NHP7aR/5yBbVxYZg2AInqld40WACdgd8og/ESo37SrP926jDpNlyrAGP7JsYswMpmhd5coqJWGbAq3mhI/F+qv41Zge8mhciUn5Bvv6MAIw74Nu80GhUbbVFIAxRyKt5odB0us/XLQJhkFCk6BNI930MDogSoZHyo3rz5wgMf2OrT32hE9aGYFmq8mJyyBxjjkloqTnfgdb9O+PZm3rr090lsefMlL8DXZspl067btFada9b1U1vwC91IDvA3JnrQ2gzIyza+/g74Cr0AiYrG34OuOukJmSysuG5Bg6F5WTwZGXDzwGbfEy672ZttEA83m/SNVi13w7NRD0WnfgO2OqkLlmdGSLIQTU64gPcFMquGP48+4aR6OSxBox1UqkefovE8B0Y3+S1J6uI8CTUfeCTQx27k5XicA75tBz+fq02zuTPu2up8IsnI+H3z2hQYK6BEflQk1X+Rj/A8CGqnb5u/5eWk/yYn5juRZ9EycoGcw0c9QlNqmRlgy6h4+ItabKy4VdKJCjSqNBnQH9tqS5zJZtF4C8vrXohvRA8j/a3hEdi8B9eFcj5fjk7/gAAAABJRU5ErkJggg==",
  discharging: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAACE4AAAhOAFFljFgAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAOdEVYdFNvZnR3YXJlAEZpZ21hnrGWYwAAApVJREFUeAHtmUGO0zAUhv/nVDDseoSZDVK74gaEE5QbMJVatoQTMNwgM+xAo8ANOEJuQDeoy+YGdDkLEmNXIxRo4vg5tmcW/TatGrfqH//2/54DnHhYCEyKXTZt7vDadnydYPP2eb5BINgCbrfvdhLynPMdCfFqPctLBEBwBn/+mb3g/vnQsASQaKyt06IKdfc1PAGgl2BCgkoExFpAsc3OlZtTMGka+oaAWAtogBR8gtpHYy1ASrkAk9D20TDWwOOzj8ZKwJdtlqoVPAWP4PbRWAkgyd8+Y9hHYyeAiO3/GPbRDJYSevus0ezAo1rNbi4QgcEZcNk+Y9lHMyhA1T5vwCSWfTRGCxU/sml91vwCj2j20UxMF+unv1NmuaRX/P52m10ODZMS+4SwWc7yCiOYmP9LslAWAgspdcldDI5Tc1+r2VLvRs3W0O1N8cjpFRCjeUlUp4aR9ApwbF6sUcXh+7H+1/QLcGherJG4Xs8/5fBApwDX5sWSKnkmruCJTgFNuMVbad8vL/I9PNEpQKJJEQIpvPi+TacAgijhGZUmH1fz/Ds8wz7YaqMOuQq11V4Oj6RyNbsevWV2wawTjkgtxijf0xKBcBag20yboDssWs++b+MswKbN9BVWJtwFDLWZHsPKhJMAizrJa1iZcBJAVKeGy97DysQEDhCJBfr6BB1W82Pf61kbUyCSFJuuHGELuD+lSLuu6bBa94RVIqBshw9whBL5Vb0c/TbbQv11EpXr2c0VIsMW0HPIGzSsTLAsdDiloGMf24SVOFPTfzeixnqCzk2BJaDrlOIQVvPhsLrflbzvTLxHTOqU4p8PIoWVCe4aSFvvo4WVCWsB/xVvUcPKhFstFKCzioJO08PTmhMn/vIHrIXuDUaICMIAAAAASUVORK5CYII=",
};

// ===== i18n =====
const HANCHUESS_I18N = {
  en: {
    device: "Device",
    select_device: "Select device",
    energy_settings: "Energy Setup",
    quick_charge: "Quick Charge/Discharge",
    mode: "Mode",
    charge: "Charging",
    discharge: "Discharging",
    stop: "Stop",
    duration_min: "Duration(min)",
    confirm: "Confirm",
    cancel: "Cancel",
    work_mode: "Work Mode",
    please_select: "Please select",
    load_data: "Load",
    submit: "Set",
    offline: "Device offline, cannot configure",
    loading: "Loading...",
    load_success: "Data loaded",
    load_fail: "Load failed: ",
    submitting: "Submitting...",
    submit_success: "Set successfully",
    submit_fail: "Set failed: ",
    no_change: "No changes",
    unknown_error: "Unknown error",
    duration_range: "Duration must be 1~1440 min",
    time_overlap: "Charging and discharging time slots overlap, please check",
    time_overlap_hint: "Union not allowed between time periods",
    remain_charging: "Remaining charging time",
    remain_discharging: "Remaining discharging time",
    cmd_sent: "Command sent",
    fail_prefix: "Failed: ",
    stopping: "Stopping...",
    stopped: "Stopped",
    apply: "Apply",
    fast_charging: "Charging",
    fast_discharging: "Discharging",
    quick_tip: "To ensure optimal performance and safety, please do not change any control settings or perform OTA updates during fast charging or discharging.",
    card_name: "Hanchuess Remote Settings",
    card_desc: "Hanchuess device remote settings card",
    select_time: "Select Time",
    select_start_time: "Select Start Time",
    select_end_time: "Select End Time",
    hour_label: "Hour (00-23)",
    minute_label: "Minute (00-59)",
  },
  "zh-Hans": {
    device: "设备",
    select_device: "请选择设备",
    energy_settings: "储能设置",
    quick_charge: "快速充放电",
    mode: "模式",
    charge: "充电",
    discharge: "放电",
    stop: "停止",
    duration_min: "时长(分)",
    confirm: "确认",
    cancel: "取消",
    work_mode: "工作模式",
    please_select: "请选择",
    load_data: "获取数据",
    submit: "设定",
    offline: "设备离线，无法设置",
    loading: "加载中...",
    load_success: "数据加载成功",
    load_fail: "加载失败: ",
    submitting: "提交中...",
    submit_success: "设定成功",
    submit_fail: "设定失败: ",
    no_change: "没有修改",
    unknown_error: "未知错误",
    duration_range: "时长需在 1~1440 分钟之间",
    time_overlap: "充电与放电时间段存在重叠，请检查",
    time_overlap_hint: "时间段之间不允许合并",
    remain_charging: "剩余充电时间",
    remain_discharging: "剩余放电时间",
    cmd_sent: "指令已发送",
    fail_prefix: "失败: ",
    stopping: "停止中...",
    stopped: "已停止",
    apply: "是否应用",
    fast_charging: "充电中",
    fast_discharging: "放电中",
    quick_tip: "为确保最佳性能和安全，快速充放电期间请勿修改任何控制设置或执行OTA升级。",
    card_name: "Hanchuess 远程设置",
    card_desc: "Hanchuess 设备远程设置卡片",
    select_time: "选择时间",
    select_start_time: "选择开始时间",
    select_end_time: "选择结束时间",
    hour_label: "小时 (00-23)",
    minute_label: "分钟 (00-59)",
  },
};


function _hassLang(hass) {
  const lang = (hass && hass.language) || "en";
  return lang.startsWith("zh") ? "zh-Hans" : "en";
}

function _t(hass, key) {
  const lang = _hassLang(hass);
  return (HANCHUESS_I18N[lang] && HANCHUESS_I18N[lang][key]) || HANCHUESS_I18N["en"][key] || key;
}

// ===== Card Editor =====
class HanchuessEnergyCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = Object.assign({ entity: "", sn: "" }, config || {});
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;

    const entities = Object.keys(this._hass.states)
      .filter(eid => eid.startsWith("sensor.") && eid.includes("device_status") && eid.includes("hanchuess"));

    this.innerHTML = `
      <div style="padding: 16px;">
        <label style="font-weight:500;display:block;margin-bottom:8px;">${_t(this._hass, 'device')}</label>
        <select id="entity_select" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:4px;">
          <option value="">${_t(this._hass, 'select_device')}</option>
          ${entities.map(eid => {
            const state = this._hass.states[eid];
            const name = (state.attributes.friendly_name || eid).replace(/ [Dd]evice [Ss]tatus| 设备状态/g, "");
            const selected = this._config.entity === eid ? "selected" : "";
            return `<option value="${eid}" ${selected}>${name}</option>`;
          }).join("")}
        </select>
      </div>
    `;

    this.querySelector("#entity_select").addEventListener("change", (e) => {
      const entityId = e.target.value;
      const state = this._hass.states[entityId];
      let sn = "";
      if (state && state.attributes) sn = state.attributes.sn || "";
      if (!sn) {
        const m = entityId.match(/hanchuess_(.+?)_device_status/);
        if (m) sn = m[1].toUpperCase();
      }

      this._config = { ...this._config, entity: entityId, sn: sn };
      this.dispatchEvent(new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }));
    });
  }
}
customElements.define("hanchuess-energy-card-editor", HanchuessEnergyCardEditor);

// ===== Card =====
class HanchuessEnergyCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._rendered && this._config && this._config.entity) {
      this._render();
      this._rendered = true;
    }
    if (this._rendered) this._updateStatus();
  }

  setConfig(config) {
    this._config = Object.assign({ entity: "", sn: "" }, config || {});
    this._rendered = false;
    this._originalValues = {};
    this._dataLoaded = false;
    this._localStartTime = 0;
    this._localFastStatus = 0;
    this._localRemainSec = 0;
    this._localCountdown = null;
    this._forceStopped = false;
  }

  static getConfigElement() {
    return document.createElement("hanchuess-energy-card-editor");
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states)
      .find(eid => eid.startsWith("sensor.") && eid.includes("device_status") && eid.includes("hanchuess")) || "";
    const state = hass.states[entity];
    let sn = state && state.attributes ? (state.attributes.sn || "") : "";
    if (!sn) {
      const m = entity.match(/hanchuess_(.+?)_device_status/);
      if (m) sn = m[1].toUpperCase();
    }
    return { entity, sn };
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { padding: 16px; }
        .sn-bar { font-size: 16px; font-weight: 500; margin-bottom: 16px; color: var(--primary-color); }
        .quick-section { border: 1px solid var(--divider-color); border-radius: 6px; padding: 12px; margin-bottom: 16px; }
        .quick-title { font-size: 14px; font-weight: 500; margin-bottom: 10px; color: var(--primary-color); }
        .quick-tip {
          font-size: 10px; color: #262626; padding: 8px;
          background: #ffddb5; border-radius: 12px; margin-bottom: 20px;
          line-height: 1.4;
        }
        .quick-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .quick-row label { min-width: 60px; font-size: 13px; color: var(--secondary-text-color); white-space: nowrap; }
        .quick-row select, .quick-row input {
          flex: 1; padding: 8px; border: 1px solid var(--divider-color);
          border-radius: 4px; background: var(--card-background-color);
          color: var(--primary-text-color); font-size: 14px; box-sizing: border-box;
        }
        .quick-btns { display: flex; gap: 8px; justify-content: flex-end; }
        .quick-status { font-size: 12px; margin-top: 6px; text-align: center; }
        .quick-status.error { color: var(--error-color); }
        .quick-status.success { color: var(--success-color, #4caf50); }
        .quick-running {
          border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;
          display: none; flex-direction: column; gap: 10px;
        }
        .quick-running .running-top {
          display: flex; align-items: center; justify-content: space-between;
        }
        .quick-running .stop-row {
          display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
          padding: 6px 14px; border-radius: 20px;
          background: rgba(0, 188, 212, 0.12);
          border: 1px solid transparent;
          transition: background 0.2s, border-color 0.2s;
        }
        .quick-running .stop-row:hover {
          background: transparent;
          border-color: #00bcd4;
        }
        .quick-running .stop-row .stop-icon {
          width: 16px; height: 16px; flex-shrink: 0;
        }
        .quick-running .stop-row .stop-label {
          font-size: 13px; font-weight: 500; color: #00bcd4; white-space: nowrap;
        }
        .quick-running .status-badge {
          display: flex; align-items: center; gap: 6px;
        }
        .quick-running .status-badge img {
          width: 24px; height: 24px;
        }
        .quick-running .status-badge .status-text {
          font-size: 13px; font-weight: 500; color: #00bcd4;
        }
        .quick-running .remain-info {
          font-size: 13px; color: var(--secondary-text-color);
        }
        .quick-running .remain-time {
          font-size: 22px; font-weight: 700; color: var(--primary-color);
        }
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .title { font-size: 18px; font-weight: 500; }
        .header-btns { display: flex; gap: 8px; }
        .btn {
          padding: 6px 16px; border: none; border-radius: 4px;
          font-size: 13px; cursor: pointer; white-space: nowrap;
        }
        .btn-load { background: var(--primary-color); color: white; }
        .btn-submit { background: var(--primary-color); color: white; }
        .btn:hover { opacity: 0.9; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .offline-banner {
          background: var(--error-color, #db4437); color: white; padding: 8px 12px;
          border-radius: 4px; margin-bottom: 12px; text-align: center; font-size: 14px;
        }
        .field { margin-bottom: 12px; }
        .field label { display: block; font-size: 13px; color: var(--secondary-text-color); margin-bottom: 4px; }
        .field select, .field input {
          width: 100%; padding: 8px; border: 1px solid var(--divider-color);
          border-radius: 4px; background: var(--card-background-color);
          color: var(--primary-text-color); font-size: 14px; box-sizing: border-box;
        }
        .field input::placeholder { color: var(--secondary-text-color); opacity: 0.6; }
        .time-row { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
        .time-row input { width: 60px; padding: 6px; border: 1px solid var(--divider-color); border-radius: 4px; background: var(--card-background-color); color: var(--primary-text-color); font-size: 14px; text-align: center; box-sizing: border-box; cursor: pointer; }
        .time-row span { color: var(--secondary-text-color); }
        .time-row .time-label { font-size: 13px; color: var(--secondary-text-color); min-width: 60px; }
        .time-overlap-hint { font-size: 12px; color: var(--error-color, #db4437); margin-top: 2px; padding-left: 2px; }
        /* 自定义时间选择器样式 */
        .time-picker-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0,0,0,0.5);
          z-index: 1000;
          display: none;
        }
        .time-picker-dialog {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: var(--card-background-color);
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.2);
          z-index: 1001;
          width: 240px;
        }
        .time-picker-header {
          font-size: 15px;
          font-weight: 500;
          margin-bottom: 12px;
          text-align: center;
          color: var(--primary-text-color);
        }
        .time-picker-selects {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
        }
        .time-picker-column {
          height: 180px;
          overflow-y: auto;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          width: 60px;
          scroll-behavior: smooth;
        }
        .time-picker-column::-webkit-scrollbar {
          width: 4px;
        }
        .time-picker-column::-webkit-scrollbar-thumb {
          background: var(--divider-color);
          border-radius: 2px;
        }
        .time-picker-item {
          padding: 4px 0;
          text-align: center;
          font-size: 14px;
          cursor: pointer;
          color: var(--primary-text-color);
          transition: background 0.15s;
        }
        .time-picker-item:hover {
          background: var(--primary-color, #03a9f4);
          color: #fff;
        }
        .time-picker-item.selected {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          font-weight: 500;
        }
        .time-picker-separator {
          font-size: 18px;
          font-weight: 500;
          color: var(--primary-text-color);
          line-height: 180px;
        }
        .time-picker-buttons {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          margin-top: 14px;
        }
        .time-picker-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
        }
        .time-picker-btn.confirm {
          background: var(--primary-color);
          color: white;
        }
        .time-picker-btn.cancel {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .icon-btn {
          background: none; border: none; cursor: pointer; font-size: 18px; padding: 4px;
          color: var(--secondary-text-color); line-height: 1;
        }
        .icon-btn:hover { color: var(--primary-text-color); }
        .icon-btn.add { color: var(--primary-color); font-size: 20px; }
        .icon-btn.del { color: var(--error-color, #db4437); }
        .dynamic-field { display: none; }
        .dynamic-field.visible { display: block; }
        .status { font-size: 12px; color: var(--secondary-text-color); margin-top: 8px; text-align: center; }
        .status.error { color: var(--error-color); }
        .status.success { color: var(--success-color, #4caf50); }
        .collapse-card { border: 1px solid var(--divider-color); border-radius: 6px; margin-bottom: 10px; overflow: hidden; }
        .collapse-header { display: flex; align-items: center; padding: 10px 12px; user-select: none; gap: 8px; }
        .collapse-arrow { font-size: 10px; transition: transform .2s; color: var(--secondary-text-color); cursor: pointer; }
        .collapse-arrow.open { transform: rotate(90deg); }
        .collapse-title { flex: 1; font-size: 14px; font-weight: 500; cursor: pointer; }
        .collapse-sw-label { font-size: 13px; color: var(--secondary-text-color); white-space: nowrap; }
        .collapse-body { display: none; padding: 0 12px 12px; }
        .collapse-body.open { display: block; }
        .collapse-row { display: flex; align-items: center; margin-bottom: 8px; gap: 8px; }
        .collapse-row label { min-width: 80px; font-size: 13px; color: var(--secondary-text-color); white-space: nowrap; }
        .collapse-row label .req { color: var(--error-color, #db4437); }
        .collapse-row input, .collapse-row select { flex: 1; padding: 8px; border: 1px solid var(--divider-color); border-radius: 4px; background: var(--card-background-color); color: var(--primary-text-color); font-size: 14px; box-sizing: border-box; }
        .toggle { position: relative; width: 40px; height: 22px; flex-shrink: 0; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle .slider { position: absolute; inset: 0; background: var(--divider-color); border-radius: 22px; cursor: pointer; transition: .3s; }
        .toggle .slider::before { content: ''; position: absolute; width: 16px; height: 16px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: .3s; }
        .toggle input:checked + .slider { background: var(--primary-color); }
        .toggle input:checked + .slider::before { transform: translateX(18px); }
      </style>
      <ha-card>
        <div class="sn-bar" id="device_sn"></div>
        <div id="offline_banner" class="offline-banner" style="display:none">${_t(this._hass, 'offline')}</div>

        <!-- 快速充放电 -->
        <div class="quick-section" id="quick_section">
          <div class="quick-title">${_t(this._hass, 'quick_charge')}</div>
          <div class="quick-tip">${_t(this._hass, 'quick_tip')}</div>
          <div class="quick-row">
            <label>${_t(this._hass, 'mode')}</label>
            <select id="quick_mode">
              <option value="2">${_t(this._hass, 'charge')}</option>
              <option value="3">${_t(this._hass, 'discharge')}</option>
            </select>
          </div>
          <div class="quick-row">
            <label>${_t(this._hass, 'duration_min')}</label>
            <input type="number" id="quick_duration" min="1" max="1440" value="30" placeholder="1~1440">
          </div>
          <div class="quick-running" id="quick_running">
            <div class="running-top">
              <div class="stop-row" id="quick_stop_btn">
                <svg class="stop-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="none" stroke="#00bcd4" stroke-width="2"/><rect x="7" y="7" width="10" height="10" rx="1" fill="#00bcd4"/></svg>
                <span class="stop-label" id="quick_stop_label"></span>
              </div>
              <div class="status-badge">
                <img id="quick_status_icon" src="" alt="">
                <span class="status-text" id="quick_remain_label"></span>
              </div>
            </div>
            <div class="remain-info" id="quick_remain_desc"></div>
            <div class="remain-time" id="quick_remain_time"></div>
          </div>
          <div class="quick-btns" id="quick_btns">
            <button class="btn btn-submit" id="quick_confirm">${_t(this._hass, 'confirm')}</button>
          </div>
          <div class="quick-status" id="quick_status"></div>
        </div>

        <!-- 储能设置 -->
        <div class="header">
          <div class="title">${_t(this._hass, 'energy_settings')}</div>
          <div class="header-btns">
            <button class="btn btn-load" id="load_btn">${_t(this._hass, 'load_data')}</button>
            <button class="btn btn-submit" id="submit_btn">${_t(this._hass, 'submit')}</button>
          </div>
        </div>

        <div class="field">
          <label>${_t(this._hass, 'work_mode')}</label>
          <select id="work_mode"><option value="">${_t(this._hass, 'please_select')}</option></select>
        </div>

        <div id="dynamic_fields"></div>

        <div class="status" id="status_msg"></div>
        
        <!-- 自定义时间选择器 -->
        <div class="time-picker-overlay" id="time_picker_overlay"></div>
        <div class="time-picker-dialog" id="time_picker_dialog" style="display:none">
          <div class="time-picker-header" id="time_picker_title">${_t(this._hass, 'select_time')}</div>
          <div class="time-picker-selects">
            <div class="time-picker-column" id="tp_hour">${Array.from({length:24},(_,i)=>`<div class="time-picker-item" data-value="${i}">${String(i).padStart(2,'0')}</div>`).join("")}</div>
            <span class="time-picker-separator">:</span>
            <div class="time-picker-column" id="tp_minute">${Array.from({length:60},(_,i)=>`<div class="time-picker-item" data-value="${i}">${String(i).padStart(2,'0')}</div>`).join("")}</div>
          </div>
          <div class="time-picker-buttons">
            <button class="time-picker-btn cancel" id="time_picker_cancel">${_t(this._hass, 'cancel')}</button>
            <button class="time-picker-btn confirm" id="time_picker_confirm">${_t(this._hass, 'confirm')}</button>
          </div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.getElementById("work_mode").addEventListener("change", (e) => {
      this._toggleFields(e.target.value);
    });

    this.shadowRoot.getElementById("load_btn").addEventListener("click", () => {
      this._loadData();
    });

    this.shadowRoot.getElementById("submit_btn").addEventListener("click", () => {
      this._submit();
    });

    this.shadowRoot.getElementById("quick_confirm").addEventListener("click", () => {
      this._quickChargeDischarge();
    });

    this.shadowRoot.getElementById("quick_stop_btn").addEventListener("click", () => {
      this._quickStop();
    });

    // 时间选择器事件监听
    this.shadowRoot.getElementById("time_picker_overlay").addEventListener("click", () => {
      this._hideTimePicker();
    });

    this.shadowRoot.getElementById("time_picker_cancel").addEventListener("click", () => {
      this._hideTimePicker();
    });

    this.shadowRoot.getElementById("time_picker_confirm").addEventListener("click", () => {
      this._confirmTimePicker();
    });

    // 时间滚轮列表点击事件
    ["tp_hour", "tp_minute"].forEach(id => {
      this.shadowRoot.getElementById(id).addEventListener("click", (e) => {
        const item = e.target.closest(".time-picker-item");
        if (!item) return;
        const col = this.shadowRoot.getElementById(id);
        col.querySelectorAll(".time-picker-item").forEach(i => i.classList.remove("selected"));
        item.classList.add("selected");
      });
    });

    // 时间输入框点击事件
    this.shadowRoot.addEventListener("click", (e) => {
      if (e.target.classList.contains("time-input")) {
        this._showTimePicker(e.target);
      }
    });
  }

  // --- localStorage optimistic state helpers ---
  _fastStateKey() {
    return `hanchuess_fast_${this._config.sn || ""}`;
  }

  _saveFastState(status, remainSec) {
    try {
      localStorage.setItem(this._fastStateKey(), JSON.stringify({
        status,
        remainSec,
        ts: Date.now(),
      }));
    } catch (e) { /* best-effort */ }
  }

  _loadFastState() {
    try {
      const raw = localStorage.getItem(this._fastStateKey());
      if (!raw) return null;
      const obj = JSON.parse(raw);
      // Expire after remainSec + 5min buffer, or if older than 24h
      if (!obj.ts || Date.now() - obj.ts > 86400000) {
        localStorage.removeItem(this._fastStateKey());
        return null;
      }
      // Estimate remaining: elapsed since saved
      const elapsed = Math.floor((Date.now() - obj.ts) / 1000);
      const remain = obj.remainSec - elapsed;
      if (remain <= 0) {
        localStorage.removeItem(this._fastStateKey());
        return null;
      }
      return { status: obj.status, remainSec: remain };
    } catch (e) { return null; }
  }

  _clearFastState() {
    try { localStorage.removeItem(this._fastStateKey()); } catch (e) { /* best-effort */ }
  }

  _updateStatus() {
    if (!this._hass || !this._config || !this._config.entity) return;

    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const snEl = this.shadowRoot.getElementById("device_sn");
    if (snEl) snEl.textContent = "SN: " + (this._config.sn || "");

    const isOnline = state.state === "online";
    const offlineBanner = this.shadowRoot.getElementById("offline_banner");
    const submitBtn = this.shadowRoot.getElementById("submit_btn");
    const loadBtn = this.shadowRoot.getElementById("load_btn");
    if (offlineBanner) offlineBanner.style.display = isOnline ? "none" : "block";
    if (submitBtn) submitBtn.disabled = !isOnline;
    if (loadBtn) loadBtn.disabled = !isOnline;

    const quickConfirm = this.shadowRoot.getElementById("quick_confirm");
    const quickMode = this.shadowRoot.getElementById("quick_mode");
    const quickDuration = this.shadowRoot.getElementById("quick_duration");
    const quickBtns = this.shadowRoot.getElementById("quick_btns");
    const quickRunning = this.shadowRoot.getElementById("quick_running");
    const quickRows = this.shadowRoot.querySelectorAll(".quick-row");

    const fastStatus = Number(state.attributes.fast_chg_status || 0);
    const serverRemain = Number(state.attributes.fast_chg_remain || 0);

    // Restore optimistic state from localStorage (survives F5)
    if (!this._localFastStatus && !this._forceStopped) {
      const saved = this._loadFastState();
      if (saved && (saved.status === 1 || saved.status === 2)) {
        // Only use saved state if server hasn't caught up yet
        if (fastStatus !== saved.status || serverRemain === 0) {
          this._localFastStatus = saved.status;
          this._localRemainSec = saved.remainSec;
          this._localStartTime = Date.now() - 1000; // approximate
          // Restart countdown
          if (this._localCountdown) clearInterval(this._localCountdown);
          this._localCountdown = setInterval(() => {
            this._localRemainSec -= 60;
            if (this._localRemainSec <= 0) {
              this._localRemainSec = 0;
              this._localFastStatus = 0;
              this._localStartTime = 0;
              this._clearFastState();
              clearInterval(this._localCountdown);
              this._localCountdown = null;
            } else {
              this._saveFastState(this._localFastStatus, this._localRemainSec);
            }
            this._updateStatus();
          }, 60000);
        }
      }
    }

    if (this._forceStopped && (fastStatus === 1 || fastStatus === 2)) {
      // server hasn't caught up yet, treat as idle
    } else {
      this._forceStopped = false;
      // 修复：当页面刷新或重新加载时，如果服务器显示正在运行，应该恢复本地状态
      if (serverRemain > 0 && (fastStatus === 1 || fastStatus === 2)) {
        this._localRemainSec = serverRemain;
        // 重要：当服务器显示正在运行时，需要恢复_localFastStatus
        // 否则页面刷新后状态会丢失
        if (!this._localFastStatus) {
          this._localFastStatus = fastStatus;
          this._localStartTime = Date.now() - ((serverRemain - 1) * 1000); // 估算开始时间
          // 启动本地倒计时（每分钟更新一次）
          if (this._localCountdown) clearInterval(this._localCountdown);
          this._localCountdown = setInterval(() => {
            this._localRemainSec -= 60;
            if (this._localRemainSec <= 0) {
              this._localRemainSec = 0;
              this._localFastStatus = 0;
              this._localStartTime = 0;
              clearInterval(this._localCountdown);
              this._localCountdown = null;
            }
            this._updateStatus();
          }, 60000);
        }
      } else if (this._localFastStatus && fastStatus !== 1 && fastStatus !== 2) {
        // Server says not running. Only trust this once the 30s grace period
        // has passed (device needs time to process the command before the server
        // reflects the new state). After 30s the server is authoritative.
        if (!this._localStartTime || Date.now() - this._localStartTime > 30000) {
          this._localFastStatus = 0;
          this._localRemainSec = 0;
          this._localStartTime = 0;
          this._clearFastState();
          if (this._localCountdown) { clearInterval(this._localCountdown); this._localCountdown = null; }
        }
      } else if (this._localFastStatus && (fastStatus === 1 || fastStatus === 2)) {
        // Server has caught up with running state, no longer need optimistic
        this._clearFastState();
      }
    }

    const isRunning = this._localFastStatus ? true : (!this._forceStopped && (fastStatus === 1 || fastStatus === 2));
    const curStatus = this._localFastStatus || fastStatus;

    const remainMin = Math.ceil((this._localRemainSec || serverRemain) / 60);

    if (isRunning && quickRunning) {
      const stopLabel = this.shadowRoot.getElementById("quick_stop_label");
      const statusIcon = this.shadowRoot.getElementById("quick_status_icon");
      const remainLabel = this.shadowRoot.getElementById("quick_remain_label");
      const remainDesc = this.shadowRoot.getElementById("quick_remain_desc");
      const remainTime = this.shadowRoot.getElementById("quick_remain_time");
      const isChg = curStatus === 1;
      if (stopLabel) stopLabel.textContent = isChg ? `${_t(this._hass, 'stop')} ${_t(this._hass, 'charge')}` : `${_t(this._hass, 'stop')} ${_t(this._hass, 'discharge')}`;
      if (statusIcon) statusIcon.src = isChg ? HANCHUESS_ICONS.charging : HANCHUESS_ICONS.discharging;
      if (remainLabel) {
        remainLabel.textContent = isChg ? _t(this._hass, 'fast_charging') : _t(this._hass, 'fast_discharging');
        remainLabel.style.color = isChg ? "#00bcd4" : "#4caf50";
      }
      if (remainDesc) remainDesc.textContent = isChg ? _t(this._hass, 'remain_charging') : _t(this._hass, 'remain_discharging');
      if (remainTime) remainTime.textContent = `${remainMin}min`;
      quickRunning.style.display = "flex";
      if (quickBtns) quickBtns.style.display = "none";
      quickRows.forEach(r => r.style.display = "none");
    } else {
      this._localFastStatus = 0;
      this._localRemainSec = 0;
      this._localStartTime = 0;
      if (this._localCountdown) { clearInterval(this._localCountdown); this._localCountdown = null; }
      if (quickRunning) quickRunning.style.display = "none";
      if (quickBtns) quickBtns.style.display = "flex";
      quickRows.forEach(r => r.style.display = "flex");
      const canOperate = isOnline && !isRunning;
      if (quickConfirm) quickConfirm.disabled = !canOperate;
      if (quickMode) quickMode.disabled = !canOperate;
      if (quickDuration) quickDuration.disabled = !canOperate;
    }

    const select = this.shadowRoot.getElementById("work_mode");
    if (!select) return;

    const options = (state.attributes.work_mode_options || []).map(opt => opt.label);
    if (select.options.length !== options.length + 1) {
      select.innerHTML = `<option value="">${_t(this._hass, 'please_select')}</option>` +
        options.map(opt => `<option value="${opt}">${opt}</option>`).join("");
    }

    const fields = state.attributes.energy_fields || [];
    const reRendered = this._renderDynamicFields(fields);

    if (this._dataLoaded) {
      if (reRendered) this._fillData(this._originalValues);
      this._toggleFields(select.value);
    }
  }

  _renderDynamicFields(fields) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    if (!container) return;
    // Re-render if fields changed
    const fieldsKey = JSON.stringify(fields.map(f => f.code + f.type));
    if (container.dataset.renderedKey === fieldsKey) return false;
    container.dataset.renderedKey = fieldsKey;

    let html = "";
    for (const field of fields) {
      const la = field.listener_code
        ? `data-listener-code="${field.listener_code}" data-listener-show="${field.listener_show}"`
        : "";
      const cls = field.hidden || field.listener_code ? "dynamic-field" : "dynamic-field visible";

      if (field.type === "1") {
        const min = field.min || "0", max = field.max || "99999";
        const step = field.step || 1;
        html += `<div class="${cls}" ${la} data-signal="${field.signal}"><div class="field"><label>${field.name}</label><input type="number" data-signal="${field.signal}" data-step="${step}" min="${min}" max="${max}" step="${step}" placeholder="[${min}, ${max}]"></div></div>`;
      }

      if (field.type === "6") {
        const sigs = (field.signal || "").split(",");
        const code = field.code || "";
        const gk = code.startsWith("chg_tim") ? "chg" : code.startsWith("dschg_tim") ? "dschg" : code;
        const idx = (code.match(/(\d)$/) || [,"1"])[1];
        const fmt = field.format || "";
        html += `<div class="${cls}" ${la} data-signal="${field.signal}" data-time-group="${gk}" data-time-index="${idx}" data-time-fmt="${fmt}"><div class="time-row"><span class="time-label">${field.name}</span><input type="text" class="time-input" data-signal="${sigs[0]||""}" data-time-type="start" readonly><span>-</span><input type="text" class="time-input" data-signal="${sigs[1]||""}" data-time-type="end" readonly><button class="icon-btn del" data-action="del-time" data-group="${gk}" data-index="${idx}">🗑</button><button class="icon-btn add" data-action="add-time" data-group="${gk}" data-index="${idx}" style="display:none">+</button></div></div>`;
      }

      if (field.type === "collapse") {
        const children = field.children || [];
        const sig = field.signal;
        // Determine time group for overlap detection from field code (e.g. TCT_CHG0 -> chg, TCT_DISCHG1 -> dschg)
        const collapseGroup = field.code && field.code.includes("DISCHG") ? "dschg" : field.code && field.code.includes("CHG") ? "chg" : "";
        let switchHtml = "";
        let bodyHtml = "";
        for (const c of children) {
          const ci = c.index != null ? c.index : 0;
          if (c.type === "3") {
            const opts = (c.options||[]).map(o => `<option value="${o.value}">${o.name}</option>`).join("");
            bodyHtml += `<div class="collapse-row"><label><span class="req">*</span>${c.name}</label><select data-arr-signal="${sig}" data-arr-index="${ci}">${opts}</select></div>`;
          } else if (c.type === "5") {
            const timeTypeAttr = c.code === "start_time" ? 'data-time-type="start"' : c.code === "end_time" ? 'data-time-type="end"' : "";
            const groupAttr = collapseGroup ? `data-time-group="${collapseGroup}"` : "";
            bodyHtml += `<div class="collapse-row"><label><span class="req">*</span>${c.name}</label><input type="text" class="time-input" data-arr-signal="${sig}" data-arr-index="${ci}" data-arr-fmt="time" ${timeTypeAttr} ${groupAttr} readonly></div>`;
          } else if (c.type === "1") {
            const mn = c.min||"0", mx = c.max||"99999", cStep = c.step||1;
            bodyHtml += `<div class="collapse-row"><label><span class="req">*</span>${c.name}</label><input type="number" data-arr-signal="${sig}" data-arr-index="${ci}" data-step="${cStep}" min="${mn}" max="${mx}" step="${cStep}" placeholder="[${mn}, ${mx}]"></div>`;
          }
        }
        // "是否应用" from FLAG_ENABLE_CYCLE, not from array
        switchHtml = `<span class="collapse-sw-label">${_t(this._hass, 'apply')}</span><label class="toggle"><input type="checkbox" data-enable-signal="${field.code}" data-collapse-switch="${field.code}"><span class="slider"></span></label>`;
        const collapseGroupAttr = collapseGroup ? `data-time-group="${collapseGroup}"` : "";
        html += `<div class="${cls}" ${la} data-signal="${sig}" data-collapse="${field.code}" ${collapseGroupAttr}><div class="collapse-card"><div class="collapse-header"><span class="collapse-arrow" data-arrow="${field.code}" data-toggle="${field.code}">▶</span><span class="collapse-title" data-toggle="${field.code}">${field.name}</span>${switchHtml}</div><div class="collapse-body" data-body="${field.code}">${bodyHtml}</div></div></div>`;
      }
    }

    container.innerHTML = html;

    container.onclick = (e) => {
      const btn = e.target.closest("[data-action]");
      if (btn) {
        const {action, group, index} = btn.dataset;
        if (action === "del-time") this._deleteTimeSlot(group, index);
        else if (action === "add-time") this._addTimeSlot(group, index);
        return;
      }
      const hdr = e.target.closest("[data-toggle]");
      if (hdr) {
        const code = hdr.dataset.toggle;
        const body = container.querySelector(`[data-body="${code}"]`);
        const arrow = container.querySelector(`[data-arrow="${code}"]`);
        if (body) body.classList.toggle("open");
        if (arrow) arrow.classList.toggle("open");
      }
    };

    container.onchange = (e) => {
      const sw = e.target.closest("[data-collapse-switch]");
      if (sw) {
        const code = sw.dataset.collapseSwitch;
        const body = container.querySelector(`[data-body="${code}"]`);
        const arrow = container.querySelector(`[data-arrow="${code}"]`);
        if (sw.checked) {
          if (body) body.classList.add("open");
          if (arrow) arrow.classList.add("open");
        } else {
          if (body) body.classList.remove("open");
          if (arrow) arrow.classList.remove("open");
        }
      }

      // Update _prevValue for time inputs after change.
      // Overlap check is handled by _confirmTimePicker before the change
      // event is dispatched, so no need to re-check here.
      const timeInput = e.target.matches("input.time-input") ? e.target : null;
      if (timeInput) {
        timeInput._prevValue = timeInput.value;
      }
    };

    return true;
  }

  _fillData(result) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    if (!container) return;

    // Fill data-signal inputs
    container.querySelectorAll("input[data-signal]").forEach(input => {
      const signal = input.dataset.signal;
      if (signal && result[signal] !== undefined) {
        if (input.classList.contains("time-input")) {
          const v = String(result[signal]);
          if (v.includes(":")) input.value = v;
          else {
            const fmt = input.closest("[data-time-fmt]")?.dataset.timeFmt || "";
            if (fmt.includes("HH") || fmt.includes("hh")) {
              input.value = this._signalToTime(result[signal]);
            } else {
              const s = v.padStart(4, "0");
              input.value = s.slice(0,2) + ":" + s.slice(2,4);
            }
          }
          // 重要：设置_prevValue，以便时间重叠检查能正常工作
          input._prevValue = input.value;
        } else if (input.type === "checkbox") {
          input.checked = String(result[signal]) === (input.dataset.on || "1");
        } else if (signal === "MIN_THRESH_CHG_DUR") {
          input.value = Math.round(Number(result[signal]) / 60);
        } else if (input.type === "number" && input.dataset.step) {
          const step = parseFloat(input.dataset.step);
          const num = Number(result[signal]);
          input.value = isNaN(num) ? result[signal] : (step < 1 ? parseFloat(num.toFixed(String(step).split(".")[1]?.length || 2)) : Math.round(num));
        } else {
          input.value = result[signal];
        }
      }
    });
    container.querySelectorAll("select[data-signal]").forEach(sel => {
      const signal = sel.dataset.signal;
      if (signal && result[signal] !== undefined) sel.value = String(result[signal]);
    });

    // Fill collapse array fields
    container.querySelectorAll("[data-arr-signal]").forEach(el => {
      const sig = el.dataset.arrSignal;
      const idx = parseInt(el.dataset.arrIndex);
      if (!sig || isNaN(idx) || result[sig] === undefined) return;
      let arr;
      try { arr = JSON.parse(result[sig]); } catch { return; }
      if (!Array.isArray(arr) || idx >= arr.length) return;
      const val = arr[idx];
      if (el.classList.contains("time-input") || el.dataset.arrFmt === "time") {
        const s = String(val).padStart(4, "0");
        el.value = s.slice(0,2) + ":" + s.slice(2,4);
        el._prevValue = el.value;
      } else if (el.tagName === "SELECT") {
        el.value = String(val);
      } else if (el.type === "number" && el.dataset.step) {
        const step = parseFloat(el.dataset.step);
        const num = Number(val);
        el.value = isNaN(num) ? val : (step < 1 ? parseFloat(num.toFixed(String(step).split(".")[1]?.length || 2)) : Math.round(num));
      } else {
        el.value = String(val).replace(/"/g, "");
      }
    });

    // Fill FLAG_ENABLE_CYCLE switches
    let enableCycle = [];
    try { enableCycle = JSON.parse(result["FLAG_ENABLE_CYCLE"] || "[]"); } catch {}
    container.querySelectorAll("[data-enable-signal]").forEach(sw => {
      const code = sw.dataset.enableSignal;
      const m = code.match(/TCT_(CHG|DISCHG)(\d)/);
      if (m && enableCycle.length) {
        const ci = m[1] === "CHG" ? Number(m[2]) : 3 + Number(m[2]);
        sw.checked = enableCycle[ci] === 1;
      }
    });

    // Expand/collapse based on switch
    container.querySelectorAll("[data-collapse-switch]").forEach(sw => {
      const code = sw.dataset.collapseSwitch;
      const body = container.querySelector(`[data-body="${code}"]`);
      const arrow = container.querySelector(`[data-arrow="${code}"]`);
      if (sw.checked) {
        if (body) body.classList.add("open");
        if (arrow) arrow.classList.add("open");
      } else {
        if (body) body.classList.remove("open");
        if (arrow) arrow.classList.remove("open");
      }
    });
  }

  _deleteTimeSlot(group, index) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    const allSlots = Array.from(container.querySelectorAll(`[data-time-group="${group}"][data-time-index]`));
    
    // Collect all visible slots' values
    const visibleValues = [];
    allSlots.forEach(slot => {
      if (slot.classList.contains("visible") && slot.dataset.timeHidden !== "true") {
        const inputs = slot.querySelectorAll("input.time-input");
        visibleValues.push({
          start: inputs[0] ? inputs[0].value : "",
          end: inputs[1] ? inputs[1].value : "",
        });
      }
    });

    // Remove the deleted index (0-based from visible list)
    const delIdx = parseInt(index) - 1;
    // Find which visible slot corresponds to this index
    let visibleIdx = 0;
    for (let i = 0; i < allSlots.length; i++) {
      if (allSlots[i].dataset.timeIndex === index && allSlots[i].classList.contains("visible")) {
        // Find position in visible list
        visibleIdx = 0;
        for (let j = 0; j < i; j++) {
          if (allSlots[j].classList.contains("visible") && allSlots[j].dataset.timeHidden !== "true") {
            visibleIdx++;
          }
        }
        break;
      }
    }
    visibleValues.splice(visibleIdx, 1);

    // Redistribute values to slots 1, 2, 3
    allSlots.forEach((slot, i) => {
      const inputs = slot.querySelectorAll("input.time-input");
      if (i < visibleValues.length) {
        inputs[0].value = visibleValues[i].start;
        inputs[1].value = visibleValues[i].end;
        // 重要：更新_prevValue
        inputs[0]._prevValue = visibleValues[i].start;
        inputs[1]._prevValue = visibleValues[i].end;
        slot.classList.add("visible");
        delete slot.dataset.timeHidden;
      } else {
        inputs[0].value = "00:00";
        inputs[1].value = "00:00";
        // 重要：更新_prevValue
        inputs[0]._prevValue = "00:00";
        inputs[1]._prevValue = "00:00";
        slot.classList.remove("visible");
        slot.dataset.timeHidden = "true";
      }
    });

    this._updateTimeButtons(group);
  }

  _addTimeSlot(group, index) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    // Find next hidden time slot in this group
    const allSlots = container.querySelectorAll(`[data-time-group="${group}"][data-time-index]`);
    for (const slot of allSlots) {
      if (slot.dataset.timeHidden === "true" || !slot.classList.contains("visible")) {
        slot.classList.add("visible");
        delete slot.dataset.timeHidden;
        // Set default values for new slot (00:00)
        const inputs = slot.querySelectorAll("input.time-input");
        inputs.forEach(inp => { inp.value = "00:00"; });
        // 重要：设置_prevValue，以便时间重叠检查能正常工作
        inputs.forEach(inp => { inp._prevValue = "00:00"; });
        break;
      }
    }

    this._updateTimeButtons(group);
  }

  _updateTimeButtons(group) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    const allSlots = container.querySelectorAll(`[data-time-group="${group}"][data-time-index]`);

    const visibleSlots = [];
    const hiddenSlots = [];
    allSlots.forEach(slot => {
      if (slot.classList.contains("visible") && slot.dataset.timeHidden !== "true") {
        visibleSlots.push(slot);
      } else {
        hiddenSlots.push(slot);
      }
    });

    allSlots.forEach(slot => {
      const addBtn = slot.querySelector("[data-action='add-time']");
      const delBtn = slot.querySelector("[data-action='del-time']");
      if (addBtn) addBtn.style.display = "none";
      if (delBtn) delBtn.style.display = "";
    });

    // Only 1 visible: hide its delete button
    if (visibleSlots.length <= 1) {
      visibleSlots.forEach(slot => {
        const delBtn = slot.querySelector("[data-action='del-time']");
        if (delBtn) delBtn.style.display = "none";
      });
    }

    // Show add button on last visible slot if there are hidden slots
    if (visibleSlots.length > 0 && hiddenSlots.length > 0) {
      const lastVisible = visibleSlots[visibleSlots.length - 1];
      const addBtn = lastVisible.querySelector("[data-action='add-time']");
      if (addBtn) addBtn.style.display = "";
    }
  }

  _toggleFields(currentWorkModeLabel) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    if (!container) return;

    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const wmOptions = state.attributes.work_mode_options || [];
    let currentValue = "";
    for (const opt of wmOptions) {
      if (opt.label === currentWorkModeLabel) {
        currentValue = String(opt.value);
        break;
      }
    }

    // Determine work mode item codes for listener matching
    const wmCodes = new Set(["work_mode"]);
    for (const opt of wmOptions) {
      if (opt.signal) wmCodes.add(opt.signal);
    }
    // Also add WORK_MODE_CMB as it's used as listener code
    wmCodes.add("WORK_MODE_CMB");

    const allFields = this.shadowRoot.querySelectorAll(".dynamic-field");
    allFields.forEach(el => {
      const listenerCode = el.dataset.listenerCode;
      const listenerShow = el.dataset.listenerShow;

      if (!listenerCode) {
        el.classList.add("visible");
        return;
      }

      if (wmCodes.has(listenerCode)) {
        const showValues = (listenerShow || "").split(",");
        if (showValues.includes(currentValue)) {
          if (el.dataset.timeHidden !== "true") {
            el.classList.add("visible");
          }
        } else {
          el.classList.remove("visible");
        }
      }
    });

    // Update add/delete buttons for time groups (only type=6 slots have data-time-index)
    const groups = new Set();
    container.querySelectorAll("[data-time-group][data-time-index]").forEach(el => {
      groups.add(el.dataset.timeGroup);
    });
    groups.forEach(g => this._updateTimeButtons(g));
  }

  _signalToTime(val) {
    const totalSeconds = Number(val) || 0;
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    return String(hours).padStart(2, "0") + ":" + String(minutes).padStart(2, "0");
  }

  _timeToSignal(timeStr) {
    const parts = timeStr.split(":");
    const hours = Number(parts[0]) || 0;
    const minutes = Number(parts[1]) || 0;
    return String(hours * 3600 + minutes * 60);
  }

  async _loadData() {
    const loadBtn = this.shadowRoot.getElementById("load_btn");
    const statusMsg = this.shadowRoot.getElementById("status_msg");
    loadBtn.disabled = true;
    statusMsg.textContent = _t(this._hass, 'loading');
    statusMsg.className = "status";

    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const keys = [];
    const fields = state.attributes.energy_fields || [];
    for (const field of fields) {
      if (field.signal) {
        field.signal.split(",").forEach(s => { if (s) keys.push(s); });
      }
    }

    const wmOptions = state.attributes.work_mode_options || [];
    if (wmOptions.length > 0) {
      keys.push(wmOptions[0].signal || "WORK_MODE_CMB");
    }
    // Only request FLAG_ENABLE_CYCLE if there are collapse (82/83) fields
    const hasCollapse = fields.some(f => f.type === "collapse");
    if (hasCollapse && !keys.includes("FLAG_ENABLE_CYCLE")) keys.push("FLAG_ENABLE_CYCLE");

    try {
      const result = await this._hass.callWS({
        type: "hanchuess/iot_get",
        sn: this._config.sn,
        dev_type: "2",
        keys: keys,
      });

      this._originalValues = { ...result };
      this._dataLoaded = true;

      // Fill work mode
      const wmSignal = wmOptions.length > 0 ? (wmOptions[0].signal || "WORK_MODE_CMB") : "WORK_MODE_CMB";
      const wmValue = result[wmSignal];
      if (wmValue !== undefined) {
        const select = this.shadowRoot.getElementById("work_mode");
        for (const opt of wmOptions) {
          if (String(opt.value) === String(wmValue)) {
            select.value = opt.label;
            break;
          }
        }
      }

      // Fill all dynamic fields (replaces duplicated fill logic)
      this._fillData(result);

      // Handle time slot visibility (only type=6 slots, which have data-time-index)
      const container = this.shadowRoot.getElementById("dynamic_fields");
      const timeSlots = container.querySelectorAll("[data-time-group][data-time-index]");
      timeSlots.forEach(slot => {
        const timeInputs = slot.querySelectorAll("input.time-input");
        const allZero = Array.from(timeInputs).every(inp => inp.value === "00:00");
        if (allZero && slot.dataset.timeIndex !== "1") {
          slot.classList.remove("visible");
          slot.dataset.timeHidden = "true";
        } else {
          delete slot.dataset.timeHidden;
        }
      });

      // Toggle fields based on work mode and update buttons
      const select = this.shadowRoot.getElementById("work_mode");
      this._toggleFields(select.value);

      statusMsg.textContent = _t(this._hass, 'load_success');
      statusMsg.className = "status success";
    } catch (err) {
      statusMsg.textContent = _t(this._hass, 'load_fail') + err.message;
      statusMsg.className = "status error";
    }

    loadBtn.disabled = false;
    setTimeout(() => { statusMsg.textContent = ""; }, 3000);
  }

  // Returns array of {start, end} in minutes (0~1439) for all visible slots in a group
  _getVisibleTimeSlots(group) {
    const container = this.shadowRoot.getElementById("dynamic_fields");
    if (!container) return [];
    const slots = [];
    const toMin = (t) => {
      const [h, m] = t.split(":").map(Number);
      return h * 60 + m;
    };
    container.querySelectorAll(`[data-time-group="${group}"]`).forEach(slot => {
      if (!slot.classList.contains("visible") || slot.dataset.timeHidden === "true") return;
      // Skip collapse cards whose enable switch is off
      const collapseSwitch = slot.querySelector("[data-collapse-switch]");
      if (collapseSwitch && !collapseSwitch.checked) return;

      const inputs = slot.querySelectorAll("input.time-input");
      if (inputs.length < 2) return;

      // Use data-time-type to identify start/end, fall back to DOM order
      let startInput = null, endInput = null;
      inputs.forEach(inp => {
        if (inp.dataset.timeType === "start") startInput = inp;
        else if (inp.dataset.timeType === "end") endInput = inp;
      });
      if (!startInput) startInput = inputs[0];
      if (!endInput) endInput = inputs[1];

      const startStr = startInput.value;
      const endStr = endInput.value;
      if (!startStr || !endStr) return;
      const start = toMin(startStr);
      const end = toMin(endStr);
      // Treat 00:00-00:00 as not set
      if (start === 0 && end === 0) return;
      slots.push({ start, end });
    });
    return slots;
  }

  // Returns true if two time intervals overlap (handles overnight wrap-around)
  _intervalsOverlap(a, b) {
    // Each interval can wrap midnight: if start > end, it spans midnight
    const ranges = (iv) => iv.start <= iv.end
      ? [[iv.start, iv.end]]
      : [[iv.start, 1439], [0, iv.end]];
    for (const ra of ranges(a)) {
      for (const rb of ranges(b)) {
        // Overlap: intervals cross only if one starts strictly before the other ends
        if (ra[0] < rb[1] && rb[0] < ra[1]) return true;
      }
    }
    return false;
  }

  // Returns true if any chg slot overlaps with any dschg slot
  _checkTimeOverlap() {
    const chgSlots = this._getVisibleTimeSlots("chg");
    const dschgSlots = this._getVisibleTimeSlots("dschg");
    for (const c of chgSlots) {
      for (const d of dschgSlots) {
        if (this._intervalsOverlap(c, d)) return true;
      }
    }
    return false;
  }

  // Check if there was already an overlap before changing the given input
  _checkTimeOverlapWith(input, prevValue) {
    const curValue = input.value;
    input.value = prevValue;
    const hadOverlap = this._checkTimeOverlap();
    input.value = curValue;
    return hadOverlap;
  }

  async _submit() {
    const submitBtn = this.shadowRoot.getElementById("submit_btn");
    const statusMsg = this.shadowRoot.getElementById("status_msg");
    submitBtn.disabled = true;
    statusMsg.textContent = _t(this._hass, 'submitting');
    statusMsg.className = "status";

    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const sn = this._config.sn;
    const valueMap = {};

    // Check charging/discharging time overlap before submitting
    if (this._checkTimeOverlap()) {
      statusMsg.textContent = _t(this._hass, 'time_overlap');
      statusMsg.className = "status error";
      submitBtn.disabled = false;
      setTimeout(() => { statusMsg.textContent = ""; }, 4000);
      return;
    }

    // Check work mode change
    const wmOptions = state.attributes.work_mode_options || [];
    const wmSignal = wmOptions.length > 0 ? (wmOptions[0].signal || "WORK_MODE_CMB") : "WORK_MODE_CMB";
    const selectEl = this.shadowRoot.getElementById("work_mode");
    const selectedLabel = selectEl ? selectEl.value : "";

    if (selectedLabel) {
      for (const opt of wmOptions) {
        if (opt.label === selectedLabel) {
          const newVal = String(opt.value);
          if (newVal !== String(this._originalValues[wmSignal] || "")) {
            valueMap[wmSignal] = newVal;
          }
          break;
        }
      }
    }

    // Check visible field changes
    const container = this.shadowRoot.getElementById("dynamic_fields");
    const visibleFields = container.querySelectorAll(".dynamic-field.visible");
    const changedSignals = new Set();

    // First pass: find changed signals (for non-collapse fields)
    visibleFields.forEach(fieldEl => {
      if (fieldEl.dataset.collapse) return;
      const inputs = fieldEl.querySelectorAll("input[data-signal], select[data-signal]");
      inputs.forEach(input => {
        const signal = input.dataset.signal;
        if (!signal) return;
        let newVal;
        if (input.classList.contains("time-input")) {
          const fmt = input.closest("[data-time-fmt]")?.dataset.timeFmt || "";
          if (fmt.includes("HH") || fmt.includes("hh")) {
            newVal = this._timeToSignal(input.value || "00:00");
          } else {
            newVal = (input.value || "00:00").replace(":", "");
          }
        } else if (input.type === "checkbox") {
          newVal = input.checked ? (input.dataset.on || "1") : (input.dataset.off || "0");
        } else if (signal === "MIN_THRESH_CHG_DUR") {
          newVal = String(Number(input.value) * 60);
        } else {
          newVal = input.value;
        }
        if (!newVal && !this._originalValues[signal]) return;
        let origVal = String(this._originalValues[signal] || "");
        if (input.type === "number" && input.dataset.step) {
          const step = parseFloat(input.dataset.step);
          const origNum = Number(origVal);
          if (!isNaN(origNum)) origVal = step < 1 ? String(parseFloat(origNum.toFixed(String(step).split(".")[1]?.length || 2))) : String(Math.round(origNum));
        }
        if (newVal !== origVal) changedSignals.add(signal);
      });
    });

    // Also check deleted time slots (hidden but were visible before, only type=6)
    const allTimeSlots = container.querySelectorAll("[data-time-group][data-time-index]");
    allTimeSlots.forEach(slot => {
      if (slot.dataset.timeHidden === "true") {
        const inputs = slot.querySelectorAll("input.time-input");
        inputs.forEach(input => {
          const signal = input.dataset.signal;
          if (signal && this._originalValues[signal] && String(this._originalValues[signal]) !== "0") {
            changedSignals.add(signal);
          }
        });
      }
    });

    // Second pass: collect non-collapse values
    visibleFields.forEach(fieldEl => {
      if (fieldEl.dataset.collapse) return;
      const inputs = fieldEl.querySelectorAll("input[data-signal], select[data-signal]");
      const fieldSignals = Array.from(inputs).map(i => i.dataset.signal).filter(Boolean);
      const hasChange = fieldSignals.some(s => changedSignals.has(s));
      if (!hasChange) return;
      inputs.forEach(input => {
        const signal = input.dataset.signal;
        if (!signal) return;
        if (input.classList.contains("time-input")) {
          const fmt = input.closest("[data-time-fmt]")?.dataset.timeFmt || "";
          if (fmt.includes("HH") || fmt.includes("hh")) {
            valueMap[signal] = this._timeToSignal(input.value || "00:00");
          } else {
            valueMap[signal] = (input.value || "00:00").replace(":", "");
          }
        } else if (signal === "MIN_THRESH_CHG_DUR") {
          valueMap[signal] = String(Number(input.value) * 60);
        } else {
          valueMap[signal] = input.value;
        }
      });
    });

    // Collect ALL collapse card (82/83) array values - must submit all together
    const collapseFields = container.querySelectorAll(".dynamic-field.visible[data-collapse]");
    if (collapseFields.length > 0) {
      let hasAnyChange = false;
      const collapseValues = {};
      collapseFields.forEach(fieldEl => {
        const sig = fieldEl.dataset.signal;
        if (!sig) return;
        const arrEls = fieldEl.querySelectorAll("[data-arr-signal]");
        let origArr;
        try { origArr = JSON.parse(this._originalValues[sig] || "[]"); } catch { origArr = []; }
        const newArr = [...origArr];
        arrEls.forEach(el => {
          const idx = parseInt(el.dataset.arrIndex);
          if (isNaN(idx)) return;
          let val;
          if (el.classList.contains("time-input") || el.dataset.arrFmt === "time") {
            val = (el.value || "00:00").replace(":", "");
          } else if (el.type === "number") {
            val = el.value;
          } else {
            val = el.tagName === "SELECT" ? Number(el.value) : el.value;
          }
          newArr[idx] = val;
        });
        collapseValues[sig] = JSON.stringify(newArr);
        if (collapseValues[sig] !== JSON.stringify(origArr)) hasAnyChange = true;
      });
      // Check FLAG_ENABLE_CYCLE change
      this._collectEnableCycle(container, collapseValues);
      if (collapseValues["FLAG_ENABLE_CYCLE"] || hasAnyChange) {
        // Submit all TCT + FLAG_ENABLE_CYCLE together
        Object.assign(valueMap, collapseValues);
        if (!valueMap["FLAG_ENABLE_CYCLE"]) {
          valueMap["FLAG_ENABLE_CYCLE"] = this._originalValues["FLAG_ENABLE_CYCLE"] || "[0,0,0,0,0,0]";
        }
      }
    }

    // Collect deleted time slots (send 0)
    allTimeSlots.forEach(slot => {
      if (slot.dataset.timeHidden === "true") {
        const inputs = slot.querySelectorAll("input.time-input");
        const hasOrig = Array.from(inputs).some(inp => {
          const sig = inp.dataset.signal;
          return sig && this._originalValues[sig] && String(this._originalValues[sig]) !== "0";
        });
        if (hasOrig) {
          inputs.forEach(inp => {
            const sig = inp.dataset.signal;
            if (sig) valueMap[sig] = "0";
          });
        }
      }
    });

    if (Object.keys(valueMap).length === 0) {
      statusMsg.textContent = _t(this._hass, 'no_change');
      statusMsg.className = "status";
      submitBtn.disabled = false;
      setTimeout(() => { statusMsg.textContent = ""; }, 2000);
      return;
    }

    try {
      await this._hass.callWS({
        type: "hanchuess/iot_set",
        sn: sn,
        dev_type: "2",
        value: valueMap,
      });

      Object.assign(this._originalValues, valueMap);

      // Sync all visible field values to _originalValues
      container.querySelectorAll("input[data-signal]").forEach(input => {
        const signal = input.dataset.signal;
        if (!signal || !input.value) return;
        if (input.classList.contains("time-input")) {
          const fmt = input.closest("[data-time-fmt]")?.dataset.timeFmt || "";
          if (fmt.includes("HH") || fmt.includes("hh")) {
            this._originalValues[signal] = this._timeToSignal(input.value || "00:00");
          } else {
            this._originalValues[signal] = (input.value || "00:00").replace(":", "");
          }
        } else if (signal === "MIN_THRESH_CHG_DUR") {
          this._originalValues[signal] = String(Number(input.value) * 60);
        } else {
          this._originalValues[signal] = input.value;
        }
      });

      statusMsg.textContent = _t(this._hass, 'submit_success');
      statusMsg.className = "status success";
    } catch (err) {
      const errMsg = err.message || err.error || _t(this._hass, 'unknown_error');
      statusMsg.textContent = _t(this._hass, 'submit_fail') + errMsg;
      statusMsg.className = "status error";
    }

    submitBtn.disabled = false;
    setTimeout(() => { statusMsg.textContent = ""; }, 3000);
  }

  _collectEnableCycle(container, targetMap) {
    let origCycle;
    try { origCycle = JSON.parse(this._originalValues["FLAG_ENABLE_CYCLE"] || "[0,0,0,0,0,0]"); } catch { origCycle = [0,0,0,0,0,0]; }
    const newCycle = [...origCycle];
    container.querySelectorAll("[data-enable-signal]").forEach(sw => {
      const code = sw.dataset.enableSignal;
      const m = code.match(/TCT_(CHG|DISCHG)(\d)/);
      if (!m) return;
      const ci = m[1] === "CHG" ? Number(m[2]) : 3 + Number(m[2]);
      newCycle[ci] = sw.checked ? 1 : 0;
    });
    const newStr = JSON.stringify(newCycle);
    if (newStr !== JSON.stringify(origCycle)) targetMap["FLAG_ENABLE_CYCLE"] = newStr;
  }

  // Reset the coordinator's polling cycle so the next data refresh happens
  // ~60s from now (when the device will have reported accurate state).
  // Calling update_entity triggers async_request_refresh() on the coordinator,
  // which resets its internal 60s timer from this moment.
  _resetCoordinatorCycle() {
    try {
      this._hass.callService("homeassistant", "update_entity", { entity_id: this._config.entity });
    } catch (e) { /* best-effort */ }
  }

  async _quickChargeDischarge() {
    const statusEl = this.shadowRoot.getElementById("quick_status");
    const confirmBtn = this.shadowRoot.getElementById("quick_confirm");
    const mode = this.shadowRoot.getElementById("quick_mode").value;
    const duration = this.shadowRoot.getElementById("quick_duration").value;

    if (!duration || Number(duration) < 1 || Number(duration) > 1440) {
      statusEl.textContent = _t(this._hass, 'duration_range');
      statusEl.className = "quick-status error";
      return;
    }

    confirmBtn.disabled = true;
    statusEl.textContent = _t(this._hass, 'submitting');
    statusEl.className = "quick-status";

    try {
      await this._hass.callWS({
        type: "hanchuess/fast_charge",
        sn: this._config.sn,
        act: Number(mode),
        duration: Number(duration) * 60,
      });
      statusEl.textContent = "";
      this._forceStopped = false;
      this._localFastStatus = Number(mode) === 2 ? 1 : 2;
      this._localRemainSec = Number(duration) * 60;
      this._localStartTime = Date.now();
      this._saveFastState(this._localFastStatus, this._localRemainSec);
      if (this._localCountdown) clearInterval(this._localCountdown);
      this._localCountdown = setInterval(() => {
        this._localRemainSec -= 60;
        if (this._localRemainSec <= 0) {
          this._localRemainSec = 0;
          this._localFastStatus = 0;
          this._localStartTime = 0;
          this._clearFastState();
          clearInterval(this._localCountdown);
          this._localCountdown = null;
        } else {
          this._saveFastState(this._localFastStatus, this._localRemainSec);
        }
        this._updateStatus();
      }, 60000);
      this._updateStatus();
      this._resetCoordinatorCycle();
    } catch (err) {
      statusEl.textContent = _t(this._hass, 'fail_prefix') + (err.message || _t(this._hass, 'unknown_error'));
      statusEl.className = "quick-status error";
    }
    confirmBtn.disabled = false;
    setTimeout(() => { statusEl.textContent = ""; }, 3000);
  }

  async _quickStop() {
    const statusEl = this.shadowRoot.getElementById("quick_status");
    const stopBtn = this.shadowRoot.getElementById("quick_stop_btn");
    if (stopBtn) stopBtn.style.pointerEvents = "none";
    statusEl.textContent = _t(this._hass, 'stopping');
    statusEl.className = "quick-status";

    const curStatus = this._localFastStatus || Number((this._hass.states[this._config.entity] || {}).attributes?.fast_chg_status || 0);
    const stopAct = curStatus === 2 ? -3 : -2;
    try {
      await this._hass.callWS({
        type: "hanchuess/fast_charge",
        sn: this._config.sn,
        act: stopAct,
        duration: 0,
      });
      this._localFastStatus = 0;
      this._localRemainSec = 0;
      this._localStartTime = 0;
      this._forceStopped = true;
      this._clearFastState();
      if (this._localCountdown) { clearInterval(this._localCountdown); this._localCountdown = null; }
      this._updateStatus();
      this._resetCoordinatorCycle();
      statusEl.textContent = _t(this._hass, 'stopped');
      statusEl.className = "quick-status success";
    } catch (err) {
      statusEl.textContent = _t(this._hass, 'fail_prefix') + (err.message || _t(this._hass, 'unknown_error'));
      statusEl.className = "quick-status error";
    }
    if (stopBtn) stopBtn.style.pointerEvents = "";
    setTimeout(() => { statusEl.textContent = ""; }, 3000);
  }

  // 时间选择器方法

  _showTimePicker(timeInput, skipRedirect) {
    // If clicking end time, redirect to start time first (but not for auto-advance)
    if (!skipRedirect && timeInput.dataset.timeType === "end") {
      const timeRow = timeInput.closest(".time-row");
      if (timeRow) {
        const startInput = timeRow.querySelector("[data-time-type='start']");
        if (startInput && startInput !== timeInput) {
          this._showTimePicker(startInput);
          return;
        }
      }
      // In collapse layout: redirect to start time in same collapse body
      const collapseBody = timeInput.closest("[data-body]");
      if (collapseBody) {
        const startInput = collapseBody.querySelector("[data-time-type='start']");
        if (startInput && startInput !== timeInput) {
          this._showTimePicker(startInput);
          return;
        }
      }
    }

    const titleEl = this.shadowRoot.getElementById("time_picker_title");
    const hourCol = this.shadowRoot.getElementById("tp_hour");
    const minuteCol = this.shadowRoot.getElementById("tp_minute");

    this._currentTimeInput = timeInput;

    // Parse current value
    const currentValue = timeInput.value || "00:00";
    const [hour, minute] = currentValue.split(":").map(Number);

    // Highlight selected hour and minute
    hourCol.querySelectorAll(".time-picker-item").forEach(item => {
      item.classList.toggle("selected", parseInt(item.dataset.value) === (hour || 0));
    });
    minuteCol.querySelectorAll(".time-picker-item").forEach(item => {
      item.classList.toggle("selected", parseInt(item.dataset.value) === (minute || 0));
    });

    // Set title based on time type
    const timeType = timeInput.dataset.timeType;
    if (titleEl) {
      if (timeType === "start") {
        titleEl.textContent = _t(this._hass, 'select_start_time');
      } else if (timeType === "end") {
        titleEl.textContent = _t(this._hass, 'select_end_time');
      } else {
        titleEl.textContent = _t(this._hass, 'select_time');
      }
    }

    // Save original value for rollback
    timeInput._prevValue = currentValue;

    // Show picker first, then scroll to selected values
    this.shadowRoot.getElementById("time_picker_overlay").style.display = "block";
    this.shadowRoot.getElementById("time_picker_dialog").style.display = "block";

    // Scroll after display is visible
    requestAnimationFrame(() => {
      const selHourItem = hourCol.querySelector(".time-picker-item.selected");
      if (selHourItem) selHourItem.scrollIntoView({ block: "center" });
      const selMinItem = minuteCol.querySelector(".time-picker-item.selected");
      if (selMinItem) selMinItem.scrollIntoView({ block: "center" });
    });
  }

  _hideTimePicker() {
    this.shadowRoot.getElementById("time_picker_overlay").style.display = "none";
    this.shadowRoot.getElementById("time_picker_dialog").style.display = "none";
    this._currentTimeInput = null;
  }

  _confirmTimePicker() {
    if (!this._currentTimeInput) return;

    const input = this._currentTimeInput;
    const prevValue = input._prevValue || input.value;

    const hourCol = this.shadowRoot.getElementById("tp_hour");
    const minuteCol = this.shadowRoot.getElementById("tp_minute");
    const selHour = hourCol.querySelector(".time-picker-item.selected");
    const selMin = minuteCol.querySelector(".time-picker-item.selected");
    const hour = selHour ? parseInt(selHour.dataset.value) : 0;
    const minute = selMin ? parseInt(selMin.dataset.value) : 0;
    const formattedTime = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;

    input.value = formattedTime;

    // Check overlap
    const hadOverlapBefore = this._checkTimeOverlapWith(input, prevValue);
    const hasOverlapNow = this._checkTimeOverlap();
    if (hasOverlapNow) {
      // Always show hint when overlap exists after change
      this._showOverlapHint(input);
      if (!hadOverlapBefore) {
        // This change introduced a new overlap — revert
        input.value = prevValue;
        input._prevValue = prevValue;
        this._hideTimePicker();
        return;
      }
      // Pre-existing overlap — allow edit (user may be fixing it), but show hint
    } else {
      // No overlap — clear any previous hint
      this._clearOverlapHint(input);
    }

    input._prevValue = formattedTime;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    this._hideTimePicker();

    // If this was a start time, auto-advance to end time
    if (input.dataset.timeType === "start") {
      // In time-row layout
      const timeRow = input.closest(".time-row");
      if (timeRow) {
        const endInput = timeRow.querySelector("[data-time-type='end']");
        if (endInput) {
          setTimeout(() => this._showTimePicker(endInput, true), 200);
        }
      } else {
        // In collapse layout: find end time in same collapse body
        const collapseBody = input.closest("[data-body]");
        if (collapseBody) {
          const endInput = collapseBody.querySelector("[data-time-type='end']");
          if (endInput) {
            setTimeout(() => this._showTimePicker(endInput, true), 200);
          }
        }
      }
    }
  }

  _showOverlapHint(input) {
    // Show hint below the time row / collapse-row (lightweight, does not revert value)
    const row = input ? (input.closest(".time-row") || input.closest(".collapse-row")) : null;
    if (row) {
      const old = row.parentNode.querySelector(".time-overlap-hint");
      if (old) old.remove();
      const hint = document.createElement("div");
      hint.className = "time-overlap-hint";
      hint.textContent = _t(this._hass, 'time_overlap_hint');
      row.parentNode.insertBefore(hint, row.nextSibling);
      setTimeout(() => { if (hint.parentNode) hint.remove(); }, 4000);
    }
  }

  _showOverlapError(input) {
    // Show hint below the time row / collapse-row + bottom status message
    this._showOverlapHint(input);
    const statusMsg = this.shadowRoot.getElementById("status_msg");
    if (statusMsg) {
      statusMsg.textContent = _t(this._hass, 'time_overlap');
      statusMsg.className = "status error";
      setTimeout(() => { statusMsg.textContent = ""; }, 4000);
    }
  }

  _clearOverlapHint(input) {
    const row = input ? (input.closest(".time-row") || input.closest(".collapse-row")) : null;
    if (row) {
      const hint = row.parentNode.querySelector(".time-overlap-hint");
      if (hint) hint.remove();
    }
  }

  getCardSize() {
    return 5;
  }
}
customElements.define("hanchuess-energy-card", HanchuessEnergyCard);

window.customCards = window.customCards || [];
const _cardLang = "en";
window.customCards.push({
  type: "hanchuess-energy-card",
  name: HANCHUESS_I18N[_cardLang].card_name,
  description: HANCHUESS_I18N[_cardLang].card_desc,
});
