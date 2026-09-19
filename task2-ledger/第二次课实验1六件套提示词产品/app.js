const root = document.documentElement;
const progressBar = document.querySelector("#progress-bar");
const backToTop = document.querySelector("#back-to-top");
const themeToggle = document.querySelector("#theme-toggle");
const copySummary = document.querySelector("#copy-summary");
const toast = document.querySelector("#toast");
const navLinks = [...document.querySelectorAll(".jump-nav a")];
const routeTabs = [...document.querySelectorAll(".route-tab")];
const routePanel = document.querySelector("#route-panel");
const routeLabel = document.querySelector("#route-label");
const routeGoal = document.querySelector("#route-goal");
const routeSteps = document.querySelector("#route-steps");

const routes = {
  newcomer: {
    label: "推荐：现代模式",
    goal: "目标不是帅，是先打完整一局",
    steps: [
      ["15 min", "角色指南", "只记一个对空和一个远距离牵制技。"],
      ["20 min", "训练场", "练一套轻攻击确认，能稳定收尾就停。"],
      ["25 min", "直接排位", "别去休闲房接千小时老哥的“新手教学”。"],
    ],
  },
  action: {
    label: "推荐：现代 / 经典都行",
    goal: "先把闪避思维收起来，学会站着防",
    steps: [
      ["15 min", "摸清系统", "试一遍 Drive Rush、格挡和 DI 的资源消耗。"],
      ["20 min", "改掉空挥", "录制木桩反击，感受什么叫“按键要付账”。"],
      ["25 min", "打定级赛", "只盯对空和防守，别急着复刻视频连段。"],
    ],
  },
  veteran: {
    label: "推荐：直接进训练场",
    goal: "先查绿冲路线，再查版本习惯",
    steps: [
      ["15 min", "确认改动", "看角色指南与帧数，确认主力技和取消窗口。"],
      ["20 min", "资源路线", "准备一套省 Drive、一套爆发、一套 Burnout 压制。"],
      ["25 min", "角色排位", "利用独立段位实战校准，录像里专抓漏确反。"],
    ],
  },
};

let toastTimer;
let ticking = false;

function showToast(message) {
  window.clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("visible");
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 2200);
}

function updateScrollUi() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? Math.min(window.scrollY / scrollable, 1) : 0;
  progressBar.style.width = `${progress * 100}%`;
  backToTop.classList.toggle("visible", window.scrollY > window.innerHeight * 0.75);
  ticking = false;
}

function requestScrollUpdate() {
  if (!ticking) {
    window.requestAnimationFrame(updateScrollUi);
    ticking = true;
  }
}

function applyTheme(theme) {
  root.dataset.theme = theme;
  const dark = theme === "dark";
  themeToggle.setAttribute("aria-pressed", String(dark));
  themeToggle.title = dark ? "切换为浅色主题" : "切换为深色主题";
  document.querySelector('meta[name="theme-color"]').content = dark ? "#16181d" : "#f3f1ea";
}

function setRoute(routeName) {
  const route = routes[routeName];
  if (!route) return;

  routeTabs.forEach((tab) => {
    const active = tab.dataset.route === routeName;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  });

  routePanel.classList.add("is-switching");
  window.setTimeout(() => {
    routeLabel.textContent = route.label;
    routeGoal.textContent = route.goal;
    routeSteps.innerHTML = route.steps
      .map(
        ([time, title, detail]) =>
          `<li><span>${time}</span><p><strong>${title}</strong>：${detail}</p></li>`,
           )
      .join("");
    routePanel.classList.remove("is-switching");
  }, 120);
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const helper = document.createElement("textarea");
  helper.value = text;
  helper.setAttribute("readonly", "");
  helper.style.position = "fixed";
  helper.style.opacity = "0";
  document.body.appendChild(helper);
  helper.select();
  document.execCommand("copy");
  helper.remove();
}

const sectionObserver = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;
    navLinks.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === `#${visible.target.id}`);
    });
  },
  { rootMargin: "-24% 0px -62%", threshold: [0, 0.1, 0.4] },
);

document.querySelectorAll("#summary, #highlights, #cons, #starter").forEach((section) => {
  sectionObserver.observe(section);
});

const revealObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
           entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    });
  },
  { rootMargin: "0px 0px -8%", threshold: 0.08 },
);

document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

window.addEventListener("scroll", requestScrollUpdate, { passive: true });
window.addEventListener("resize", requestScrollUpdate);

backToTop.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
});

themeToggle.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  localStorage.setItem("sf6-review-theme", nextTheme);
});

copySummary.addEventListener("click", async () => {
  const summary =
    "《街头霸王6》省流：对战系统 9/10，入门引导 9/10，单人内容 7/10，收费观感 5/10。只玩剧情建议等折扣；愿意碰排位，本体就很值。现代模式能让新人先学博弈，Drive 系统和回滚网络则足够老玩家长期深挖。";

  try {
    await copyText(summary);
    showToast("省流已复制，去论坛开团吧");
  } catch {
    showToast("浏览器没有给剪贴板权限");
  }
});

routeTabs.forEach((tab) => {
  tab.addEventListener("click", () => setRoute(tab.dataset.route));
});

const savedTheme = localStorage.getItem("sf6-review-theme");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
applyTheme(savedTheme || (prefersDark ? "dark" : "light"));
updateScrollUi();
