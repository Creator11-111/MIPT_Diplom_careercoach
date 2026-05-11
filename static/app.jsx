/* global React, ReactDOM, Landing, Interview, Results */
const { useState: useStateApp, useEffect: useEffectApp } = React;

function App() {
  const [screen, setScreen] = useStateApp("landing"); // landing | interview | results
  const [theme, setTheme] = useStateApp("light");
  const [palette, setPalette] = useStateApp("meridian");

  // Сохраняем настройки темы
  useEffectApp(() => {
    const savedTheme = localStorage.getItem("coach_theme") || "light";
    const savedPalette = localStorage.getItem("coach_palette") || "meridian";
    setTheme(savedTheme);
    setPalette(savedPalette);
  }, []);

  useEffectApp(() => {
    document.documentElement.setAttribute("data-palette", palette);
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("coach_theme", theme);
    localStorage.setItem("coach_palette", palette);
  }, [palette, theme]);

  const tweak = {
    palette,
    theme,
    briefingNo: "0142",
    briefingYear: "MMXXVI"
  };

  const toggleTheme = () => {
    setTheme(t => t === "light" ? "dark" : "light");
  };

  const cyclePalette = () => {
    const palettes = ["meridian", "emerald", "onyx"];
    const idx = palettes.indexOf(palette);
    setPalette(palettes[(idx + 1) % palettes.length]);
  };

  const screens = {
    landing: <Landing onStart={() => setScreen("interview")} tweak={tweak} />,
    interview: <Interview onDone={() => setScreen("results")} onBack={() => setScreen("landing")} />,
    results: <Results onRestart={() => setScreen("interview")} tweak={tweak} />,
  };

  return (
    <div className="app" data-screen-label={
      screen === "landing" ? "01 Landing" :
      screen === "interview" ? "02 Interview" : "03 Results map"
    }>
      {screens[screen]}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
