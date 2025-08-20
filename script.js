// 各設備可選動作
const deviceActions = {
  tv: [
    { value: '', text: '請選擇動作' },
    { value: 'home', text: '回主畫面' },
    { value: 'power', text: '開關機' },
    { value: 'choose', text: '選擇鍵' },
    { value: 'return', text: '返回鍵' },
    { value: 'volume_up', text: '音量增加' },
    { value: 'volume_down', text: '音量減少' },
    { value: 'channel_right', text: '方向鍵右' },
    { value: 'channel_left', text: '方向鍵左' },
    { value: 'channel_up', text: '方向鍵上' },
    { value: 'channel_down', text: '方向鍵下' },
    { value: 'Youtube', text: '啟動Youtube' }
  ],
  fan: [
    { value: '', text: '請選擇動作' },
    { value: 'power', text: '開關' },
    { value: 'air_down', text: '風速減少' },
    { value: 'air_up', text: '風速增加' }
  ],
  ac: [
    { value: '', text: '請選擇動作' },
    { value: 'power', text: '開關' },
    { value: 'degree_down', text: '溫度減少' },
    { value: 'degree_up', text: '溫度增加' }
  ]
};
const defaultGestures = {
  tv: {
    PALM: { cmd: 'home', desc: '回主畫面' },
    FIST: { cmd: 'power', desc: '開關機' },
    OK: { cmd: 'choose', desc: '選擇鍵' },
    THUMB_LEFT: { cmd: 'return', desc: '返回鍵' },
    THUMB_UP: { cmd: 'volume_up', desc: '音量增加' },
    THUMB_DOWN: { cmd: 'volume_down', desc: '音量減少' },
    RIGHT: { cmd: 'channel_right', desc: '方向鍵右' },
    LEFT: { cmd: 'channel_left', desc: '方向鍵左' },
    UP: { cmd: 'channel_up', desc: '方向鍵上' },
    DOWN: { cmd: 'channel_down', desc: '方向鍵下' },
    YA: { cmd: 'Youtube', desc: '啟動Youtube' }
  },
  fan: {
    FIST: { cmd: 'power', desc: '開關' },
    DOWN: { cmd: 'air_down', desc: '風量減' },
    UP: { cmd: 'air_up', desc: '風量加' }
  },
  ac: {
    FIST: { cmd: 'power', desc: '開關' },
    DOWN: { cmd: 'degree_down', desc: '溫度減' },
    UP: { cmd: 'degree_up', desc: '溫度加' }
  }
};
const gestureLabels = {
  PALM: "🖐️ PALM", FIST: "✊ FIST", OK: "👌 OK",
  THUMB_LEFT: "👈 THUMB_LEFT", THUMB_UP: "👍 THUMB_UP", THUMB_DOWN: "👎 THUMB_DOWN",
  RIGHT: "👉 RIGHT", LEFT: "👈 LEFT", UP: "👆 UP", DOWN: "👇 DOWN", YA: "✌️ YA"
};
const gestures = Object.keys(gestureLabels);

function createForm(device, config = {}) {
  let html = `<form class="gesture-form" data-device="${device}">`;
  gestures.forEach(gesture => {
    const defInfo = defaultGestures[device]?.[gesture] || null;
    html += `<div class="gesture-card">
      <div class="gesture-title">${gestureLabels[gesture]}</div>
      <select name="${gesture}" class="action-select">`;
    deviceActions[device].forEach((act, idx) => {
      let optionText = act.text;
      let optionValue = act.value;
      if (idx === 0 && defInfo) {
        optionText = `請選擇動作 // 預設: ${defInfo.desc}`;
        optionValue = defInfo.cmd;
      }
      const selected = config[gesture] === optionValue ? 'selected' : '';
      html += `<option value="${optionValue}" ${selected}>${optionText}</option>`;
    });
    html += `</select></div>`;
  });

  if (device === 'ac') {
    const tempValue = config.ac_init_temp ?? 0;
    html += `<div class="ac-temp-block" style="margin-top:16px;">
      <label>冷氣目前設定溫度：
        <input type="number" name="ac_init_temp" min="23" max="27" value="${tempValue}">
        °C
      </label>
    </div>`;
  }
  html += `</form>`;
  return html;
}

function loadAllConfigs(data = {}) {
  const container = document.getElementById('forms-container');
  container.innerHTML = '';
  ['tv', 'fan', 'ac'].forEach(device => {
    container.insertAdjacentHTML('beforeend', createForm(device, data[device] || {}));
  });
}
function updateCurrentModeUI(mode) {
  document.querySelectorAll('.mode-checkbox-block input[name="mode"]').forEach(r => {
    r.checked = r.value === mode;
  });
  document.getElementById('device-title').innerText =
    (mode === 'tv' ? '電視' : mode === 'fan' ? '電風扇' : '冷氣') + '手勢控制設定';
  document.querySelectorAll('.gesture-form').forEach(form => {
    form.style.display = form.dataset.device === mode ? 'block' : 'none';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  fetch('/get_gesture_config')
    .then(res => res.json())
    .then(data => {
      loadAllConfigs(data);
      updateCurrentModeUI(data.current_mode || 'tv');
    });

  document.querySelectorAll('.mode-checkbox-block input[name="mode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.checked) updateCurrentModeUI(radio.value);
    });
  });

  document.getElementById('save-all-btn').addEventListener('click', () => {
    const currentMode = document.querySelector('.mode-checkbox-block input[name="mode"]:checked')?.value;
    if (!currentMode) return alert('請先選擇目前模式');
    const configs = {};
    document.querySelectorAll('.gesture-form').forEach(form => {
      const dev = form.dataset.device;
      const fd = new FormData(form);
      configs[dev] = {};
      for (const [k, v] of fd.entries()) configs[dev][k] = v;
    });
    const acTemp = parseInt(configs.ac.ac_init_temp, 10);
    if (isNaN(acTemp) || acTemp < 23 || acTemp > 27) {
      return alert('冷氣溫度必須在 23~27 度');
    }
    fetch('/save_gesture_config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ configs, current_mode: currentMode })
    })
    .then(res => res.json())
    .then(data => alert(data.status === 'success' ? '設定已儲存' : '儲存失敗'))
    .catch(() => alert('儲存失敗'));
  });
});

document.getElementById('start-project-btn').addEventListener('click', () => {
  fetch('/start_gesture_project', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      document.getElementById('run-status').innerText = '執行狀態：' + data.status;
      alert('狀態：' + data.status);
    })
    .catch(() => alert('啟動失敗'));
});

document.getElementById('stop-project-btn').addEventListener('click', () => {
  fetch('/stop_gesture_project', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      document.getElementById('run-status').innerText = '執行狀態：' + data.status;
      alert('狀態：' + data.status);
    })
    .catch(() => alert('停止失敗'));
});

