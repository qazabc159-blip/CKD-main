const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');
const navLinks = document.querySelectorAll('.site-nav a');
const tabs = document.querySelectorAll('.workflow-tab');
const panels = document.querySelectorAll('.workflow-panel');
const reveals = document.querySelectorAll('.reveal');
const tiltCards = document.querySelectorAll('.tilt-card');
const sections = document.querySelectorAll('main section[id]');
const showcaseGauge = document.querySelector('.showcase-gauge');
const showcaseGaugeProgress = document.querySelector('.showcase-gauge-progress');
const heroStage = document.querySelector('.hero-stage');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const SHOWCASE_GAUGE_RADIUS = 62;
const SHOWCASE_GAUGE_CIRCUMFERENCE = 2 * Math.PI * SHOWCASE_GAUGE_RADIUS;

if (showcaseGaugeProgress) {
  showcaseGaugeProgress.style.strokeDasharray = `${SHOWCASE_GAUGE_CIRCUMFERENCE}`;
  showcaseGaugeProgress.style.strokeDashoffset = `${SHOWCASE_GAUGE_CIRCUMFERENCE}`;
}

if (menuToggle && nav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      nav.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    const key = tab.dataset.tab;
    tabs.forEach((button) => button.classList.toggle('active', button === tab));
    panels.forEach((panel) => panel.classList.toggle('active', panel.id === `panel-${key}`));
  });
});

if ('IntersectionObserver' in window && reveals.length) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.14 });

  reveals.forEach((section) => revealObserver.observe(section));
} else {
  reveals.forEach((section) => section.classList.add('is-visible'));
}

function animateShowcaseGauge() {
  if (!showcaseGauge || !showcaseGaugeProgress || showcaseGauge.dataset.animated === 'true') return;

  const score = Number(showcaseGauge.dataset.score || '0');
  const clampedScore = Math.max(0, Math.min(1, score));
  const offset = SHOWCASE_GAUGE_CIRCUMFERENCE * (1 - clampedScore);
  showcaseGauge.dataset.animated = 'true';

  if (prefersReducedMotion) {
    showcaseGaugeProgress.style.strokeDashoffset = `${offset}`;
    return;
  }

  showcaseGaugeProgress.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)';
  requestAnimationFrame(() => {
    showcaseGaugeProgress.style.strokeDashoffset = `${offset}`;
  });
}

if (showcaseGauge && showcaseGaugeProgress) {
  if ('IntersectionObserver' in window) {
    const gaugeObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateShowcaseGauge();
        observer.disconnect();
      });
    }, { threshold: 0.28 });

    gaugeObserver.observe(heroStage || showcaseGauge);
  } else {
    animateShowcaseGauge();
  }
}

if ('IntersectionObserver' in window && sections.length) {
  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      navLinks.forEach((link) => {
        link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`);
      });
    });
  }, { threshold: 0.28 });

  sections.forEach((section) => navObserver.observe(section));
}

tiltCards.forEach((card) => {
  card.addEventListener('pointermove', (event) => {
    if (window.innerWidth <= 900) return;
    const rect = card.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    const ry = ((px - 0.5) * 8).toFixed(2);
    const rx = ((0.5 - py) * 8).toFixed(2);
    card.style.setProperty('--ry', `${ry}deg`);
    card.style.setProperty('--rx', `${rx}deg`);
  });

  card.addEventListener('pointerleave', () => {
    card.style.setProperty('--ry', '0deg');
    card.style.setProperty('--rx', '0deg');
  });
});
