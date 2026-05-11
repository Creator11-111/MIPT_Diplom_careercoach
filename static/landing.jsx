/* global React, ReactDOM */
const { useState, useEffect, useMemo, useRef } = React;
const D = window.COACH_DATA;

// ============ Tiny helpers ============
function fmtMoney(k) {
  return new Intl.NumberFormat("ru-RU").format(k * 1000);
}
function rangeStr(from, to) {
  return `${fmtMoney(from)} – ${fmtMoney(to)} ₽`;
}

// ============ Landing ============
function Landing({ onStart, tweak }) {
  return (
    <div className="shell">
      <Topbar active="home" />
      <section className="hero">
        <div>
          <div className="eyebrow">Карьерный консьерж · финансовый сектор</div>
          <h1>
            Карьера<br/>как <span className="ital">портфель</span>.<br/>
            Управляем стратегически.
          </h1>
          <p className="lead">
            Финансовый карьерный коуч строит вашу траекторию на 3–5 лет вперёд:
            подбирает 20 точных вакансий по рынку, формирует план обучения
            и показывает позиции, до которых вы дорастёте.
          </p>
          <div className="hero-cta">
            <button className="btn accent" onClick={onStart}>
              Начать интервью →
            </button>
            <button className="btn ghost">Войти через hh.ru</button>
          </div>
          <div className="hero-meta">
            <div>
              <div className="num">12 480</div>
              <div className="lbl">Вакансий в индексе</div>
            </div>
            <div>
              <div className="num">8 мин</div>
              <div className="lbl">Среднее интервью</div>
            </div>
            <div>
              <div className="num">94<span style={{fontSize:24,color:'var(--c-accent)'}}>%</span></div>
              <div className="lbl">Релевантность подбора</div>
            </div>
          </div>
        </div>

        <div className="hero-art">
          <div className="hero-art-head">
            <div>
              <div className="eyebrow">Coach Briefing</div>
              <div style={{fontFamily:'var(--f-display)', fontSize:28, marginTop:8, lineHeight:1.1}}>
                №&nbsp;{tweak.briefingNo}<br/>
                <span style={{color:'var(--c-accent)', fontStyle:'italic'}}>{tweak.briefingYear}</span>
              </div>
            </div>
            <div style={{fontFamily:'var(--f-mono)', fontSize:11, color:'var(--c-ink-3)', textAlign:'right'}}>
              CONFIDENTIAL<br/>
              FOR&nbsp;CLIENT&nbsp;USE
            </div>
          </div>
          <div className="hero-art-foot">
            <div className="eyebrow" style={{marginBottom: 10}}>Сегменты подбора</div>
            <div style={{fontFamily:'var(--f-display)', fontSize:22, fontWeight:500, lineHeight:1.4}}>
              Investment Banking · Asset Management · Corporate Finance · Risk · Fintech
            </div>
            <div style={{borderTop:'1px solid var(--c-line)', marginTop:18, paddingTop:14, display:'flex', justifyContent:'space-between', fontFamily:'var(--f-mono)', fontSize:11, color:'var(--c-ink-3)'}}>
              <span>v 2.4 · MIPT × HSE</span>
              <span>{new Date().toLocaleDateString('ru-RU')}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="process">
        <div className="eyebrow">Как это работает</div>
        <h2 className="serif" style={{fontSize:42, fontWeight:500, margin:'10px 0 0', letterSpacing:'-0.02em'}}>
          Три шага до <span style={{color:'var(--c-accent)', fontStyle:'italic'}}>карты карьеры</span>.
        </h2>
        <div className="process-grid">
          <div className="process-step">
            <div className="num">01</div>
            <h4>Интервью с AI-коучем</h4>
            <p>8 точных вопросов о роли, навыках, целях и ожиданиях. Без анкет — диалог в темпе разговора.</p>
          </div>
          <div className="process-step">
            <div className="num">02</div>
            <h4>Семантический подбор</h4>
            <p>FAISS&nbsp;+&nbsp;LLM-фильтрация по 12 480 актуальным вакансиям. Каскад из четырёх стадий.</p>
          </div>
          <div className="process-step">
            <div className="num">03</div>
            <h4>Карта развития</h4>
            <p>20 вакансий по рынку, программа обучения и позиции на вырост — с разрывом по навыкам и срокам.</p>
          </div>
        </div>
      </section>
    </div>
  );
}

// ============ Topbar (shared) ============
function Topbar({ active }) {
  return (
    <div className="topbar">
      <div className="brand">
        <div className="brand-mark">M</div>
        <div className="brand-name">
          Méridien
          <small>Financial Career Coach</small>
        </div>
      </div>
      <nav className="topnav">
        <a href="#" className={active==='home'?'active':''}>Главная</a>
        <a href="#" className={active==='dash'?'active':''}>Кабинет</a>
        <a href="#">Методология</a>
        <a href="#">Об авторе</a>
      </nav>
      <div className="topright">
        <span className="mono">RU · ₽</span>
        <ThemeToggle/>
      </div>
    </div>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(document.documentElement.getAttribute('data-theme') === 'dark');
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  }, [dark]);
  return (
    <button className="theme-toggle" onClick={() => setDark(d => !d)} title="Сменить тему">
      {dark ? "☼" : "☾"}
    </button>
  );
}

window.Landing = Landing;
window.Topbar = Topbar;
window.fmtMoney = fmtMoney;
window.rangeStr = rangeStr;
