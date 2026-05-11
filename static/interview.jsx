/* global React */
const { useState: useStateIv, useEffect: useEffectIv, useRef: useRefIv } = React;

function formatAnswer(q, value) {
  if (value === undefined || value === null) return "";
  if (q.kind === "multi") return Array.isArray(value) ? value.join(", ") : String(value);
  if (q.kind === "range") return `${value} ${q.unit || ""}`.trim();
  if (q.kind === "choice") return String(value);
  return String(value).trim();
}

function Interview({ onDone, onBack }) {
  const D = window.COACH_DATA;
  const Qs = D.interview;
  const [idx, setIdx] = useStateIv(0);
  const [answers, setAnswers] = useStateIv({});
  const [loading, setLoading] = useStateIv(false);
  const [error, setError] = useStateIv(null);
  const q = Qs[idx];
  const total = Qs.length;
  const progress = ((idx) / total) * 100;
  const inputRef = useRefIv(null);

  useEffectIv(() => {
    if (inputRef.current && q.kind === "text") inputRef.current.focus();
  }, [idx]);

  function setAns(v) { setAnswers(a => ({ ...a, [q.id]: v })); }
  function toggleMulti(opt) {
    const cur = answers[q.id] || [];
    if (cur.includes(opt)) setAns(cur.filter(x => x !== opt));
    else setAns([...cur, opt]);
  }

  async function submitInterview() {
    setLoading(true);
    setError(null);
    
    try {
      // 1. Создаём сессию
      const sessionRes = await fetch('/v1/sessions', { method: 'POST' });
      if (!sessionRes.ok) throw new Error('Не удалось создать сессию');
      const sessionData = await sessionRes.json();
      const sid = sessionData.session_id;
      
      // 2. Отправляем все ответы как сообщения в чат
      for (const question of Qs) {
        const answer = formatAnswer(question, answers[question.id]);
        if (answer) {
          const chatRes = await fetch(`/v1/chat/${sid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: `[${question.id}] ${question.prompt}: ${answer}` })
          });
          if (!chatRes.ok) {
            console.warn(`Ошибка при отправке ответа на вопрос ${question.id}`);
          }
        }
      }
      
      // 3. Получаем профиль
      const profileRes = await fetch(`/v1/profile/${sid}`);
      const profileData = profileRes.ok ? await profileRes.json() : { profile: {} };
      
      // 4. Получаем вакансии
      const matchRes = await fetch(`/v1/match/vacancies/by-session/${sid}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const matchData = matchRes.ok ? await matchRes.json() : { result: [] };
      
      // 5. Получаем курсы и план развития
      const growthRes = await fetch('/v1/match/career-development', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid })
      });
      const growthData = growthRes.ok ? await growthRes.json() : { courses: [], next_roles: [] };
      
      // 6. Обновляем COACH_DATA с реальными данными (смержим с моками для недостающих полей)
      const mockData = window.COACH_DATA;
      
      // Преобразуем данные из API в формат фронта
      const apiVacancies = (matchData.result || []).map((v, i) => ({
        id: v.idx || i + 1,
        title: v.title || "Вакансия",
        company: v.company || "Компания",
        logo: (v.company || "").substring(0, 2).toUpperCase() || "XX",
        sector: detectSector(v.title, v.description),
        city: v.location || "Москва",
        remote: v.job_type || "Гибрид",
        salaryFrom: parseSalary(v.salary).min,
        salaryTo: parseSalary(v.salary).max,
        match: Math.round(90 - i * 2),
        skills: (v.key_skills || "").split(",").map(s => s.trim()).filter(Boolean).slice(0, 6),
        posted: "недавно",
        url: v.hh_url || `https://hh.ru/search/vacancy?text=${encodeURIComponent(v.title)}`,
        description: v.description || ""
      }));
      
      // Создаём профиль из ответов и API
      const userProfile = {
        name: answers.name || profileData.profile?.name || "Пользователь",
        role: answers.current_role || profileData.profile?.professional_context?.professional_role || "Финансовый специалист",
        seniority: detectSeniority(answers.experience),
        field: answers.field || profileData.profile?.professional_context?.professional_field || "Финансы",
        years: parseYears(answers.experience),
        skills: buildSkillsFromAnswers(answers),
        goal: answers.goal || profileData.profile?.goals?.desired_role || "Карьерный рост",
        location: `${answers.city_now || "Москва"} · ${answers.work_format || "Гибрид"}`,
        salaryCurrent: answers.salary_current || 380,
        salaryTarget: answers.salary_target || 750,
        certifications: answers.certifications || [],
        languages: answers.languages || []
      };
      
      window.COACH_DATA = {
        ...mockData,
        profile: userProfile,
        vacancies: apiVacancies.length > 0 ? apiVacancies : mockData.vacancies,
        courses: growthData.courses?.length > 0 ? transformCourses(growthData.courses) : mockData.courses,
        growth: growthData.next_roles?.length > 0 ? transformGrowth(growthData.next_roles) : mockData.growth
      };
      
      onDone(answers);
      
    } catch (err) {
      console.error('Ошибка при отправке интервью:', err);
      setError(err.message || 'Произошла ошибка. Попробуйте ещё раз.');
      
      // Fallback: используем мок-данные с профилем из ответов
      const mockData = window.COACH_DATA;
      window.COACH_DATA = {
        ...mockData,
        profile: {
          ...mockData.profile,
          name: answers.name || mockData.profile.name,
          role: answers.current_role || mockData.profile.role,
          field: answers.field || mockData.profile.field,
          goal: answers.goal || mockData.profile.goal,
          salaryCurrent: answers.salary_current || mockData.profile.salaryCurrent,
          salaryTarget: answers.salary_target || mockData.profile.salaryTarget
        }
      };
      onDone(answers);
    } finally {
      setLoading(false);
    }
  }

  function next() {
    if (idx < total - 1) {
      setIdx(idx + 1);
    } else {
      submitInterview();
    }
  }
  
  function prev() { if (idx > 0) setIdx(idx - 1); }

  function onKey(e) {
    if (loading) return;
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); next(); }
    if (e.key === "Escape") prev();
  }

  const canNext = (() => {
    const v = answers[q.id];
    if (q.kind === "multi") return (v || []).length >= 1;
    if (q.kind === "range") return v !== undefined || q.defaultValue !== undefined;
    return v && String(v).trim().length > 0;
  })();

  return (
    <div className="iv-shell">
      <div className="iv-progress"><span style={{ width: progress + "%" }} /></div>
      <div className="iv-top">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div className="brand-name">Méridien<small>Интервью</small></div>
        </div>
        <div className="iv-step-label">{String(idx+1).padStart(2,"0")} / {String(total).padStart(2,"0")}</div>
        <button className="btn ghost small" onClick={onBack} disabled={loading}>Выйти</button>
      </div>

      <div className="iv-body" onKeyDown={onKey} tabIndex={-1}>
        {loading ? (
          <div className="iv-card">
            <div className="iv-q-num">Обработка</div>
            <h2 className="iv-question">Анализируем ваш профиль...</h2>
            <div className="iv-hint">Подбираем вакансии и составляем план развития. Это займёт несколько секунд.</div>
            <div style={{ marginTop: 32, display: 'flex', justifyContent: 'center' }}>
              <div style={{ 
                width: 48, height: 48, 
                border: '3px solid var(--c-line)', 
                borderTopColor: 'var(--c-accent)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
            </div>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </div>
        ) : (
          <div className="iv-card" key={idx}>
            <div className="iv-q-num">Вопрос {idx+1}</div>
            <h2 className="iv-question">{q.prompt}</h2>
            {q.hint && <div className="iv-hint">{q.hint}</div>}
            {error && <div style={{ color: 'var(--c-neg)', marginBottom: 16 }}>{error}</div>}

            {q.kind === "text" && (
              <input
                ref={inputRef}
                className="iv-input"
                type="text"
                placeholder={q.placeholder || "Напишите здесь..."}
                value={answers[q.id] || ""}
                onChange={e => setAns(e.target.value)}
                onKeyDown={onKey}
              />
            )}

            {q.kind === "choice" && (
              <div className="iv-choices">
                {q.options.map((opt, i) => (
                  <button
                    key={opt}
                    className={"iv-choice" + (answers[q.id] === opt ? " selected" : "")}
                    onClick={() => { setAns(opt); setTimeout(next, 220); }}
                  >
                    <span className="key">{String.fromCharCode(65 + i)}</span>
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {q.kind === "multi" && (
              <div className="iv-multi">
                {q.options.map(opt => (
                  <button
                    key={opt}
                    className={"iv-chip" + ((answers[q.id]||[]).includes(opt) ? " selected" : "")}
                    onClick={() => toggleMulti(opt)}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {q.kind === "range" && (
              <div className="iv-range">
                <div className="iv-range-display">
                  {answers[q.id] || q.defaultValue}
                  <small>{q.unit}</small>
                </div>
                <input
                  type="range"
                  min={q.min} max={q.max} step={q.step}
                  value={answers[q.id] || q.defaultValue}
                  onChange={e => setAns(Number(e.target.value))}
                />
                <div className="iv-range-bounds">
                  <span>{q.min} {q.unit}</span>
                  <span>{q.max}+ {q.unit}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="iv-foot">
        <div className="hint">
          <kbd>Enter</kbd> дальше&nbsp;&nbsp;·&nbsp;&nbsp;<kbd>Esc</kbd> назад
        </div>
        <div style={{display:'flex', gap: 10}}>
          {idx > 0 && <button className="btn ghost small" onClick={prev} disabled={loading}>Назад</button>}
          <button className="btn accent small" onClick={next} disabled={!canNext || loading}>
            {idx === total - 1 ? "Сформировать карту →" : "Дальше →"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Вспомогательные функции
function detectSector(title, description) {
  const text = `${title || ""} ${description || ""}`.toLowerCase();
  if (text.includes("инвестиц") || text.includes("invest")) return "Investment Banking";
  if (text.includes("asset") || text.includes("управлен") && text.includes("актив")) return "Asset Management";
  if (text.includes("банк") || text.includes("bank")) return "Banking";
  if (text.includes("аудит") || text.includes("audit")) return "Audit";
  if (text.includes("fintech") || text.includes("финтех")) return "Fintech";
  if (text.includes("tech") || text.includes("it") || text.includes("яндекс") || text.includes("ozon")) return "Tech";
  return "Corporate";
}

function parseSalary(salaryStr) {
  if (!salaryStr) return { min: 300, max: 500 };
  const numbers = salaryStr.match(/\d+/g);
  if (!numbers) return { min: 300, max: 500 };
  const nums = numbers.map(n => parseInt(n, 10));
  // Если числа большие (>10000), это рубли, делим на 1000
  const normalized = nums.map(n => n > 10000 ? Math.round(n / 1000) : n);
  return {
    min: Math.min(...normalized),
    max: Math.max(...normalized)
  };
}

function detectSeniority(experience) {
  if (!experience) return "Middle";
  const exp = experience.toLowerCase();
  if (exp.includes("до 1") || exp.includes("1 год")) return "Junior";
  if (exp.includes("1–3") || exp.includes("3–5")) return "Middle";
  if (exp.includes("5–8") || exp.includes("8–12")) return "Senior";
  if (exp.includes("12–18") || exp.includes("18+")) return "Lead";
  return "Middle";
}

function parseYears(experience) {
  if (!experience) return 5;
  const match = experience.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : 5;
}

function buildSkillsFromAnswers(answers) {
  const skills = answers.skills || [];
  const software = answers.software || [];
  const allSkills = [...skills, ...software].slice(0, 8);
  return allSkills.map((name, i) => ({
    name,
    level: Math.max(0.4, 0.95 - i * 0.08)
  }));
}

function transformCourses(apiCourses) {
  return apiCourses.map((c, i) => ({
    id: c.idx || i + 1,
    title: c.name || "Курс",
    provider: c.provider || "Online",
    duration: c.duration || "4 нед.",
    price: "—",
    priority: i < 2 ? "Высокий" : "Средний",
    skill: c.skills || "Навыки",
    level: c.level || "Intermediate",
    gap: 0.35 + i * 0.1,
    url: c.url || "#"
  }));
}

function transformGrowth(apiRoles) {
  return apiRoles.map((r, i) => ({
    id: 200 + i,
    title: r.title || "Позиция роста",
    company: r.company || "—",
    logo: (r.company || "XX").substring(0, 2).toUpperCase(),
    salaryFrom: parseSalary(r.salary).min,
    salaryTo: parseSalary(r.salary).max,
    gapMonths: 12 + i * 6,
    missing: r.missing_skills || ["Развитие навыков"],
    match: 75 - i * 5,
    url: r.url || "#"
  }));
}

window.Interview = Interview;
