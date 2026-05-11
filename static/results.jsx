/* global React */
const { useState: useStateR, useMemo: useMemoR } = React;

function Results({ onRestart, tweak }) {
  const D = window.COACH_DATA;
  const { profile, vacancies, courses, growth, salaryMarket, trajectory, adjacent } = D;

  const [tab, setTab] = useStateR("now"); // now | learn | next | path | adj
  const [filter, setFilter] = useStateR("Все");
  const [openVac, setOpenVac] = useStateR(null);

  const sectors = ["Все", "Investment Banking", "Asset Management", "Corporate", "Banking", "Tech", "Audit", "Fintech"];
  const filtered = vacancies.filter(v => filter === "Все" || v.sector === filter);

  return (
    <div className="shell">
      <Topbar active="dash" />

      {/* Hero */}
      <section className="res-hero">
        <div>
          <div className="eyebrow">Карта карьеры · {profile.name}</div>
          <h1 className="res-title">
            Senior Финансовый Аналитик<br/>
            <span className="accent">→ Head of Investment Strategy</span>
          </h1>
          <div className="muted" style={{maxWidth:540, fontSize:15}}>
            На основе ваших ответов и индекса из 12 480 вакансий мы построили
            карту с тремя горизонтами: текущий рынок, программа развития
            и позиции, до которых вы дорастёте за 12–18 месяцев.
          </div>
        </div>
        <div className="kpi-strip">
          <div className="kpi"><div className="lbl">Текущая ЗП</div><div className="val">{profile.salaryCurrent}<small style={{fontSize:14, color:'var(--c-ink-3)', fontFamily:'var(--f-body)', marginLeft:4}}>тыс. ₽</small></div><div className="delta">медиана рынка: 420</div></div>
          <div className="kpi"><div className="lbl">Целевая ЗП</div><div className="val">{profile.salaryTarget}<small style={{fontSize:14, color:'var(--c-ink-3)', fontFamily:'var(--f-body)', marginLeft:4}}>тыс. ₽</small></div><div className="delta">+97% за 18 мес.</div></div>
          <div className="kpi"><div className="lbl">Покрытие навыков</div><div className="val">74<span style={{fontSize:18, color:'var(--c-accent)'}}>%</span></div><div className="delta">+12 п.п. с курсами</div></div>
          <div className="kpi"><div className="lbl">Подобрано вакансий</div><div className="val">{vacancies.length}</div><div className="delta">из 12 480 в индексе</div></div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="roadmap">
        <div className="roadmap-rail"></div>
        <div className="roadmap-track">
          <div className="rm-station">
            <div className="rm-eyebrow">Горизонт I · Сейчас</div>
            <div className="rm-dot filled"></div>
            <h3>20 вакансий по рынку</h3>
            <div className="rm-sub">Подходят прямо сейчас по навыкам и опыту</div>
            <div className="rm-meta">
              <div>Match&nbsp;<b>96%</b></div>
              <div>До&nbsp;<b>{fmtMoney(550)} ₽</b></div>
              <div>Срок&nbsp;<b>1–3 мес.</b></div>
            </div>
            <button className="btn ghost small" style={{marginTop:18}} onClick={() => setTab("now")}>Смотреть подбор →</button>
          </div>
          <div className="rm-station">
            <div className="rm-eyebrow">Горизонт II · Развитие</div>
            <div className="rm-dot"></div>
            <h3>Программа обучения</h3>
            <div className="rm-sub">6 курсов закрывают разрыв до целевой роли</div>
            <div className="rm-meta">
              <div>Курсов&nbsp;<b>6</b></div>
              <div>Длительность&nbsp;<b>6–9 мес.</b></div>
              <div>Бюджет&nbsp;<b>~$3 800</b></div>
            </div>
            <button className="btn ghost small" style={{marginTop:18}} onClick={() => setTab("learn")}>Смотреть план →</button>
          </div>
          <div className="rm-station">
            <div className="rm-eyebrow">Горизонт III · Цель</div>
            <div className="rm-dot"></div>
            <h3>Позиции на вырост</h3>
            <div className="rm-sub">До этих ролей вы дорастёте за 12–18 месяцев</div>
            <div className="rm-meta">
              <div>Позиций&nbsp;<b>{growth.length}</b></div>
              <div>До&nbsp;<b>{fmtMoney(1100)} ₽</b></div>
              <div>Срок&nbsp;<b>12–18 мес.</b></div>
            </div>
            <button className="btn ghost small" style={{marginTop:18}} onClick={() => setTab("next")}>Смотреть рост →</button>
          </div>
        </div>
      </section>

      {/* Tabs */}
      <div className="tabs">
        <button className={"tab" + (tab==="now"?" active":"")} onClick={() => setTab("now")}>
          Текущий подбор<span className="count">{vacancies.length}</span>
        </button>
        <button className={"tab" + (tab==="learn"?" active":"")} onClick={() => setTab("learn")}>
          План обучения<span className="count">{courses.length}</span>
        </button>
        <button className={"tab" + (tab==="next"?" active":"")} onClick={() => setTab("next")}>
          Позиции на вырост<span className="count">{growth.length}</span>
        </button>
        <button className={"tab" + (tab==="path"?" active":"")} onClick={() => setTab("path")}>
          Карьерная траектория<span className="count">{trajectory.length}</span>
        </button>
        <button className={"tab" + (tab==="adj"?" active":"")} onClick={() => setTab("adj")}>
          Смежные отрасли<span className="count">{adjacent.length}</span>
        </button>
      </div>

      {/* Body */}
      <div className="results-grid">
        <div>
          {tab === "now" && (
            <>
              <div className="filters">
                {sectors.map(s => (
                  <button key={s} className={"filter" + (filter===s?" active":"")} onClick={() => setFilter(s)}>{s}</button>
                ))}
                <span className="count">{filtered.length} вакансий</span>
              </div>
              <div className="vac-list">
                {filtered.map(v => (
                  <div key={v.id} className={"vac" + (openVac?.id===v.id?" active":"")} onClick={() => setOpenVac(v)}>
                    <div className="vac-logo">{v.logo}</div>
                    <div>
                      <div className="vac-title">{v.title}</div>
                      <div className="vac-meta">
                        <span>{v.company}</span>
                        <span className="sep"></span>
                        <span>{v.city} · {v.remote}</span>
                        <span className="sep"></span>
                        <span className="mono">{v.posted}</span>
                      </div>
                      <div className="vac-skills">
                        {v.skills.slice(0,4).map(s => <span key={s} className="vac-skill">{s}</span>)}
                      </div>
                    </div>
                    <div className="vac-right">
                      <div className="vac-salary">{v.salaryFrom}–{v.salaryTo}<small>тыс. ₽</small></div>
                      <div className="vac-match">MATCH {v.match}%</div>
                    </div>
                    {v.badge && <div className="vac-badge">{v.badge}</div>}
                  </div>
                ))}
              </div>
            </>
          )}

          {tab === "learn" && <LearnPlan courses={courses} profile={profile} />}

          {tab === "next" && <GrowthList items={growth} onOpen={setOpenVac} />}

          {tab === "path" && <TrajectoryLadder steps={trajectory} />}

          {tab === "adj" && <AdjacentIndustries items={adjacent} />}
        </div>

        {/* Aside */}
        <aside>
          <div className="aside-panel">
            <div className="eyebrow">Профиль</div>
            <h3 className="serif" style={{fontSize:22, fontWeight:500, margin:'8px 0 14px'}}>{profile.role}</h3>
            <div style={{fontSize:13, color:'var(--c-ink-2)', marginBottom: 18}}>
              {profile.seniority} · {profile.years} лет · {profile.field}<br/>
              <span className="muted">{profile.location}</span>
            </div>
            <div className="eyebrow" style={{marginBottom:10}}>Сильные стороны</div>
            {profile.skills.slice(0,5).map(s => (
              <div className="skillrow" key={s.name}>
                <div className="name">{s.name}</div>
                <div className="bar"><i style={{width: (s.level*100)+"%"}}/></div>
                <div className="num">{Math.round(s.level*100)}</div>
              </div>
            ))}
            <button className="btn ghost small" style={{marginTop:14, width:'100%'}} onClick={onRestart}>Пройти заново</button>
          </div>

          <div className="aside-panel">
            <div className="eyebrow">Зарплата по рынку</div>
            <div style={{fontSize:13, color:'var(--c-ink-2)', margin:'8px 0 4px'}}>
              Senior Financial Analyst · Москва
            </div>
            <SalaryChart data={salaryMarket} highlightBucket="400–500" />
            <div style={{display:'flex', justifyContent:'space-between', marginTop:14, fontSize:12}}>
              <div className="muted">Медиана</div>
              <div className="mono"><b>{fmtMoney(420)} ₽</b></div>
            </div>
            <div style={{display:'flex', justifyContent:'space-between', marginTop:4, fontSize:12}}>
              <div className="muted">Ваша позиция</div>
              <div className="mono accent-text">{fmtMoney(profile.salaryCurrent)} ₽ · p38</div>
            </div>
          </div>

          <div className="aside-panel">
            <div className="eyebrow">Gap-анализ</div>
            <div className="donut-row" style={{margin:'14px 0'}}>
              <Donut value={0.74} />
              <div>
                <div className="donut-num">74<small>%</small></div>
                <div style={{fontSize:12, color:'var(--c-ink-3)'}}>покрытие до целевой роли</div>
              </div>
            </div>
            <div style={{fontSize:12, color:'var(--c-ink-2)', lineHeight:1.6}}>
              Закрыть: <b>CFA II</b>, <b>стратегическое лидерство</b>, <b>M&A на стороне buy-side</b>.
              План в разделе «Обучение».
            </div>
          </div>
        </aside>
      </div>

      {openVac && <VacancyDrawer vac={openVac} onClose={() => setOpenVac(null)} profile={profile} />}
    </div>
  );
}

function SalaryChart({ data, highlightBucket }) {
  const max = Math.max(...data.map(d => d.count));
  return (
    <>
      <div className="salary-chart">
        {data.map(d => (
          <div key={d.bucket}
            className={"col" + (d.bucket===highlightBucket?" highlight":"")}
            style={{ height: (d.count/max*100) + "%" }}>
          </div>
        ))}
      </div>
      <div className="salary-chart-x">
        <span>200</span><span>400</span><span>600</span><span>900+</span>
      </div>
    </>
  );
}

function Donut({ value }) {
  const r = 28, c = 2 * Math.PI * r;
  const off = c * (1 - value);
  return (
    <svg width="76" height="76" viewBox="0 0 76 76">
      <circle cx="38" cy="38" r={r} fill="none" stroke="var(--c-chart-soft)" strokeWidth="6"/>
      <circle cx="38" cy="38" r={r} fill="none" stroke="var(--c-accent)" strokeWidth="6"
        strokeDasharray={c} strokeDashoffset={off}
        transform="rotate(-90 38 38)" strokeLinecap="butt"/>
    </svg>
  );
}

function LearnPlan({ courses, profile }) {
  return (
    <div>
      <div style={{display:'grid', gap: 12}}>
        {courses.map((c, i) => (
          <div className="course" key={c.id}>
            <div>
              <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:6}}>
                <span className="mono" style={{fontSize:11, color:'var(--c-ink-3)'}}>0{i+1}</span>
                <span className="course-tag">{c.priority} приоритет</span>
              </div>
              <div className="course-title">{c.title}</div>
              <div className="course-meta">{c.provider} · {c.duration} · {c.level} · закрывает <b style={{color:'var(--c-ink-2)'}}>{c.skill}</b></div>
              <div style={{marginTop:10, display:'flex', alignItems:'center', gap:10}}>
                <div style={{flex:1, height:3, background:'var(--c-chart-soft)', position:'relative'}}>
                  <i style={{position:'absolute', inset:0, width: ((1-c.gap)*100)+'%', background:'var(--c-accent)'}}/>
                </div>
                <span className="mono" style={{fontSize:11, color:'var(--c-ink-3)'}}>покрытие +{Math.round((1-c.gap)*100)}%</span>
              </div>
            </div>
            <div style={{textAlign:'right'}}>
              <div className="serif" style={{fontSize:22, fontWeight:500}}>{c.price}</div>
              <a className="btn small ghost" style={{marginTop:10, display:'inline-block', textDecoration:'none'}}
                 href={c.url} target="_blank" rel="noopener noreferrer">К курсу →</a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TrajectoryLadder({ steps }) {
  return (
    <div className="ladder">
      <div className="ladder-intro">
        <div className="eyebrow">Карьерная лестница · финансы</div>
        <h3 className="serif" style={{fontSize:24, fontWeight:500, margin:'6px 0 4px'}}>
          От Junior до CFO — путь вашей роли
        </h3>
        <div className="muted" style={{fontSize:13, maxWidth:540}}>
          Каждый этап — реальная позиция, вилка по рынку и срок до перехода.
          Текущая ступень подсвечена золотом.
        </div>
      </div>
      <ol className="ladder-list">
        {steps.map((s, i) => (
          <li key={i} className={"ladder-step " + s.status}>
            <div className="ladder-rail">
              <div className="ladder-dot"></div>
              {i < steps.length - 1 && <div className="ladder-line"></div>}
            </div>
            <div className="ladder-card">
              <div className="ladder-meta">
                <span className="mono">{String(i+1).padStart(2,"0")}</span>
                <span className="ladder-years">{s.years} лет</span>
                {s.status === "current" && <span className="ladder-tag now">вы здесь</span>}
                {s.status === "next" && <span className="ladder-tag next">следующий шаг</span>}
                {s.status === "past" && <span className="ladder-tag past">пройдено</span>}
                {s.status === "future" && <span className="ladder-tag future">горизонт</span>}
              </div>
              <div className="ladder-title">{s.title}</div>
              <div className="ladder-salary">
                <span className="serif">{s.salaryFrom}–{s.salaryTo}</span>
                <small>тыс. ₽ / мес</small>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function AdjacentIndustries({ items }) {
  return (
    <div className="adj">
      <div className="ladder-intro" style={{marginBottom:18}}>
        <div className="eyebrow">Смежные отрасли</div>
        <h3 className="serif" style={{fontSize:24, fontWeight:500, margin:'6px 0 4px'}}>
          Куда ещё можно перейти со схожим бэкграундом
        </h3>
        <div className="muted" style={{fontSize:13, maxWidth:560}}>
          Шесть направлений, в которых ваш профиль конкурентен. Совпадение
          навыков, типичные роли и ожидаемая разница в компенсации.
        </div>
      </div>
      <div className="adj-grid">
        {items.map((a, i) => (
          <div className="adj-card" key={i}>
            <div className="adj-head">
              <div>
                <div className="eyebrow">Сектор {String(i+1).padStart(2,"0")}</div>
                <div className="adj-title serif">{a.sector}</div>
              </div>
              <div className="adj-overlap">
                <div className="adj-num">{a.overlap}<small>%</small></div>
                <div className="muted" style={{fontSize:11}}>совпадение</div>
              </div>
            </div>
            <div className="adj-why">{a.why}</div>
            <div className="adj-roles">
              {a.roles.map(r => <span key={r} className="vac-skill">{r}</span>)}
            </div>
            <div className="adj-foot">
              <div className="mono" style={{fontSize:12, color:'var(--c-ink-3)'}}>Δ компенсации</div>
              <div className="serif" style={{fontSize:20, fontWeight:500, color:'var(--c-accent)'}}>{a.salaryShift}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GrowthList({ items, onOpen }) {
  return (
    <div style={{display:'grid', gap:14}}>
      {items.map(v => (
        <div key={v.id} className="course" style={{gridTemplateColumns:'60px 1fr auto'}}>
          <div className="vac-logo" style={{width:60, height:60, fontSize:22}}>{v.logo}</div>
          <div>
            <div className="course-title" style={{fontSize:22}}>{v.title}</div>
            <div className="course-meta">{v.company}</div>
            <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:10}}>
              {v.missing.map(m => (
                <span key={m} className="vac-skill" style={{borderColor:'var(--c-accent)', color:'var(--c-accent)'}}>{m}</span>
              ))}
            </div>
          </div>
          <div style={{textAlign:'right'}}>
            <div className="serif" style={{fontSize:20, fontWeight:500}}>{v.salaryFrom}–{v.salaryTo}<small style={{fontSize:12, color:'var(--c-ink-3)', fontFamily:'var(--f-body)', marginLeft:4}}>тыс. ₽</small></div>
            <div className="vac-match" style={{marginTop:4}}>~{v.gapMonths} мес.</div>
            <button className="btn small accent" style={{marginTop:10}} onClick={() => onOpen(v)}>Открыть</button>
          </div>
        </div>
      ))}
    </div>
  );
}

function VacancyDrawer({ vac, onClose, profile }) {
  const profSkills = (profile.skills || []).map(s => s.name.toLowerCase());
  const matched = (vac.skills || []).filter(s => profSkills.some(ps => ps.includes(s.toLowerCase()) || s.toLowerCase().includes(ps)));
  const missing = (vac.skills || []).filter(s => !matched.includes(s));
  return (
    <>
      <div className="drawer-bg" onClick={onClose}></div>
      <div className="drawer">
        <div className="drawer-head">
          <div>
            <div className="eyebrow">{vac.sector || "Финансовый сектор"}</div>
            <h2>{vac.title}</h2>
            <div className="company-row">
              <div className="vac-logo" style={{width:36, height:36, fontSize:14}}>{vac.logo}</div>
              <div>
                <div style={{fontWeight:600}}>{vac.company}</div>
                <div className="muted" style={{fontSize:12}}>{vac.city || "Москва"} · {vac.remote || "Гибрид"}</div>
              </div>
            </div>
          </div>
          <button className="drawer-close" onClick={onClose}>✕</button>
        </div>

        <div className="drawer-body">
          <div className="kv-list">
            <div className="kv"><div className="l">Вилка</div><div className="v">{(vac.salaryFrom||'')}–{(vac.salaryTo||'')} <small style={{fontSize:12, color:'var(--c-ink-3)', fontFamily:'var(--f-body)'}}>тыс. ₽</small></div></div>
            <div className="kv"><div className="l">Match</div><div className="v" style={{color:'var(--c-accent)'}}>{vac.match||78}%</div></div>
            <div className="kv"><div className="l">Размещено</div><div className="v">{vac.posted || "2 дня"}</div></div>
            <div className="kv"><div className="l">Тип</div><div className="v">{vac.remote || "Гибрид"}</div></div>
          </div>

          <div className="section-h">Совпадение навыков <span className="mono muted">{matched.length}/{(vac.skills||[]).length}</span></div>
          {(vac.skills||[]).map(s => (
            <div key={s} className="skillrow">
              <div className="name">{s}</div>
              <div className="bar"><i style={{width: matched.includes(s)?'100%':'30%', background: matched.includes(s)?'var(--c-pos)':'var(--c-accent)'}}/></div>
              <div className="num">{matched.includes(s)?"есть":"gap"}</div>
            </div>
          ))}

          {vac.missing && (
            <>
              <div className="section-h">Что прокачать до этой роли</div>
              <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
                {vac.missing.map(m => <span key={m} className="vac-skill" style={{padding:'6px 12px', fontSize:12}}>{m}</span>)}
              </div>
            </>
          )}

          <div className="section-h">Описание</div>
          <p style={{fontSize:14, lineHeight:1.7, color:'var(--c-ink-2)'}}>
            {vac.company} ищет {vac.title.toLowerCase()} в команду {vac.sector?.toLowerCase() || 'финансов'}.
            Роль предполагает участие в формировании инвестиционных решений, построении финансовых
            моделей и взаимодействии с senior-стейкхолдерами. Команда из {Math.round(8 + (vac.match||50)/10)} человек,
            гибридный формат, расширенный соцпакет и опционная программа.
          </p>

          <div style={{display:'flex', gap:10, marginTop:24}}>
            <a className="btn accent" style={{flex:1, textAlign:'center', textDecoration:'none'}}
               href={vac.url || `https://hh.ru/search/vacancy?text=${encodeURIComponent(vac.title)}`}
               target="_blank" rel="noopener noreferrer">Откликнуться через hh.ru ↗</a>
            <button className="btn ghost">Сохранить</button>
          </div>
        </div>
      </div>
    </>
  );
}

window.Results = Results;
