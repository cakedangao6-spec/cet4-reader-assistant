(function () {
  const STORAGE_KEY = "cet4_2025_06_1_player_state";
  const data = structuredClone(window.CET4_DATA);
  const timeline = window.CET4_TIMELINE || { segments: [] };
  const groups = new Map(data.groups.map((group) => [group.id, group]));
  let selectedId = 1;
  let loopA = null;
  let loopB = null;
  let loopEnabled = false;
  let objectUrl = null;
  let searchTerm = "";

  const els = {};

  document.addEventListener("DOMContentLoaded", () => {
    bindElements();
    restoreState();
    bindEvents();
    initialiseAudio();
    render();
  });

  function bindElements() {
    [
      "answerPdfLink",
      "applyTimingButton",
      "audioInput",
      "clearLoopButton",
      "countLabel",
      "currentTime",
      "detailContent",
      "duration",
      "jsonInput",
      "loopAInput",
      "loopBInput",
      "loopStatus",
      "mediaLabel",
      "player",
      "questionEndInput",
      "questionList",
      "questionStartInput",
      "questionText",
      "saveJsonButton",
      "searchInput",
      "selectedTitle",
      "setAButton",
      "setBButton",
      "setQuestionTimeButton",
      "speedSelect",
      "timingBadge",
      "toggleLoopButton",
      "useQuestionLoopButton"
    ].forEach((id) => {
      els[id] = document.getElementById(id);
    });
  }

  function bindEvents() {
    els.audioInput.addEventListener("change", handleAudioImport);
    els.jsonInput.addEventListener("change", handleJsonImport);
    els.saveJsonButton.addEventListener("click", saveJson);
    els.searchInput.addEventListener("input", () => {
      searchTerm = els.searchInput.value.trim();
      render();
    });

    els.speedSelect.addEventListener("change", () => {
      els.player.playbackRate = Number(els.speedSelect.value);
      persistState();
    });

    els.player.addEventListener("loadedmetadata", () => {
      els.duration.textContent = formatTime(els.player.duration);
    });

    els.player.addEventListener("timeupdate", () => {
      els.currentTime.textContent = formatTime(els.player.currentTime);
      handleLoop();
      renderPlayingState();
    });

    els.setQuestionTimeButton.addEventListener("click", () => {
      const question = getSelectedQuestion();
      question.start = roundTime(els.player.currentTime);
      if (!Number.isFinite(question.end) || question.end <= question.start) {
        question.end = roundTime(Math.min(question.start + 25, safeDuration()));
      }
      data.timingStatus = "custom";
      persistState();
      render();
    });

    els.setAButton.addEventListener("click", () => {
      loopA = roundTime(els.player.currentTime);
      if (Number.isFinite(loopB) && loopB <= loopA) loopB = null;
      renderLoop();
    });

    els.setBButton.addEventListener("click", () => {
      loopB = roundTime(els.player.currentTime);
      if (Number.isFinite(loopA) && loopB <= loopA) loopA = null;
      renderLoop();
    });

    els.useQuestionLoopButton.addEventListener("click", () => {
      const question = getSelectedQuestion();
      loopA = question.start;
      loopB = question.end || getNextStart(question.id);
      loopEnabled = Number.isFinite(loopA) && Number.isFinite(loopB) && loopB > loopA;
      if (loopEnabled) els.player.currentTime = loopA;
      renderLoop();
    });

    els.toggleLoopButton.addEventListener("click", () => {
      loopEnabled = !loopEnabled;
      if (loopEnabled && (!Number.isFinite(loopA) || !Number.isFinite(loopB) || loopB <= loopA)) {
        const question = getSelectedQuestion();
        loopA = question.start;
        loopB = question.end || getNextStart(question.id);
      }
      loopEnabled = loopEnabled && Number.isFinite(loopA) && Number.isFinite(loopB) && loopB > loopA;
      renderLoop();
    });

    els.clearLoopButton.addEventListener("click", () => {
      loopA = null;
      loopB = null;
      loopEnabled = false;
      renderLoop();
    });

    els.loopAInput.addEventListener("change", () => {
      loopA = parseTime(els.loopAInput.value);
      renderLoop();
    });

    els.loopBInput.addEventListener("change", () => {
      loopB = parseTime(els.loopBInput.value);
      renderLoop();
    });

    els.applyTimingButton.addEventListener("click", () => {
      const question = getSelectedQuestion();
      const start = parseTime(els.questionStartInput.value);
      const end = parseTime(els.questionEndInput.value);
      if (Number.isFinite(start)) question.start = roundTime(start);
      if (Number.isFinite(end)) question.end = roundTime(end);
      if (Number.isFinite(question.end) && question.end <= question.start) {
        question.end = roundTime(question.start + 1);
      }
      data.timingStatus = "custom";
      persistState();
      render();
    });

    els.detailContent.addEventListener("click", (event) => {
      const marker = event.target.closest("[data-marker-id]");
      if (marker) {
        seekToQuestion(Number(marker.dataset.markerId), true);
        return;
      }

      const timelineButton = event.target.closest("[data-timeline-id]");
      if (!timelineButton) return;
      const segment = timeline.segments.find((item) => item.id === Number(timelineButton.dataset.timelineId));
      if (!segment) return;
      if (timelineButton.dataset.timelineAction === "loop") {
        loopA = segment.start;
        loopB = segment.end;
        loopEnabled = true;
        els.player.currentTime = segment.start;
        els.player.play().catch(() => {});
        renderLoop();
        renderPlayingState();
      } else {
        seekToTime(segment.start, true);
      }
    });
  }

  function initialiseAudio() {
    els.player.src = data.audioFile;
    els.answerPdfLink.href = data.answerPdf;
    els.mediaLabel.textContent = data.audioFile.replace("materials/listening/25-6-1/", "");
    els.player.playbackRate = Number(els.speedSelect.value);
  }

  function restoreState() {
    try {
      const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      if (Array.isArray(state.questions)) mergeQuestions(state.questions);
      if (Number.isFinite(state.selectedId)) selectedId = state.selectedId;
      if (Number.isFinite(state.loopA)) loopA = state.loopA;
      if (Number.isFinite(state.loopB)) loopB = state.loopB;
      if (typeof state.loopEnabled === "boolean") loopEnabled = state.loopEnabled;
      if (state.timingStatus) data.timingStatus = state.timingStatus;
      if (state.speed) {
        els.speedSelect.value = String(state.speed);
      }
    } catch (error) {
      console.warn("Could not restore saved CET-4 player state.", error);
    }
  }

  function persistState() {
    const state = {
      selectedId,
      loopA,
      loopB,
      loopEnabled,
      speed: Number(els.speedSelect.value),
      timingStatus: data.timingStatus,
      questions: data.questions.map(({ id, start, end }) => ({ id, start, end }))
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function mergeQuestions(questions) {
    const byId = new Map(data.questions.map((question) => [question.id, question]));
    questions.forEach((incoming) => {
      const target = byId.get(incoming.id);
      if (!target) return;
      if (Number.isFinite(incoming.start)) target.start = incoming.start;
      if (Number.isFinite(incoming.end)) target.end = incoming.end;
    });
  }

  function render() {
    const question = getSelectedQuestion();
    renderQuestionList();
    renderQuestionEditor(question);
    renderDetails(question);
    renderLoop();
    renderPlayingState();
    els.countLabel.textContent = String(filteredQuestions().length);
  }

  function renderQuestionList() {
    const fragment = document.createDocumentFragment();
    const filtered = filteredQuestions();

    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "无匹配题目";
      fragment.appendChild(empty);
    }

    filtered.forEach((question) => {
      const group = groups.get(question.groupId);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "question-button";
      button.dataset.questionId = String(question.id);
      button.addEventListener("click", () => seekToQuestion(question.id, true));

      const qid = document.createElement("span");
      qid.className = "qid";
      qid.textContent = String(question.id);

      const meta = document.createElement("span");
      meta.className = "qmeta";
      meta.textContent = `${group.section} · ${group.title}`;

      const time = document.createElement("span");
      time.className = "qtime";
      time.textContent = formatTime(question.start);

      button.append(qid, meta, time);
      fragment.appendChild(button);
    });

    els.questionList.replaceChildren(fragment);
  }

  function renderQuestionEditor(question) {
    const group = groups.get(question.groupId);
    els.selectedTitle.textContent = `Question ${question.id} · ${group.title}`;
    els.timingBadge.textContent = data.timingStatus === "custom" ? "已自定义" : "估算时间";
    els.questionStartInput.value = formatTime(question.start);
    els.questionEndInput.value = formatTime(question.end);

    const choices = Object.entries(question.choices)
      .map(([key, value]) => `<div class="choice ${key === question.answer ? "correct" : ""}"><strong>${key})</strong> ${escapeHtml(value)}</div>`)
      .join("");

    els.questionText.innerHTML = `
      <h3>${escapeHtml(question.stem)}</h3>
      <div class="choices">${choices}</div>
    `;
  }

  function renderDetails(question) {
    const group = groups.get(question.groupId);
    const answer = `${question.answer}) ${question.choices[question.answer]}`;
    els.detailContent.innerHTML = `
      <section class="detail-block">
        <h3>${escapeHtml(group.section)} · ${escapeHtml(group.title)}</h3>
        <div class="transcript">${renderTranscript(group.transcript)}</div>
      </section>
      <section class="detail-block">
        <h3>答案</h3>
        <div class="answer-line">${escapeHtml(answer)}</div>
      </section>
      <section class="detail-block">
        <h3>解析</h3>
        <p>${highlight(escapeHtml(question.analysis))}</p>
      </section>
      <section class="detail-block">
        <h3>AI 时间轴</h3>
        ${renderTimeline(question)}
      </section>
    `;
  }

  function renderLoop() {
    els.loopAInput.value = Number.isFinite(loopA) ? formatTime(loopA) : "";
    els.loopBInput.value = Number.isFinite(loopB) ? formatTime(loopB) : "";
    const valid = Number.isFinite(loopA) && Number.isFinite(loopB) && loopB > loopA;
    if (!valid) loopEnabled = false;
    els.toggleLoopButton.classList.toggle("active", loopEnabled);
    els.toggleLoopButton.setAttribute("aria-pressed", String(loopEnabled));
    els.loopStatus.textContent = valid
      ? `${formatTime(loopA)} - ${formatTime(loopB)}${loopEnabled ? " 循环中" : ""}`
      : "A-B 未启用";
    persistState();
  }

  function renderPlayingState() {
    const current = els.player.currentTime;
    const active = getActiveQuestion(current);
    document.querySelectorAll(".question-button").forEach((button) => {
      const id = Number(button.dataset.questionId);
      button.classList.toggle("selected", id === selectedId);
      button.classList.toggle("playing", active && id === active.id);
    });
    document.querySelectorAll(".timeline-item").forEach((item) => {
      const start = Number(item.dataset.start);
      const end = Number(item.dataset.end);
      item.classList.toggle("active", current >= start && current < end);
    });
  }

  function filteredQuestions() {
    if (!searchTerm) return data.questions;
    const needle = searchTerm.toLowerCase();
    return data.questions.filter((question) => {
      const group = groups.get(question.groupId);
      const relatedTimeline = getTimelineForQuestion(question).map((segment) => segment.text).join(" ");
      const haystack = [
        question.id,
        question.stem,
        question.answer,
        question.analysis,
        Object.values(question.choices).join(" "),
        group.title,
        group.transcript,
        relatedTimeline
      ].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }

  function seekToQuestion(id, play) {
    const question = data.questions.find((item) => item.id === id);
    if (!question) return;
    selectedId = id;
    els.player.currentTime = Number.isFinite(question.start) ? question.start : 0;
    if (play) {
      els.player.play().catch(() => {});
    }
    persistState();
    render();
  }

  function seekToTime(time, play) {
    if (!Number.isFinite(time)) return;
    els.player.currentTime = time;
    const active = getActiveQuestion(time);
    if (active) selectedId = active.id;
    if (play) {
      els.player.play().catch(() => {});
    }
    persistState();
    render();
  }

  function handleLoop() {
    if (!loopEnabled || !Number.isFinite(loopA) || !Number.isFinite(loopB)) return;
    if (els.player.currentTime >= loopB) {
      els.player.currentTime = loopA;
      els.player.play().catch(() => {});
    }
  }

  function handleAudioImport(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    els.player.src = objectUrl;
    els.mediaLabel.textContent = file.name;
    els.player.load();
  }

  function handleJsonImport(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const incoming = JSON.parse(String(reader.result || "{}"));
        const payload = Array.isArray(incoming.questions) ? incoming : incoming.data;
        if (!payload || !Array.isArray(payload.questions)) throw new Error("Invalid JSON");
        mergeQuestions(payload.questions);
        data.timingStatus = "custom";
        persistState();
        render();
      } catch (error) {
        window.alert("JSON 格式不正确。");
      }
    };
    reader.readAsText(file, "utf-8");
  }

  function saveJson() {
    const payload = {
      savedAt: new Date().toISOString(),
      source: data.title,
      data
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "cet4_2025_06_1_timings.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function getSelectedQuestion() {
    return data.questions.find((question) => question.id === selectedId) || data.questions[0];
  }

  function getActiveQuestion(time) {
    return data.questions.find((question) => {
      const start = Number.isFinite(question.start) ? question.start : -Infinity;
      const end = Number.isFinite(question.end) ? question.end : getNextStart(question.id);
      return time >= start && time < end;
    });
  }

  function getNextStart(id) {
    const index = data.questions.findIndex((question) => question.id === id);
    const next = data.questions[index + 1];
    if (next && Number.isFinite(next.start)) return next.start;
    return safeDuration();
  }

  function getTimelineForQuestion(question) {
    if (!timeline.segments.length) return [];
    const start = Number.isFinite(question.start) ? Math.max(0, question.start - 4) : 0;
    const end = Number.isFinite(question.end) ? question.end : getNextStart(question.id);
    return timeline.segments.filter((segment) => {
      const belongsToQuestion = segment.questionId === question.id;
      const inRange = segment.start >= start && segment.start < end;
      return belongsToQuestion || inRange;
    });
  }

  function safeDuration() {
    return Number.isFinite(els.player.duration) && els.player.duration > 0 ? els.player.duration : 1416;
  }

  function parseTime(value) {
    const clean = String(value || "").trim();
    if (!clean) return null;
    if (/^\d+(\.\d+)?$/.test(clean)) return Number(clean);
    const parts = clean.split(":").map(Number);
    if (parts.some((part) => !Number.isFinite(part))) return null;
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    return null;
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return "--:--";
    const total = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function roundTime(value) {
    return Math.round(Number(value) * 10) / 10;
  }

  function renderTranscript(text) {
    const escaped = highlight(escapeHtml(text));
    return escaped.replace(/\[(\d{1,2})\]/g, (_match, id) => {
      return `<button class="marker" type="button" data-marker-id="${id}">[${id}]</button>`;
    });
  }

  function renderTimeline(question) {
    const segments = getTimelineForQuestion(question);
    if (!segments.length) {
      return `<div class="empty">暂无 AI 时间轴。运行 scripts/generate_timeline.py 后会显示。</div>`;
    }
    const rows = segments.map((segment) => {
      const text = highlight(escapeHtml(segment.text));
      return `
        <div class="timeline-item" data-start="${segment.start}" data-end="${segment.end}">
          <button class="timeline-play" type="button" data-timeline-id="${segment.id}" data-timeline-action="play">
            <span>${formatTime(segment.start)}-${formatTime(segment.end)}</span>
            <span>${text}</span>
          </button>
          <button class="timeline-loop" type="button" data-timeline-id="${segment.id}" data-timeline-action="loop">循环</button>
        </div>
      `;
    }).join("");
    return `
      <p class="timeline-note">由本地 faster-whisper base.en 自动生成；适合快速定位句子，个别识别词可能与标准原文不同。</p>
      <div class="timeline-list">${rows}</div>
    `;
  }

  function highlight(html) {
    if (!searchTerm) return html;
    const escapedNeedle = escapeRegExp(escapeHtml(searchTerm));
    if (!escapedNeedle) return html;
    return html.replace(new RegExp(`(${escapedNeedle})`, "gi"), "<mark>$1</mark>");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
})();
